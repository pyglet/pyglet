from __future__ import annotations

import queue
import sys
import threading
from typing import TYPE_CHECKING, Any, Callable

from pyglet import app, clock, event

if TYPE_CHECKING:
    from pyglet.event import EventDispatcher
    from pyglet.window import BaseWindow

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


class PlatformEventLoop:
    """Abstract class, implementation depends on platform.

    .. versionadded:: 1.2
    """
    def __init__(self) -> None:  # noqa: D107
        self._event_queue = queue.Queue()
        self._is_running = threading.Event()

    def is_running(self) -> bool:
        """If the event loop is currently processing.

        ``True`` if running, or ``False`` if it is blocked or not activated.
        """
        return self._is_running.is_set()

    def post_event(self, dispatcher: EventDispatcher, event: str, *args: Any) -> None:
        """Post an event into the main application thread.

        The event is queued internally until the :py:meth:`run` method's thread
        is able to dispatch the event.  This method can be safely called
        from any thread.

        If the method is called from the :py:meth:`run` method's thread (for
        example, from within an event handler), the event may be dispatched
        within the same runloop iteration or the next one; the choice is
        nondeterministic.
        """
        self._event_queue.put((dispatcher, event, args))
        self.notify()

    def dispatch_posted_events(self) -> None:
        """Immediately dispatch all pending events.

        Normally this is called automatically by the runloop iteration.
        """
        while True:
            try:
                dispatcher, evnt, args = self._event_queue.get(False)
                dispatcher.dispatch_event(evnt, *args)
            except queue.Empty:
                break
            except ReferenceError:
                # weakly-referenced object no longer exists
                pass

    def notify(self) -> None:
        """Notify the event loop that something needs processing.

        If the event loop is blocked, it will unblock and perform an iteration
        immediately.  If the event loop is running, another iteration is
        scheduled for immediate execution afterward.
        """
        raise NotImplementedError('abstract')

    def start(self) -> None:
        pass

    def step(self, timeout: None | float = None) -> None:
        raise NotImplementedError('abstract')

    def set_timer(self, func: Callable, interval: float) -> None:
        pass

    def stop(self) -> None:
        pass


class EventLoop(event.EventDispatcher):
    """The main run loop of the application.

    Calling `run` begins the application event loop, which processes
    operating system events, calls :py:func:`pyglet.clock.tick` to call
    scheduled functions and calls :py:meth:`pyglet.window.Window.on_draw` and
    :py:meth:`pyglet.window.Window.flip` to update window contents.

    Applications can subclass :py:class:`EventLoop` and override certain methods
    to integrate another framework's run loop, or to customise processing
    in some other way.  You should not in general override :py:meth:`run`, as
    this method contains platform-specific code that ensures the application
    remains responsive to the user while keeping CPU usage to a minimum.
    """

    _has_exit_condition = None
    _has_exit = False

    def __init__(self) -> None:  # noqa: D107
        self._has_exit_condition = threading.Condition()
        self.clock = clock.get_default()
        self.is_running = False
        self._interval = None

    @staticmethod
    def _redraw_windows(dt: float) -> None:
        # Redraw all windows
        for window in app.windows:
            window.draw(dt)

    def run(self, interval: float | None = 1/60) -> None:
        """Begin processing events, scheduled functions and window updates.

        This method enters into the main event loop and, if the ``interval``
        argument is not changed, schedules calling the :py:meth:`pyglet.window.Window.draw`
        method. You can change the ``interval`` argument to suit your needs.

        Args:
            interval:
                Windows redraw interval, in seconds (framerate).
                If ``interval == 0``, windows will redraw as fast as possible.
                This can saturate a CPU core, so do not do this unless GPU bound.
                If ``interval is None``, pyglet will not schedule calls to the
                :py:meth:`pyglet.window.Window.draw` method. Users must schedule
                this themselves for each Window (or call it on-demand). This allows
                setting a custom framerate per window, or changing framerate during
                runtime (see example in the documentation).

        This method returns when :py:attr:`has_exit` is set to True. IE: when
        :py:meth:`exit` is called.

        Developers are discouraged from overriding the ``run`` method, as the
        implementation is platform-specific.
        """
        self._interval = interval
        if interval is None:
            # User will schedule Window.draw manually
            pass
        elif interval == 0:
            self.clock.schedule(self._redraw_windows)
        else:
            self.clock.schedule_interval(self._redraw_windows, interval)

        self.has_exit = False

        from pyglet.window import Window
        Window._enable_event_queue = False

        # Dispatch pending events
        for window in app.windows:
            window.switch_to()
            window.dispatch_pending_events()

        platform_event_loop = app.platform_event_loop
        platform_event_loop.start()
        self.dispatch_event('on_enter')
        self.is_running = True

        while not self.has_exit:
            timeout = self.idle()
            platform_event_loop.step(timeout)

        self.is_running = False
        self.dispatch_event('on_exit')
        platform_event_loop.stop()

    def enter_blocking(self) -> None:
        """Called by pyglet internal processes when the operating system is about to block due to a user interaction.

        For example, this is common when the user begins resizing or moving a window.

        This method provides the event loop with an opportunity to set up
        an OS timer on the platform event loop, which will continue to
        be invoked during the blocking operation.

        The default implementation ensures that :py:meth:`idle` continues to be
        called as documented.

        .. versionadded:: 1.2
        """
        timeout = self.idle()
        app.platform_event_loop.set_timer(self._blocking_timer, timeout)

    @staticmethod
    def exit_blocking() -> None:
        """Called by pyglet internal processes when the blocking operation completes.

        :see: :py:meth:`enter_blocking`.
        """
        app.platform_event_loop.set_timer(None, None)

    def _blocking_timer(self) -> None:
        dt = self.clock.update_time()
        self.clock.call_scheduled_functions(dt)
        if self._interval is None:
            self._redraw_windows(dt)

        # Update timout
        timeout = self.clock.get_sleep_time(True)
        app.platform_event_loop.set_timer(self._blocking_timer, timeout)

    def idle(self) -> None | float:
        """Called during each iteration of the event loop.

        The method is called immediately after any window events (i.e., after
        any user input).  The method can return a duration after which
        the idle method will be called again.  The method may be called
        earlier if the user creates more input events.  The method
        can return `None` to only wait for user events.

        For example, return ``1.0`` to have the idle method called every
        second, or immediately after any user events.

        The default implementation dispatches the
        :py:meth:`pyglet.window.Window.on_draw` event for all windows and uses
        :py:func:`pyglet.clock.tick` and :py:func:`pyglet.clock.get_sleep_time`
        on the default clock to determine the return value.

        This method should be overridden by advanced users only.  To have
        code execute at regular intervals, use the
        :py:func:`pyglet.clock.schedule` methods.

        Returns:
            The number of seconds before the idle method should
            be called again, or ``None`` to block for user input.
        """
        dt = self.clock.update_time()
        self.clock.call_scheduled_functions(dt)

        # Update timout
        return self.clock.get_sleep_time(True)

    @property
    def has_exit(self) -> bool:
        """Flag indicating if the event loop will exit in the next iteration.

        When set, all waiting threads are interrupted.

        :see :py:meth:`sleep`:

        Thread-safe since pyglet 1.2.
        """
        self._has_exit_condition.acquire()
        result = self._has_exit
        self._has_exit_condition.release()
        return result

    @has_exit.setter
    def has_exit(self, value: bool) -> None:
        self._has_exit_condition.acquire()
        self._has_exit = value
        self._has_exit_condition.notify()
        self._has_exit_condition.release()

    def exit(self) -> None:
        """Safely exit the event loop at the end of the current iteration.

        This method is a thread-safe equivalent for setting
        :py:attr:`has_exit` to ``True``.  All waiting threads will be
        interrupted (see :py:meth:`sleep`).
        """
        self.has_exit = True
        app.platform_event_loop.notify()

    def sleep(self, timeout: float) -> bool:
        """Wait for some amount of time.

        Waits until the :py:attr:`has_exit` flag is set or :py:meth:`exit` is called.

        This method is thread-safe.

        Args:
            timeout: Time to sleep, in seconds.

        .. versionadded:: 1.2
        """
        self._has_exit_condition.acquire()
        self._has_exit_condition.wait(timeout)
        result = self._has_exit
        self._has_exit_condition.release()
        return result

    def on_window_close(self, window: BaseWindow) -> None:
        """Default window close handler."""
        if len(app.windows) == 0:
            self.exit()

    if _is_pyglet_doc_run:
        # Events

        def on_window_close(self, window: BaseWindow) -> None:
            """A window was closed.

            This event is dispatched when a window is closed.  It is not
            dispatched if the window's close button was pressed but the
            window did not close.

            The default handler calls :py:meth:`exit` if no more windows are
            open.  You can override this handler to base your application exit
            on some other policy.
            """

        def on_enter(self) -> None:
            """The event loop is about to begin.

            This is dispatched when the event loop is prepared to enter
            the main run loop, and represents the last chance for an
            application to initialise itself.
            """

        def on_exit(self) -> None:
            """The event loop is about to exit.

            After dispatching this event, the :py:meth:`run` method returns (the
            application may not actually exit if you have more code
            following the :py:meth:`run` invocation).
            """


EventLoop.register_event_type('on_window_close')
EventLoop.register_event_type('on_enter')
EventLoop.register_event_type('on_exit')
