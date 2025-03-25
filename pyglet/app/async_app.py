import asyncio
import sys
from typing import Any, Callable, TYPE_CHECKING
from pyglet import app, clock, event

if TYPE_CHECKING:
    from pyglet.event import EventDispatcher

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

class AsyncEventLoop(event.EventDispatcher):
    """Asyncio-based event loop for Pyglet."""

    def __init__(self) -> None:
        self._has_exit_event = asyncio.Event()
        self.clock = clock.get_default()
        self.is_running = False
        self._interval = None

    async def run(self, interval: float | None = 1/60) -> None:
        try:
            """Begin processing events asynchronously."""
            self._interval = interval

            # if interval is None:
            #     pass  # User will manually schedule updates
            # elif interval == 0:
            #     self.clock.schedule(self._redraw_windows)
            # else:
            #     self.clock.schedule_interval(self._redraw_windows, interval)

            self._has_exit_event.clear()
            platform_event_loop = app.platform_event_loop

            await platform_event_loop.start()
            self.dispatch_event('on_enter')
            self.is_running = True

            while not self._has_exit_event.is_set():
                timeout = self.idle()
                await platform_event_loop.step(timeout)
                if timeout is not None:
                    await asyncio.sleep(timeout)
                else:
                    await asyncio.sleep(0.001)

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

    async def on_window_close(self, window: "BaseWindow") -> None:
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

    async def post_event(self, dispatcher: "EventDispatcher", event: str, *args: Any) -> None:
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
