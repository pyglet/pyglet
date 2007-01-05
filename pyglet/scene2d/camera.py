#!/usr/bin/env python

'''
Camera for projecting 2d flat scenes
====================================

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.GL.VERSION_1_1 import *

class FlatCamera(object):
    def __init__(self, x, y, width, height, near=-50, far=50):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.near, self.far = near, far

    def project(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glViewport(self.x, self.y, self.width, self.height)
        glOrtho(self.x, self.width, self.y, self.height, self.near, self.far)

    def on_resize(self, width, height):
        self.width, self.height = width, height

