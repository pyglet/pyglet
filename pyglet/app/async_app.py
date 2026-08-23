"""Asyncio event-loop support for the Emscripten platform."""
from __future__ import annotations

import asyncio
from contextlib import suppress
import sys
from typing import Any, Callable, TYPE_CHECKING

import pyglet
from pyglet import app, clock, event
from pyglet.app.base import ClockWindowDrawSource, WindowDrawSource

if TYPE_CHECKING:
    from pyglet.event import EventDispatcher
    from pyglet.window import BaseWindow

try:
    from js import cancelAnimationFrame, requestAnimationFrame, performance
except ImportError as exc:
    raise ImportError('Pyodide not available.') from exc

from pyglet.libs.emscripten.proxies import ProxyRegistry


class AsyncEventLoop(event.EventDispatcher):
    """Browser event loop which preserves pyglet's normal clock semantics."""

    def __init__(self) -> None:
        """Create the browser clock and callback state."""
        self._has_exit_event = asyncio.Event()
        self.clock = clock.Clock(self._get_js_time)
        pyglet.clock.set_default(self.clock)
        self.is_running = False
        self._interval: float | None = None
        self._run_task: asyncio.Task[None] | None = None
        self._window_draw_source: WindowDrawSource | None = None
        self._window_draw_exception: tuple[type[BaseException], BaseException, Any] | None = None

    def _get_js_time(self) -> float:
        """Use Javascripts performance.now for the clock accuracy.

        May not be needed, but just to be accurate.
        """
        return performance.now() / 1000

    def _redraw_windows(self, dt: float) -> None:
        for window in tuple(app.windows):
            self._dispatch_platform_draw(window, dt)

    def _dispatch_platform_draw(self, window: BaseWindow, dt: float) -> None:
        try:
            window.draw(dt)
        except BaseException:  # noqa: BLE001 - JS callbacks cannot unwind Python exceptions.
            self._window_draw_exception = sys.exc_info()
            self.exit()

    def _raise_window_draw_exception(self) -> None:
        if self._window_draw_exception is None:
            return

        _, exception, traceback = self._window_draw_exception
        self._window_draw_exception = None
        raise exception.with_traceback(traceback)

    def _schedule_window_draw(self, interval: float | None) -> None:
        self._interval = interval
        if interval is None:
            return

        draw_source = app.platform_event_loop.create_window_draw_source(self)
        if draw_source is None:
            draw_source = ClockWindowDrawSource(self.clock, self._redraw_windows)

        self._window_draw_source = draw_source
        if not draw_source.start(interval):
            draw_source.stop()
            self._window_draw_source = ClockWindowDrawSource(self.clock, self._redraw_windows)
            self._window_draw_source.start(interval)

    def _unschedule_window_draw(self) -> None:
        if self._window_draw_source is not None:
            self._window_draw_source.stop()
            self._window_draw_source = None

    def run(self, interval: float | None = 1 / 60) -> None:
        """Start processing browser events, scheduled functions, and window draws."""
        if self._run_task is not None and not self._run_task.done():
            raise RuntimeError("The pyglet event loop is already running.")

        task = asyncio.create_task(self._run(interval))
        self._run_task = task

        def clear_task(completed_task: asyncio.Task[None]) -> None:
            if self._run_task is completed_task:
                self._run_task = None

        task.add_done_callback(clear_task)

    async def _run(self, interval: float | None = 1 / 60) -> None:
        """Process pyglet clock callbacks and browser events."""
        if self.is_running:
            raise RuntimeError("The pyglet event loop is already running.")

        self._interval = interval
        self._has_exit_event.clear()
        platform_event_loop = app.platform_event_loop

        try:
            platform_event_loop.start()
            self._schedule_window_draw(interval)
            self.dispatch_event('on_enter')
            self.is_running = True

            while not self._has_exit_event.is_set():
                timeout = self.idle()
                await platform_event_loop.wait(timeout)
                platform_event_loop.dispatch_posted_events()
        finally:
            self.is_running = False
            platform_event_loop.stop()
            self._unschedule_window_draw()
            self.dispatch_event('on_exit')

        self._raise_window_draw_exception()

    def enter_blocking(self) -> None:
        timeout = self.idle()
        app.platform_event_loop.set_timer(self._blocking_timer, timeout)

    def exit_blocking(self) -> None:
        app.platform_event_loop.set_timer(None, None)

    def _blocking_timer(self) -> None:
        dt = self.clock.update_time()
        self.clock.call_scheduled_functions(dt)
        timeout = self.clock.get_sleep_time(True)
        app.platform_event_loop.set_timer(self._blocking_timer, timeout)

    def idle(self) -> float | None:
        dt = self.clock.update_time()
        self.clock.call_scheduled_functions(dt)
        return self.clock.get_sleep_time(True)

    def exit(self) -> None:
        self._has_exit_event.set()
        app.platform_event_loop.notify()

    async def sleep(self, timeout: float) -> bool:
        try:
            await asyncio.wait_for(self._has_exit_event.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def on_window_close(self, _window: BaseWindow) -> None:
        if len(app.windows) == 0:
            self.exit()


AsyncEventLoop.register_event_type('on_window_close')
AsyncEventLoop.register_event_type('on_enter')
AsyncEventLoop.register_event_type('on_exit')


class AsyncPlatformEventLoop:
    """An asyncio-based platform event loop, currently for supporting Pyodide."""

    def __init__(self) -> None:
        """Create the browser event queue and wakeup state."""
        self._event_queue: asyncio.Queue[tuple[EventDispatcher, str, tuple[Any, ...]]] = asyncio.Queue()
        self._is_running = False
        self._wake_event = asyncio.Event()
        self._timer_task: asyncio.Task[None] | None = None

    def is_running(self) -> bool:
        return self._is_running

    def post_event(self, dispatcher: EventDispatcher, event: str, *args: Any) -> None:
        self._event_queue.put_nowait((dispatcher, event, args))
        self.notify()

    def dispatch_posted_events(self) -> None:
        while True:
            try:
                dispatcher, event, args = self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                return
            with suppress(ReferenceError):
                dispatcher.dispatch_event(event, *args)

    def notify(self) -> None:
        self._wake_event.set()

    def start(self) -> None:
        self._is_running = True

    async def wait(self, timeout: float | None) -> None:
        if not self._event_queue.empty():
            return

        self._wake_event.clear()
        if not self._event_queue.empty():
            return

        if timeout is None:
            await self._wake_event.wait()
        elif timeout > 0:
            with suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self._wake_event.wait(), timeout)
        else:
            await asyncio.sleep(0)

    async def step(self, timeout: float | None = None) -> None:
        await self.wait(timeout)
        self.dispatch_posted_events()

    def set_timer(self, func: Callable | None, interval: float | None) -> None:
        if self._timer_task is not None:
            self._timer_task.cancel()
            self._timer_task = None

        if func is None or interval is None or not self.is_running():
            return

        async def timer() -> None:
            while self.is_running():
                await asyncio.sleep(interval)
                if self.is_running():
                    func()

        self._timer_task = asyncio.create_task(timer())

    def create_window_draw_source(self, event_loop: AsyncEventLoop) -> WindowDrawSource:
        return RequestAnimationFrameDrawSource(event_loop)

    def stop(self) -> None:
        self._is_running = False
        self.set_timer(None, None)
        self.notify()


class RequestAnimationFrameDrawSource(WindowDrawSource):
    """Draw browser windows when the browser requests an animation frame."""

    def __init__(self, event_loop: AsyncEventLoop) -> None:
        """Attaches to the browser event loop."""
        self._event_loop = event_loop
        self._last_timestamp: float | None = None
        self._request_id: int | None = None
        self._running = False
        self._callback = None
        self._proxies = ProxyRegistry()

    def start(self, _interval: float) -> bool:
        self._running = True
        self._last_timestamp = None
        if self._callback is None:
            self._callback = self._proxies.create(self._on_animation_frame)
        self._request_next_frame()
        return True

    def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        if self._request_id is not None:
            cancelAnimationFrame(self._request_id)
            self._request_id = None
        self._proxies.destroy()
        self._callback = None

    def _request_next_frame(self) -> None:
        self._request_id = requestAnimationFrame(self._callback)

    def _on_animation_frame(self, timestamp: float) -> None:
        if not self._running:
            return

        now = timestamp / 1000.0
        dt = 0.0 if self._last_timestamp is None else now - self._last_timestamp
        self._last_timestamp = now
        self._request_id = None
        self._event_loop._redraw_windows(dt)  # noqa: SLF001

        if self._running:
            self._request_next_frame()
