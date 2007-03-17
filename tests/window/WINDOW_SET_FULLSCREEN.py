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

from pyglet import window
from pyglet.window.event import WindowEventLogger
from pyglet.window import key
from pyglet.gl import *

class WINDOW_SET_FULLSCREEN(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        if symbol == key.F:
            print 'Setting fullscreen.'
            self.w.set_fullscreen(True)
        elif symbol == key.G:
            print 'Leaving fullscreen.'
            self.w.set_fullscreen(False)

    def on_expose(self):
        glClearColor(1, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        self.w.flip()

    def test_set_fullscreen(self):
        self.w = w = window.Window(200, 200)
        w.push_handlers(self)
        w.push_handlers(WindowEventLogger())
        self.on_expose()
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
