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
from pyglet.scene2d import *


class Marker:
    def draw(self):
        glColor4f(1, 0, 0, 1)
        glPointSize(5)
        glBegin(GL_POINTS)
        glVertex2f(0, 0)
        glEnd()


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
                if text == 'd':
                    self.show_debug = not self.show_debug
                    raise NotImplemented()
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
        self.w.push_handlers(r.camera)

        print 'NOTE: allow_oob =', r.allow_oob
        marker = None
        if show_focus:
            # add in a "sprite"
            marker = Sprite(0, 0, 1, 1, Marker())
            s.sprites.append(marker)

        while running:
            self.w.dispatch_events()
            r.fx += input.left + input.right
            r.fy += input.up + input.down
            if marker is not None:
                marker.x = r.fx
                marker.y = r.fy
            r.clear()
            r.draw()
            self.w.flip()
        self.w.close()


