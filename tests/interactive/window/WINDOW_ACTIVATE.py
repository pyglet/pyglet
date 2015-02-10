#!/usr/bin/env python

'''Test that the window can be activated (focus set).

Expected behaviour:
    One window will be opened.  Every 5 seconds it will be activated;
    it should be come to the front and accept keyboard input (this will
    be shown on the terminal).

    On Windows XP, the taskbar icon may flash (indicating the application
    requires attention) rather than moving the window to the foreground.  This
    is the correct behaviour.

    Press escape or close the window to finished the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import time
import unittest

from pyglet import window
from pyglet.window.event import WindowEventLogger

class WINDOW_ACTVATE(unittest.TestCase):
    def test_activate(self):
        w = window.Window(200, 200)
        w.push_handlers(WindowEventLogger())
        last_time = time.time()
        while not w.has_exit:
            if time.time() - last_time > 5:
                w.activate()
                last_time = time.time()
                print 'Activated window.'
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
