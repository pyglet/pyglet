#!/usr/bin/env python

'''Test that text events work correctly.

Expected behaviour:
    One window will be opened.  Type into this window and check the console
    output for text events.  
     - Repeated when keys are held down
     - Motion events (e.g., arrow keys, HOME/END, etc) are reported
     - Select events (motion + SHIFT) are reported
     - Non-keyboard text entry is used (e.g., pen or international palette).
     - Combining characters do not generate events, but the modified
       character is sent.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window
from pyglet.window import key

class EVENT_KEYPRESS(unittest.TestCase):
    def on_text(self, text):
        print 'Typed %r' % text

    def on_text_motion(self, motion):
        print 'Motion %s' % key.motion_string(motion)

    def on_text_motion_select(self, motion):
        print 'Select %s' % key.motion_string(motion)

    def test_text(self):
        w = window.Window(200, 200)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
