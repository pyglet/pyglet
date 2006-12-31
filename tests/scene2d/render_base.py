#!/usr/bin/env python

'''Base class for rendering tests.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest

from pyglet.GL.VERSION_1_1 import *
import pyglet.window
import pyglet.window.event
import pyglet.clock

class RenderBase(unittest.TestCase):
    def run_test(self, m):
        w = pyglet.window.Window(width=m.pxw, height=m.pxh)
        s = pyglet.scene2d.Scene(maps=[m])
        r = pyglet.scene2d.FlatView(s, 0, 0, m.pxw, m.pxh)

        class running(pyglet.window.event.ExitHandler):
            def __init__(self, fps=5):
                self.clock = pyglet.clock.Clock(fps)
            def __nonzero__(self):
                if self.exit: return False
                self.clock.tick()
                return True
            lines = True
            def on_text(self, text):
                if text != 's': return pyglet.window.event.EVENT_UNHANDLED
                self.lines = not self.lines

        running = running()
        w.push_handlers(running)

        while running:
            w.switch_to()
            w.dispatch_events()
            glClear(GL_COLOR_BUFFER_BIT)
            r.debug((0,0), running.lines and 'lines' or 'checkered')
            w.flip()
        w.close()

class DummyImage:
    def draw(self):
        pass

