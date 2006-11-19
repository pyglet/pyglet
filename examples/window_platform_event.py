#!/usr/bin/env python

'''Demonstrates how to handle a platform-specific event not defined in
pyglet by subclassing Window.  

A message will be printed to stdout when the following events are caught:

 - On Mac OS X, the window resize region is clicked.
 - On Windows, ...
 - On Linux, ...

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet.window import *
from pyglet.window.event import *

try:
    from pyglet.window.carbon import *
    from pyglet.window.carbon.constants import *
    _have_carbon = True
except ImportError:
    _have_carbon = False

class MyWindow(Window):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.exit_handler = ExitHandler()
        self.push_handlers(self.exit_handler)

    def run(self):
        while not self.exit_handler.exit:
            self.dispatch_events()

    if _have_carbon:
         @CarbonEventHandler(kEventClassWindow, kEventWindowClickResizeRgn)
         def _on_window_click_resize_rgn(self, next_handler, event, data):
            print 'Clicked resize rgn.'
            carbon.CallNextEventHandler(next_handler, event)
            return noErr

if __name__ == '__main__':
    MyWindow().run()
