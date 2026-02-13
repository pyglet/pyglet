"""Loading and manipulation of raw image data.

Only basic functionality is described here; for full reference see the
accompanying documentation. Images are loaded as :py:class:`ImageData`.
For simplicity, the terms "image" and "image data" may be used interchangeably
below.

To load an image::

    from pyglet import image
    pic = image.load('picture.png')

The supported image file types include PNG, BMP, GIF, JPG, and many more,
somewhat depending on the operating system.  To load an image from a file-like
object instead of a filename::

    pic = image.load('hint.jpg', file=fileobj)

The hint helps the module locate an appropriate decoder to use based on the
file extension.  It is optional.

All images have a width and height you can access::

    width, height = pic.width, pic.height

You can extract a region of an image (this keeps the original image intact;
the memory is shared efficiently)::

    subimage = pic.get_region(x, y, width, height)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO

if TYPE_CHECKING:
    from pyglet.image.animation import Animation
    from pyglet.image.base import _AbstractImage
    from pyglet.customtypes import RGBAColor

from pyglet.image import animation  # noqa: F401
from pyglet.image.animation import AnimationFrame  # noqa: F401
from pyglet.image.base import ImageData, ImageDataRegion, CompressedImageData, ImageException  # noqa: F401

from pyglet.image.base import ImageGrid, ImagePattern, _color_as_bytes  # noqa: F401
from pyglet.image.codecs import ImageDecoder
from pyglet.image.codecs import add_default_codecs as _add_default_codecs
from pyglet.image.codecs import registry as _codec_registry


def load(filename: str, file: BinaryIO | None = None, decoder: ImageDecoder | None = None) -> ImageData:
    """Load an image from a file on disk, or from an open file-like object.

    Args:
        filename:
            Used to guess the image format, and to load the file if ``file``
            is unspecified.
        file:
            Optional file containing the image data in any supported format.
        decoder:
            If unspecified, all decoders that are registered for the filename
            extension are tried.  If none succeed, the exception from the
            first decoder is raised.

    .. note:: You can make no assumptions about the return type; usually it will
              be ImageData or CompressedImageData, but decoders are free to return
              any subclass of AbstractImage.
    """
    if decoder:
        return decoder.decode(filename, file)

    return _codec_registry.decode(filename, file)


def load_animation(filename: str, file: BinaryIO | None = None, decoder: ImageDecoder | None = None) -> Animation:
    """Load an animation from a file on disk, or from an open file-like object.

    Args:
        filename:
            Used to guess the animation format, and to load the file if ``file``
            is unspecified.
        file:
            Optional file containing the animation data in any supported format.
        decoder:
            If unspecified, all decoders that are registered for the filename
            extension are tried.  If none succeed, the exception from the
            first decoder is raised.
    """
    if decoder:
        return decoder.decode_animation(filename, file)

    return _codec_registry.decode_animation(filename, file)


def create(width: int, height: int, pattern: ImagePattern | None = None) -> _AbstractImage:
    """Create an image optionally filled with the given pattern.

    :Parameters:
        width:
            Width of image to create.
        height:
            Height of image to create.
        pattern:
            Optional pattern to fill image with. If unspecified, the image will
            initially be transparent.

    .. note:: You can make no assumptions about the return type; usually it will
              be ImageData or CompressedImageData, but patterns are free to return
              any subclass of AbstractImage.
    """
    if not pattern:
        pattern = SolidColorImagePattern()
    return pattern.create_image(width, height)


class SolidColorImagePattern(ImagePattern):
    """Creates an image filled with a solid RGBA color."""

    def __init__(self, color: RGBAColor = (0, 0, 0, 0)) -> None:
        """Create a solid image pattern with the given color.

        Args:
            color:
                4-tuple of ints in range [0,255] giving RGBA components of
                color to fill with.
        """
        self.color = _color_as_bytes(color)

    def create_image(self, width: int, height: int) -> _AbstractImage:
        data = self.color * width * height
        return ImageData(width, height, 'RGBA', data)


class CheckerImagePattern(ImagePattern):
    """Create an image with a tileable checker image."""

    def __init__(self, color1: RGBAColor = (150, 150, 150, 255), color2: RGBAColor = (200, 200, 200, 255)) -> None:
        """Initialize with the given colors.

        Args:
            color1:
                4-tuple of ints in range [0,255] giving RGBA components of
                color to fill with.  This color appears in the top-left and
                bottom-right corners of the image.
            color2:
                4-tuple of ints in range [0,255] giving RGBA components of
                color to fill with.  This color appears in the top-right and
                bottom-left corners of the image.
        """
        self.color1 = _color_as_bytes(color1)
        self.color2 = _color_as_bytes(color2)

    def create_image(self, width: int, height: int) -> _AbstractImage:
        hw = width // 2
        hh = height // 2
        row1 = self.color1 * hw + self.color2 * hw
        row2 = self.color2 * hw + self.color1 * hw
        data = row1 * hh + row2 * hh
        return ImageData(width, height, 'RGBA', data)


# Initialise default codecs
_add_default_codecs()
