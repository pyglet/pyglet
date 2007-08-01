#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.window import Window
from pyglet import clock
from scene2d.textsprite import *
from pyglet import font

width, height = 640, 480
window = Window(width=width, height=height)

arial = font.load('Arial', 500, bold=True)
commander = TextSprite(arial, 'COMMANDER', color=(1, 1, 1, 0.5))
keen = TextSprite(arial, 'KEEN', color=(1, 1, 1, 0.5))

print dir(keen)
commander.x = width
keen.x = -keen.width
commander.dx = -(commander.width + width) / 10
keen.dx = (keen.width + width) / 10 

clock.set_fps_limit(30)

while not window.has_exit:
    window.dispatch_events()
    time = clock.tick()
    glClear(GL_COLOR_BUFFER_BIT)
    for text in (commander, keen):
        glLoadIdentity()
        text.x += text.dx * time
        text.draw()
    window.flip()
