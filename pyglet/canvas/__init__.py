#!/usr/bin/python
# $Id:$

import sys
_is_epydoc = hasattr(sys, 'is_epydoc') and sys.is_epydoc

def get_display():
    '''Get the default display device.

    If there is already a `Display` connection, that display will be returned.
    Otherwise, a default `Display` is created and returned.  If multiple
    display connections are active, an arbitrary one is returned.

    :since: pyglet 1.2

    :rtype: `Display`
    '''
    # If there's an existing display, return it (return arbitrary display if
    # there are multiple).
    from pyglet.app import displays
    for display in displays:
        return display

    # Otherwise, create a new display and return it.
    return Display()

if _is_epydoc:
    from pyglet.canvas.base import Display, Screen, Canvas
else:
    if sys.platform == 'darwin':
        from pyglet.canvas.carbon import CarbonDisplay as Display
        from pyglet.canvas.carbon import CarbonScreen as Screen
        from pyglet.canvas.carbon import CarbonCanvas as Canvas
    elif sys.platform in ('win32', 'cygwin'):
        from pyglet.canvas.win32 import Win32Display as Display
        from pyglet.canvas.win32 import Win32Screen as Screen
        from pyglet.canvas.win32 import Win32Canvas as Canvas
    else:
        from pyglet.canvas.xlib import XlibDisplay as Display
        from pyglet.canvas.xlib import XlibScreen as Screen
        from pyglet.canvas.xlib import XlibCanvas as Canvas
