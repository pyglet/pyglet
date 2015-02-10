#!/usr/bin/env python

'''Test that window can be set to and from various fullscreen sizes.

Expected behaviour:
    One window will be opened.  Press a number to switch to the corresponding
    fullscreen size; hold control and press a number to switch back
    to the corresponding window size:

        0 - Default size
        1 - 320x200
        2 - 640x480
        3 - 800x600
        4 - 1024x768
        5 - 1280x800 (widescreen)
        6 - 1280x1024

    In all cases the window bounds will be indicated by a green rectangle
    which should be completely visible.

    All events will be printed to the terminal.

    Press ESC to end the test.
     
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import unittest

from pyglet import window
from pyglet.window.event import WindowEventLogger
from pyglet.window import key
from pyglet.gl import *

import window_util

class WINDOW_SET_FULLSCREEN(unittest.TestCase):
    def on_key_press(self, symbol, modifiers):
        fullscreen = not modifiers & key.MOD_CTRL
        doing = fullscreen and 'Setting' or 'Restoring from'
        if symbol == key._0:
            print '%s default size' % doing
            self.w.set_fullscreen(fullscreen)
            return
        elif symbol == key._1:
            width, height = 320, 200
        elif symbol == key._2:
            width, height = 640, 480
        elif symbol == key._3:
            width, height = 800, 600
        elif symbol == key._4:
            width, height = 1024, 768
        elif symbol == key._5:
            width, height = 1280, 800 # 16:10
        elif symbol == key._6:
            width, height = 1280, 1024
        else:
            return
        print '%s width=%d, height=%d' % (doing, width, height)
        self.w.set_fullscreen(fullscreen, width=width, height=height)

    def on_expose(self):
        glClearColor(1, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        window_util.draw_client_border(self.w)
        self.w.flip()

    def test_set_fullscreen(self):
        self.w = w = window.Window(200, 200)
        w.push_handlers(self)
        w.push_handlers(WindowEventLogger())
        self.on_expose()
        try:
            while not w.has_exit:
                w.dispatch_events()
            w.close()
        except SystemExit:
            # Child process on linux calls sys.exit(0) when it's done.
            pass

if __name__ == '__main__':
    unittest.main()
