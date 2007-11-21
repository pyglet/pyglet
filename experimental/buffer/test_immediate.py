#!/usr/bin/python
# $Id:$

from pyglet.gl import *
from pyglet import window

import graphics

win = window.Window()

while not win.has_exit:
    win.dispatch_events()
    win.clear()
    graphics.draw(GL_TRIANGLES,
        ('v2f', [10., 10., 
                 100., 10., 
                 100., 100.]),
        ('c3B', [255, 0, 0,
                 0, 255, 0,
                 0, 0, 255]))
    win.flip()
