"""Application-wide functionality.

Applications
------------

Most applications need only call :func:`run` after creating one or more 
windows to begin processing events.  For example, a simple application 
consisting of one window is::

    import pyglet

    win = pyglet.window.Window()
    pyglet.app.run()


Events
======

To handle events on the main event loop, instantiate it manually.  The
following example exits the application as soon as any window is closed (the
default policy is to wait until all windows are closed)::

    event_loop = pyglet.app.EventLoop()

    @event_loop.event
    def on_window_close(window):
        event_loop.exit()

.. versionadded:: 1.1
"""

import platform
import sys
import weakref

import pyglet
from pyglet import compat_platform
from pyglet.app.base import EventLoop

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

if _is_pyglet_doc_run:
    from pyglet.app.base import PlatformEventLoop
else:
    if compat_platform == 'darwin':
        from pyglet.app.cocoa import CocoaPlatformEventLoop as PlatformEventLoop

        if platform.machine() == 'arm64' or pyglet.options["osx_alt_loop"]:
            from pyglet.app.cocoa import CocoaAlternateEventLoop as EventLoop
    elif compat_platform in ('win32', 'cygwin'):
        from pyglet.app.win32 import Win32EventLoop as PlatformEventLoop
    else:
        from pyglet.app.xlib import XlibEventLoop as PlatformEventLoop


class AppException(Exception):
    pass


windows = weakref.WeakSet()
"""Set of all open windows (including invisible windows).  Instances of
:class:`pyglet.window.Window` are automatically added to this set upon 
construction. The set uses weak references, so windows are removed from 
the set when they are no longer referenced or are closed explicitly.
"""


def run(interval=1 / 60):
    """Begin processing events, scheduled functions and window updates.

    This is a convenience function, equivalent to::

        pyglet.app.event_loop.run()

    """
    event_loop.run(interval)


def exit():
    """Exit the application event loop.

    Causes the application event loop to finish, if an event loop is currently
    running.  The application may not necessarily exit (for example, there may
    be additional code following the `run` invocation).

    This is a convenience function, equivalent to::

        event_loop.exit()

    """
    event_loop.exit()


#: The global event loop.  Applications can replace this
#: with their own subclass of :class:`EventLoop` before calling 
#: :meth:`EventLoop.run`.
event_loop = EventLoop()

#: The platform-dependent event loop. Applications must not subclass
# or replace this :class:`PlatformEventLoop` object.
platform_event_loop = PlatformEventLoop()
