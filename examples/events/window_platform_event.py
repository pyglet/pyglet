#!/usr/bin/env python
"""Demonstrates how to handle a platform-specific event not defined in
pyglet by subclassing Window.  This is not for the faint-hearted!

A message will be printed to stdout when the following events are caught:

 - On Mac OS X, the window drag region is clicked.
 - On Windows, the display resolution is changed.
 - On Linux, the window properties are changed.

"""


import pyglet


_have_cocoa = _have_win32 = _have_xlib = False

if pyglet.compat_platform.startswith('linux'):
    _have_xlib = True
    from pyglet.window.xlib import XlibEventHandler, xlib

elif pyglet.compat_platform == 'darwin':
    _have_cocoa = True
    # from pyglet.window.cocoa import *

elif pyglet.compat_platform in ('win32', 'cygwin'):
    _have_win32 = True
    from pyglet.window.win32 import Win32EventHandler, WM_DISPLAYCHANGE


# Subclass Window
class MyWindow(pyglet.window.Window):
    if _have_cocoa:
        # TODO This is currently not supported in Cocoa (#156).
        pass

    if _have_win32:
        @Win32EventHandler(WM_DISPLAYCHANGE)
        def _on_window_display_change(self, msg, lParam, wParam):
            print('Display resolution changed.')
            return 0

    if _have_xlib:
        @XlibEventHandler(xlib.PropertyNotify)
        def _on_window_property_notify(self, event):
            print('Property notify.')


if __name__ == '__main__':
    window = MyWindow()
    pyglet.app.run()
