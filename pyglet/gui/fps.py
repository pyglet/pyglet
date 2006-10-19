import os

from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *

from pyglet.text import Font

# XXX 
filename = os.path.join(os.path.split(__file__)[0], '../../tests/Vera.ttf')
f = Font(filename, 26)

class FPS(object):
    def __init__(self):
        self.f = Font(filename, 26)
        self.ifps = None
        self.text = None

    def draw(self, window, clock, align=('top', 'left')):
        window.switch_to()
        glPushAttrib(GL_TRANSFORM_BIT)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, window.width, 0, window.height, -10, 10)
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)

        fps = clock.get_fps()
        ifps = int(fps)
        if fps - ifps > .5: ifps += 1
        if ifps != self.ifps:
            self.text = self.f.render(str(ifps) + ' fps')
            self.ifps = ifps

        # XXX handle align
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glTranslatef(window.width/2, window.height/2, 0)
        glTranslatef(-self.text.width/2, -self.text.height/2, 0)
        glColor4f(0, 0, 0, 1)
        glBegin(GL_QUADS)
        glVertex3f(-5, -5, 5)
        glVertex3f(self.text.width+5, -5, 5)
        glVertex3f(self.text.width+5, self.text.height+5, 5)
        glVertex3f(-5, self.text.height+5, 5)
        glEnd()

        glTranslatef(0, self.text.height, 0)
        self.text.color = (1,1,1,1)
        self.text.draw()

        glPopMatrix()

        glPopAttrib()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

        glPopAttrib()
