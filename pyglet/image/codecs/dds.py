#!/usr/bin/env python

'''DDS texture loader.

http://msdn.microsoft.com/library/en-us/directx9_c/dx9_graphics_reference_dds_file.asp
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *
import struct

from pyglet.gl import *
from pyglet.gl.gl_info import *
from pyglet.image import *
from pyglet.image.codecs import *

class DDSException(ImageDecodeException):
    pass

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
        if len(data) < self.get_size():
            raise DDSException('Not a DDS file')
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

_compression_formats = {
    'DXT1': GL_COMPRESSED_RGB_S3TC_DXT1_EXT,
    'DXT3': GL_COMPRESSED_RGBA_S3TC_DXT3_EXT,
    'DXT5': GL_COMPRESSED_RGBA_S3TC_DXT5_EXT
}

def _check_error():
    e = glGetError()
    if e != 0:
        print 'GL error %d' % e

class DDSImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        return ['.dds']

    def decode(self, file, filename):
        # TODO: Write a software decoding fallback.
        if not gl_info.have_extension('GL_EXT_texture_compression_s3tc'):
            raise DDSException('S3TC extension not supported by device.')

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

        if not desc.ddpfPixelFormat.dwFlags & DDPF_FOURCC:
            raise DDSException('Uncompressed DDS textures not supported.')

        format = None
        format = _compression_formats.get(desc.ddpfPixelFormat.dwFourCC,
                                          None)
        if not format:
            raise DDSException('Unsupported texture compression %s' % \
                desc.ddpfPixelFormat.dwFourCC)

        if format == GL_COMPRESSED_RGB_S3TC_DXT1_EXT:
            block_size = 8
        else:
            block_size = 16

        mipmap_images = []
        w, h = width, height
        for i in range(mipmaps):
            if not w and not h:
                break
            if not w:
                w = 1
            if not h:
                h = 1
            size = ((w + 3) / 4) * ((h + 3) / 4) * block_size
            mipmap_images.append(DDSMipmap(i, w, h, file.read(size)))
            w >>= 1
            h >>= 1

        return DDSCompressedImage(width, height, format, mipmap_images)
   
class DDSMipmap(object):
    def __init__(self, level, width, height, data):
        self.level = level
        self.width = width
        self.height = height
        self.data = data

class DDSCompressedImage(Image):
    def __init__(self, width, height, format, mipmaps):
        super(DDSCompressedImage, self).__init__(width, height)
        self.format = format
        self.mipmaps = mipmaps

    def texture(self, internalformat=None):
        id = c_uint()
        glGenTextures(1, byref(id))
        glBindTexture(GL_TEXTURE_2D, id.value)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
            GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        for mipmap in self.mipmaps:
            glCompressedTexImage2DARB(GL_TEXTURE_2D, 
                mipmap.level, self.format, 
                mipmap.width, mipmap.height, 0, 
                len(mipmap.data), mipmap.data)

        return Texture(self.width, self.height, 'RGBA', id, 1., 1.)

    def texture_subimage(self, x, y):
        for mipmap in self.mipmaps:
            glCompressedTexSubImage2DARB(GL_TEXTURE_2D,
                mipmap.level,
                x, y, 
                mipmap.width,
                mipmap.height,
                self.format,
                len(mipmap.data),
                mipmap.data)

    def get_raw_image(self, type=GL_UNSIGNED_BYTE):
        raise NotImplementedError('No software decoder for DDSCompressedImage')
        

def get_decoders():
    return [DDSImageDecoder()]

def get_encoders():
    return []
