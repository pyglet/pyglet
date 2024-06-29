"""Group multiple small images into larger Textures.

This module provides classes to efficiently pack small images into larger Textures.
This can have major performance benefits when dealiing with a large number of images.

:py:class:`~pyglet.image.atlas.TextureAtlas` maintains one texture; :py:class:`TextureBin`
manages a collection of atlases of a given size. :py:class:`TextureArrayBin` works similarly
except for :py:class:`~pyglet.image.TextureArray`s instead of altases.

This module is used internally by the :py:mod:`pyglet.resource` module.

Example usage::

    # Load images from disk
    car_image = pyglet.image.load('car.png')
    boat_image = pyglet.image.load('boat.png')

    # Pack these images into one or more textures
    bin = TextureBin()
    car_texture = bin.add(car_image)
    boat_texture = bin.add(boat_image)

The result of :py:meth:`TextureBin.add` is a :py:class:`TextureRegion`
containing the image. Once added, an image cannot be removed from a bin (or an 
atlas); nor can a list of images be obtained from a given bin or atlas -- it is 
the application's responsibility to keep track of the regions returned by the
``add`` methods.

.. versionadded:: 1.1
"""
from __future__ import annotations

import pyglet

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.image import AbstractImage, ImageData, TextureRegion, TextureArrayRegion


class AllocatorException(Exception):
    """The allocator does not have sufficient free space for the requested
    image size."""
    pass


class _Strip:
    __slots__ = 'x', 'y', 'max_height', 'y2'

    def __init__(self, y: int, max_height: int) -> None:
        self.x = 0
        self.y = y
        self.max_height = max_height
        self.y2 = y

    def add(self, width: int, height: int) -> tuple[int, int]:
        assert width > 0 and height > 0
        assert height <= self.max_height

        x, y = self.x, self.y
        self.x += width
        self.y2 = max(self.y + height, self.y2)
        return x, y

    def compact(self) -> None:
        self.max_height = self.y2 - self.y


class Allocator:
    """Rectangular area allocation algorithm.

    An ``Allocator`` is initialized with a specified ``width`` and ``height``.
    The :py:meth:`~alloc` method can then be called to retrieve free regions
    of that area (and protect them from future allocations).

    ``Allocator`` uses a fairly simple strips-based algorithm. It performs
    best when rectangles are allocated of the same size, or in decreasing
    height order.
    """
    __slots__ = 'width', 'height', 'strips', 'used_area'

    def __init__(self, width: int, height: int) -> None:
        """Create an ``Allocator`` of the given size."""
        assert width > 0 and height > 0
        self.width = width
        self.height = height
        self.strips = [_Strip(0, height)]
        self.used_area = 0

    def alloc(self, width: int, height: int) -> tuple[int, int]:
        """Get the position of a free area in the allocator of the given size

        If a suitable position can be found for the requested size, the position
        will be marked as in-use and returned. (The same position will never be
        returned twice).
        If there is not enough room to fit the given area, ``AllocatorException``
        is raised.
        """
        for strip in self.strips:
            if self.width - strip.x >= width and strip.max_height >= height:
                self.used_area += width * height
                return strip.add(width, height)

        strip = self.strips[-1]

        if self.width >= width and self.height - strip.y2 >= height:
            self.used_area += width * height
            strip.compact()
            newstrip = _Strip(strip.y2, self.height - strip.y2)
            self.strips.append(newstrip)
            return newstrip.add(width, height)

        raise AllocatorException(f"No more space in {self} for box {width}x{height}")

    def get_usage(self) -> float:
        """Get the fraction of area already allocated.

        This method is useful for debugging and profiling only.
        """
        return self.used_area / float(self.width * self.height)

    def get_fragmentation(self) -> float:
        """Get the fraction of area that's unlikely to ever be used, based on
        current allocation behaviour.

        This method is useful for debugging and profiling only.
        """
        # The total unused area in each compacted strip is summed.
        if not self.strips:
            return 0.0
        possible_area = self.strips[-1].y2 * self.width
        return 1.0 - self.used_area / possible_area


class TextureAtlas:
    """A large Texture made up of multiple smaller images.

    A TextureAtlas is one maximally sized Texture which is made up of
    multiple smaller Images. This can improve rendering performance
    by allowing all the Images to be drawn together with a single
    Texture bind, rather than multiple tiny Texture binds per draw.

    When creating a TextureAtlas instance, a new :py:class:`~pyglet.image.Texture`
    object will be created at the requested size. If the maximum texture
    size supported by the OpenGL driver is less than requested, the
    smaller of the two will be used.
    """

    def __init__(self, width: int = 2048, height: int = 2048) -> None:
        """Create a Texture Atlas of the given size."""
        max_texture_size = pyglet.image.get_max_texture_size()
        width = min(width, max_texture_size)
        height = min(height, max_texture_size)

        self.texture = pyglet.image.Texture.create(width, height)
        self.allocator = Allocator(width, height)

    def add(self, img: ImageData, border: int = 0) -> TextureRegion:
        """Add ImageData to the atlas.

        Given :py:class:`~pyglet.image.ImageData`, add it to the Atlas and
        return a new :py:class:`~pyglet.image.TextureRegion` object. An
        optional ``border`` argument can be passed, which will leave the
        specified number of blank pixels around the added ImageData. This
        can be useful in certain situations and blend modes, where
        neighboring pixel data can "bleed" into the edges.

        This method will fail if the given image cannot be transferred directly
        to a texture (for example, if it is not an instance of ImageData, such
        as another Texture). ``AllocatorException`` will be raised if there is
        no room in the atlas for the image.
        """
        x, y = self.allocator.alloc(img.width + border * 2, img.height + border * 2)
        self.texture.blit_into(img, x + border, y + border, 0)
        return self.texture.get_region(x + border, y + border, img.width, img.height)


class TextureBin:
    """Collection of TextureAtlases.

    :py:class:`~pyglet.image.atlas.TextureBin` maintains a collection
    of TextureAtlases, and creates new ones as necessary to accommodate
    adding an unbound number of Images. When one TextureAltas is full,
    a new one is automatically created to fit the next ImageData.
    """

    def __init__(self, texture_width: int = 2048, texture_height: int = 2048) -> None:
        """Create a texture bin for holding atlases of the given size."""
        max_texture_size = pyglet.image.get_max_texture_size()
        self.texture_width = min(texture_width, max_texture_size)
        self.texture_height = min(texture_height, max_texture_size)
        self.atlases = []

    def add(self, img: ImageData | AbstractImage, border: int = 0) -> TextureRegion:
        """Add an image into this texture bin.

        This method calls :py:meth:`~TextureAtlas.add` for the first atlas
        that has room for the image.

        ``AllocatorException`` is raised if the image exceeds the dimensions
        of ``texture_width`` and ``texture_height``.
        """
        for atlas in list(self.atlases):
            try:
                return atlas.add(img, border)
            except AllocatorException:
                # Remove atlases that are no longer useful (so that their textures
                # can later be freed if the images inside them get collected).
                if img.width < 64 and img.height < 64:
                    self.atlases.remove(atlas)

        atlas = TextureAtlas(self.texture_width, self.texture_height)
        self.atlases.append(atlas)
        return atlas.add(img, border)


class TextureArrayBin:
    """Collection of texture arrays.

    :py:class:`~pyglet.image.atlas.TextureArrayBin` maintains a collection of
    texture arrays, and creates new ones as necessary as the depth is exceeded.
    This works similarly to TextureBin, but it manages TextureArrays instead of
    TextureAtlases.
    """

    def __init__(self, texture_width: int = 2048, texture_height: int = 2048, max_depth: int | None = None) -> None:
        max_texture_size = pyglet.image.get_max_texture_size()
        self.max_depth = max_depth or pyglet.image.get_max_array_texture_layers()
        self.texture_width = min(texture_width, max_texture_size)
        self.texture_height = min(texture_height, max_texture_size)
        self.arrays = []

    def add(self, img: ImageData) -> TextureArrayRegion:
        """Add an image into this texture array bin.

        This method calls :py:meth:`~pyglet.image.TextureArray.add` for the first
        array that has room for the image.

        ``TextureArraySizeExceeded`` is raised if the image exceeds the dimensions of
        ``texture_width`` and ``texture_height``.
        """
        try:
            array = self.arrays[-1]
            return array.add(img)
        except pyglet.image.TextureArrayDepthExceeded:
            pass
        except IndexError:
            pass

        array = pyglet.image.TextureArray.create(self.texture_width, self.texture_height, max_depth=self.max_depth)
        self.arrays.append(array)
        return array.add(img)
