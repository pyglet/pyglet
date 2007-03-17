#!/usr/bin/env python

'''Test that the window can be hidden and shown.

Expected behaviour:
    One window will be opened.  Every 5 seconds it will toggle between
    hidden and shown.

    Press escape or close the window to finish the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import time
import unittest

from pyglet import window
from pyglet.window.event import WindowEventLogger

class WINDOW_SET_VISIBLE(unittest.TestCase):
    def test_set_visible(self):
        w = window.Window(200, 200)
        w.push_handlers(WindowEventLogger())
        last_time = time.time()
        visible = True
        while not w.has_exit:
            if time.time() - last_time > 5:
                visible = not visible
                w.set_visible(visible)
                last_time = time.time()
                print 'Set visibility to %r.' % visible
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
