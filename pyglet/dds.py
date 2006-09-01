#!/usr/bin/env python

'''DDS texture loader.

http://msdn.microsoft.com/library/en-us/directx9_c/dx9_graphics_reference_dds_file.asp
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *
import struct

from pyglet.GL.VERSION_1_1 import *
import pyglet.image

try:
    from pyglet.GL.ARB_texture_compression import *
    from pyglet.GL.EXT_texture_compression_s3tc import *
    _have_s3tc = True
except ImportError:
    _have_s3tc = False

# dwFlags of DDSURFACEDESC2
DDSD_CAPS           = 0x00000001
DDSD_HEIGHT         = 0x00000002
DDSD_WIDTH          = 0x00000004
DDSD_PITCH          = 0x00000008
DDSD_PIXELFORMAT    = 0x00001000
DDSD_MIPMAPCOUNT    = 0x00020000
DDSD_LINEARSIZE     = 0x00080000
DDSD_DEPTH          = 0x00800000

# ddpfPixelFormat of DDSURFACEDESC2
DDPF_ALPHAPIXELS  	= 0x00000001
DDPF_FOURCC 	    = 0x00000004
DDPF_RGB 	        = 0x00000040

# dwCaps1 of DDSCAPS2
DDSCAPS_COMPLEX  	= 0x00000008
DDSCAPS_TEXTURE 	= 0x00001000
DDSCAPS_MIPMAP 	    = 0x00400000

# dwCaps2 of DDSCAPS2
DDSCAPS2_CUBEMAP 	        = 0x00000200
DDSCAPS2_CUBEMAP_POSITIVEX  = 0x00000400
DDSCAPS2_CUBEMAP_NEGATIVEX  = 0x00000800
DDSCAPS2_CUBEMAP_POSITIVEY  = 0x00001000
DDSCAPS2_CUBEMAP_NEGATIVEY  = 0x00002000
DDSCAPS2_CUBEMAP_POSITIVEZ  = 0x00004000
DDSCAPS2_CUBEMAP_NEGATIVEZ  = 0x00008000
DDSCAPS2_VOLUME 	        = 0x00200000

class _filestruct(object):
    def __init__(self, data):
        items = struct.unpack(self.get_format(), data)
        for field, value in map(None, self._fields, items):
            setattr(self, field[0], value)

    def __repr__(self):
        name = self.__class__.__name__
        return '%s(%s)' % \
            (name, (', \n%s' % (' ' * (len(name) + 1))).join( \
                      ['%s = %s' % (field[0], repr(getattr(self, field[0]))) \
                       for field in self._fields]))

    @classmethod
    def get_format(cls):
        return '<' + ''.join([f[1] for f in cls._fields])

    @classmethod
    def get_size(cls):
        return struct.calcsize(cls.get_format())
        


class DDSURFACEDESC2(_filestruct):
    _fields = [
        ('dwMagic', '4s'),
        ('dwSize', 'I'),
        ('dwFlags', 'I'),
        ('dwHeight', 'I'),
        ('dwWidth', 'I'),
        ('dwPitchOrLinearSize', 'I'),
        ('dwDepth', 'I'),
        ('dwMipMapCount', 'I'),
        ('dwReserved1', '44s'),
        ('ddpfPixelFormat', '32s'),
        ('dwCaps1', 'I'),
        ('dwCaps2', 'I'),
        ('dwCapsReserved', '8s'),
        ('dwReserved2', 'I')
    ]

    def __init__(self, data):
        super(DDSURFACEDESC2, self).__init__(data)
        self.ddpfPixelFormat = DDPIXELFORMAT(self.ddpfPixelFormat)

class DDPIXELFORMAT(_filestruct):
    _fields = [
        ('dwSize', 'I'),
        ('dwFlags', 'I'),
        ('dwFourCC', '4s'),
        ('dwRGBBitCount', 'I'),
        ('dwRBitMask', 'I'),
        ('dwGBitMask', 'I'),
        ('dwBBitMask', 'I'),
        ('dwRGBAlphaBitMask', 'I')
    ]

class DDSException(Exception):
    pass

if _have_s3tc:
    _compression_formats = {
        'DXT1': GL_COMPRESSED_RGB_S3TC_DXT1_EXT,
        'DXT3': GL_COMPRESSED_RGBA_S3TC_DXT3_EXT,
        'DXT5': GL_COMPRESSED_RGBA_S3TC_DXT5_EXT
    }

def _check_error():
    e = glGetError()
    if e != 0:
        print 'GL error %d' % e

def load_dds(file):
    if not hasattr(file, 'read'):
        file = open(file, 'rb')

    header = file.read(DDSURFACEDESC2.get_size())
    desc = DDSURFACEDESC2(header)
    if desc.dwMagic != 'DDS ' or desc.dwSize != 124:
        raise DDSException('Invalid DDS file (incorrect header).')

    width = desc.dwWidth
    height = desc.dwHeight
    compressed = False
    volume = False
    mipmaps = 1

    if desc.dwFlags & DDSD_PITCH:
        pitch = desc.dwPitchOrLinearSize
    elif desc.dwFlags & DDSD_LINEARSIZE:
        image_size = desc.dwPitchOrLinearSize
        compressed = True

    if desc.dwFlags & DDSD_DEPTH:
        raise DDSException('Volume DDS files unsupported')
        volume = True
        depth = desc.dwDepth

    if desc.dwFlags & DDSD_MIPMAPCOUNT:
        mipmaps = desc.dwMipMapCount

    if desc.ddpfPixelFormat.dwSize != 32:
        raise DDSException('Invalid DDS file (incorrect pixel format).')

    if desc.dwCaps2 & DDSCAPS2_CUBEMAP:
        raise DDSException('Cubemap DDS files unsupported')

    if desc.ddpfPixelFormat.dwFlags & DDPF_FOURCC:
        format = None
        if _have_s3tc:
            format = _compression_formats.get(desc.ddpfPixelFormat.dwFourCC,
                                              None)
        if not format:
            raise DDSException('Unsupported texture compression %s' % \
                desc.ddpfPixelFormat.dwFourCC)

        if format == GL_COMPRESSED_RGB_S3TC_DXT1_EXT:
            block_size = 8
        else:
            block_size = 16
        
        tex = c_uint()
        glGenTextures(1, byref(tex))
        tex = tex.value
        glBindTexture(GL_TEXTURE_2D, tex)
        w, h = width, height
        for i in range(mipmaps):
            if not w and not h:
                break
            if not w:
                w = 1
            if not h:
                h = 1
            size = ((w + 3) / 4) * ((h + 3) / 4) * block_size
            glCompressedTexImage2DARB(GL_TEXTURE_2D, i, format, w, h, 0,
                                      size, file.read(size))
            w >>= 1
            h >>= 1
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, 
                        GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        return pyglet.image.Texture(tex, width, height, (1., 1.))
    else:
        raise DDSException('Uncompressed texture not supported')

