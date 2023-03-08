"""Group multiple small images into larger textures.

This module is used by :py:mod:`pyglet.resource` to efficiently pack small
images into larger textures.  :py:class:`~pyglet.image.atlas.TextureAtlas` maintains one texture;
:py:class:`TextureBin` manages a collection of atlases of a given size.

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
from typing import TYPE_CHECKING, Tuple

import pyglet

if TYPE_CHECKING:
    from pyglet.image import AbstractImage, TextureRegion, TextureArrayRegion


class AllocatorException(Exception):
    """The allocator does not have sufficient free space for the requested
    image size."""
    pass


class _Strip:
    __slots__ = 'x', 'y', 'max_height', 'y2'

    def __init__(self, y: int, max_height: int):
        self.x = 0
        self.y = y
        self.max_height = max_height
        self.y2 = y

    def add(self, width: int, height: int):
        assert width > 0 and height > 0
        assert height <= self.max_height

        x, y = self.x, self.y
        self.x += width
        self.y2 = max(self.y + height, self.y2)
        return x, y

    def compact(self):
        self.max_height = self.y2 - self.y


class Allocator:
    """Rectangular area allocation algorithm.

    Initialise with a given ``width`` and ``height``, then repeatedly
    call `alloc` to retrieve free regions of the area and protect that
    area from future allocations.

    `Allocator` uses a fairly simple strips-based algorithm.  It performs best
    when rectangles are allocated in decreasing height order.
    """
    __slots__ = 'width', 'height', 'strips', 'used_area'

    def __init__(self, width: int, height: int):
        """Create an `Allocator` of the given size.

        :Parameters:
            `width` : int
                Width of the allocation region.
            `height` : int
                Height of the allocation region.

        """
        assert width > 0 and height > 0
        self.width = width
        self.height = height
        self.strips = [_Strip(0, height)]
        self.used_area = 0

    def alloc(self, width: int, height: int) -> Tuple[int, int]:
        """Get a free area in the allocator of the given size.

        After calling `alloc`, the requested area will no longer be used.
        If there is not enough room to fit the given area `AllocatorException`
        is raised.

        :Parameters:
            `width` : int
                Width of the area to allocate.
            `height` : int
                Height of the area to allocate.

        :rtype: int, int
        :return: The X and Y coordinates of the bottom-left corner of the
            allocated region.
        """
        for strip in self.strips:
            if self.width - strip.x >= width and strip.max_height >= height:
                self.used_area += width * height
                return strip.add(width, height)

        if self.width >= width and self.height - strip.y2 >= height:
            self.used_area += width * height
            strip.compact()
            newstrip = _Strip(strip.y2, self.height - strip.y2)
            self.strips.append(newstrip)
            return newstrip.add(width, height)

        raise AllocatorException('No more space in %r for box %dx%d' % (self, width, height))

    def get_usage(self) -> float:
        """Get the fraction of area already allocated.

        This method is useful for debugging and profiling only.

        :rtype: float
        """
        return self.used_area / float(self.width * self.height)

    def get_fragmentation(self) -> float:
        """Get the fraction of area that's unlikely to ever be used, based on
        current allocation behaviour.

        This method is useful for debugging and profiling only.

        :rtype: float
        """
        # The total unused area in each compacted strip is summed.
        if not self.strips:
            return 0.0
        possible_area = self.strips[-1].y2 * self.width
        return 1.0 - self.used_area / float(possible_area)


class TextureAtlas:
    """Collection of images within a texture."""

    def __init__(self, width: int = 2048, height: int = 2048):
        """Create a texture atlas of the given size.

        :Parameters:
            `width` : int
                Width of the underlying texture.
            `height` : int
                Height of the underlying texture.

        """
        max_texture_size = pyglet.image.get_max_texture_size()
        width = min(width, max_texture_size)
        height = min(height, max_texture_size)

        self.texture = pyglet.image.Texture.create(width, height)
        self.allocator = Allocator(width, height)

    def add(self, img: 'AbstractImage', border: int = 0) -> 'TextureRegion':
        """Add an image to the atlas.

        This method will fail if the given image cannot be transferred
        directly to a texture (for example, if it is another texture).
        :py:class:`~pyglet.image.ImageData` is the usual image type for this method.

        `AllocatorException` will be raised if there is no room in the atlas
        for the image.

        :Parameters:
            `img` : `~pyglet.image.AbstractImage`
                The image to add.
            `border` : int
                Leaves specified pixels of blank space around
                each image added to the Atlas.

        :rtype: :py:class:`~pyglet.image.TextureRegion`
        :return: The region of the atlas containing the newly added image.
        """
        x, y = self.allocator.alloc(img.width + border * 2, img.height + border * 2)
        self.texture.blit_into(img, x + border, y + border, 0)
        return self.texture.get_region(x + border, y + border, img.width, img.height)


class TextureBin:
    """Collection of texture atlases.

    :py:class:`~pyglet.image.atlas.TextureBin` maintains a collection of texture atlases, and creates new
    ones as necessary to accommodate images added to the bin.
    """

    def __init__(self, texture_width: int = 2048, texture_height: int = 2048):
        """Create a texture bin for holding atlases of the given size.

        :Parameters:
            `texture_width` : int
                Width of texture atlases to create.
            `texture_height` : int
                Height of texture atlases to create.
            `border` : int
                Leaves specified pixels of blank space around
                each image added to the Atlases.

        """
        max_texture_size = pyglet.image.get_max_texture_size()
        self.texture_width = min(texture_width, max_texture_size)
        self.texture_height = min(texture_height, max_texture_size)
        self.atlases = []

    def add(self, img: 'AbstractImage', border: int = 0) -> 'TextureRegion':
        """Add an image into this texture bin.

        This method calls `TextureAtlas.add` for the first atlas that has room
        for the image.

        `AllocatorException` is raised if the image exceeds the dimensions of
        ``texture_width`` and ``texture_height``.

        :Parameters:
            `img` : `~pyglet.image.AbstractImage`
                The image to add.
            `border` : int
                Leaves specified pixels of blank space around
                each image added to the Atlas.

        :rtype: :py:class:`~pyglet.image.TextureRegion`
        :return: The region of an atlas containing the newly added image.
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

    :py:class:`~pyglet.image.atlas.TextureArrayBin` maintains a collection of texture arrays, and creates new
    ones as necessary as the depth is exceeded.
    """

    def __init__(self, texture_width=2048, texture_height=2048, max_depth=None):
        max_texture_size = pyglet.image.get_max_texture_size()
        self.max_depth = max_depth or pyglet.image.get_max_array_texture_layers()
        self.texture_width = min(texture_width, max_texture_size)
        self.texture_height = min(texture_height, max_texture_size)
        self.arrays = []

    def add(self, img: 'AbstractImage') -> 'TextureArrayRegion':
        """Add an image into this texture array bin.

        This method calls `TextureArray.add` for the first array that has room
        for the image.

        `TextureArraySizeExceeded` is raised if the image exceeds the dimensions of
        ``texture_width`` and ``texture_height``.

        :Parameters:
            `img` : `~pyglet.image.AbstractImage`
                The image to add.

        :rtype: :py:class:`~pyglet.image.TextureArrayRegion`
        :return: The region of an array containing the newly added image.
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
