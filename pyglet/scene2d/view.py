#!/usr/bin/env python

'''
View code for displaying 2d scenes of maps and sprites
======================================================

---------------
Getting Started
---------------

Creating a simple scene and displaying it:

    >>> import pyglet.window
    >>> import pyglet.scene2d
    >>> m = pyglet.scene2d.Map(32, 32, images=[[0]*4]*4)
    >>> w = pyglet.window.Window(width=m.pxw, height=m.pxh)
    >>> s = pyglet.scene2d.Scene(maps=[m])
    >>> r = pyglet.scene2d.FlatView(s, 0, 0, m.pxw, m.pxh)
    >>> r.debug((0,0))
    >>> w.flip()

------------------
Events and Picking
------------------


'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import operator

from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *

class FlatView:
    '''Render a flat view of a pyglet.scene2d.Scene.

    Attributes:

        scene           -- a pyglet.scene2d.Scene instance
        x, y, w, h      -- viewport specification
        allow_oob       -- indicates whether the viewport will allow
                           viewing of out-of-bounds tile positions (ie.
                           for which there is no tile image). If set to
                           False then the map will not scroll to attempt
                           to display oob tiles.
        scale, rotation -- scale to apply to the map (rotation in degrees)
        focus           -- pixel point to center in the viewport, subject
                           to OOB checks
    '''
    def __init__(self, scene, x, y, w, h, allow_oob=True, scale=1,
            rotation=0, focus=(0, 0)):
        self.scene = scene
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.allow_oob = allow_oob
        self.scale = scale
        self.rotation = rotation
        self.focus = focus

    def get(self, x, y):
        ''' Pick whatever is on the top at the position x, y. '''

    def draw(self):
        '''Draw the scene centered (or closest, depending on allow_oob)
        on position which is (x, y). '''
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glViewport(self.x, self.y, self.w, self.h)
        glOrtho(self.x, self.w, self.y, self.h, -50, 50)
        glMatrixMode(GL_MODELVIEW)

        # sort by depth
        self.scene.maps.sort(key=operator.attrgetter('z'))

        # now draw
        for map in self.scene.maps:
            glPushMatrix()
            glTranslatef(map.x, map.y, map.z)
            for column in images:
                glPushMatrix()
                for image in column:
                    image.draw()
                    glTranslatef(0, map.th, 0)
                glPopMatrix()
                glTranslatef(map.tw, 0, 0)
            glPopMatrix()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

    CHECKERED = 'checkered'
    LINES = 'lines'
    def debug(self, style=CHECKERED):
        '''Draw the scene centered (or closest, depending on allow_oob)
        on position which is (x, y). '''
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glViewport(self.x, self.y, self.w, self.h)
        glOrtho(self.x, self.w, self.y, self.h, -50, 50)
        glMatrixMode(GL_MODELVIEW)

        # sort by depth
        self.scene.maps.sort(key=operator.attrgetter('z'))

        # now draw
        for map in self.scene.maps:
            glPushMatrix()
            glTranslatef(map.x, map.y, map.z)
            if style is self.CHECKERED:
                glColor4f(.5, .5, .5, 1)
                glBegin(GL_QUADS)
                glVertex2f(0, 0)
                glVertex2f(0, map.pxh)
                glVertex2f(map.pxw, map.pxh)
                glVertex2f(map.pxw, 0)
                glColor4f(.7, .7, .7, 1)
                glEnd()
            else:
                glColor4f(1, 1, 1, 1)

            if hasattr(map, 'edge_length'):
                # hexes
                for m, column in enumerate(map.images):
                    for n, image in enumerate(column):
                        tile = map.get((m,n))
                        if style is self.LINES:
                            glBegin(GL_LINE_LOOP)
                            glVertex2f(*tile.topleft)
                            glVertex2f(*tile.topright)
                            glVertex2f(*tile.right)
                            glVertex2f(*tile.bottomright)
                            glVertex2f(*tile.bottomleft)
                            glVertex2f(*tile.left)
                            glEnd()
                            glPushMatrix()
                            bl = tile.bottomleft
                            glTranslatef(bl[0], bl[1]+2, 0)
                            image.draw()
                            glPopMatrix()
                        elif style is self.CHECKERED:
                            if not m % 2:  n = n + 1
                            if n%3 == 0:
                                glColor4f(.7, .7, .7, 1)
                            if n%3 == 1:
                                glColor4f(.9, .9, .9, 1)
                            elif n%3 == 2:
                                glColor4f(1, 1, 1, 1)
                            glBegin(GL_POLYGON)
                            glVertex2f(*tile.topleft)
                            glVertex2f(*tile.topright)
                            glVertex2f(*tile.right)
                            glVertex2f(*tile.bottomright)
                            glVertex2f(*tile.bottomleft)
                            glVertex2f(*tile.left)
                            glEnd()
                        else:
                            raise ValueError, "style not 'lines' or 'checkered'"
            else:
                # rects
                for m, column in enumerate(map.images):
                    for n, image in enumerate(column):
                        tile = map.get((m,n))
                        if style is self.LINES:
                            glBegin(GL_LINE_LOOP)
                            glVertex2f(*tile.topleft)
                            glVertex2f(*tile.topright)
                            glVertex2f(*tile.bottomright)
                            glVertex2f(*tile.bottomleft)
                            glEnd()
                        elif style is self.CHECKERED:
                            if (m + n) % 2:
                                glBegin(GL_QUADS)
                                glVertex2f(*tile.topleft)
                                glVertex2f(*tile.topright)
                                glVertex2f(*tile.bottomright)
                                glVertex2f(*tile.bottomleft)
                                glEnd()
                        else:
                            raise ValueError, "style not 'lines' or 'checkered'"
            glPopMatrix()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
 
    def tile_at(self, (x, y)):
        ' query for tile at given screen pixel position '
        pass
 
    def sprite_at(self, (x, y)):
        ' query for sprite at given screen pixel position '
        pass
 
'''
class AxiometricView:
    viewport = (x, y, w, h)     # origin, dimensions
    allow_oob = False
    scale = (x, y, z, w)        # per-axis scaling
    scene =                     # Scene instance
    rotation =
 
    def draw(self, position):
 
    def sprite_at(self, (x, y)):
        ' query for sprite at given screen pixel position '
 
class PerspectiveView:
    viewport = (x, y, w, h)     # origin, dimensions
    allow_oob = False
    scale = 1
    eye_offset = (x, y, z)      # offset from render position
    scene =                     # Scene instance
    rotation =
 
    def draw(self, position):
'''
