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

from pyglet import window
from pyglet.window.event import *

class EVENT_KEYPRESS(unittest.TestCase):
    def on_text(self, text):
        print 'Typed %r' % text

    def test_text(self):
        w = window.Window(200, 200)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
