#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.window import *
from pyglet.window.event import *
from pyglet.clock import *
from pyglet.text import *

width, height = 640, 480
window = Window(width=width, height=height)

def on_resize(width, height):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)

    layout.width = width 

exit_handler = ExitHandler()
window.push_handlers(exit_handler)
window.push_handlers(on_resize=on_resize)

font = Font('Georgia', 12)
layout = font.render(
'''In olden times when wishing still helped one, there lived a king whose
daughters were all beautiful, but the youngest was so beautiful that the sun
itself, which has seen so much, was astonished whenever it shone in her face.
Close by the king's castle lay a great dark forest, and under an old lime-tree
in the forest was a well, and when the day was very warm, the king's child
went out into the forest and sat down by the side of the cool fountain, and
when she was bored she took a golden ball, and threw it up on high and caught
it, and this ball was her favorite plaything.'''.replace('\n', ' '),
color=(0, 0, 0, 1))

clock = Clock()

on_resize(width, height)
glClearColor(1, 1, 1, 1)
while not exit_handler.exit:
    window.dispatch_events()
    time = clock.tick()
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0, window.height - font.ascent, 0)
    layout.draw()
    window.flip()
