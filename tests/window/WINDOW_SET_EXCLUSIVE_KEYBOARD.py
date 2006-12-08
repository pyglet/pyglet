#!/usr/bin/env python

'''Test that exclusive keyboard mode can be set.

Expected behaviour:
    One window will be opened.  Press 'e' to enable exclusive mode and 'E'
    to disable exclusive mode.

    In exclusive mode:
     - Pressing system keys, the Expose keys, etc., should have no effect
       besides displaying as keyboard events.
        - On OS X, the Power switch is not disabled (though this is possible
          if desired, see source).
        - On OS X, the menu bar and dock will disappear during keyboard
          exclusive mode.
        - On Windows, only Alt+Tab is disabled.  A user can still switch away
          using Ctrl+Escape, Alt+Escape, the Windows key or Ctrl+Alt+Del.
     - Switching to another application (i.e., with the mouse) should make
       these keys work normally again until this application regains focus.

    Close the window or press ESC to end the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *

class WINDOW_SET_EXCLUSIVE_KEYBOARD(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        print 'Pressed %s with modifiers %s' % \
            (pyglet.window.event._symbol_to_string(symbol),
             pyglet.window.event._modifiers_to_string(modifiers))

        if symbol == K_E:
            exclusive = not (modifiers & MOD_SHIFT)
            self.w.set_exclusive_keyboard(exclusive)
            print 'Exclusive keyboard is now %r' % exclusive

    def on_key_release(self, symbol, modifiers):
        print 'Released %s with modifiers %s' % \
            (pyglet.window.event._symbol_to_string(symbol),
             pyglet.window.event._modifiers_to_string(modifiers))

    def test_set_exclusive_keyboard(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height)
        exit_handler = ExitHandler()
        w.push_handlers(self)
        w.push_handlers(exit_handler)
        while not exit_handler.exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
