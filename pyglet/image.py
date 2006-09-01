#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import re

from OpenGL.GL import *
from SDL import *

try:
    from SDL.image import *
    _have_SDL_image = True
except:
    _have_SDL_image = False

try:
    import Image
    _have_PIL = True
except:
    _have_PIL = False

def load(file):
    '''Load an SDL_Surface from a file object or filename.'''
    if not hasattr(file, 'read'):
        file = open(file, 'rb')

    image = None
    if _have_SDL_image:
        try:
            image = IMG_Load_RW(SDL_RWFromObject(file), 0)
        except:
            pass

    if not image and _have_PIL:
        try:
            # TODO load with PIL
            pass
        except:
            pass

    if not image:
        try:
            image = SDL_LoadBMP_RW(SDL_RWFromObject(file), 0)
        except:
            pass

    if not image:
        raise IOError('Could not open file using any available image loader.')

    return image

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

    id = glGenTextures(1)
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
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    return id, uv

class Texture(object):
    __slots__ = ['size', 'id', 'uv', 'quad_list']

    def __init__(self, surface):
        self.size = surface.w, surface.h
        self.id, self.uv = _get_texture(surface)

        # Make quad display list
        self.quad_list = glGenLists(1)
        glNewList(self.quad_list, GL_COMPILE)
        glBindTexture(GL_TEXTURE_2D, self.id)
        glBegin(GL_QUADS)
        glTexCoord(0, 0)
        glVertex(0, 0)
        glTexCoord(self.uv[0], 0)
        glVertex(self.size[0], 0)
        glTexCoord(self.uv[0], self.uv[1])
        glVertex(self.size[0], self.size[1])
        glTexCoord(0, self.uv[1])
        glVertex(0, self.size[1])
        glEnd()
        glEndList()

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)
        glCallList(self.quad_list)
        glPopAttrib()

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
                    glTexCoord(u, v)
                    glVertex(0, 0)
                    glTexCoord(u + du, v)
                    glVertex(elem_size[0], 0)
                    glTexCoord(u + du, v + dv)
                    glVertex(elem_size[0], elem_size[1])
                    glTexCoord(u, v + dv)
                    glVertex(0, elem_size[1])
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
                glTexCoord(u, v)
                glVertex(0, 0)
                glTexCoord(u + du, v)
                glVertex(elem_size[0], 0)
                glTexCoord(u + du, v + dv)
                glVertex(elem_size[0], elem_size[1])
                glTexCoord(u, v + dv)
                glVertex(0, elem_size[1])
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
