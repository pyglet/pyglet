#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import re

from ctypes import *

from pyglet.GL.VERSION_1_1 import *

class Image(object):
    def __init__(self, data, width, height, components):
        self.data = data
        self.width = width
        self.height = height
        self.components = components

def _nearest_pow2(n):
    i = 1
    while i < n:
        i <<= 1
    return i

def _get_texture(surface):
    if surface.format.BitsPerPixel != 24 and \
       surface.format.BitsPerPixel != 32:
        raise AttributeError('Unsupported surface format')

    bpp = surface.format.BytesPerPixel
    size = surface.w, surface.h
    width = _nearest_pow2(surface.w)
    height = _nearest_pow2(surface.h)
    uv = (float(surface.w) / width,
               float(surface.h) / height)

    data = surface.pixels.to_string()
    if width * bpp > surface.pitch:
        # Pad rows
        pad = '\0' * (width * bpp - surface.pitch)
        rows = re.findall('.' * surface.pitch, data, re.DOTALL)
        rows = [row + pad for row in rows]
        data = ''.join(rows)
    if height > surface.h:
        data += '\0' * ((height - surface.h) * width * bpp)

    id = c_uint()
    glGenTextures(1, byref(id))
    id = id.value
    glBindTexture(GL_TEXTURE_2D, id)
    glTexImage2D(GL_TEXTURE_2D,
                 0,
                 bpp,
                 width,
                 height,
                 0,
                 GL_RGBA,
                 GL_UNSIGNED_BYTE,
                 data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    return id, uv

class Texture(object):
    __slots__ = ['size', 'id', 'uv', 'quad_list']

    def __init__(self, id, width, height, uv):
        self.id = id
        self.size = width, height
        self.uv = uv

        # Make quad display list
        self.quad_list = glGenLists(1)
        glNewList(self.quad_list, GL_COMPILE)
        glBindTexture(GL_TEXTURE_2D, self.id)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(0, 0)
        glTexCoord2f(self.uv[0], 0)
        glVertex2f(self.size[0], 0)
        glTexCoord2f(self.uv[0], self.uv[1])
        glVertex2f(self.size[0], self.size[1])
        glTexCoord2f(0, self.uv[1])
        glVertex2f(0, self.size[1])
        glEnd()
        glEndList()

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)
        glCallList(self.quad_list)
        glPopAttrib()

    @classmethod
    def from_surface(cls, surface):
        id, uv = _get_texture(surface)
        return Texture(id, surface.w, surface.h, uv)

class TextureAtlas(object):
    __slots__ = ['size', 'id', 'rows', 'cols', 
                 'elem_sizes', 'uvs', 'quad_lists']

    def __init__(self, surface, rows=1, cols=1, rects=[]):
        assert rects or (rows >= 1 and cols >= 1)
        self.size = surface.w, surface.h
        self.id, uv = _get_texture(surface)
        self.uvs = []
        self.quad_lists = []
        self.elem_sizes = []

        if not rects:
            # Use rows and cols
            self.rows = rows
            self.cols = cols

            elem_size = self.size[0] / cols, self.size[1] / rows
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

