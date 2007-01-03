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

def gencells(l, w, h, klass):
    r = []
    for i, m in enumerate(l):
        c = []
        r.append(c)
        for j, n in enumerate(m):
            c.append(klass(i, j, w, h, n, None))
    return r

class RenderBase(unittest.TestCase):
    w = None
    def init_window(self, vx, vy):
        self.w = pyglet.window.Window(width=vx, height=vy)

    def run_test(self, m, viewsize=None, show_focus=False, debug=True,
            allow_oob = False):
        if self.w is None:
            if viewsize is None: vx, vy = m.pxw, m.pxh
            else: vx, vy = viewsize
            self.init_window(vx, vy)
        else:
            vx = self.w.width
            vy = self.w.height

        s = pyglet.scene2d.Scene(maps=[m])
        r = pyglet.scene2d.FlatView(s, 0, 0, vx, vy)
        r.allow_oob = allow_oob

        class running(pyglet.window.event.ExitHandler):
            def __init__(self, fps=30):
                self.clock = pyglet.clock.Clock(fps)
            def __nonzero__(self):
                if self.exit: return False
                self.clock.tick()
                return True

        class InputHandler(object):
            up = down = left = right = 0
            def on_key_press(self, symbol, modifiers):
                if symbol == pyglet.window.key.K_UP: self.up = 5
                if symbol == pyglet.window.key.K_DOWN: self.down = -5
                if symbol == pyglet.window.key.K_LEFT: self.left = -5
                if symbol == pyglet.window.key.K_RIGHT: self.right = 5
                return pyglet.window.event.EVENT_UNHANDLED
            def on_key_release(self, symbol, modifiers):
                if symbol == pyglet.window.key.K_UP: self.up = 0
                if symbol == pyglet.window.key.K_DOWN: self.down = 0
                if symbol == pyglet.window.key.K_LEFT: self.left = 0
                if symbol == pyglet.window.key.K_RIGHT: self.right = 0
                return pyglet.window.event.EVENT_UNHANDLED
            lines = False
            def on_text(self, text):
                if text == 's':
                    self.lines = not self.lines
                    return
                if text == 'o':
                    r.allow_oob = not r.allow_oob
                    print 'NOTE: allow_oob =', r.allow_oob
                    return
                return pyglet.window.event.EVENT_UNHANDLED

        running = running()
        self.w.push_handlers(running)
        input = InputHandler()
        self.w.push_handlers(input)

        print 'NOTE: allow_oob =', r.allow_oob

        while running:
            self.w.switch_to()
            self.w.dispatch_events()
            glClear(GL_COLOR_BUFFER_BIT)
            r.fx += input.left + input.right
            r.fy += input.up + input.down
            if debug:
                r.debug(input.lines and r.LINES or r.CHECKERED, show_focus)
            else:
                r.draw()
            self.w.flip()
        self.w.close()

class DummyImage:
    def draw(self):
        pass

