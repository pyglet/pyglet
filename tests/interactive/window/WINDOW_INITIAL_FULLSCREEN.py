#!/usr/bin/env python
'''Test that a window can be opened fullscreen.

Expected behaviour: 
    A fullscreen window will be created, with a flat purple colour.

     - Press 'g' to leave fullscreen mode and create a window.
     - Press 'f' to re-enter fullscreen mode.
     - All events will be printed to the console.  Ensure that mouse,
       keyboard and activation/deactivation events are all correct.

    Close either window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet import window
from pyglet.window.event import WindowEventLogger
from pyglet.window import key
from pyglet.gl import *

class WINDOW_INITIAL_FULLSCREEN(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        if symbol == key.F:
            print 'Setting fullscreen.'
            self.w.set_fullscreen(True)
        elif symbol == key.G:
            print 'Leaving fullscreen.'
            self.w.set_fullscreen(False)

    def on_expose(self):
        glClearColor(1, 0, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        self.w.flip()

    def test_initial_fullscreen(self):
        self.w = window.Window(fullscreen=True)
        self.w.push_handlers(self)
        self.w.push_handlers(WindowEventLogger())
        self.on_expose()
        while not self.w.has_exit:
            self.w.dispatch_events()
        self.w.close()

if __name__ == '__main__':
    unittest.main()

