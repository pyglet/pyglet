#!/usr/bin/env python
'''Test that vsync can be set.

Expected behaviour: 
    A window will alternate between red and green fill.  

      - Press "v" to toggle vsync on/off.  "Tearing" should only be visible
        when vsync is off (as indicated at the terminal).

    Not all video drivers support vsync.  On Linux, check the output of
    `tools/info.py`:

      - If GLX_SGI_video_sync extension is present, should work as expected.
      - If GLX_MESA_swap_control extension is present, should work as expected.
      - If GLX_SGI_swap_control extension is present, vsync can be enabled,
        but once enabled, it cannot be switched off (there will be no error
        message).
      - If none of these extensions are present, vsync is not supported by
        your driver, but no error message or warning will be printed.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet import window
from pyglet.window import key
from pyglet.gl import *

class WINDOW_SET_VSYNC(unittest.TestCase):
    colors = [(1, 0, 0, 1), (0, 1, 0, 1)]
    color_index = 0

    def open_window(self):
        return window.Window(200, 200, vsync=False)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.V:
            vsync = not self.w1.vsync
            self.w1.set_vsync(vsync)
            print 'vsync is %r' % self.w1.vsync

    def draw_window(self, window, colour):
        window.switch_to()
        glClearColor(*colour)
        glClear(GL_COLOR_BUFFER_BIT)
        window.flip()

    def test_open_window(self):
        self.w1 = self.open_window()
        self.w1.push_handlers(self)
        print 'vsync is %r' % self.w1.vsync
        while not self.w1.has_exit:
            self.color_index = 1 - self.color_index
            self.draw_window(self.w1, self.colors[self.color_index])
            self.w1.dispatch_events()
        self.w1.close()

if __name__ == '__main__':
    unittest.main()

