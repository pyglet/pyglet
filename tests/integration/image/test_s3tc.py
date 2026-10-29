"""Known compressed blocks exercise the software path without S3TC hardware."""

import struct

import pytest

from pyglet.image.codecs import s3tc


def color_block(first=0xf800, second=0, selectors=0):
    return struct.pack('<HHI', first, second, selectors)


def pixels(image):
    channels = len(image.format)
    data = image.get_bytes(image.format, image.width * channels)
    return [tuple(data[i:i + channels]) for i in range(0, len(data), channels)]


@pytest.mark.parametrize('decoder, prefix, expected', [
    (s3tc.decode_dxt1_rgb, b'', (248, 0, 0)),
    (s3tc.decode_dxt1_rgba, b'', (248, 0, 0, 255)),
    (s3tc.decode_dxt3, b'\xff' * 8, (248, 0, 0, 255)),
    (s3tc.decode_dxt5, bytes([255, 0]) + bytes(6), (248, 0, 0, 255)),
])
def test_bytes_block(decoder, prefix, expected):
    assert pixels(decoder(prefix + color_block(), 4, 4)) == [expected] * 16


def test_dxt1_transparent_selector():
    image = s3tc.decode_dxt1_rgba(color_block(0, 0xffff, 0xffffffff), 4, 4)
    assert pixels(image) == [(0, 0, 0, 0)] * 16


def test_dxt3_explicit_alpha():
    image = s3tc.decode_dxt3(bytes([0xf8]) * 8 + color_block(), 4, 4)
    assert [pixel[3] for pixel in pixels(image)] == [136, 255] * 8


@pytest.mark.parametrize('first, second, expected', [
    (240, 30, [240, 30, 210, 180, 150, 120, 90, 60]),
    (20, 220, [20, 220, 60, 100, 140, 180, 0, 255]),
])
def test_dxt5_alpha_palette(first, second, expected):
    selectors = sum((index % 8) << (3 * index) for index in range(16))
    block = bytes([first, second]) + selectors.to_bytes(6, 'little') + color_block()
    assert [pixel[3] for pixel in pixels(s3tc.decode_dxt5(block, 4, 4))] == expected * 2


@pytest.mark.parametrize('decoder, prefix', [
    (s3tc.decode_dxt3, b'\xff' * 8),
    (s3tc.decode_dxt5, bytes([255, 0]) + bytes(6)),
])
def test_explicit_alpha_formats_use_four_colors(decoder, prefix):
    # DXT3/5 always interpolate both colors, even when the first endpoint is smaller.
    selectors = sum((2 + index % 2) << (2 * index) for index in range(16))
    image = decoder(prefix + color_block(0, 0xffff, selectors), 4, 4)
    assert pixels(image) == [(80, 84, 80, 255), (160, 168, 160, 255)] * 8


@pytest.mark.parametrize('size', [(8, 4), (4, 8), (8, 8)])
def test_multiple_blocks(size):
    width, height = size
    colors = [0xf800, 0x07e0, 0x001f, 0xffff]
    expected_colors = [(248, 0, 0), (0, 252, 0), (0, 0, 248), (248, 252, 248)]
    count = width * height // 16
    image = s3tc.decode_dxt1_rgb(b''.join(color_block(color) for color in colors[:count]), width, height)
    expected = [expected_colors[(y // 4) * (width // 4) + x // 4]
                for y in range(height) for x in range(width)]
    assert pixels(image) == expected
