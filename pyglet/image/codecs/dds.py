"""DDS texture loader.

Reference: http://msdn2.microsoft.com/en-us/library/bb172993.aspx
"""
from __future__ import annotations

import struct
import itertools
from typing import BinaryIO

from pyglet.image.base import CompressedImageData, CompressionFormat
from pyglet.image import codecs
from pyglet.image.codecs import ImageDecodeException

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


class _FileStruct:
    _fields = []

    def __init__(self, data):
        if len(data) < self.get_size():
            raise ImageDecodeException('Not a DDS file')
        items = struct.unpack(self.get_format(), data)
        for field, value in itertools.zip_longest(self._fields, items, fillvalue=None):
            setattr(self, field[0], value)

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return '{}({})'.format(name, (', \n%s' % (' ' * (len(name) + 1))).join(
            [f'{field[0]} = {getattr(self, field[0])!r}' for field in self._fields]))

    @classmethod
    def get_format(cls):
        return '<' + ''.join([f[1] for f in cls._fields])

    @classmethod
    def get_size(cls):
        return struct.calcsize(cls.get_format())


class DDSURFACEDESC2(_FileStruct):
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
        ('dwReserved2', 'I'),
    ]

    def __init__(self, data):
        super().__init__(data)
        self.ddpfPixelFormat = DDPIXELFORMAT(self.ddpfPixelFormat)

class DDS_HEADER_DXT10(_FileStruct):
    _fields = [
        ('dxgiFormat', 'I'),
        ('resourceDimension', 'I'),
        ('miscFlag', 'I'),
        ('arraySize', 'I'),
        ('miscFlags2', 'I'),
    ]

class DDPIXELFORMAT(_FileStruct):
    _fields = [
        ('dwSize', 'I'),
        ('dwFlags', 'I'),
        ('dwFourCC', '4s'),
        ('dwRGBBitCount', 'I'),
        ('dwRBitMask', 'I'),
        ('dwGBitMask', 'I'),
        ('dwBBitMask', 'I'),
        ('dwRGBAlphaBitMask', 'I'),
    ]

def _get_dds_block_size_dxgi(dxgi_format: int) -> int:
    if dxgi_format in (71, 72, 80, 81):  # BC1 = 8 bytes per 4x4 block
        return 8
    if dxgi_format in (74, 75, # BC2  = 16 bytes per 4x4 block
                       77, 78, # BC3
                       83, 84, # BC5
                       95, 96,  # B6
                       98, 99):  # BC7
        return 16
    msg = f"Unsupported DXGI format {dxgi_format}"
    raise ImageDecodeException(msg)


def _get_dds_block_size(fourcc: bytes) -> int:
    """Return block size in bytes based on the below formats."""
    if fourcc in (b'DXT1', b'BC1 '):
        return 8
    if fourcc in (b'DXT3', b'DXT5', b'BC2 ', b'BC3 ', b'BC5 ', b'ATI2'):
        return 16
    if fourcc in (b'BC4 ', b'ATI1'):
        return 8

    return 0  # Not block compressed


class DDSImageDecoder(codecs.ImageDecoder):
    def get_file_extensions(self) -> list[str]:
        return ['.dds']

    def decode(self, filename: str, file: BinaryIO | None = None):
        if not file:
            file = open(filename, 'rb')

        header = file.read(DDSURFACEDESC2.get_size())
        desc = DDSURFACEDESC2(header)
        if desc.dwMagic != b'DDS ' or desc.dwSize != 124:
            raise ImageDecodeException('Invalid DDS file (incorrect header).')

        width = desc.dwWidth
        height = desc.dwHeight
        mipmaps = 1

        if desc.dwFlags & DDSD_DEPTH:
            raise ImageDecodeException('Volume DDS files unsupported')

        if desc.dwFlags & DDSD_MIPMAPCOUNT:
            mipmaps = desc.dwMipMapCount

        if desc.ddpfPixelFormat.dwSize != 32:
            raise ImageDecodeException('Invalid DDS file (incorrect pixel format).')

        if desc.dwCaps2 & DDSCAPS2_CUBEMAP:
            raise ImageDecodeException('Cubemap DDS files unsupported')

        if not desc.ddpfPixelFormat.dwFlags & DDPF_FOURCC:
            raise ImageDecodeException('Uncompressed DDS textures not supported.')

        has_alpha = desc.ddpfPixelFormat.dwRGBAlphaBitMask != 0

        fourcc = desc.ddpfPixelFormat.dwFourCC
        if fourcc == b'DX10':
            dx10_header_data = file.read(DDS_HEADER_DXT10.get_size())
            dx10_header = DDS_HEADER_DXT10(dx10_header_data)
            fmt = CompressionFormat(fourcc, has_alpha, dx10_header.dxgiFormat)
            block_size = _get_dds_block_size_dxgi(dx10_header.dxgiFormat)
        else:
            block_size = _get_dds_block_size(fourcc)
            fmt = CompressionFormat(fourcc, has_alpha)

        datas = []
        w, h = width, height
        for _ in range(mipmaps):
            if not w and not h:
                break
            if not w:
                w = 1
            if not h:
                h = 1
            size = ((w + 3) // 4) * ((h + 3) // 4) * block_size
            data = file.read(size)
            datas.append(data)
            w >>= 1
            h >>= 1

        image = CompressedImageData(width, height, fmt, datas[0])
        level = 0
        for data in datas[1:]:
            level += 1
            image.set_mipmap_data(level, data)

        return image


def get_decoders() -> list[DDSImageDecoder]:
    return [DDSImageDecoder()]


def get_encoders() -> list:
    return []
