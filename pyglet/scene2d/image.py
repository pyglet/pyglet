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
from pyglet.scene2d.drawable import *
from pyglet.resource import register_factory, ResourceError


@register_factory('imageatlas')
def imageatlas_factory(resource, tag):
    filename = resource.find_file(tag.getAttribute('file'))
    if not filename:
        raise ResourceError, 'No file= on <imageatlas> tag'
    atlas = Image2d.load(filename)
    atlas.properties = resource.handle_properties(tag)
    if tag.hasAttribute('id'):
        atlas.id = tag.getAttribute('id')
        resource.add_resource(atlas.id, atlas)

    # figure default size if specified
    if tag.hasAttribute('size'):
        d_width, d_height = map(int, tag.getAttribute('size').split('x'))
    else:
        d_width = d_height = None

    for child in tag.childNodes:
        if not hasattr(child, 'tagName'): continue
        if child.tagName != 'image':
            raise ValueError, 'invalid child'

        if child.hasAttribute('size'):
            width, height = map(int, child.getAttribute('size').split('x'))
        elif d_width is None:
            raise ValueError, 'atlas or subimage must specify size'
        else:
            width, height = d_width, d_height

        x, y = map(int, child.getAttribute('offset').split(','))
        image = atlas.subimage(x, y, width, height)
        id = child.getAttribute('id')
        resource.add_resource(id, image)

    image.properties = resource.handle_properties(tag)

    if tag.hasAttribute('id'):
        image.id = tag.getAttribute('id')
        resource.add_resource(image.id, image)
        
    return atlas


@register_factory('image')
def image_factory(resource, tag):
    filename = resource.find_file(tag.getAttribute('file'))
    if not filename:
        raise ResourceError, 'No file= on <image> tag'
    image = Image2d.load(filename)

    image.properties = resource.handle_properties(tag)

    if tag.hasAttribute('id'):
        image.id = tag.getAttribute('id')
        resource.add_resource(image.id, image)

    return image


class Image2d(Drawable):
    def __init__(self, texture, x, y, width, height):
        super(Image2d, self).__init__()
        self.texture = texture
        self.x, self.y = x, y
        self.width, self.height = width, height

        # textures are upside-down so we need to compensate for that
        # XXX make textures not lie about their size
        tw, th = self.texture.width, self.texture.height
        tw, th, x, x = self.texture.get_texture_size(tw, th)
        l = float(self.x) / tw
        b = float(self.y) / th
        r = float(self.x + self.width) / tw
        t = float(self.y + self.height) / th
        self.uvs = [(l,b),(l,t),(r,t),(r,b)]

    @classmethod
    def load(cls, filename=None, file=None):
        '''Image is loaded from the given file.'''
        image = RawImage.load(filename=filename, file=file)
        image = cls(image.texture(), 0, 0, image.width, image.height)
        image.filename = filename
        return image

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

    __quad_list = None
    def quad_list(self):
        if self.__quad_list is not None:
            return self.__quad_list

        # Make quad display list
        self.__quad_list = glGenLists(1)
        glNewList(self.__quad_list, GL_COMPILE)
        glBegin(GL_QUADS)
        glTexCoord2f(*self.uvs[0])
        glVertex2f(0, 0)
        glTexCoord2f(*self.uvs[1])
        glVertex2f(0, self.height)
        glTexCoord2f(*self.uvs[2])
        glVertex2f(self.width, self.height)
        glTexCoord2f(*self.uvs[3])
        glVertex2f(self.width, 0)
        glEnd()
        glEndList()
        return self.__quad_list
    quad_list = property(quad_list)

    def get_drawstyle(self):
        return DrawStyle(color=(1, 1, 1, 1), texture=self.texture,
            x=self.x, y=self.y, z=0, width=self.width,
            height=self.height, uvs=self.uvs, draw_list=self.quad_list,
            draw_env=DRAW_BLENDED)

    def subimage(self, x, y, width, height):
        # XXX should we care about recursive sub-image calls??
        return self.__class__(self.texture, x, y, width, height)

