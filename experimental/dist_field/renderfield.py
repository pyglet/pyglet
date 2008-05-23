#!/usr/bin/python
# $Id:$

import sys

import pyglet
from pyglet.gl import *

class DistFieldTextureGroup(pyglet.sprite.SpriteGroup):
    def set_state(self):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)

        glPushAttrib(GL_COLOR_BUFFER_BIT)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GREATER, 0.5)

class DistFieldSprite(pyglet.sprite.Sprite):
    def __init__(self, 
                 img, x=0, y=0,
                 blend_src=GL_SRC_ALPHA,
                 blend_dest=GL_ONE_MINUS_SRC_ALPHA,
                 batch=None,
                 group=None,
                 usage='dynamic'):
        super(DistFieldSprite, self).__init__(
            img, x, y, blend_src, blend_dest, batch, group, usage)
        
        self._group = DistFieldTextureGroup(
            self._texture, blend_src, blend_dest, group)
        self._usage = usage
        self._create_vertex_list()

window = pyglet.window.Window(resizable=True)

image = pyglet.image.load(sys.argv[1])
image.anchor_x = image.width // 2
image.anchor_y = image.height // 2
sprite = DistFieldSprite(image)

@window.event
def on_resize(width, height):
    scale_width = width / float(image.width)
    scale_height = height / float(image.height)
    sprite.scale = min(scale_width, scale_height)
    sprite.x = width / 2
    sprite.y = height / 2

@window.event
def on_draw():
    window.clear()
    sprite.draw()

pyglet.app.run()
