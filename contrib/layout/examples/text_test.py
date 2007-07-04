import sys
import os
import time

from pyglet.window import *
from pyglet.window.event import *
from pyglet.gl import *
from pyglet import clock

from layout import *

from ctypes import *

w = Window(width=400, height=200)

layout = render_html('''<p style="font-size: 26px"><strong>hello</strong>
    <em>world</em></p>''')
layout.render_device.width = 400
layout.render_device.height = 200
layout.layout()

c = clock.Clock(10)

glClearColor(1, 1, 1, 1)

while not w.has_exit:
    c.tick()
    w.dispatch_events()

    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    glTranslatef(10, 100, 0)#, (text.Align.center, text.Align.center))
    layout.draw()

    w.flip()

