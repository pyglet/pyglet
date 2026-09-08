"""Browser-backed image decoder for Pyodide.

The browser decodes formats supported by ``createImageBitmap``.  This module
uses a Blob instead of a data URL so the image payload is not base64 encoded
(which previously added a large Python/JavaScript conversion cost).
"""

from __future__ import annotations

import os.path
from typing import BinaryIO

from pyglet.image import ImageData
from pyglet.image.codecs import ImageDecodeException, ImageDecoder

try:
    import js  # noqa: F821
    from pyodide.ffi import run_sync  # noqa: F821
except ImportError:
    raise ImportError


_image_canvas = js.document.createElement("canvas")
_image_context = _image_canvas.getContext("2d", willReadFrequently=True)

_MIME_TYPES = {
    ".avif": "image/avif",
    ".bmp": "image/bmp",
    ".gif": "image/gif",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def _read_file(filename: str, file: BinaryIO | None) -> bytes:
    if file is not None:
        return file.read()
    with open(filename, "rb") as source:
        return source.read()


class JSImageDecoder(ImageDecoder):
    """Decode browser-supported images through Canvas 2D."""

    def get_file_extensions(self) -> list[str]:
        return list(_MIME_TYPES)

    def decode(self, filename: str, file: BinaryIO | None) -> ImageData:
        try:
            return run_sync(self._decode(filename, file))
        except Exception as error:
            raise ImageDecodeException(f"Browser cannot read {filename!r}: {error}") from error

    async def _decode(self, filename: str, file: BinaryIO | None) -> ImageData:
        # Blobs avoid the base64 expansion and the additional string copies
        # caused by data URLs. createImageBitmap also skips Image element setup.
        data = _read_file(filename, file)
        encoded = js.Uint8Array.new(data)
        mime_type = _MIME_TYPES.get(os.path.splitext(filename)[1].lower(), "")
        blob = js.Blob.new([encoded], {"type": mime_type})
        bitmap = await js.createImageBitmap(blob)
        try:
            width, height = bitmap.width, bitmap.height
            _image_canvas.width = width
            _image_canvas.height = height
            _image_context.drawImage(bitmap, 0, 0)
            pixels = _image_context.getImageData(0, 0, width, height).data
        finally:
            bitmap.close()

        return ImageData(width, height, "RGBA", pixels, -width * 4)

    def decode_animation(self, filename, file):
        raise ImageDecodeException("This decoder cannot decode animations.")


def get_decoders():
    return [JSImageDecoder()]


def get_encoders():
    return []
