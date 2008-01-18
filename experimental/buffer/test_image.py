#!/usr/bin/python
# $Id:$

from pyglet.gl import *
from pyglet import graphics
from pyglet import image
from pyglet import window

win = window.Window()

kitten = image.load('examples/programming_guide/kitten.jpg').texture

batch = graphics.Batch()
t = kitten.tex_coords
w = kitten.width
h = kitten.height
batch.add(4, GL_QUADS, graphics.TextureState(kitten),
    ('v3f', (0., 0., 0.) + (w, 0., 0.) + (w, h, 0.) + (0., h, 0.)),
    ('t3f', t))

while not win.has_exit:
    win.dispatch_events()
    win.clear()
    batch.draw()
    win.flip()

