# KTX2 decoder, based on the spec here: https://github.khronos.org/KTX-Specification/ktxspec.v2.html

from __future__ import annotations

import struct
import itertools
import zlib
from typing import BinaryIO

try:
    import zstandard
    _zstandard_available = True
except ImportError:
    _zstandard_available = False

from pyglet.image.base import CompressedImageData, CompressionFormat
from pyglet.image import codecs
from pyglet.image.codecs import ImageDecodeException


class _FileStruct:
    _fields = []

    def __init__(self, data):
        if len(data) < self.get_size():
            raise ImageDecodeException('Not a KTX2 file')
        items = struct.unpack(self.get_format(), data)
        for field, value in itertools.zip_longest(self._fields, items, fillvalue=None):
            setattr(self, field[0], value)

    def __repr__(self):
        name = self.__class__.__name__
        return '{}({})'.format(name, (', \n%s' % (' ' * (len(name) + 1))).join(
            [f'{field[0]} = {getattr(self, field[0])!r}' for field in self._fields]))

    @classmethod
    def get_format(cls):
        return '<' + ''.join([f[1] for f in cls._fields])

    @classmethod
    def get_size(cls):
        return struct.calcsize(cls.get_format())


class KTX2Header(_FileStruct):
    _fields = [
        ('vkFormat', 'I'),
        ('typeSize', 'I'),
        ('pixelWidth', 'I'),
        ('pixelHeight', 'I'),
        ('pixelDepth', 'I'),
        ('layerCount', 'I'),
        ('faceCount', 'I'),
        ('levelCount', 'I'),
        ('supercompressionScheme', 'I'),

        ('dfdByteOffset', 'I'),
        ('dfdByteLength', 'I'),
        ('kvdByteOffset', 'I'),
        ('kvdByteLength', 'I'),
        ('sgdByteOffset', 'Q'),
        ('sgdByteLength', 'Q'),
    ]

class KTX2LevelIndex(_FileStruct):
    _fields = [
        ('byteOffset', 'Q'),
        ('byteLength', 'Q'),
        ('uncompressedByteLength', 'Q'),
    ]

class KTX2ImageDecoder(codecs.ImageDecoder):
    def get_file_extensions(self) -> list[str]:
        return ['.ktx2']

    def decode(self, filename: str, file: BinaryIO | None = None) -> CompressedImageData:
        file_opened = False
        if not file:
            file = open(filename, 'rb')
            file_opened = True

        # Magic header, if supported
        magic = file.read(12)
        if magic != b'\xABKTX 20\xBB\r\n\x1A\n':
            raise ImageDecodeException('Invalid KTX2 file (bad magic)')

        header_data = file.read(KTX2Header.get_size())
        header = KTX2Header(header_data)

        width = header.pixelWidth
        height = header.pixelHeight
        mipmaps = header.levelCount or 1

        fmt = CompressionFormat(
            fmt=b'KTX2',
            alpha=header.vkFormat in (131, 147, 148),
            dxgi_format=0,
            vk_format=header.vkFormat,
        )

        # Mip map level indexes
        level_indices = []
        for _ in range(mipmaps):
            index_data = file.read(KTX2LevelIndex.get_size())
            level_indices.append(KTX2LevelIndex(index_data))

        # 2 = ZStandard compression
        # 1 = Zlib compression.
        # 0 = Not compressed.
        if header.supercompressionScheme != 0:
            if header.sgdByteOffset == 0:
                datas = self.decompress_ktx2_per_level(file, header, level_indices)
        else:
            datas = []
            for idx in level_indices:
                file.seek(idx.byteOffset)
                data = file.read(idx.byteLength)
                datas.append(data)

        image = CompressedImageData(width, height, fmt, datas[0])
        for level, data in enumerate(datas[1:], 1):
            image.set_mipmap_data(level, data)

        if file_opened:
            file.close()

        return image

    def decompress_ktx2_per_level(self, file: BinaryIO, header: KTX2Header, level_indices: list):
        datas = []
        for idx in level_indices:
            file.seek(idx.byteOffset)
            compressed_data = file.read(idx.byteLength)

            if header.supercompressionScheme == 3:
                decompressed = zlib.decompress(compressed_data)
            elif header.supercompressionScheme == 2:
                if _zstandard_available:
                    dctx = zstandard.ZstdDecompressor()
                    with dctx.stream_reader(compressed_data) as reader:
                        decompressed = reader.read(idx.uncompressedByteLength)
                else:
                    msg = "File was supercompressed with Zstandard, but zstandard package is not installed."
                    raise ImageDecodeException(msg)
            else:
                msg = f"Unsupported supercompression scheme: {header.supercompressionScheme}"
                raise ImageDecodeException(msg)

            if len(decompressed) != idx.uncompressedByteLength:
                msg = f"Size mismatch at level: expected {idx.uncompressedByteLength}, got {len(decompressed)}"
                raise ImageDecodeException(msg)

            datas.append(decompressed)
        return datas

def get_decoders():
    return [KTX2ImageDecoder()]


def get_encoders():
    return []
