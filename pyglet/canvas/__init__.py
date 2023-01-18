"""Display and screen management.

Rendering is performed on a :class:`Canvas`, which conceptually could be an
off-screen buffer, the content area of a :class:`pyglet.window.Window`, or an
entire screen. Currently, canvases can only be created with windows (though
windows can be set fullscreen).

Windows and canvases must belong to a :class:`Display`. On Windows and Mac OS X
there is only one display, which can be obtained with :func:`get_display`.
Linux supports multiple displays, corresponding to discrete X11 display
connections and screens.  :func:`get_display` on Linux returns the default
display and screen 0 (``localhost:0.0``); if a particular screen or display is
required then :class:`Display` can be instantiated directly.

Within a display one or more screens are attached.  A :class:`Screen` often
corresponds to a physical attached monitor, however a monitor or projector set
up to clone another screen will not be listed.  Use :meth:`Display.get_screens`
to get a list of the attached screens; these can then be queried for their
sizes and virtual positions on the desktop.

The size of a screen is determined by its current mode, which can be changed
by the application; see the documentation for :class:`Screen`.

.. versionadded:: 1.2
"""

import sys
import weakref


_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


_displays = weakref.WeakSet()
"""Set of all open displays.  Instances of :class:`Display` are automatically
added to this set upon construction.  The set uses weak references, so displays
are removed from the set when they are no longer referenced.

:type: :class:`WeakSet`
"""


def get_display():
    """Get the default display device.

    If there is already a :class:`Display` connection, that display will be
    returned. Otherwise, a default :class:`Display` is created and returned.
    If multiple display connections are active, an arbitrary one is returned.

    .. versionadded:: 1.2

    :rtype: :class:`Display`
    """
    # If there are existing displays, return one of them arbitrarily.
    for display in _displays:
        return display

    # Otherwise, create a new display and return it.
    return Display()


if _is_pyglet_doc_run:
    from pyglet.canvas.base import Display, Screen, Canvas, ScreenMode
else:
    from pyglet import compat_platform, options
    if options['headless']:
        from pyglet.canvas.headless import HeadlessDisplay as Display
        from pyglet.canvas.headless import HeadlessScreen as Screen
        from pyglet.canvas.headless import HeadlessCanvas as Canvas
    elif compat_platform == 'darwin':
        from pyglet.canvas.cocoa import CocoaDisplay as Display
        from pyglet.canvas.cocoa import CocoaScreen as Screen
        from pyglet.canvas.cocoa import CocoaCanvas as Canvas
    elif compat_platform in ('win32', 'cygwin'):
        from pyglet.canvas.win32 import Win32Display as Display
        from pyglet.canvas.win32 import Win32Screen as Screen
        from pyglet.canvas.win32 import Win32Canvas as Canvas
    else:
        from pyglet.canvas.xlib import XlibDisplay as Display
        from pyglet.canvas.xlib import XlibScreen as Screen
        from pyglet.canvas.xlib import XlibCanvas as Canvas
