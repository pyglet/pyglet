"""Asyncio event-loop support for the Emscripten platform."""
from __future__ import annotations

import asyncio
from contextlib import suppress
import sys
from typing import Any, TYPE_CHECKING

import pyglet
from pyglet import app, clock, event
from pyglet.app.base import ClockWindowDrawSource, WindowDrawSource

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyglet.event import EventDispatcher
    from pyglet.window import BaseWindow

try:
    from js import cancelAnimationFrame, requestAnimationFrame, performance
except ImportError as exc:
    raise ImportError('Pyodide not available.') from exc

from pyglet.libs.emscripten.proxies import ProxyRegistry


class _AsyncClock(clock.Clock):
    """Wake the event loop when new clock work is due sooner."""

    def __init__(self, time_function: Callable[[], float], on_schedule: Callable[[float | None], None]) -> None:
        """Bind the clock to the event loop's deadline notification callback."""
        super().__init__(time_function)
        self._schedule_callback = on_schedule

    def _next_interval_deadline(self) -> float:
        if self._schedule_interval_items:
            return self._schedule_interval_items[0].next_ts
        return float('inf')

    def _notify_earlier_deadline(self, previous_deadline: float) -> None:
        deadline = self._next_interval_deadline()
        if deadline < previous_deadline:
            self._schedule_callback(deadline)

    def schedule(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        super().schedule(func, *args, **kwargs)
        self._schedule_callback(None)

    def schedule_once(self, func: Callable, delay: float, *args: Any, **kwargs: Any) -> None:
        previous_deadline = self._next_interval_deadline()
        super().schedule_once(func, delay, *args, **kwargs)
        self._notify_earlier_deadline(previous_deadline)

    def schedule_interval(self, func: Callable, interval: float, *args: Any, **kwargs: Any) -> None:
        previous_deadline = self._next_interval_deadline()
        super().schedule_interval(func, interval, *args, **kwargs)
        self._notify_earlier_deadline(previous_deadline)

    def schedule_interval_fixed_delay(self, func: Callable, interval: float, *args: Any, **kwargs: Any) -> None:
        previous_deadline = self._next_interval_deadline()
        super().schedule_interval_fixed_delay(func, interval, *args, **kwargs)
        self._notify_earlier_deadline(previous_deadline)

    def schedule_interval_soft(self, func: Callable, interval: float, *args: Any, **kwargs: Any) -> None:
        previous_deadline = self._next_interval_deadline()
        super().schedule_interval_soft(func, interval, *args, **kwargs)
        self._notify_earlier_deadline(previous_deadline)


class AsyncEventLoop(event.EventDispatcher):
    """Browser event loop which preserves pyglet's normal clock semantics."""

    def __init__(self) -> None:
        """Create the browser clock and callback state."""
        self._has_exit_event = asyncio.Event()
        self._clock_wait_deadline: float | None = None
        self.clock = _AsyncClock(self._get_js_time, self._on_clock_schedule)
        pyglet.clock.set_default(self.clock)
        self.is_running = False
        self._interval: float | None = None
        self._run_task: asyncio.Task[None] | None = None
        self._window_draw_source: WindowDrawSource | None = None
        self._window_draw_exception: tuple[type[BaseException], BaseException, Any] | None = None

    def _on_clock_schedule(self, next_ts: float | None) -> None:
        """Wake the loop if new work is due before its next wakeup."""
        deadline = self._clock_wait_deadline
        if deadline is not None and (next_ts is None or next_ts < deadline):
            app.platform_event_loop.notify()

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
                # idle finishes before wait() yields, so its timeout includes
                # any work scheduled during that clock tick.
                if timeout is None:
                    self._clock_wait_deadline = float('inf')
                elif timeout > 0:
                    self._clock_wait_deadline = self.clock.time() + timeout
                try:
                    await platform_event_loop.wait(timeout)
                finally:
                    self._clock_wait_deadline = None
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
        # Keep a wakeup sent before the wait(), so the loop can process it now.
        if self._event_queue.empty() and not self._wake_event.is_set():
            if timeout is None:
                await self._wake_event.wait()
            elif timeout > 0:
                # wait_for() uses call_at(); Pyodide rejects its deadline if
                # it expires during timer setup. Keep the delay relative.
                timer = asyncio.get_running_loop().call_later(timeout, self._wake_event.set)
                try:
                    await self._wake_event.wait()
                finally:
                    timer.cancel()
            else:
                await asyncio.sleep(0)
        self._wake_event.clear()

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
