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
        fx, fy          -- pixel point to center in the viewport, subject
                           to OOB checks
    '''
    def __init__(self, scene, x, y, w, h, allow_oob=True, scale=1,
            rotation=0, fx=0, fy=0):
        self.scene = scene
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.allow_oob = allow_oob
        self.scale = scale
        self.rotation = rotation
        self.fx, self.fy = fx, fy

    def get(self, x, y):
        ''' Pick whatever is on the top at the position x, y. '''
        raise NotImplemented()

    def _determine_focus(self):
        '''Determine the focal point of the view based on foxus (fx, fy),
        allow_oob and maps.

        Note that this method does not actually change the focus attributes
        fx and fy.
        '''
        if not self.scene.maps or self.allow_oob: return (self.fx, self.fy)

        # figure the bounds min/max
        map = self.scene.maps[0]
        b_min_x = map.x
        b_min_y = map.y
        b_max_x = map.x + map.pxw
        b_max_y = map.y + map.pxh
        for map in self.scene.maps[1:]:
            b_min_x = min(b_min_x, map.x)
            b_min_y = min(b_min_y, map.y)
            b_max_x = min(b_max_x, map.x + map.pxw)
            b_max_y = min(b_max_y, map.y + map.pxh)

        # figure the view min/max based on focus
        w2 = self.w/2
        h2 = self.h/2
        fx, fy = self.fx, self.fy
        v_min_x = fx - w2
        v_min_y = fy - w2
        x_moved = y_moved = False
        if v_min_x < b_min_x:
            fx += b_min_x - v_min_x
            x_moved = True
        if v_min_y < b_min_y:
            fy += b_min_y - v_min_y
            y_moved = True

        v_max_x = fx + w2
        v_max_y = fy + w2
        if not x_moved and v_max_x > b_max_x:
            fx -= v_max_x - b_max_x
        if not y_moved and v_max_y > b_max_y:
            fy -= v_max_y - b_max_y

        return fx, fy

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

        # determine the focus point
        fx, fy = self._determine_focus()

        # now draw
        glPushMatrix()
        glTranslatef(self.w/2-fx, self.h/2-fy, 0)
        for map in self.scene.maps:
            glPushMatrix()
            glTranslatef(map.x, map.y, map.z)
            if hasattr(map, 'edge_length'):
                raise NotImplemented()
            else:
                for column in images:
                    glPushMatrix()
                    for image in column:
                        image.draw()
                        glTranslatef(0, map.th, 0)
                    glPopMatrix()
                    glTranslatef(map.tw, 0, 0)
            glPopMatrix()
        glPopMatrix()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

    CHECKERED = 'checkered'
    LINES = 'lines'
    def debug(self, style=CHECKERED, show_focus=False):
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

        # determine the focus point
        fx, fy = self._determine_focus()

        # now draw
        glPushMatrix()
        glTranslatef(self.w/2-fx, self.h/2-fy, 0)
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
                for m, column in enumerate(map.cells):
                    for n, cell in enumerate(column):
                        if style is self.LINES:
                            glBegin(GL_LINE_LOOP)
                            glVertex2f(*cell.topleft)
                            glVertex2f(*cell.topright)
                            glVertex2f(*cell.right)
                            glVertex2f(*cell.bottomright)
                            glVertex2f(*cell.bottomleft)
                            glVertex2f(*cell.left)
                            glEnd()
                            glPushMatrix()
                            bl = cell.bottomleft
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
                            glVertex2f(*cell.topleft)
                            glVertex2f(*cell.topright)
                            glVertex2f(*cell.right)
                            glVertex2f(*cell.bottomright)
                            glVertex2f(*cell.bottomleft)
                            glVertex2f(*cell.left)
                            glEnd()
                        else:
                            raise ValueError, "style not 'lines' or 'checkered'"
            else:
                # rects
                for m, column in enumerate(map.cells):
                    for n, cell in enumerate(column):
                        if style is self.LINES:
                            glBegin(GL_LINE_LOOP)
                            glVertex2f(*cell.topleft)
                            glVertex2f(*cell.topright)
                            glVertex2f(*cell.bottomright)
                            glVertex2f(*cell.bottomleft)
                            glEnd()
                        elif style is self.CHECKERED:
                            if (m + n) % 2:
                                glBegin(GL_QUADS)
                                glVertex2f(*cell.topleft)
                                glVertex2f(*cell.topright)
                                glVertex2f(*cell.bottomright)
                                glVertex2f(*cell.bottomleft)
                                glEnd()
                        else:
                            raise ValueError, "style not 'lines' or 'checkered'"

            if show_focus:
                glColor4f(1, 0, 0, 1)
                glPointSize(5)
                glBegin(GL_POINTS)
                glVertex3f(self.fx, self.fy, 10)
                glEnd()
            glPopMatrix()
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
