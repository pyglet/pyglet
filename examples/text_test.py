import sys
import os
import time

from pyglet.window import *
from pyglet.window.event import *
from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *
from pyglet import clock
from pyglet import text

from ctypes import *

w1 = Window(width=400, height=200)

sample = text.layout_html('''<font size="26"><i>Hello</i>,
    <b>World</b>.<br>gVAWAVA. <b><i>Mr.</i></b> T.</font>''')

exit_handler = ExitHandler()
w1.push_handlers(exit_handler)

c = clock.Clock()

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, w1.width, 0, w1.height, -1, 1)
glEnable(GL_COLOR_MATERIAL)

glMatrixMode(GL_MODELVIEW)
glClearColor(1, 1, 1, 1)
r = 0

while not exit_handler.exit:
    c.set_fps(10)
    w1.dispatch_events()

    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    text.begin()
    sample.draw((200, 100), (text.Align.center, text.Align.center))
    text.end()

    w1.flip()

