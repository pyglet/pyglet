#!/usr/bin/env python

'''Test that text events work correctly.

Expected behaviour:
    One window will be opened.  Type into this window and check the console
    output for text events.  
     - Repeated when keys are held down
     - No motion or command events generated
     - Non-keyboard text entry is used (e.g., pen or international palette).
     - Combining characters do not generate events, but the modified
       character is sent.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

import pyglet.window
from pyglet.window.event import *

class EVENT_KEYPRESS(unittest.TestCase):
    def on_text(self, text):
        print 'Typed %r' % text

    def test_text(self):
        w = pyglet.window.create(200, 200)
        exit_handler = ExitHandler()
        w.push_handlers(self)
        w.push_handlers(exit_handler)
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
