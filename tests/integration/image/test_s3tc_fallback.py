"""Load DDS bytes and force the CPU fallback through real texture readback."""

import io
import struct

import pytest

from pyglet.image import CompressedImageData
from pyglet.image.codecs.dds import DDSImageDecoder


@pytest.mark.parametrize('fourcc, alpha_mask, prefix', [
    (b'DXT1', 0, b''),
    (b'DXT1', 1, b''),
    (b'DXT3', 0, b'\xff' * 8),
    (b'DXT5', 0, bytes([255, 0]) + bytes(6)),
])
def test_dds_software_texture(monkeypatch, fourcc, alpha_mask, prefix):
    fields = [0] * 31
    fields[0:4] = [124, 0x1007, 4, 4]
    fields[18:21] = [32, 4, int.from_bytes(fourcc, 'little')]
    fields[25] = alpha_mask
    fields[26] = 0x1000
    header = struct.pack('<4s31I', b'DDS ', *fields)
    block = prefix + struct.pack('<HHI', 0xf800, 0, 0)
    image = DDSImageDecoder().decode('test.dds', io.BytesIO(header + block))
    monkeypatch.setattr(CompressedImageData, '_have_extension', lambda self: False)
    texture = image.get_texture()
    try:
        assert (texture.width, texture.height) == (4, 4)
        assert bytes(texture.get_image_data().get_bytes('RGBA', 16)) == bytes((248, 0, 0, 255)) * 16
    finally:
        texture.delete()
