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
from pyglet.window.event import *

class WINDOW_CAPTION(unittest.TestCase):
    def test_caption(self):
        w1 = pyglet.window.create(200, 200)
        w2 = pyglet.window.create(200, 200)
        exit_handler = ExitHandler()
        w1.push_handlers(exit_handler)
        w2.push_handlers(exit_handler)
        count = 1
        w1.set_caption('Window caption %d' % count)
        w2.set_caption(u'\u00bfHabla espa\u00f1ol?')
        last_time = time.time()
        while not exit_handler.exit:
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
