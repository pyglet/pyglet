#!/usr/bin/env python

'''
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
    def on_text(self, text):
        text = text[:1]
        i = ord(text) - ord('a')
        if 0 <= i < len(self.modes):
            print 'Switching to %s' % self.modes[i]
            self.w.screen.set_mode(self.modes[i])

    def on_expose(self):
        glClearColor(1, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        window_util.draw_client_border(self.w)
        self.w.flip()

    def test_set_fullscreen(self):
        self.w = w = window.Window(200, 200)

        self.modes = w.screen.get_modes()
        print 'Press a letter to switch to the corresponding mode:'
        for i, mode in enumerate(self.modes):
            print '%s: %s' % (chr(i + ord('a')), mode)

        w.push_handlers(self)
        #w.push_handlers(WindowEventLogger())
        self.on_expose()
        while not w.has_exit:
            w.dispatch_events()
        w.close()

if __name__ == '__main__':
    unittest.main()
