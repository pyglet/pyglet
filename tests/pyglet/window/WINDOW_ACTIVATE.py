#!/usr/bin/env python

'''Test that the window can be activated (focus set).

Expected behaviour:
    One window will be opened.  Every 5 seconds it will be activated;
    it should be come to the front and accept keyboard input (this will
    be shown on the terminal).

    Press escape or close the window to finished the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import time
import unittest
from pyglet.window.event import *

class WINDOW_ACTVATE(unittest.TestCase):
    def test_activate(self):
        w = pyglet.window.create(200, 200)
        exit_handler = ExitHandler()
        w.push_handlers(exit_handler)
        w.push_handlers(DebugEventHandler())
        last_time = time.time()
        while not exit_handler.exit:
            if time.time() - last_time > 5:
                w.activate()
                last_time = time.time()
                print 'Activated window.'
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
