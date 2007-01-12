#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.window import *
from pyglet.window.event import *
from pyglet.clock import *
from pyglet.scene2d.textsprite import *
from pyglet.text import *

width, height = 640, 480
window = Window(width=width, height=height)

font = Font('Arial', 500, bold=True)
commander = TextSprite(font, 'COMMANDER', color=(1, 1, 1, 0.5))
keen = TextSprite(font, 'KEEN', color=(1, 1, 1, 0.5))

commander.x = width
keen.x = -keen.width
commander.dx = -(commander.width + width) / 10
keen.dx = (keen.width + width) / 10 

glMatrixMode(GL_PROJECTION)
glOrtho(0, width, 0, height, -1, 1)
glMatrixMode(GL_MODELVIEW)

clock = Clock()

while not window.has_exit:
    window.dispatch_events()
    time = clock.tick()
    glClear(GL_COLOR_BUFFER_BIT)
    for text in (commander, keen):
        glLoadIdentity()
        text.x += text.dx * time
        text.draw()
    window.flip()
