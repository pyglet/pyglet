#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import sys
import threading

from pyglet import app
from pyglet import clock
from pyglet import event

_is_epydoc = hasattr(sys, 'is_epydoc') and sys.is_epydoc

class Display(object):
    '''A display device supporting one or more screens.

    :Ivariables:
        `name` : str
            Name of this display, if applicable.
        `x_screen` : int
            The X11 screen number of this display, if applicable.

    :since: pyglet 1.2
    '''
    name = None
    x_screen = None

    def __init__(self, name=None, x_screen=None):
        '''Create a display connection for the given name and screen.

        On X11, `name` is of the form ``"hostname:display"``, where the
        default is usually ``":1"``.  On X11, `x_screen` gives the X screen
        number to use with this display.  A pyglet display can only be used
        with one X screen; open multiple display connections to access
        multiple X screens.  
        
        Note that TwinView, Xinerama, xrandr and other extensions present
        multiple monitors on a single X screen; this is usually the preferred
        mechanism for working with multiple monitors under X11 and allows each
        screen to be accessed through a single pyglet `Display`.

        On platforms other than X11, `name` and `x_screen` are ignored; there is
        only a single display device on these systems.

        :Parameters:
            `name` : str
                The name of the display to connect to.
            `x_screen` : int
                The X11 screen number to use.

        '''
        app.displays.add(self)

    def get_screens(self):
        '''Get the available screens.

        A typical multi-monitor workstation comprises one `Display` with
        multiple `Screen` s.  This method returns a list of screens which
        can be enumerated to select one for full-screen display.

        For the purposes of creating an OpenGL config, the default screen
        will suffice.

        :rtype: list of `Screen`
        '''
        raise NotImplementedError('abstract')    

    def get_default_screen(self):
        '''Get the default screen as specified by the user's operating system
        preferences.

        :rtype: `Screen`
        '''
        return self.get_screens()[0]

    def get_windows(self):
        '''Get the windows currently attached to this display.

        :rtype: sequence of `Window`
        '''
        return [window for window in windows if window.display is self]


class EventLoop(event.EventDispatcher):
    '''The main run loop of the application.

    Calling `run` begins the application event loop, which processes
    operating system events, calls `pyglet.clock.tick` to call scheduled
    functions and calls `pyglet.window.Window.on_draw` and
    `pyglet.window.Window.flip` to update window contents.

    Applications can subclass `EventLoop` and override certain methods
    to integrate another framework's run loop, or to customise processing
    in some other way.  You should not in general override `run`, as
    this method contains platform-specific code that ensures the application
    remains responsive to the user while keeping CPU usage to a minimum.
    '''

    _exit_functions = None
    _has_exit_condition = None
    _has_exit = False

    def __init__(self):
        self._has_exit_condition = threading.Condition()
        self._exit_functions = []

    def run(self):
        '''Begin processing events, scheduled functions and window updates.

        This method returns when `has_exit` is set to True.

        Developers are discouraged from overriding this method, as the
        implementation is platform-specific.
        '''
        raise NotImplementedError('abstract')

    def post_event(self, dispatcher, event, *args):
        '''Post an event into the main application thread.

        The event is queued internally until the `run` method's thread
        is able to dispatch the event.  This method can be safely called
        from any thread.

        If the method is called from the `run` method's thread (for example,
        from within an event handler), the event may be dispatched within
        the same runloop iteration or the next one; the choice is
        nondeterministic.

        :Parameters:
            `dispatcher` : EventDispatcher
                Dispatcher to process the event.
            `event` : str
                Event name.
            `args` : sequence
                Arguments to pass to the event handlers.

        '''
        raise NotImplementedError('abstract')

    def _setup(self):
        global event_loop
        event_loop = self

        # Disable event queuing for dispatch_events
        from pyglet.window import Window
        Window._enable_event_queue = False
        
        # Dispatch pending events
        for window in app.windows:
            window.switch_to()
            window.dispatch_pending_events()

    def _idle_chance(self):
        '''If timeout has expired, manually force an idle loop.

        Called by window that have blocked the event loop (e.g. during
        resizing).
        '''

    def idle(self):
        '''Called during each iteration of the event loop.

        The method is called immediately after any window events (i.e., after
        any user input).  The method can return a duration after which
        the idle method will be called again.  The method may be called
        earlier if the user creates more input events.  The method
        can return `None` to only wait for user events.

        For example, return ``1.0`` to have the idle method called every
        second, or immediately after any user events.

        The default implementation dispatches the
        `pyglet.window.Window.on_draw` event for all windows and uses
        `pyglet.clock.tick` and `pyglet.clock.get_sleep_time` on the default
        clock to determine the return value.

        This method should be overridden by advanced users only.  To have
        code execute at regular intervals, use the
        `pyglet.clock.schedule` methods.

        :rtype: float
        :return: The number of seconds before the idle method should
            be called again, or `None` to block for user input.
        '''
        dt = clock.tick(True)

        # Redraw all windows
        for window in app.windows:
            if window.invalid:
                window.switch_to()
                window.dispatch_event('on_draw')
                window.flip()

        # Update timout
        return clock.get_sleep_time(True)

    def _get_has_exit(self):
        self._has_exit_condition.acquire()
        result = self._has_exit
        self._has_exit_condition.release()
        return result

    def _set_has_exit(self, value):
        self._has_exit_condition.acquire()
        self._has_exit = value
        self._has_exit_condition.notify()
        self._has_exit_condition.release()

    has_exit = property(_get_has_exit, _set_has_exit,
                        doc='''Flag indicating if the event loop will exit in
    the next iteration.  When set, all waiting threads are interrupted (see
    `sleep`).
    
    Thread-safe since pyglet 1.2.

    :see: `exit`
    :type: bool
    ''')

    def exit(self):
        '''Safely exit the event loop at the end of the current iteration.

        This method is a thread-safe equivalent for for setting `has_exit` to
        ``True``.  All waiting threads will be interrupted (see
        `sleep`).
        '''
        self._set_has_exit(True)
        self.post_event(None, None) # XXX

    def sleep(self, timeout):
        '''Wait for some amount of time, or until the `has_exit` flag is
        set or `exit` is called.

        This method is thread-safe.

        :Parameters:
            `timeout` : float
                Time to wait, in seconds.

        :since: pyglet 1.2

        :rtype: bool
        :return: ``True`` if the `has_exit` flag is now set, otherwise
        ``False``.
        '''
        self._has_exit_condition.acquire()
        self._has_exit_condition.wait(timeout)
        result = self._has_exit
        self._has_exit_condition.release()
        return result

    def on_window_close(self, window):
        '''Default window close handler.'''
        if not app.windows:
            self.exit()

    if _is_epydoc:
        def on_window_close(window):
            '''A window was closed.

            This event is dispatched when a window is closed.  It is not
            dispatched if the window's close button was pressed but the
            window did not close.

            The default handler calls `exit` if no more windows are open.  You
            can override this handler to base your application exit on some
            other policy.

            :event:
            '''

        def on_enter():
            '''The event loop is about to begin.

            This is dispatched when the event loop is prepared to enter
            the main run loop, and represents the last chance for an 
            application to initialise itself.

            :event:
            '''

        def on_exit():
            '''The event loop is about to exit.

            After dispatching this event, the `run` method returns (the
            application may not actually exit if you have more code
            following the `run` invocation).

            :event:
            '''

EventLoop.register_event_type('on_window_close')
EventLoop.register_event_type('on_enter')
EventLoop.register_event_type('on_exit')
