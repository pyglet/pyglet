import sys
import os
import ctypes

import pyglet.window
from pyglet.gl import *
from pyglet import clock
from pyglet import image

if len(sys.argv) != 2:
    print 'Usage: %s <PNG/JPEG filename>'%sys.argv[0]
    sys.exit()

window = pyglet.window.Window(width=400, height=400)
image = image.load(sys.argv[1])
imx = imy = 0
@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    global imx, imy
    imx += dx
    imy += dy

clock.set_fps_limit(30)
while not window.has_exit:
    clock.tick()
    window.dispatch_events()
    glClear(GL_COLOR_BUFFER_BIT)
    image.blit(imx, imy, 0)
    window.flip()

