"""Windows Imaging Component integration tests."""
from __future__ import annotations

from io import BytesIO

import pytest

from tests.annotations import Platform, require_platform


pytestmark = require_platform(Platform.WINDOWS)


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _assert_round_trip(encoded: bytes, expected: bytes) -> None:
    from pyglet.image.codecs.wic import WICDecoder  # noqa: PLC0415

    decoded = WICDecoder().decode("round_trip.png", BytesIO(encoded))
    assert decoded.width == 2
    assert decoded.height == 3
    assert decoded.get_bytes("RGBA", 8) == expected


def _assert_file_round_trip(filename, expected: bytes) -> None:
    from pyglet.image.codecs.wic import WICDecoder  # noqa: PLC0415

    decoded = WICDecoder().decode(str(filename), None)
    assert decoded.width == 2
    assert decoded.height == 3
    assert decoded.get_bytes("RGBA", 8) == expected


def test_wic_encodes_rgba_png_to_stream_and_filename(tmp_path):
    """WIC preserves RGBA pixels when producing PNG bytes or a PNG file."""
    from pyglet.image import ImageData  # noqa: PLC0415
    from pyglet.image.codecs.wic import WICEncoder  # noqa: PLC0415

    # Each row is deliberately distinct, which verifies that the negative
    # pitch supplied to WIC is correctly restored by its decoder.
    pixels = bytes((
        255, 0, 0, 255, 0, 255, 0, 128,
        0, 0, 255, 64, 255, 255, 0, 32,
        255, 0, 255, 16, 0, 255, 255, 0,
    ))
    source = ImageData(2, 3, "RGBA", pixels, 8)
    encoder = WICEncoder()

    stream = BytesIO()
    encoder.encode(source, "round_trip.png", stream)
    stream_bytes = stream.getvalue()
    assert stream_bytes.startswith(PNG_SIGNATURE)
    _assert_round_trip(stream_bytes, pixels)

    filename = tmp_path / "round_trip.png"
    encoder.encode(source, str(filename), None)
    file_bytes = filename.read_bytes()
    assert file_bytes.startswith(PNG_SIGNATURE)
    _assert_file_round_trip(filename, pixels)
