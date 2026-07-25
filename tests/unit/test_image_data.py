from pyglet.image import ImageData


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
