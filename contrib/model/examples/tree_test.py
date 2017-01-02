#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: gl_tree_test.py 114 2006-10-22 09:46:11Z r1chardj0n3s $'

import math
import random
from pyglet.window import *
from pyglet.window import mouse
from pyglet import clock
from ctypes import *
from pyglet.window.event import *
# from pyglet.ext.model.geometric import tree_list
from model.geometric import tree_list

from pyglet.gl import *

four_floats = c_float * 4

def setup_scene():
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., 1., 1., 100.)
    glMatrixMode(GL_MODELVIEW)
    glClearColor(1, 1, 1, 1)

class Tree(object):
    def __init__(self, n=2, r=False):
        self.tree = tree_list(n, r)
        self.x = self.y = 0
        self.rx = self.ry = 0
        self.zpos = -10
        self.lmb = False
        self.rmb = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & mouse.LEFT:
            self.rx += dx
            self.ry += dy
        if buttons & mouse.RIGHT:
            self.x += dx
            self.y += dy

    def on_mouse_scroll(self, x, y, dx, dy):
        self.zpos = max(-10, self.zpos + dy)

    def draw(self):
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(self.x/10., -self.y/10., self.zpos)
        glRotatef(self.ry, 1., 0., 0.)
        glRotatef(self.rx, 0., 1., 0.)
        self.tree.draw()
        glPopMatrix()

# need one display list per window
w1 = Window(width=300, height=300)
w1.switch_to()
setup_scene()
tree1 = Tree(n=10, r=True)
w1.push_handlers(tree1)

w2 = Window(width=300, height=300)
w2.switch_to()
setup_scene()
tree2 = Tree(n=10, r=False)
w2.push_handlers(tree2)

n = 0
clock.set_fps_limit(30)
while not (w1.has_exit or w2.has_exit):
    clock.tick()
    n += 1

    # draw
    w1.switch_to()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    w1.dispatch_events()
    tree1.draw()
    w1.flip()

    w2.switch_to()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    w2.dispatch_events()
    tree2.draw()
    w2.flip()

