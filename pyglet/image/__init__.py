#!/usr/bin/env python

'''

Image loading is performed by OS components we believe we can rely on.

We ONLY support PNG and JPEG formats, thus enforcing that we only load the
formats we have base support for.

Linux (in order of preference):

   GTK?
   Qt?
   SDL?
   libpng           (will ABORT program if PNG is corrupted)
   libjpeg

Windows:

OS X:

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import re

from ctypes import *

from pyglet.GL.VERSION_1_1 import *

from pyglet.image import png, jpeg

# XXX include the image filename in the args? might help debugging?
class Image(object):
    def __init__(self, data, width, height, bpp):
        self.data = data
        self.width = width
        self.height = height
        self.bpp = bpp

    @classmethod
    def load(cls, filename):
        if re.match(r'.*?\.png$', filename, re.I):
            return png.read(filename)
        if re.match(r'.*?\.jpe?g$', filename, re.I):
            return jpeg.read(filename)
        if png.is_png(filename):
            return png.read(filename)
        if jpeg.is_png(filename):
            return jpeg.read(filename)
        raise ValueError, 'File is not a PNG or JPEG'

    def as_texture(self):
        return Texture.from_image(self)

def _nearest_pow2(n):
    i = 1
    while i < n:
        i <<= 1
    return i

def _get_texture_from_surface(surface):
    if surface.format.BitsPerPixel != 24 and \
       surface.format.BitsPerPixel != 32:
        raise AttributeError('Unsupported surface format')
    return _get_texture(surface.pixels.to_string(), surface.w, surface.h,
        surface.format.BytesPerPixel)

def _get_texture(data, width, height, bpp):
    tex_width = _nearest_pow2(width)
    tex_height = _nearest_pow2(height)
    uv = (float(width) / tex_width, float(height) / tex_height)

    blank = '\0' * tex_width * tex_height * bpp
    if bpp == 3: format = GL_RGB
    else: format = GL_RGBA

    id = c_uint()
    glGenTextures(1, byref(id))
    id = id.value
    glBindTexture(GL_TEXTURE_2D, id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, format, tex_width, tex_height, 0, format,
        GL_UNSIGNED_BYTE, blank)
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, format,
        GL_UNSIGNED_BYTE, data)

    return id, uv

class Texture(object):
    def __init__(self, id, width, height, uv):
        self.id = id
        self.width, self.height = width, height
        self.uv = uv

        # Make quad display list
        self.quad_list = glGenLists(1)
        glNewList(self.quad_list, GL_COMPILE)
        glBindTexture(GL_TEXTURE_2D, self.id)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(0, 0)
        glTexCoord2f(0, self.uv[1])
        glVertex2f(0, self.height)
        glTexCoord2f(self.uv[0], self.uv[1])
        glVertex2f(self.width, self.height)
        glTexCoord2f(self.uv[0], 0)
        glVertex2f(self.width, 0)

        glEnd()
        glEndList()

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)
        glCallList(self.quad_list)
        glPopAttrib()

    @classmethod
    def from_image(cls, image):
        id, uv = _get_texture(image.data, image.width, image.height,
            image.bpp)
        return Texture(id, image.width, image.height, uv)

    @classmethod
    def from_surface(cls, surface):
        id, uv = _get_texture_from_surface(surface)
        return Texture(id, surface.w, surface.h, uv)


class TextureAtlas(object):
    def __init__(self, id, width, height, uv, rows=1, cols=1, rects=[]):
        assert rects or (rows >= 1 and cols >= 1)
        self.size = (width, height)
        self.id = id
        self.uvs = []
        self.quad_lists = []
        self.elem_sizes = []

        if not rects:
            # Use rows and cols
            self.rows = rows
            self.cols = cols

            elem_size = width / cols, height / rows
            n = glGenLists(rows * cols)
            self.quad_lists = range(n, n + rows * cols)
            du = uv[0] / cols
            dv = uv[1] / rows
            i = v = 0
            for row in range(rows):
                u = 0
                for col in range(cols):
                    glNewList(self.quad_lists[i], GL_COMPILE)
                    glBindTexture(GL_TEXTURE_2D, self.id)
                    glBegin(GL_QUADS)
                    glTexCoord2f(u, v)
                    glVertex2f(0, 0)
                    glTexCoord2f(u + du, v)
                    glVertex2f(elem_size[0], 0)
                    glTexCoord2f(u + du, v + dv)
                    glVertex2f(elem_size[0], elem_size[1])
                    glTexCoord2f(u, v + dv)
                    glVertex2f(0, elem_size[1])
                    glEnd()
                    glEndList()

                    elem_uv = (u, v, u + du, v + dv)
                    self.uvs.append(elem_uv)
                    self.elem_sizes.append(elem_size)
                    u += du
                    i += 1
                v += dv
        else:
            self.rows = 1
            self.cols = len(rects)
            n = glGenLists(len(rects))
            self.quad_lists = range(n, n + len(rects))
            for i, rect in enumerate(rects):
                u = float(rect[0]) / surface.w * uv[0]
                v = float(rect[1]) / surface.h * uv[1]
                du = float(rect[2]) / surface.w * uv[0]
                dv = float(rect[3]) / surface.h * uv[1]
                elem_uv = (u, v, u + du, v + dv)
                elem_size = (rect[2], rect[3])

                glNewList(self.quad_lists[i], GL_COMPILE)
                glBindTexture(GL_TEXTURE_2D, self.id)
                glBegin(GL_QUADS)
                glTexCoord2f(u, v)
                glVertex2f(0, 0)
                glTexCoord2f(u + du, v)
                glVertex2f(elem_size[0], 0)
                glTexCoord2f(u + du, v + dv)
                glVertex2f(elem_size[0], elem_size[1])
                glTexCoord2f(u, v + dv)
                glVertex2f(0, elem_size[1])
                glEnd()
                glEndList()

                self.uvs.append(elem_uv)
                self.elem_sizes.append(elem_size)

    @classmethod
    def from_image(cls, image, rows=1, cols=1, rects=[]):
        id, uv = _get_texture(image.data, image.width, image.height,
            image.bpp)
        return TextureAtlas(id, image.width, image.height, uv, rows,
            cols, rects)

    @classmethod
    def from_surface(cls, surface, rows=1, cols=1, rects=[]):
        id, uv = _get_texture_from_surface(surface)
        return TextureAtlas(id, surface.w, surface.h, uv, rows, cols,
            rects)

    def draw(self, row, col):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)
        glCallList(self.quad_lists[row * self.cols + col])
        glPopAttrib()

    def get_size(self, row, col):
        return self.elem_sizes[row * self.cols + col]

    def get_quad(self, row, col):
        i = row * self.cols + col
        return self.elem_sizes[i], self.uvs[i]

