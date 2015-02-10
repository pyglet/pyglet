#!/usr/bin/env python

'''Test that the window caption can be set.

Expected behaviour:
    Two windows will be opened, one with the caption "Window caption 1"
    counting up every second; the other with a Unicode string including
    some non-ASCII characters.

    Press escape or close either window to finished the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import time
import unittest
from pyglet import window

class WINDOW_CAPTION(unittest.TestCase):
    def test_caption(self):
        w1 = window.Window(400, 200, resizable=True)
        w2 = window.Window(400, 200, resizable=True)
        count = 1
        w1.set_caption('Window caption %d' % count)
        w2.set_caption(u'\u00bfHabla espa\u00f1ol?')
        last_time = time.time()
        while not (w1.has_exit or w2.has_exit):
            if time.time() - last_time > 1:
                count += 1
                w1.set_caption('Window caption %d' % count)
                last_time = time.time()
            w1.dispatch_events()
            w2.dispatch_events()
        w1.close()
        w2.close()

if __name__ == '__main__':
    unittest.main()
