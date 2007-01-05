#!/usr/bin/env python

'''
Draw OpenGL textures in 2d scenes
=================================

---------------
Getting Started
---------------

You may create a drawable image with:

    >>> from pyglet.scene2d import *
    >>> i = Image2d.load('kitten.jpg')
    >>> i.draw()

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.GL.VERSION_1_1 import *
from pyglet.image import RawImage

# XXX remember file image comes from
class Image2d(object):
    def __init__(self, texture, x, y, width, height):
        self.texture = texture
        self.x, self.y = x, y
        self.width, self.height = width, height

    __quad_list = None
    def quad_list(self):
        if self.__quad_list is not None:
            return self.__quad_list

        # textures are upside-down so we need to compensate for that
        # XXX make textures not lie about their size
        tw, th = self.texture.width, self.texture.height
        tw, th, x, x = self.texture.get_texture_size(tw, th)
        l = float(self.x) / tw
        b = float(self.y) / th
        r = float(self.x + self.width) / tw
        t = float(self.y + self.height) / th

        # Make quad display list
        self.__quad_list = glGenLists(1)
        glNewList(self.__quad_list, GL_COMPILE)
        glBindTexture(GL_TEXTURE_2D, self.texture.id)
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)

        glBegin(GL_QUADS)
        glTexCoord2f(l, b)
        glVertex2f(0, 0)
        glTexCoord2f(l, t)
        glVertex2f(0, self.height)
        glTexCoord2f(r, t)
        glVertex2f(self.width, self.height)
        glTexCoord2f(r, b)
        glVertex2f(self.width, 0)
        glEnd()

        glPopAttrib()
        glEndList()
        return self.__quad_list
    quad_list = property(quad_list)

    def draw(self):
        glCallList(self.quad_list)

    @classmethod
    def load(cls, filename=None, file=None):
        '''Image is loaded from the given file.'''
        image = RawImage.load(filename=filename, file=file)
        return cls(image.texture(), 0, 0, image.width, image.height)

    @classmethod
    def from_image(cls, image):
        return cls(image.texture(), 0, 0, image.width, image.height)

    @classmethod
    def from_texture(cls, texture):
        '''Image is the entire texture.'''
        return cls(texture, 0, 0, texture.width, texture.height)

    @classmethod
    def from_subtexture(cls, texture, x, y, width, height):
        '''Image is a section of the texture.'''
        return cls(texture, x, y, width, height)

    def subimage(self, x, y, width, height):
        # XXX should we care about recursive sub-image calls??
        return self.__class__(self.texture, x, y, width, height)

