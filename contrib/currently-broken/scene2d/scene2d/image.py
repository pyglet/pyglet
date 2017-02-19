#!/usr/bin/env python

'''
Draw OpenGL textures in 2d scenes
=================================

---------------
Getting Started
---------------

You may create a drawable image with:

    >>> from scene2d import *
    >>> i = Image2d.load('kitten.jpg')
    >>> i.draw()

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.gl import *

from pyglet import image
from scene2d.drawable import *
from resource import register_factory, ResourceError


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
    def __init__(self, texture, x, y):
        super(Image2d, self).__init__()
        self.texture = texture
        self.x = x
        self.y = y
        self.width = texture.width
        self.height = texture.height
        self.uvs = texture.tex_coords

    @classmethod
    def load(cls, filename=None, file=None):
        '''Image is loaded from the given file.'''
        img = image.load(filename=filename, file=file)
        img = cls(img.texture, 0, 0)
        img.filename = filename
        return img

    @classmethod
    def from_image(cls, image):
        return cls(image.texture, 0, 0)

    @classmethod
    def from_texture(cls, texture):
        '''Image is the entire texture.'''
        return cls(texture, 0, 0)

    @classmethod
    def from_subtexture(cls, texture, x, y, width, height):
        '''Image is a section of the texture.'''
        return cls(texture.get_region(x, y, width, height), x, y)

    __quad_list = None
    def quad_list(self):
        if self.__quad_list is not None:
            return self.__quad_list

        # Make quad display list
        self.__quad_list = glGenLists(1)
        glNewList(self.__quad_list, GL_COMPILE)
        #self.texture.blit(0, 0, 0)  # This does same as QUADS below
        glBegin(GL_QUADS)
        glTexCoord3f(*self.uvs[:3])
        glVertex2f(0, 0)
        glTexCoord3f(*self.uvs[3:6])
        glVertex2f(0, self.height)
        glTexCoord3f(*self.uvs[6:9])
        glVertex2f(self.width, self.height)
        glTexCoord3f(*self.uvs[9:12])
        glVertex2f(self.width, 0)
        glEnd()
        glEndList()
        return self.__quad_list
    quad_list = property(quad_list)

    def get_drawstyle(self):
        # XXX note we don't pass in self.x/y here as they're offsets into the
        # texture, not offsets to use when rendering the image to screen
        # for other scene2d objects that *is* what .x/y are for - perhaps
        # that's what they should be for here...
        return DrawStyle(color=(1, 1, 1, 1), texture=self.texture,
            # <ah> uvs looks quite wrong here
            width=self.width, height=self.height, uvs=(0,0,0,0),
            draw_list=self.quad_list, draw_env=DRAW_BLENDED)

    def subimage(self, x, y, width, height):
        return self.__class__(self.texture.get_region(x, y, width, height), 
                              x, y)

