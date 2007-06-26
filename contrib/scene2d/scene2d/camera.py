#!/usr/bin/env python

'''
Camera for projecting 2d flat scenes
====================================

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.gl import *
from pyglet.event import *

class Camera(object):
    def project(self):
        '''Set up the GL projection matrix. Leave us in GL_MODELVIEW mode.
        '''
        raise NotImplemented()

    def on_resize(self, width, height):
        '''Handle resize of the viewport.
        '''
        raise NotImplemented()

class FlatCamera(Camera):
    def __init__(self, x, y, width, height, near=-50, far=50):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.near, self.far = near, far

    def project(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glViewport(self.x, self.y, self.width, self.height)
        glOrtho(0, self.width, 0, self.height, self.near, self.far)
        glMatrixMode(GL_MODELVIEW)

    def on_resize(self, width, height):
        self.width, self.height = width, height
        return EVENT_UNHANDLED

    def __repr__(self):
        return '<%s object at 0x%x pos=(%d,%d) size=(%d,%d)>'%(
            self.__class__.__name__, id(self), self.x, self.y, self.width,
            self.height)
