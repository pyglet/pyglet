import os

from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *

from pyglet.text import Font

# XXX 
filename = os.path.join(os.path.split(__file__)[0], '../../tests/Vera.ttf')
f = Font.load_font(filename, 26)

def render(window, clock, align=('top', 'left')):
    window.switch_to()
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, window.width, 0, window.height, -1, 1)

    fps = clock.get_fps()
    ifps = int(fps)
    if fps - ifps > .5: ifps += 1
    text = f.render(str(ifps) + ' fps')

    # XXX handle align
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glTranslatef(window.width/2, window.height/2, 0)
    glTranslatef(-text.width/2, -text.height/2, 0)
    glColor4f(0, 0, 0, 1)
    glBegin(GL_QUADS)
    glVertex3f(0, 0, 5)
    glVertex3f(text.width, 0, 5)
    glVertex3f(text.width, text.height, 5)
    glVertex3f(0, text.height, 5)
    glEnd()
    text.draw()
    glPopMatrix()

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()

    glMatrixMode(GL_MODELVIEW)
