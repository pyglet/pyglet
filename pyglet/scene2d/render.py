import operator

from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *

class FlatRenderer:
    def __init__(self, scene, x, y, w, h, allow_oob=True, scale=1,
            rotation=0):
        self.scene = scene
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.allow_oob = allow_oob
        self.scale = scale
        self.rotation = rotation

    def draw(self, position):
        ''' Draw the scene centered (or closest, depending on allow_oob)
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

    def debug(self, position, style='lines'):
        ''' Draw the scene centered (or closest, depending on allow_oob)
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
            if style == 'checkered':
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
                        if style == 'lines':
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
                        elif style == 'checkered':
                            if n % 3 == 0:
                                glColor4f(.7, .7, .7, 1)
                            if n % 3 == 1:
                                glColor4f(.9, .9, .9, 1)
                            elif n % 3 == 2:
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
                        if style == 'lines':
                            glBegin(GL_LINE_LOOP)
                            glVertex2f(*tile.topleft)
                            glVertex2f(*tile.topright)
                            glVertex2f(*tile.bottomright)
                            glVertex2f(*tile.bottomleft)
                            glEnd()
                        elif style == 'checkered':
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
class AxiometricRenderer:
    viewport = (x, y, w, h)     # origin, dimensions
    allow_oob = False
    scale = (x, y, z, w)        # per-axis scaling
    scene =                     # Scene instance
    rotation =
 
    def draw(self, position):
 
    def sprite_at(self, (x, y)):
        ' query for sprite at given screen pixel position '
 
class PerspectiveRenderer:
    viewport = (x, y, w, h)     # origin, dimensions
    allow_oob = False
    scale = 1
    eye_offset = (x, y, z)      # offset from render position
    scene =                     # Scene instance
    rotation =
 
    def draw(self, position):
'''
