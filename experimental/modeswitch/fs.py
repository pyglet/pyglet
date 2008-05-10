#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import pyglet
from pyglet.gl import *

window = pyglet.window.Window(fullscreen=True)

@window.event
def on_draw():
    glClearColor(.5, .5, .5, 1)
    glClear(GL_COLOR_BUFFER_BIT)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glColor3f(1, 0, 0)
    glRectf(1, 1, 759, 599)
    glColor3f(0, 1, 0)
    glRectf(1, 1, 639, 479)

pyglet.app.run()
