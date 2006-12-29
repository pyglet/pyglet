#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import warnings

from pyglet.GL.VERSION_1_1 import *
from pyglet.image import *
from pyglet.layout.base import *

class ImageBoxGenerator(BoxGenerator):
    def __init__(self, locator):
        self.locator = locator
        self.cache = {}

    def add_to_formatter(self, formatter):
        formatter.add_box_generator('img', self)

    def create_box(self, name, attrs):
        file = None
        if not attrs.has_key('src'):
            warnings.warn('Image does not have src attribute')
            return Box()

        src = attrs['src']
        if src in self.cache:
            return ImageBox(self.cache[src])

        file = self.locator.get_stream(src)
        if not file:
            # TODO broken image if not file
            warnings.warn('Image not loaded: "%s"' % attrs['src'])
            return Box()

        image = Image.load(file=file)
        self.cache[src] = image
        return ImageBox(image)

class ImageBox(Box):
    def __init__(self, image):
        if not isinstance(image, Texture):
            self.texture = image.texture()
        else:
            self.texture = image

        self.intrinsic_width = image.width
        self.intrinsic_height = image.height
        self.intrinsic_ratio = image.width / float(image.height)

    def draw(self, render_device, left, top, right, bottom):
        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
        glColor3f(1, 1, 1)
        glEnable(GL_TEXTURE_2D)        
        glBindTexture(GL_TEXTURE_2D, self.texture.id)
        glBegin(GL_QUADS)

        # TODO use image.tex_coords to allow subimages here
        glTexCoord2f(0, self.texture.uv[1])
        glVertex2f(left, top)
        glTexCoord2f(0, 0)
        glVertex2f(left, bottom)
        glTexCoord2f(self.texture.uv[0], 0)
        glVertex2f(right, bottom)
        glTexCoord2f(self.texture.uv[0], self.texture.uv[1])
        glVertex2f(right, top)

        glEnd()
        glPopAttrib()
