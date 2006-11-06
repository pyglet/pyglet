import os

from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *

from pyglet.text import Font

# XXX 
filename = os.path.join(os.path.split(__file__)[0], '../../examples/Vera.ttf')
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
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        fps = clock.get_fps()
        ifps = int(fps)
        if fps - ifps > .5: ifps += 1
        if ifps != self.ifps:
            self.text = self.f.render(str(ifps) + ' fps')
            self.text.set_anchor('top', 'left')
            self.ifps = ifps

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()

        # handle align
        vert, horiz = align
        y = {
            'top': window.height,
            'middle': window.height/2 - self.text.height/2,
            'bottom': self.text.height,
        }[vert]
        x = {
            'left': 0,
            'center': window.width/2 - self.text.width/2,
            'right': window.width - self.text.width,
        }[horiz]
        glTranslatef(x, y, 0)

        glColor4f(0, 0, 0, .5)
        glBegin(GL_QUADS)
        glVertex3f(-5, +5, 5)
        glVertex3f(self.text.width, +5, 5)
        glVertex3f(self.text.width, -self.text.height-5, 5)
        glVertex3f(-5, -self.text.height-5, 5)
        glEnd()

        self.text.color = (1,1,1,1)
        self.text.draw()

        glPopMatrix()

        glPopAttrib()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

        glPopAttrib()
