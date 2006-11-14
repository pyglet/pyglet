import sys
import os
import time

import pyglet.window
from pyglet.window.event import *
from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *
from pyglet import clock
from pyglet import text

from ctypes import *

w1 = pyglet.window.create(400, 200)

if len(sys.argv) == 2:
    filename = sys.argv[1]
else:
    filename = os.path.join(os.path.split(__file__)[0], 'Vera.ttf')
factory = text.LocalFontFactory(os.path.split(__file__)[0])
font = factory.get_font('bitstream vera sans', 26)
#sample = text.layout_text('Hello, World. gVAWAVA. Mr. T.', font=font)
sample = text.layout_html('''<font size="26"><i>Hello</i>,
    <b>World</b>.<br>gVAWAVA. <b><i>Mr.</i></b> T.</font>''',
    font_factory=factory)

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

