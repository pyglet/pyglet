"""Image load, capture and high-level texture functions.

Only basic functionality is described here; for full reference see the
accompanying documentation.

To load an image::

    from pyglet import image
    pic = image.load('picture.png')

The supported image file types include PNG, BMP, GIF, JPG, and many more,
somewhat depending on the operating system.  To load an image from a file-like
object instead of a filename::

    pic = image.load('hint.jpg', file=fileobj)

The hint helps the module locate an appropriate decoder to use based on the
file extension.  It is optional.

Once loaded, images can be used directly by most other modules of pyglet.  All
images have a width and height you can access::

    width, height = pic.width, pic.height

You can extract a region of an image (this keeps the original image intact;
the memory is shared efficiently)::

    subimage = pic.get_region(x, y, width, height)

Remember that y-coordinates are always increasing upwards.

Drawing images
--------------

To draw an image at some point on the screen::

    pic.blit(x, y, z)

This assumes an appropriate view transform and projection have been applied.

Some images have an intrinsic "anchor point": this is the point which will be
aligned to the ``x`` and ``y`` coordinates when the image is drawn.  By
default, the anchor point is the lower-left corner of the image.  You can use
the anchor point to center an image at a given point, for example::

    pic.anchor_x = pic.width // 2
    pic.anchor_y = pic.height // 2
    pic.blit(x, y, z)

Texture access
--------------

If you are using OpenGL directly, you can access the image as a texture::

    texture = pic.get_texture()

(This is the most efficient way to obtain a texture; some images are
immediately loaded as textures, whereas others go through an intermediate
form).  To use a texture with pyglet.gl::

    from pyglet.graphics.api.gl import *
    glEnable(texture.target)        # typically target is GL_TEXTURE_2D
    glBindTexture(texture.target, texture.id)
    # ... draw with the texture

Pixel access
------------

To access raw pixel data of an image::

    rawimage = pic.get_image_data()

(If the image has just been loaded this will be a very quick operation;
however if the image is a texture a relatively expensive readback operation
will occur).  The pixels can be accessed as bytes::

    format = 'RGBA'
    pitch = rawimage.width * len(format)
    pixels = rawimage.get_bytes(format, pitch)

"format" strings consist of characters that give the byte order of each color
component.  For example, if rawimage.format is 'RGBA', there are four color
components: red, green, blue and alpha, in that order.  Other common format
strings are 'RGB', 'LA' (luminance, alpha) and 'I' (intensity).

The "pitch" of an image is the number of bytes in a row (this may validly be
more than the number required to make up the width of the image, it is common
to see this for word alignment).  If "pitch" is negative the rows of the image
are ordered from top to bottom, otherwise they are ordered from bottom to top.

Retrieving data with the format and pitch given in `ImageData.format` and
`ImageData.pitch` avoids the need for data conversion (assuming you can make
use of the data in this arbitrary format).

"""

from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO, Sequence

import pyglet

if TYPE_CHECKING:
    from pyglet.image.base import _AbstractImage

from pyglet.image import animation  # noqa: F401
from pyglet.image.animation import Animation, AnimationFrame  # noqa: F401, TC001
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

    def __init__(self, color: Sequence[int, int, int, int] = (0, 0, 0, 0)):
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

    def __init__(
        self,
        color1: Sequence[int, int, int, int] = (150, 150, 150, 255),
        color2: Sequence[int, int, int, int] = (200, 200, 200, 255),
    ):
        """Initialise with the given colors.

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
