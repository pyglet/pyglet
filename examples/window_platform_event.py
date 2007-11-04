#!/usr/bin/env python

'''Demonstrates how to handle a platform-specific event not defined in
pyglet by subclassing Window.  This is not for the faint-hearted!

A message will be printed to stdout when the following events are caught:

 - On Mac OS X, the window drag region is clicked.
 - On Windows, the display resolution is changed.
 - On Linux, the window properties are changed.

'''

from pyglet.window import Window

# Check for Carbon (OS X)
try:
    from pyglet.window.carbon import *
    _have_carbon = True
except ImportError:
    _have_carbon = False

# Check for Win32
try:
    from pyglet.window.win32 import *
    from pyglet.window.win32.constants import *
    _have_win32 = True
except ImportError:
    _have_win32 = False

# Check for Xlib (Linux)
try:
    from pyglet.window.xlib import *
    _have_xlib = True
except ImportError:
    _have_xlib = False

# Subclass Window
class MyWindow(Window):
    def run(self):
        while not self.has_exit:
            self.dispatch_events()

    if _have_carbon:
        @CarbonEventHandler(kEventClassWindow, kEventWindowClickDragRgn)
        def _on_window_click_drag_rgn(self, next_handler, event, data):
            print 'Clicked drag rgn.'
            carbon.CallNextEventHandler(next_handler, event)
            return noErr

    if _have_win32:
        @Win32EventHandler(WM_DISPLAYCHANGE)
        def _on_window_display_change(self, msg, lParam, wParam):
            print 'Display resolution changed.'
            return 0

    if _have_xlib:
        @XlibEventHandler(xlib.PropertyNotify)
        def _on_window_property_notify(self, event):
            print 'Property notify.'

if __name__ == '__main__':
    MyWindow().run()
