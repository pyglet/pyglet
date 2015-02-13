#!/usr/bin/env python

'''Draws a full-window quad with two texture units enabled and multi
texcoords.  Texture unit 0 is a checker pattern of yellow and cyan with
env mode replace.  Texture unit 1 is a checker pattern of cyan and yellow,
with env mode modulate.  The result should be flat green (with some variation
in the center cross).

The test will correctly detect the asbence of multitexturing, or if texture
coords are not supplied for a unit, but will still pass if the texture
coordinates for each unit are swapped (the tex coords are identical).
'''

import unittest

import pyglet
from pyglet.gl import *

class MultiTextureTestCase(unittest.TestCase):
    def test_multitexture(self):
        window = pyglet.window.Window(width=64, height=64)
        window.dispatch_events()
        w = window.width
        h = window.height

        pattern0 = pyglet.image.CheckerImagePattern(
            (255, 255, 0, 255), (0, 255, 255, 255))
        texture0 = pattern0.create_image(64, 64).get_texture()

        pattern1 = pyglet.image.CheckerImagePattern(
            (0, 255, 255, 255), (255, 255, 0, 255))
        texture1 = pattern1.create_image(64, 64).get_texture()

        batch = pyglet.graphics.Batch()
        batch.add(4, GL_QUADS, None, 
            ('v2i', [0, 0, w, 0, w, h, 0, h]),
            ('0t3f', texture1.tex_coords),
            ('1t3f', texture0.tex_coords)
        )

        glActiveTexture(GL_TEXTURE0)
        glEnable(texture0.target)
        glBindTexture(texture0.target, texture0.id)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        glActiveTexture(GL_TEXTURE1)
        glEnable(texture1.target)
        glBindTexture(texture1.target, texture1.id)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        batch.draw()
        self.assertEqual(self.sample(2,   2), (0, 255, 0))
        self.assertEqual(self.sample(62,  2), (0, 255, 0))
        self.assertEqual(self.sample(62, 62), (0, 255, 0))
        self.assertEqual(self.sample(2,  62), (0, 255, 0))

        window.close()
    
    def sample(self, x, y):
        color_buffer = pyglet.image.get_buffer_manager().get_color_buffer()
        buffer = color_buffer.get_image_data()
        data = buffer.get_data('RGB', buffer.pitch)
        i = y * buffer.pitch + x * 3
        r, g, b = data[i:i+3]
        if type(r) is str:
            r, g, b = map(ord, (r, g, b))
        return r, g, b

