#!/usr/bin/env python
'''Test that screens can be selected for fullscreen.

Expected behaviour: 
    One window will be created fullscreen on the primary screen.  When you
      close this window, another will open on the next screen, and so 
      on until all screens have been tested.

    Each screen will be filled with a different color:
     - Screen 0: Red
     - Screen 1: Green
     - Screen 2: Blue
     - Screen 3: Purple

    The test will end when all screens have been tested.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet.window.event import *
from pyglet.gl import *

colours = [
    (1, 0, 0, 1),
    (0, 1, 0, 1),
    (0, 0, 1, 1),
    (1, 0, 1, 1)]

class MULTIPLE_SCREEN(unittest.TestCase):
    def open_next_window(self):
        screen = self.screens[self.index]
        factory = pyglet.window.get_factory()
        factory.set_size(screen.width, screen.height)
        factory.set_fullscreen(True)
        factory.set_gl_attribute('doublebuffer', True)
        factory.set_screen(screen)
        self.w = factory.create_window()
        self.w.push_handlers(self)
        self.w.set_visible()

    def on_expose(self):
        self.w.switch_to()
        glClearColor(*colours[self.index])
        glClear(GL_COLOR_BUFFER_BIT)
        self.w.flip()

    def test_multiple_screen(self):
        self.screens = pyglet.window.get_factory().get_screens()
        for i in range(len(self.screens)):
            self.index = i
            self.open_next_window()
            self.on_expose()
            while not self.w.has_exit:
                self.w.dispatch_events()
            self.w.close()

if __name__ == '__main__':
    unittest.main()

