# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

import sys
import queue
import threading

from pyglet import app
from pyglet import clock
from pyglet import event

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


class PlatformEventLoop:
    """ Abstract class, implementation depends on platform.

    .. versionadded:: 1.2
    """
    def __init__(self):
        self._event_queue = queue.Queue()
        self._is_running = threading.Event()
        self._is_running.clear()

    def is_running(self):
        """Return True if the event loop is currently processing, or False
        if it is blocked or not activated.

        :rtype: bool
        """
        return self._is_running.is_set()

    def post_event(self, dispatcher, event, *args):
        """Post an event into the main application thread.

        The event is queued internally until the :py:meth:`run` method's thread
        is able to dispatch the event.  This method can be safely called
        from any thread.

        If the method is called from the :py:meth:`run` method's thread (for
        example, from within an event handler), the event may be dispatched
        within the same runloop iteration or the next one; the choice is
        nondeterministic.

        :Parameters:
            `dispatcher` : EventDispatcher
                Dispatcher to process the event.
            `event` : str
                Event name.
            `args` : sequence
                Arguments to pass to the event handlers.

        """
        self._event_queue.put((dispatcher, event, args))
        self.notify()

    def dispatch_posted_events(self):
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

    def notify(self):
        """Notify the event loop that something needs processing.

        If the event loop is blocked, it will unblock and perform an iteration
        immediately.  If the event loop is running, another iteration is
        scheduled for immediate execution afterwards.
        """
        raise NotImplementedError('abstract')

    def start(self):
        pass

    def step(self, timeout=None):
        raise NotImplementedError('abstract')

    def set_timer(self, func, interval):
        pass

    def stop(self):
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

    def __init__(self):
        self._has_exit_condition = threading.Condition()
        self.clock = clock.get_default()
        self.is_running = False

    @staticmethod
    def _redraw_windows(dt):
        # Redraw all windows
        for window in app.windows:
            window.switch_to()
            window.dispatch_event('on_draw')
            window.dispatch_event('on_refresh', dt)
            window.flip()

    def run(self, interval=1/60):
        """Begin processing events, scheduled functions and window updates.

        This method returns when :py:attr:`has_exit` is set to True.

        Developers are discouraged from overriding this method, as the
        implementation is platform-specific.
        """
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

    def enter_blocking(self):
        """Called by pyglet internal processes when the operating system
        is about to block due to a user interaction.  For example, this
        is common when the user begins resizing or moving a window.

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
    def exit_blocking():
        """Called by pyglet internal processes when the blocking operation
        completes.  See :py:meth:`enter_blocking`.
        """
        app.platform_event_loop.set_timer(None, None)

    def _blocking_timer(self):
        timeout = self.idle()
        app.platform_event_loop.set_timer(self._blocking_timer, timeout)

    def idle(self):
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

        :rtype: float
        :return: The number of seconds before the idle method should
            be called again, or `None` to block for user input.
        """
        dt = self.clock.update_time()
        self.clock.call_scheduled_functions(dt)

        # Update timout
        return self.clock.get_sleep_time(True)

    @property
    def has_exit(self):
        """Flag indicating if the event loop will exit in
        the next iteration.  When set, all waiting threads are interrupted (see
        :py:meth:`sleep`).
        
        Thread-safe since pyglet 1.2.
    
        :see: `exit`
        :type: bool
        """
        self._has_exit_condition.acquire()
        result = self._has_exit
        self._has_exit_condition.release()
        return result

    @has_exit.setter
    def has_exit(self, value):
        self._has_exit_condition.acquire()
        self._has_exit = value
        self._has_exit_condition.notify()
        self._has_exit_condition.release()

    def exit(self):
        """Safely exit the event loop at the end of the current iteration.

        This method is a thread-safe equivalent for setting
        :py:attr:`has_exit` to ``True``.  All waiting threads will be
        interrupted (see :py:meth:`sleep`).
        """
        self.has_exit = True
        app.platform_event_loop.notify()

    def sleep(self, timeout):
        """Wait for some amount of time, or until the :py:attr:`has_exit` flag
        is set or :py:meth:`exit` is called.

        This method is thread-safe.

        :Parameters:
            `timeout` : float
                Time to wait, in seconds.

        .. versionadded:: 1.2

        :rtype: bool
        :return: ``True`` if the `has_exit` flag is set, otherwise ``False``.
        """
        self._has_exit_condition.acquire()
        self._has_exit_condition.wait(timeout)
        result = self._has_exit
        self._has_exit_condition.release()
        return result

    def on_window_close(self, window):
        """Default window close handler."""
        if len(app.windows) == 0:
            self.exit()

    if _is_pyglet_doc_run:
        def on_window_close(self, window):
            """A window was closed.

            This event is dispatched when a window is closed.  It is not
            dispatched if the window's close button was pressed but the
            window did not close.

            The default handler calls :py:meth:`exit` if no more windows are
            open.  You can override this handler to base your application exit
            on some other policy.

            :event:
            """

        def on_enter(self):
            """The event loop is about to begin.

            This is dispatched when the event loop is prepared to enter
            the main run loop, and represents the last chance for an
            application to initialise itself.

            :event:
            """

        def on_exit(self):
            """The event loop is about to exit.

            After dispatching this event, the :py:meth:`run` method returns (the
            application may not actually exit if you have more code
            following the :py:meth:`run` invocation).

            :event:
            """


EventLoop.register_event_type('on_window_close')
EventLoop.register_event_type('on_enter')
EventLoop.register_event_type('on_exit')
