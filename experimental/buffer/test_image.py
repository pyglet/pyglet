#!/usr/bin/python
# $Id:$

from pyglet.gl import *
from pyglet import window, image

import graphics

win = window.Window()

class TextureState:
    def __init__(self, texture):
        self.texture = texture

    def set(self):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)

    def unset(self):
        glDisable(self.texture.target)

kitten = image.load('examples/programming_guide/kitten.jpg').texture

batch = graphics.Batch()
t = kitten.tex_coords
w = kitten.width
h = kitten.height
batch.add(4, GL_QUADS, TextureState(kitten),
    ('v3f', (0., 0., 0.) + (w, 0., 0.) + (w, h, 0.) + (0., h, 0.)),
    ('t3f', t[0] + t[1] + t[2] + t[3]))

while not win.has_exit:
    win.dispatch_events()
    win.clear()
    batch.draw()
    win.flip()

