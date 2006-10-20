#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import math
import random
import pyglet.window
import pyglet.clock
from ctypes import *
from pyglet.window.event import *
from pyglet.gui import fps
from pyglet import euclid

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

ROT_30_X = euclid.Matrix4.new_rotatex(math.pi / 12)
ROT_N30_X = euclid.Matrix4.new_rotatex(-math.pi / 12)
ROT_30_Z = euclid.Matrix4.new_rotatez(math.pi / 12)
ROT_N30_Z = euclid.Matrix4.new_rotatez(-math.pi / 12)
def drawBranch(n, l, r):
    glVertex3f(l.p1.x, l.p1.y, l.p1.z)
    glVertex3f(l.p2.x, l.p2.y, l.p2.z)
    if n == 0:
        return

    if r:
        if random.random() > .9: return
        mag = abs(l.v) * (.5 + .5 * random.random())
    else:
        mag = abs(l.v) * .75
    if n%2:
        v1 = ROT_30_X * l.v
        v2 = ROT_N30_X * l.v
    else:
        v1 = ROT_30_Z * l.v
        v2 = ROT_N30_Z * l.v
    drawBranch(n-1, euclid.Line3(l.p2, v1, mag), r)
    drawBranch(n-1, euclid.Line3(l.p2, v2, mag), r)

def drawTree(n=2, r=False):
    glLineWidth(2.)
    glColor4f(.5, .5, .5, .5)
    glBegin(GL_LINES)
    drawBranch(n-1, euclid.Line3(euclid.Point3(0., 0., 0.),
        euclid.Vector3(0., 1., 0.), 1.), r)
    glEnd()

class Tree(object):
    def __init__(self, n=2, r=False):
        self.dl = glGenLists(1)
        glNewList(self.dl, GL_COMPILE)
        drawTree(n, r)
        glEndList()
        self.x = self.y = 0
        self.rx = self.ry = 0
        self.zpos = -10
        self.lmb = False
        self.rmb = False

    def on_mousemotion(self, x, y, dx, dy):
        if self.lmb:
            self.rx += dx
            self.ry += dy
        if self.rmb:
            self.x += dx
            self.y += dy

    def on_buttonpress(self, button, x, y, modifiers):
        if button == MOUSE_LEFT_BUTTON:
            self.lmb = True
        elif button == MOUSE_RIGHT_BUTTON:
            self.rmb = True
        elif button == MOUSE_SCROLL_UP:
            self.zpos = max(-10, self.zpos + 1)
        elif button == MOUSE_SCROLL_DOWN:
            self.zpos -= 1
    def on_buttonrelease(self, button, x, y, modifiers):
        if button == MOUSE_LEFT_BUTTON:
            self.lmb = False
        elif button == MOUSE_RIGHT_BUTTON:
            self.rmb = False

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
tree2 = Tree(n=10, r=True)
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

