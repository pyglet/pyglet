#!/usr/bin/env python

'''Test that window can be set fullscreen and back again.

Expected behaviour:
    One window will be opened.  

     - press "f" to enter fullscreen mode.
     - press "g" to leave fullscreen mode.

    All events will be printed to the terminal.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *
from pyglet.GL.VERSION_1_1 import *

class WINDOW_SET_FULLSCREEN(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        if symbol == K_F:
            print 'Setting fullscreen.'
            self.w.set_fullscreen(True)
        elif symbol == K_G:
            print 'Leaving fullscreen.'
            self.w.set_fullscreen(False)

    def on_expose(self):
        glClearColor(1, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        self.w.flip()

    def test_set_fullscreen(self):
        self.w = w = Window(200, 200)
        exit_handler = ExitHandler()
        w.push_handlers(self)
        w.push_handlers(exit_handler)
        w.push_handlers(DebugEventHandler())
        self.on_expose()
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
