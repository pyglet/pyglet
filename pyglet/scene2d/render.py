
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

        # XXX save state
        glClear(GL_COLOR_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)

        # sort by depth
        l = []
        for map in self.scene.maps:
            if not map.images: continue
            l.append((map.z, map.images, map))
        l.sort()

        # now draw
        for x, images, map in l:
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
