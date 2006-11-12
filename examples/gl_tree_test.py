#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: gl_tree_test.py 114 2006-10-22 09:46:11Z r1chardj0n3s $'

import math
import random
import pyglet.window
import pyglet.clock
from ctypes import *
from pyglet.window.event import *
from pyglet.gui import fps
from pyglet.model.geometric import tree_list

from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *

four_floats = c_float * 4

def setup_scene():
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., 1., 1., 100.)
    glMatrixMode(GL_MODELVIEW)
    glClearColor(1, 1, 1, 1)

# handle exit
exit_handler = ExitHandler()

w1 = pyglet.window.create(300, 300)
w1.push_handlers(exit_handler)
w1.switch_to()
setup_scene()

w2 = pyglet.window.create(300, 300)
w2.push_handlers(exit_handler)
w2.switch_to()
setup_scene()

c = pyglet.clock.Clock()

class Tree(object):
    def __init__(self, n=2, r=False):
        self.dl = tree_list(n, r)
        self.x = self.y = 0
        self.rx = self.ry = 0
        self.zpos = -10
        self.lmb = False
        self.rmb = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & MOUSE_LEFT_BUTTON:
            self.rx += dx
            self.ry += dy
        if buttons & MOUSE_RIGHT_BUTTON:
            self.x += dx
            self.y += dy

    def on_mouse_scroll(self, dx, dy):
        self.zpos = max(-10, self.zpos + dy)

    def render(self):
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(self.x/10., -self.y/10., self.zpos)
        glRotatef(self.ry, 1., 0., 0.)
        glRotatef(self.rx, 0., 1., 0.)
        glCallList(self.dl)
        glPopMatrix()

# need one display list per window
w1.switch_to()
tree1 = Tree(n=10, r=True)
w1.push_handlers(tree1)
fps = fps.FPS()

w2.switch_to()
tree2 = Tree(n=10, r=False)
w2.push_handlers(tree2)

n = 0
while not exit_handler.exit:
    n += 1
    c.set_fps(50)

    # render
    w1.switch_to()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    w1.dispatch_events()
    tree1.render()
    fps.draw(w1, c)
    w1.flip()

    w2.switch_to()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    w2.dispatch_events()
    tree2.render()
    w2.flip()

