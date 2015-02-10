#!/usr/bin/env python

'''Test that activate and deactivate events work correctly.

Expected behaviour:
    One window will be opened.  Clicking on the window should activate it,
    clicking on another window should deactivate it.  Messages will be
    printed to the console for both events.

    On OS X you can also (de)activate a window with Command+Tab, or using
    Expose (F9) or the Dock.

    On Windows and most Linux window managers you can use Alt+Tab or the
    task bar.
    
    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window

class EVENT_ACTIVATE_DEACTIVATE(unittest.TestCase):
    def on_activate(self):
        print 'Window activated.'

    def on_deactivate(self):
        print 'Window deactivated.'

    def test_activate_deactivate(self):
        w = window.Window(200, 200)
        w.push_handlers(self)
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
