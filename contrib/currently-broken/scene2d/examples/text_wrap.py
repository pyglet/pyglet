#!/usr/bin/env python

'''Example of simple text wrapping without using layout.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.gl import *
from pyglet.window import Window
from pyglet.window import key
from pyglet import clock
from pyglet import font
from scene2d.textsprite import *

window = Window(visible=False, resizable=True)
arial = font.load('Arial', 24)
text = 'Type away... '

@window.event
def on_resize(width, height):
    sprite.width = width
    sprite.x = 10

@window.event
def on_text(text):
    sprite.text += text.replace('\r', '\n')

@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.BACKSPACE:
        sprite.text = sprite.text[:-1]

sprite = TextSprite(arial, text, color=(0, 0, 0, 1))

fps = clock.ClockDisplay()
window.push_handlers(fps)

glClearColor(1, 1, 1, 1)


window.set_visible()
while not window.has_exit:
    window.dispatch_events()
    clock.tick()

    glClear(GL_COLOR_BUFFER_BIT)
    sprite.y = sprite.height # TODO align on bottom
    sprite.draw()
    fps.draw()
    window.flip()
