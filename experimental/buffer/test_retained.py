#!/usr/bin/python
# $Id:$

from pyglet.gl import *
from pyglet import graphics
from pyglet import window

win = window.Window()

batch = graphics.Batch()
batch.add(3, GL_TRIANGLES, None,
    ('v2f', [10., 10., 
             100., 10., 
             100., 100.]),
    ('c3B', [255, 0, 0,
             0, 255, 0,
             0, 0, 255]))

while not win.has_exit:
    win.dispatch_events()
    win.clear()
    batch.draw()    
    win.flip()
