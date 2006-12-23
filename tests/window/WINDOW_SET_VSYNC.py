#!/usr/bin/env python
'''Test that vsync can be set.

Expected behaviour: 
    A window will alternate between red and green fill.  

      - Press "v" to toggle vsync on/off.  "Tearing" should only be visible
        when vsync is off (as indicated at the terminal).

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *
from pyglet.GL.VERSION_1_1 import *

class WINDOW_OPEN(unittest.TestCase):
    colors = [(1, 0, 0, 1), (0, 1, 0, 1)]
    color_index = 0

    def open_window(self):
        w = Window(200, 200)
        w.push_handlers(self.exit_handler)
        return w

    def on_key_press(self, key, modifiers):
        if key == K_V:
            vsync = not (self.w1.get_vsync() or False)
            self.w1.set_vsync(vsync)
            print 'vsync is %r' % self.w1.get_vsync()
        return True

    def draw_window(self, window, colour):
        window.switch_to()
        glClearColor(*colour)
        glClear(GL_COLOR_BUFFER_BIT)
        window.flip()

    def test_open_window(self):
        self.exit_handler = ExitHandler()
        self.w1 = self.open_window()
        self.w1.push_handlers(self.on_key_press)
        print 'vsync is %r' % self.w1.get_vsync()
        while not self.exit_handler.exit:
            self.color_index = 1 - self.color_index
            self.draw_window(self.w1, self.colors[self.color_index])
            self.w1.dispatch_events()
        self.w1.close()

if __name__ == '__main__':
    unittest.main()

