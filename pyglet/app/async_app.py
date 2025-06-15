from __future__ import annotations

import asyncio
import sys
from typing import Any, Callable, TYPE_CHECKING

import pyglet
from pyglet import app, clock, event

if TYPE_CHECKING:
    from pyglet.event import EventDispatcher
    from pyglet.window import BaseWindow

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run
try:
    from js import requestAnimationFrame, performance
    from pyodide.ffi import create_proxy
except ImportError:
    raise ImportError('Pyodide not available.')


class AsyncEventLoop(event.EventDispatcher):
    """Asyncio-based event loop for Pyglet."""

    def __init__(self) -> None:
        self._has_exit_event = asyncio.Event()
        # Change the default clock to use the javascript performance timer.
        self.clock = clock.Clock(self._get_js_time)
        pyglet.clock.set_default(self.clock)
        self.is_running = False
        self._interval = None
        self._last_ts = 0.0
        self._frame_dt = 0.0

        self._frame_future = None
        self._frame_proxy = create_proxy(self._frame_cb)

    def _get_js_time(self) -> float:
        """Use Javascripts performance.now for the clock accuracy.

        May not be needed, but just to be accurate.
        """
        return performance.now() / 1000

    @staticmethod
    def _redraw_windows(dt: float) -> None:
        # Redraw all windows
        for window in app.windows:
            window.draw(dt)

    def _frame_cb(self, ts: float) -> None:
        """Callback for the requestAnimationFrame."""
        now = ts / 1000.0
        _frame_dt = now - self._last_ts

        self._last_ts = now

        if self._frame_future:
            self._frame_future.set_result(_frame_dt)
            self._frame_future = None

    async def _next_animation_frame(self) -> float:
        self._frame_future = asyncio.Future()
        requestAnimationFrame(self._frame_proxy)
        return await self._frame_future

    async def draw_frame(self) -> None:
        frame_dt = await self._next_animation_frame()
        self._redraw_windows(frame_dt)

    async def run(self, interval: float | None = 1/60) -> None:
        try:
            """Begin processing events asynchronously."""
            self._interval = interval

            self._has_exit_event.clear()
            platform_event_loop = app.platform_event_loop

            await platform_event_loop.start()
            self.dispatch_event('on_enter')
            self.is_running = True

            # Use the browser's requestAnimationFrame for the loop if None is used.
            if self._interval is None:
                while not self._has_exit_event.is_set():
                    await self.draw_frame()
                    self.idle()  # Ticks clock and runs scheduled functions.
                    await platform_event_loop.dispatch_posted_events()
            else:
                _schedule_rate = self._interval / 1000.0

                # Separate draw loop so clock timeout doesn't block rendering if it's slower.
                async def _draw_loop() -> None:
                    while not self._has_exit_event.is_set():
                        await self.draw_frame()

                asyncio.create_task(_draw_loop())  # noqa: RUF006

                while not self._has_exit_event.is_set():
                    timeout = self.idle()
                    await platform_event_loop.dispatch_posted_events()
                    await asyncio.sleep(0 if timeout is None else timeout)

            self.is_running = False
            self.dispatch_event('on_exit')
            await platform_event_loop.stop()
        except Exception as err:
            import traceback
            print("Error in wrapped task", err)
            traceback.print_exc()

    async def enter_blocking(self) -> None:
        """Ensure `idle()` continues to be called during blocking operations."""
        timeout = self.idle()
        await app.platform_event_loop.set_timer(self._blocking_timer, timeout)

    async def exit_blocking(self) -> None:
        """Stop the blocking timer."""
        await app.platform_event_loop.set_timer(None, None)

    async def _blocking_timer(self) -> None:
        """Called to process scheduled events during blocking operations."""
        dt = self.clock.update_time()
        self.clock.call_scheduled_functions(dt)
        if self._interval is None:
            self._redraw_windows(dt)

        timeout = self.clock.get_sleep_time(True)
        await app.platform_event_loop.set_timer(self._blocking_timer, timeout)

    def idle(self) -> float | None:
        """Called each iteration to process events."""
        dt = self.clock.update_time()
        self.clock.call_scheduled_functions(dt)
        return self.clock.get_sleep_time(True)

    async def exit(self) -> None:
        """Exit the event loop asynchronously."""
        self._has_exit_event.set()
        app.platform_event_loop.notify()

    async def sleep(self, timeout: float) -> bool:
        """Pause execution for a given time unless `exit()` is called."""
        try:
            await asyncio.wait_for(self._has_exit_event.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def on_window_close(self, _window: BaseWindow) -> None:
        """Exit when the last window is closed."""
        if len(app.windows) == 0:
            await self.exit()

AsyncEventLoop.register_event_type('on_window_close')
AsyncEventLoop.register_event_type('on_enter')
AsyncEventLoop.register_event_type('on_exit')

class AsyncPlatformEventLoop:
    """An asyncio-based platform event loop."""

    def __init__(self) -> None:
        """Initialize the event loop with an asyncio queue and event."""
        self._event_queue = asyncio.Queue()
        self._is_running = asyncio.Event()

    def is_running(self) -> bool:
        """Check if the event loop is currently processing."""
        return self._is_running.is_set()

    async def post_event(self, dispatcher: EventDispatcher, event: str, *args: Any) -> None:
        """Post an event into the main application thread asynchronously."""
        await self._event_queue.put((dispatcher, event, args))
        self.notify()

    async def dispatch_posted_events(self) -> None:
        """Dispatch all pending events asynchronously."""
        while not self._event_queue.empty():
            try:
                dispatcher, evnt, args = await self._event_queue.get()
                dispatcher.dispatch_event(evnt, *args)
            except asyncio.CancelledError:
                break
            except ReferenceError:
                # weakly-referenced object no longer exists
                pass

    def notify(self) -> None:
        """Trigger an iteration of the asyncio event loop."""
        if self.is_running():
            asyncio.create_task(self.dispatch_posted_events())

    async def start(self) -> None:
        """Start the asyncio-based event loop."""
        self._is_running.set()

    async def step(self, timeout: float | None = None) -> None:
        """Run one iteration of the asyncio event loop with a timeout."""
        try:
            await asyncio.wait_for(self.dispatch_posted_events(), timeout)
        except asyncio.TimeoutError:
            pass

    async def set_timer(self, func: Callable, interval: float) -> None:
        """Schedule a timer function asynchronously."""
        while self.is_running():
            await asyncio.sleep(interval)
            func()

    async def stop(self) -> None:
        """Stop the asyncio-based event loop."""
        self._is_running.clear()
