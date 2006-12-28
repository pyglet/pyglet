#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import re

from ctypes import *
from math import ceil

from pyglet.GL.info import have_extension
from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *
from pyglet.image.codecs import *

class ImageException(Exception):
    pass

class Image(object):
    '''Abstract class representing an image.
    '''

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def texture(self, internalformat=None):
        '''Return a Texture of this image.  This method does not cache
        textures, it will create a new one each time it is called.
        internalformat can be a valid argument to glTexImage2D to specify
        how the image is stored internally, or to specify internal
        compression.
        '''
        raise NotImplementedError()

    def texture_subimage(self, x, y):
        '''Copy the image into the current texture at the given coordinates.
        '''
        raise NotImplementedError()

    def get_raw_image(self, type=GL_UNSIGNED_BYTE):
        '''Read the image and return a RawImage for pixel access.  
        '''
        raise NotImplementedError()

    def save(self, filename=None, file=None, options={}):
        if not file:
            file = open(filename, 'wb')

        first_exception = None
        for encoder in get_encoders(filename):
            try:
                encoder.encode(self, file, filename, options)
                return
            except ImageDecodeException, e:
                first_exception = first_exception or e
                file.seek(0)

        if not first_exception:
            raise ImageEncodeException('No image encoders are available')
        raise first_exception

    @staticmethod
    def load(filename=None, file=None):
        if not file:
            file = open(filename, 'rb')

        first_exception = None
        for decoder in get_decoders(filename):
            try:
                image = decoder.decode(file, filename)
                return image
            except ImageDecodeException, e:
                first_exception = first_exception or e
                file.seek(0)

        if not first_exception:
            raise ImageDecodeException('No image decoders are available')
        raise first_exception

    @staticmethod
    def create_checkerboard(size, 
                          colour1=(150, 150, 150, 255), 
                          colour2=(200, 200, 200, 255)):
        half = size/2
        colour1 = '%c%c%c%c' % colour1
        colour2 = '%c%c%c%c' % colour2
        row1 = colour1 * half + colour2 * half
        row2 = colour2 * half + colour1 * half
        data = row1 * half + row2 * half
        return RawImage(data, size, size, 'RGBA', GL_UNSIGNED_BYTE)

    @staticmethod
    def get_type_ctype(type):
        if type == GL_UNSIGNED_BYTE:
            return c_ubyte
        assert False

    _gl_formats = {
        GL_STENCIL_INDEX: 'L',
        GL_DEPTH_COMPONENT: 'L',
        GL_RED: 'L',
        GL_GREEN: 'L',
        GL_BLUE: 'L',
        GL_ALPHA: 'A',
        GL_RGB: 'RGB',
        GL_BGR: 'BGR',
        GL_RGBA: 'RGBA',
        GL_BGRA: 'BGRA',
        GL_LUMINANCE: 'L',
        GL_LUMINANCE_ALPHA: 'LA',
    }

    @staticmethod
    def get_glformat_format(format):
        return Image._gl_formats[format]

class RawImage(Image):
    '''Encapsulate image data stored in an OpenGL pixel format.
    '''

    _swap1_pattern = re.compile('(.)', re.DOTALL)
    _swap2_pattern = re.compile('(.)(.)', re.DOTALL)
    _swap3_pattern = re.compile('(.)(.)(.)', re.DOTALL)
    _swap4_pattern = re.compile('(.)(.)(.)(.)', re.DOTALL)

    def __init__(self, data, width, height, format, type, 
                 top_to_bottom=False, alignment=1, row_length=0):
        '''Initialise image data.

        data
            String or array/list of bytes giving the decoded data.
        width, height
            Width and height of the image, in pixels
        format
            A valid format string, such as 'RGB', 'RGBA', 'ARGB', etc.
        type
            A valid type argument to glTexImage2D, for example
            GL_UNSIGNED_BYTE, etc.
        top_to_bottom
            If True, rows begin at the top of the image and increase
            downwards; otherwise they begin at the bottom and increase
            upwards.
        alignment
            Alignment of pixels within data: 1 for no alignment, 4 for
            word alignment.

        '''
        super(RawImage, self).__init__(width, height)

        self.data = data
        self.format = format
        self.type = type
        self.top_to_bottom = top_to_bottom
        self.alignment = alignment
        self.row_length = row_length

    def _ensure_string_data(self):
        if type(self.data) is not str:
            buf = create_string_buffer(len(self.data))
            memmove(buf, self.data, len(self.data))
            self.data = buf.raw

    def _pack_rows(self):
        '''Reduce alignment to 1 to simplify format changes.'''
        if self.alignment == 1:
            return

        self._ensure_string_data()
        pitch = len(self.format) * self.width
        old_pitch = int(ceil(float(pitch) / self.alignment)) * self.alignment 
        diff = old_pitch - pitch
        pattern = re.compile('(%s)%s' % ('.' * pitch, '.' * diff), re.DOTALL)
        self.data = pattern.sub(r'\1', self.data)
        self.alignment = 1

    def tostring(self):
        self._ensure_string_data()
        return self.data

    def swap_rows(self):
        self._ensure_string_data()
        pitch = len(self.format) * self.width
        pitch = int(ceil(float(pitch) / self.alignment)) * self.alignment 
        rows = re.findall('.' * pitch, self.data, re.DOTALL)
        rows.reverse()
        self.data = ''.join(rows)
        self.top_to_bottom = not self.top_to_bottom

    def set_format(self, new_format):
        if self.format == new_format:
            return

        self._ensure_string_data()
        self._pack_rows()

        # Create replacement string, e.g. r'\4\1\2\3' to convert RGBA to ARGB
        repl = ''
        for c in new_format:
            try:
                idx = self.format.index(c) + 1
            except ValueError:
                idx = 1
            repl += r'\%d' % idx

        if len(self.format) == 1:
            self.data = self._swap1_pattern.sub(repl, self.data)
        elif len(self.format) == 2:
            self.data = self._swap2_pattern.sub(repl, self.data)
        elif len(self.format) == 3:
            self.data = self._swap3_pattern.sub(repl, self.data)
        elif len(self.format) == 4:
            self.data = self._swap4_pattern.sub(repl, self.data)

        self.format = new_format

    def _get_gl_format_and_type(self):
        if self.format == 'L':
            return GL_LUMINANCE, self.type
        elif self.format == 'LA':
            return GL_LUMINANCE_ALPHA, self.type
        elif self.format == 'RGB':
            return GL_RGB, self.type
        elif self.format == 'RGBA':
            return GL_RGBA, self.type
        elif self.format == 'ARGB':
            if (self.type == GL_UNSIGNED_BYTE and
                have_extension('GL_EXT_bgra') and
                have_extension('GL_APPLE_packed_pixel')):
                return GL_BGRA, GL_UNSIGNED_INT_8_8_8_8_REV
        elif self.format == 'ABGR':
            if have_extension('GL_EXT_abgr'):
                return GL_ABGR_EXT, self.type
        elif self.format == 'BGR':
            if have_extension('GL_EXT_bgra'):
                return GL_BGR, self.type

        # No luck so far, probably in a format like ABGR but we don't
        # have the required extension, so reorder components manually.
        if self.type == GL_UNSIGNED_BYTE:
            if len(self.format) == 2:
                self.set_format('LA')
                return GL_LUMINANCE, GL_UNSIGNED_BYTE
            elif len(self.format) == 3:
                self.set_format('RGB')
                return GL_RGB, GL_UNSIGNED_BYTE
            elif len(self.format) == 4:
                self.set_format('RGBA')
                return GL_RGBA, GL_UNSIGNED_BYTE
        
        raise ImageException('Cannot use format "%s" with GL.' % self.format)

    def texture(self, internalformat=None):
        tex_width, tex_height, u, v = \
            Texture.get_texture_size(self.width, self.height)

        format, type = self._get_gl_format_and_type()
        if self.top_to_bottom:
            self.swap_rows()

        if not internalformat:
            if format in (GL_LUMINANCE, GL_LUMINANCE_ALPHA, GL_ALPHA):
                internalformat = format
            elif format in (GL_RGBA, GL_BGRA):
                internalformat = GL_RGBA
            else:
                internalformat = GL_RGB

        id = c_uint()
        glGenTextures(1, byref(id))
        glBindTexture(GL_TEXTURE_2D, id.value)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glPixelStorei(GL_UNPACK_ALIGNMENT, self.alignment)
        if tex_width == self.width and tex_height == self.height:
            glTexImage2D(GL_TEXTURE_2D,
                0,
                internalformat,
                tex_width, tex_height,
                0,
                format, type,
                self.data)
        else:
            blank = (c_ubyte * tex_width * tex_height)()
            glTexImage2D(GL_TEXTURE_2D,
                0,
                internalformat,
                tex_width,
                tex_height,
                0,
                GL_RED,
                GL_UNSIGNED_BYTE,
                blank)
            self.texture_subimage(0, 0)

        return Texture(self.width, self.height, self.format, id, u, v)

    def texture_subimage(self, x, y):
        format, type = self._get_gl_format_and_type()
        if self.top_to_bottom:
            self.swap_rows()

        glPixelStorei(GL_UNPACK_ALIGNMENT, self.alignment)
        glTexSubImage2D(GL_TEXTURE_2D,
            0,
            x, y,
            self.width, self.height,
            format, type,
            self.data)

    def get_raw_image(self, type=GL_UNSIGNED_BYTE):
        return self

class BufferImage(Image):
    def __init__(self, gl_format=GL_RGBA, buffer=GL_BACK, 
                 x=None, y=None, width=None, height=None):
        self.gl_format = gl_format
        self.buffer = buffer
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_raw_image(self, type=GL_UNSIGNED_BYTE):
        x = self.x
        y = self.y
        width = self.width
        height = self.height
        viewport = (c_int * 4)()
        glGetIntegerv(GL_VIEWPORT, viewport)
        if x is None:
            x = viewport[0]
        if y is None:
            y = viewport[1]
        if width is None:
            width = viewport[2]
        if height is None:
            height = viewport[3]

        format = self.get_glformat_format(self.gl_format)
        pixels = (self.get_type_ctype(type) * (len(format) * width * height))()

        glReadBuffer(self.buffer)
        glReadPixels(x, y, width, height, self.gl_format, type, pixels)

        return RawImage(pixels, width, height, format, type)

    def texture(self, internalformat=None):
        raise NotImplementedError('TODO')

    def texture_subimage(self, x, y):
        raise NotImplementedError('TODO')

class StencilImage(BufferImage):
    def __init__(self, x=None, y=None, width=None, height=None):
        super(StencilImage, self).__init__(GL_STENCIL_INDEX, GL_BACK,
            x, y, width, height)

class DepthImage(BufferImage):
    def __init__(self, x=None, y=None, width=None, height=None):
        super(DepthImage, self).__init__(GL_DEPTH_COMPONENT, GL_BACK,
            x, y, width, height)

def _nearest_pow2(n):
    i = 1
    while i < n:
        i <<= 1
    return i

class Texture(Image):
    def __init__(self, width, height, format, id, u, v):
        super(Texture, self).__init__(width, height)
        self.format = format
        self.id = id
        self.uv = u, v

        # Make quad display list
        self.quad_list = glGenLists(1)
        glNewList(self.quad_list, GL_COMPILE)
        glBindTexture(GL_TEXTURE_2D, self.id)
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)

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

        glPopAttrib()
        glEndList()

    # TODO: <ah> I think this should be a sprite function only: 3D games
    #       and pyglet.layout will have no need for this DL.
    def draw(self):
        glCallList(self.quad_list)

    _gl_formats = {
        'L': (GL_LUMINANCE, 'L'),
        'A': (GL_ALPHA, 'A'),
        'LA': (GL_LUMINANCE_ALPHA, 'LA'),
        'RGB': (GL_RGB, 'RGB'),
        'BGR': (GL_RGB, 'RGB'),
        'RGBA': (GL_RGBA, 'RGBA'),
        'ABGR': (GL_RGBA, 'RGBA'),
        'BGRA': (GL_RGBA, 'RGBA'),
        'ARGB': (GL_RGBA, 'RGBA'),
    }

    def get_raw_image(self, type=GL_UNSIGNED_BYTE):
        glBindTexture(GL_TEXTURE_2D, self.id)

        width = c_int()
        glGetTexLevelParameteriv(GL_TEXTURE_2D, 
            0, GL_TEXTURE_WIDTH, byref(width))
        width = width.value

        height = c_int()
        glGetTexLevelParameteriv(GL_TEXTURE_2D, 
            0, GL_TEXTURE_HEIGHT, byref(height))
        height = height.value

        gl_format, format = self._gl_formats[self.format]

        buffer = (self.get_type_ctype(type) * 
                  (width * height * len(format)))()
        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        glGetTexImage(GL_TEXTURE_2D, 0, gl_format, type, buffer)

        return RawImage(buffer, width, height, format, type)

    @classmethod
    def create(cls, width, height, internalformat):
        id = c_uint()
        glGenTextures(1, byref(id))
        glBindTexture(GL_TEXTURE_2D, id.value)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        blank = (c_ubyte * width * height)()
        glTexImage2D(GL_TEXTURE_2D, 0,
            internalformat,
            width,
            height,
            0,
            GL_ALPHA,
            GL_UNSIGNED_BYTE,
            blank)
        return cls(width, height, 'RGBA', id.value, 1., 1.)

    @staticmethod
    def load(filename=None, file=None, internalformat=None):
        return Image.load(filename, file).texture(internalformat)

    @staticmethod
    def get_texture_size(width, height):
        '''Return the texture size that should be used to hold an image
        of the given size.  On older cards this should be rounded up to
        2^n dimensions.  On newer cards this is not necessary.

        Returns (width, height, u, v)
        '''
        # TODO detect when non-power2 textures are permitted.
        # TODO square textures required by some cards?
        tex_width = _nearest_pow2(width)
        tex_height = _nearest_pow2(height)
        u = float(width) / tex_width
        v = float(height) / tex_height
        return tex_width, tex_height, u, v

# TODO derive from image and implement blits
class TextureSubImage(object):
    def __init__(self, texture, x, y, width, height):
        self.texture = texture
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.tex_coords = (
            float(x) / texture.width,
            float(y) / texture.height,
            float(x + width) / texture.width,
            float(y + height) / texture.height)

    def flip_vertical(self):
        self.tex_coords = (
            self.tex_coords[0], 
            self.tex_coords[3], 
            self.tex_coords[2],
            self.tex_coords[1])

class AllocatingTextureAtlasOutOfSpaceException(ImageException):
    pass

class AllocatingTextureAtlas(Texture):
    x = 0
    y = 0
    line_height = 0
    subimage_class = TextureSubImage

    def allocate(self, width, height):
        '''Returns (x, y) position for a new glyph, and reserves that
        space.'''
        if self.x + width > self.width:
            self.x = 0
            self.y += self.line_height
            self.line_height = 0
        if self.y + height > self.height:
            raise AllocatingTextureAtlasOutOfSpaceException()

        self.line_height = max(self.line_height, height)
        x = self.x
        self.x += width
        return self.subimage_class(self, x, self.y, width, height)


# Initialise default codecs
add_default_image_codecs()
