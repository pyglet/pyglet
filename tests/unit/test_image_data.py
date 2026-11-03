import pytest

from pyglet.image import ImageData


@pytest.mark.parametrize("source_format", ["RGB", "BGR"])
@pytest.mark.parametrize("target_format", ["RGBA", "BGRA", "ARGB"])
@pytest.mark.parametrize("source_pitch", [6, 8, -8])
def test_rgb_expansion_adds_opaque_alpha(source_format, target_format, source_pitch):
    pixels = [(0, 20, 30), (10, 40, 50), (20, 60, 70), (40, 80, 90)]
    rows = []
    for row in (pixels[:2], pixels[2:]):
        data = bytes(value for pixel in row for value in (pixel if source_format == "RGB" else pixel[::-1]))
        rows.append(data + bytes(abs(source_pitch) - 6))
    if source_pitch < 0:
        rows.reverse()
    image = ImageData(2, 2, source_format, b"".join(rows), source_pitch)

    expected = bytes(dict(zip("RGBA", (*pixel, 255)))[channel]
                     for pixel in pixels for channel in target_format)
    assert image.get_bytes(target_format, 8) == expected


def test_rgba_conversion_preserves_existing_alpha():
    image = ImageData(2, 1, "RGBA", bytes((10, 20, 30, 0, 40, 50, 60, 127)))
    assert image.get_bytes("BGRA", 8) == bytes((30, 20, 10, 0, 60, 50, 40, 127))


@pytest.mark.parametrize("source_format", ["R", "L", "I"])
def test_single_channel_expansion_preserves_replication(source_format):
    image = ImageData(2, 1, source_format, bytes((0, 127)))
    assert image.get_bytes("RGBA", 8) == bytes((0, 0, 0, 0, 127, 127, 127, 127))


def test_rgb_packed_from_rgba():
    """Packed RGBA to packed RGB should keep row count and channel order.
    This validates basic format conversion without pitch resizing."""
    width, height = 384, 2
    data = bytes((i % 256 for i in range(width * height * 4)))
    image = ImageData(width, height, "RGBA", data, width * 4)

    rgb_pitch = width * len("RGB")
    rgb_data = image.get_bytes("RGB", rgb_pitch)

    assert len(rgb_data) == rgb_pitch * height
    assert rgb_data[:6] == bytes((0, 1, 2, 4, 5, 6))


def test_rgb_short_pitch_truncates_rows():
    """When target pitch is smaller, each row should be truncated independently.
    No bytes from the next source row should leak into the current output row."""
    width, height = 8, 2
    data = bytes(range(width * height * 4))
    image = ImageData(width, height, "RGBA", data, width * 4)

    rgb_data = image.get_bytes("RGB", 4)

    assert len(rgb_data) == 8
    assert rgb_data == bytes((0, 1, 2, 4, 32, 33, 34, 36))


def test_same_format_short_pitch_strips_padding():
    """Same-format pitch shrink should remove per-row padding bytes.
    Pixel payload must remain intact for each row."""
    width, height = 3, 2
    data = bytes((
        1, 2, 3, 4, 5, 6, 7, 8, 9, 100, 101, 102,
        11, 12, 13, 14, 15, 16, 17, 18, 19, 110, 111, 112,
    ))
    image = ImageData(width, height, "RGB", data, 12)

    rgb_data = image.get_bytes("RGB", 9)

    assert len(rgb_data) == 18
    assert rgb_data == bytes((
        1, 2, 3, 4, 5, 6, 7, 8, 9,
        11, 12, 13, 14, 15, 16, 17, 18, 19,
    ))


def test_rg_packed_from_rgba():
    """RGBA to packed RG should preserve row structure with channel selection.
    This checks multi-channel reduction without padding."""
    width, height = 4, 2
    data = bytes(range(width * height * 4))
    image = ImageData(width, height, "RGBA", data, width * 4)

    rg_data = image.get_bytes("RG", width * 2)

    assert len(rg_data) == width * 2 * height
    assert rg_data == bytes((
        0, 1, 4, 5, 8, 9, 12, 13,
        16, 17, 20, 21, 24, 25, 28, 29,
    ))


def test_r_padded_pitch_from_rgba():
    """If target pitch is wider than packed R, each row must be zero-padded.
    Padding should be appended per row, not across the full buffer."""
    width, height = 4, 2
    data = bytes(range(width * height * 4))
    image = ImageData(width, height, "RGBA", data, width * 4)

    r_data = image.get_bytes("R", 6)

    assert len(r_data) == 12
    assert r_data == bytes((
        0, 4, 8, 12, 0, 0,
        16, 20, 24, 28, 0, 0,
    ))


def test_rgb_padded_pitch_from_r():
    """R to RGB should replicate the single channel before row padding.
    Additional pitch bytes must be zero-filled at the end of each row."""
    width, height = 4, 2
    data = bytes((1, 2, 3, 4, 5, 6, 7, 8))
    image = ImageData(width, height, "R", data, width)

    rgb_data = image.get_bytes("RGB", 14)

    assert len(rgb_data) == 28
    assert rgb_data == bytes((
        1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 0, 0,
        5, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 0, 0,
    ))


def test_rgba_from_padded_r_with_output_padding():
    """Source row padding must be discarded before format conversion.
    Converted rows should then receive target padding bytes."""
    width, height = 4, 2
    data = bytes((
        1, 2, 3, 4, 99, 98,
        5, 6, 7, 8, 97, 96,
    ))
    image = ImageData(width, height, "R", data, 6)

    rgba_data = image.get_bytes("RGBA", 18)

    assert len(rgba_data) == 36
    assert rgba_data == bytes((
        1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 0, 0,
        5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8, 0, 0,
    ))
