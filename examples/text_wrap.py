#!/usr/bin/env python

'''Example of simple text wrapping without using layout.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.gl import *
from pyglet.window import *
from pyglet.window.event import *
from pyglet.window import key
from pyglet import clock
from pyglet.ext.scene2d.textsprite import *
from pyglet.font import *

window = Window(visible=False, resizable=True)
font = load_font('Arial', 24)
text = 'Type away... '

def on_resize(width, height):
    sprite.width = width
    sprite.x = 10
    return True

def on_text(text):
    sprite.text += text.replace('\r', '\n')

def on_key_press(symbol, modifiers):
    if symbol == key.BACKSPACE:
        sprite.text = sprite.text[:-1]
    else:
        return EVENT_UNHANDLED

window.push_handlers(on_resize)
window.push_handlers(on_text)
window.push_handlers(on_key_press)

sprite = TextSprite(font, text, color=(0, 0, 0, 1))

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
