#!/usr/bin/env python

'''Test that show and hide events work correctly.

Expected behaviour:
    One window will be opened.  There should be one shown event printed
    initially.  Minimizing and restoring the window should produce hidden
    and shown events, respectively.

    On OS X the events should also be fired when the window is hidden
    and shown (using Command+H or the dock context menu).
    
    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window

class EVENT_SHOW_HIDE(unittest.TestCase):
    def on_show(self):
        print 'Window shown.'

    def on_hide(self):
        print 'Window hidden.'

    def test_show_hide(self):
        w = window.Window(200, 200, visible=False)
        w.push_handlers(self)
        w.set_visible()
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
