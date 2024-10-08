from __future__ import annotations

import re
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import BinaryIO, Callable, Iterator, Literal, NamedTuple, Sequence

from pyglet.enums import TextureType, TextureFilter, AddressMode, ComponentFormat
from pyglet.image.animation import Animation
from pyglet.image.codecs import ImageEncoder
from pyglet.image.codecs import registry as _codec_registry
from pyglet.util import asbytes

class ImagePattern(ABC):
    """Abstract image creation class."""

    @abstractmethod
    def create_image(self, width: int, height: int) -> AbstractImage:
        """Create an image of the given size."""
        raise NotImplementedError('method must be defined in subclass')

def _color_as_bytes(color: Sequence[int, int, int, int]) -> bytes:
    if len(color) != 4:
        raise TypeError("color is expected to have 4 components")
    return bytes(color)

class ImageException(Exception):
    pass


class TextureArraySizeExceeded(ImageException):
    """Exception occurs ImageData dimensions are larger than the array supports."""


class TextureArrayDepthExceeded(ImageException):
    """Exception occurs when depth has hit the maximum supported of the array."""


class AbstractImage(ABC):
    """Abstract class representing an image."""

    anchor_x: int = 0
    """X coordinate of anchor, relative to left edge of image data."""

    anchor_y: int = 0
    """Y coordinate of anchor, relative to bottom edge of image data."""

    def __init__(self, width: int, height: int):
        """Initialized in subclass."""
        self.width = width
        self.height = height

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(size={self.width}x{self.height})"

    @abstractmethod
    def get_image_data(self) -> ImageData:
        """Get an ImageData view of this image.

        Changes to the returned instance may or may not be reflected in this image.
        """

    @abstractmethod
    def get_texture(self) -> TextureBase:
        """A :py:class:`~pyglet.image.Texture` view of this image."""

    @abstractmethod
    def get_mipmapped_texture(self) -> TextureBase:
        """Retrieve a :py:class:`~pyglet.image.Texture` instance with all mipmap levels filled in."""

    @abstractmethod
    def get_region(self, x: int, y: int, width: int, height: int) -> AbstractImage:
        """Retrieve a rectangular region of this image."""

    def save(self, filename: str | None = None,
             file: BinaryIO | None = None, encoder: ImageEncoder | None = None) -> None:
        """Save this image to a file.

        Args:
            filename:
                Used to set the image file format, and to open the output file
                if ``file`` is unspecified.
            file:
                An optional file-like object to write image data to.
            encoder:
                If unspecified, all encoders matching the filename extension
                are tried, or all encoders if no filename is provided. If all
                fail, the exception from the first one attempted is raised.
        """
        if file is None:
            assert filename is not None, "Either filename or file must be specified."
            file = open(filename, 'wb')

        if encoder is not None:
            encoder.encode(self, filename, file)
        else:
            _codec_registry.encode(self, filename, file)

    @abstractmethod
    def blit(self, x: int, y: int, z: int = 0) -> None:
        """Draw this image to the active framebuffer.

        The image will be drawn with the lower-left corner at
        (``x - anchor_x``, ``y - anchor_y``, ``z``).

        .. note:: This is a relatively slow method, as a full OpenGL setup and
                  draw call is required for each blit. For performance, consider
                  creating a Sprite from the Image, and adding it to a Batch.
        """

    @abstractmethod
    def blit_into(self, source, x: int, y: int, z: int) -> None:
        """Draw the provided ``source`` data INTO this image.

        ``source`` will be copied into this image such that its anchor point
        is aligned with the ``x`` and ``y`` parameters. If this image is a 3D
        Texture, the ``z`` coordinate gives the image slice to copy into.

        Note that if ``source`` is larger than this image (or the positioning
        would cause the copy to go out of bounds), an exception may be raised.
        To prevent errors, you can use the ``source.get_region(x, y, w, h)``
        method to get a smaller section that will fall within the bounds of
        this image.
        """

    @abstractmethod
    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None) -> None:
        """Draw this image on the currently bound texture at ``target``.

        This image is copied into the texture such that this image's anchor
        point is aligned with the given ``x`` and ``y`` coordinates of the
        destination texture.  If the currently bound texture is a 3D texture,
        the ``z`` coordinate gives the image slice to blit into.
        """


class AbstractImageSequence(ABC):
    """Abstract sequence of images.

    Image sequence are useful for storing image animations or slices of a volume.
    The class implements the sequence interface (``__len__``, ``__getitem__``,
    ``__setitem__``).
    """

    @abstractmethod
    def get_texture_sequence(self) -> TextureSequence:
        """Get a TextureSequence.

        :rtype: `TextureSequence`

        .. versionadded:: 1.1
        """

    def get_animation(self, period: float, loop: bool = True) -> Animation:
        """Create an animation over this image sequence for the given constant
        framerate.

        Args:
            period:
                Number of seconds to display each frame.
            loop:
                If True, the animation will loop continuously.
        """
        return Animation.from_image_sequence(self, period, loop)

    @abstractmethod
    def __getitem__(self, item) -> AbstractImage:
        """Retrieve one or more images by index."""

    @abstractmethod
    def __setitem__(self, item, image: AbstractImage) -> AbstractImage:
        """Replace one or more images in the sequence.

        Args:
            image:
                The replacement image. The actual instance may not be used,
                depending on this implementation.
        """

    @abstractmethod
    def __len__(self) -> int:
        """Length of the image sequence."""

    @abstractmethod
    def __iter__(self) -> Iterator[AbstractImage]:
        """Iterate over the images in sequence."""


class TextureSequence(AbstractImageSequence):
    """Interface for a sequence of textures.

    Typical implementations store multiple :py:class:`~pyglet.image.TextureRegion`s
    within one :py:class:`~pyglet.image.Texture` to minimise state changes.
    """

    def __getitem__(self, item) -> TextureBase:
        raise NotImplementedError

    def __setitem__(self, item, texture: type[TextureBase]) -> AbstractImage:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __iter__(self) -> Iterator[TextureBase]:
        raise NotImplementedError

    def get_texture_sequence(self) -> TextureSequence:
        return self

class ImageData(AbstractImage):
    """An image represented as a string of unsigned bytes."""

    _swap1_pattern = re.compile(asbytes('(.)'), re.DOTALL)
    _swap2_pattern = re.compile(asbytes('(.)(.)'), re.DOTALL)
    _swap3_pattern = re.compile(asbytes('(.)(.)(.)'), re.DOTALL)
    _swap4_pattern = re.compile(asbytes('(.)(.)(.)(.)'), re.DOTALL)

    _current_texture = None
    _current_mipmap_texture = None

    def __init__(self, width: int, height: int, fmt: str, data: bytes, pitch: int | None = None):
        """Initialise image data.

        Args:
            width:
                Width of image data
            height:
                Height of image data
            fmt:
                A valid format string, such as 'RGB', 'RGBA', 'ARGB', etc.
            data:
                A sequence of bytes containing the raw image data.
            pitch:
                If specified, the number of bytes per row.  Negative values
                indicate a top-to-bottom arrangement.  Defaults to
                ``width * len(format)``.
        """
        super().__init__(width, height)

        self._current_format = self._desired_format = fmt.upper()
        self._current_data = data
        self.pitch = pitch or width * len(fmt)
        self._current_pitch = self.pitch
        self.mipmap_images = []

    def __getstate__(self):
        return {
            'width': self.width,
            'height': self.height,
            '_current_data': self.get_bytes(self._current_format, self._current_pitch),
            '_current_format': self._current_format,
            '_desired_format': self._desired_format,
            '_current_pitch': self._current_pitch,
            'pitch': self.pitch,
            'mipmap_images': self.mipmap_images,
        }

    def get_image_data(self) -> ImageData:
        return self

    @property
    def format(self) -> str:
        """Format string of the data. Read-write."""
        return self._desired_format

    @format.setter
    def format(self, fmt: str):
        self._desired_format = fmt.upper()
        self._current_texture = None

    def get_bytes(self, fmt: str | None = None, pitch: int | None = None) -> bytes:
        """Get the byte data of the image

        This method returns the raw byte data of the image, with optional conversion.
        To convert the data into another format, you can provide ``fmt`` and ``pitch``
        arguments. For example, if the image format is ``RGBA``, and you wish to get
        the byte data in ``RGB`` format::

            rgb_pitch = my_image.width // len('RGB')
            rgb_img_bytes = my_image.get_bytes(fmt='RGB', pitch=rgb_pitch)

        The image ``pitch`` may be negative, so be sure to check that when converting
        to another format. Switching the sign of the ``pitch`` will cause the image
        to appear "upside-down".

        Args:
            fmt:
                If provided, get the data in another format.
            pitch:
                The number of bytes per row. This generally means the length
                of the format string * the number of pixels per row.
                Negative values indicate a top-to-bottom arrangement.

        Note:
             Conversion to another format is done on the CPU, and can be
             somewhat costly for larger images. Consider performing conversion
             at load time for framerate sensitive applictions.
        """
        fmt = fmt or self._desired_format
        pitch = pitch or self._current_pitch

        if fmt == self._current_format and pitch == self._current_pitch:
            return self._current_data
        return self._convert(fmt, pitch)

    def set_bytes(self, fmt: str, pitch: int, data: bytes) -> None:
        """Set the byte data of the image.

        Args:
            fmt:
                The format string of the supplied data.
                For example: "RGB" or "RGBA"
            pitch:
                The number of bytes per row. This generally means the length
                of the format string * the number of pixels per row.
                Negative values indicate a top-to-bottom arrangement.
            data:
                Image data as bytes.
        """
        self._current_format = fmt
        self._current_pitch = pitch
        self._current_data = data
        self._current_texture = None
        self._current_mipmap_texture = None

    def get_data(self, fmt: str | None = None, pitch: int | None = None) -> bytes:
        """Get the byte data of the image.

        Warning:
            This method is deprecated and will be removed in the next version.
            Use :py:meth:`~get_bytes` instead.
        """
        return self.get_bytes(fmt, pitch)

    def set_data(self, fmt: str, pitch: int, data: bytes) -> None:
        """Set the byte data of the image.

        Warning:
            This method is deprecated and will be removed in the next version.
            Use :py:meth:`~set_bytes` instead.
        """
        self.set_bytes(fmt, pitch, data)

    def set_mipmap_image(self, level: int, image: AbstractImage) -> None:
        """Set a user-defined mipmap image for a particular level.

        These mipmap images will be applied to textures obtained via
        :py:meth:`~get_mipmapped_texture`, instead of automatically
        generated images for each level.

        Args:
            level:
                Mipmap level to set image at, must be >= 1.
            image:
                Image to set.  Must have correct dimensions for that mipmap
                level (i.e., width >> level, height >> level)
        """
        if level == 0:
            msg = 'Cannot set mipmap image at level 0 (it is this image)'
            raise ImageException(msg)

        # Check dimensions of mipmap
        width, height = self.width, self.height
        for i in range(level):
            width >>= 1
            height >>= 1
        if width != image.width or height != image.height:
            raise ImageException(f"Mipmap image has wrong dimensions for level {level}")

        # Extend mipmap_images list to required level
        self.mipmap_images += [None] * (level - len(self.mipmap_images))
        self.mipmap_images[level - 1] = image

    def create_texture(self, cls: type[TextureBase], rectangle: bool = False) -> TextureBase:
        """Given a texture class, create a texture containing this image."""
        raise NotImplementedError

    def get_texture(self, rectangle: bool = False) -> TextureBase:
        if not self._current_texture:
            self._current_texture = self.create_texture(TextureBase)
        return self._current_texture

    def get_mipmapped_texture(self) -> TextureBase:
        """Return a Texture with mipmaps.

        If :py:class:`~pyglet.image.set_mipmap_Image` has been called with at least
        one image, the set of images defined will be used. Otherwise, mipmaps will be
        automatically generated.
        """
        raise NotImplementedError

    def get_region(self, x: int, y: int, width: int, height: int) -> ImageDataRegion:
        """Retrieve a rectangular region of this image data."""
        return ImageDataRegion(x, y, width, height, self)

    def blit(self, x: int, y: int, z: int = 0, width: int | None = None, height: int | None = None) -> None:
        self.get_texture().blit(x, y, z, width, height)

    def blit_into(self, source, x: int, y: int, z: int) -> None:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        """Draw this image to the currently bound texture at ``target``.

        This image's anchor point will be aligned to the given ``x`` and ``y``
        coordinates.  If the currently bound texture is a 3D texture, the ``z``
        parameter gives the image slice to blit into.

        If ``internalformat`` is specified, ``glTexImage`` is used to initialise
        the texture; otherwise, ``glTexSubImage`` is used to update a region.
        """
        raise NotImplementedError

    def _apply_region_unpack(self):
        # Not needed on full images
        pass

    def _default_region_unpack(self):
        # Not needed on full images
        pass

    def _convert(self, fmt: str, pitch: int) -> bytes:
        """Return data in the desired format.

        This method does not alter this instance's current format or pitch.
        """
        if fmt == self._current_format and pitch == self._current_pitch:
            return self._current_data

        self._ensure_bytes()
        data = self._current_data
        current_pitch = self._current_pitch
        current_format = self._current_format
        sign_pitch = current_pitch // abs(current_pitch)
        if fmt != self._current_format:
            # Create replacement string, e.g. r'\4\1\2\3' to convert RGBA to ARGB
            repl = asbytes('')
            for c in fmt:
                try:
                    idx = current_format.index(c) + 1
                except ValueError:
                    idx = 1
                repl += asbytes(r'\%d' % idx)

            if len(current_format) == 1:
                swap_pattern = self._swap1_pattern
            elif len(current_format) == 2:
                swap_pattern = self._swap2_pattern
            elif len(current_format) == 3:
                swap_pattern = self._swap3_pattern
            elif len(current_format) == 4:
                swap_pattern = self._swap4_pattern
            else:
                raise ImageException('Current image format is wider than 32 bits.')

            packed_pitch = self.width * len(current_format)
            if abs(self._current_pitch) != packed_pitch:
                # Pitch is wider than pixel data, need to go row-by-row.
                new_pitch = abs(self._current_pitch)
                rows = [data[i:i + new_pitch] for i in range(0, len(data), new_pitch)]
                rows = [swap_pattern.sub(repl, r[:packed_pitch]) for r in rows]
                data = b''.join(rows)
            else:
                # Rows are tightly packed, apply regex over whole image.
                data = swap_pattern.sub(repl, data)

            # After conversion, rows will always be tightly packed
            current_pitch = sign_pitch * (len(fmt) * self.width)

        if pitch != current_pitch:
            diff = abs(current_pitch) - abs(pitch)
            if diff > 0:
                # New pitch is shorter than old pitch, chop bytes off each row
                new_pitch = abs(pitch)
                rows = [data[i:i + new_pitch - diff] for i in range(0, len(data), new_pitch)]
                data = b''.join(rows)

            elif diff < 0:
                # New pitch is longer than old pitch, add '0' bytes to each row
                new_pitch = abs(current_pitch)
                padding = bytes(1) * -diff
                rows = [data[i:i + new_pitch] + padding for i in range(0, len(data), new_pitch)]
                data = b''.join(rows)

            if current_pitch * pitch < 0:
                # Pitch differs in sign, swap row order
                new_pitch = abs(pitch)
                rows = [data[i:i + new_pitch] for i in range(0, len(data), new_pitch)]
                rows.reverse()
                data = b''.join(rows)

        return data

    def _ensure_bytes(self) -> None:
        if type(self._current_data) is not bytes:
            self._current_data = asbytes(self._current_data)

    @staticmethod
    def _get_gl_format_and_type(fmt):
        raise NotImplementedError

    @staticmethod
    def _get_internalformat(fmt):
        raise NotImplementedError


class ImageDataRegion(ImageData):
    def __init__(self, x, y, width, height, image_data):
        super().__init__(width, height,
                         image_data._current_format,
                         image_data._current_data,
                         image_data._current_pitch)
        self.x = x
        self.y = y

    def __getstate__(self):
        return {
            'width': self.width,
            'height': self.height,
            '_current_data': self.get_bytes(self._current_format, self._current_pitch),
            '_current_format': self._current_format,
            '_desired_format': self._desired_format,
            '_current_pitch': self._current_pitch,
            'pitch': self.pitch,
            'mipmap_images': self.mipmap_images,
            'x': self.x,
            'y': self.y,
        }

    def get_bytes(self, fmt=None, pitch=None):
        x1 = len(self._current_format) * self.x
        x2 = len(self._current_format) * (self.x + self.width)

        self._ensure_bytes()
        data = self._convert(self._current_format, abs(self._current_pitch))
        new_pitch = abs(self._current_pitch)
        rows = [data[i:i + new_pitch] for i in range(0, len(data), new_pitch)]
        rows = [row[x1:x2] for row in rows[self.y:self.y + self.height]]
        self._current_data = b''.join(rows)
        self._current_pitch = self.width * len(self._current_format)
        self._current_texture = None
        self.x = 0
        self.y = 0

        fmt = fmt or self._desired_format
        pitch = pitch or self._current_pitch
        return super().get_bytes(fmt, pitch)

    def set_bytes(self, fmt, pitch, data):
        self.x = 0
        self.y = 0
        super().set_bytes(fmt, pitch, data)

    def _apply_region_unpack(self):
        raise NotImplementedError

    def _default_region_unpack(self):
        raise NotImplementedError

    def get_region(self, x, y, width, height):
        x += self.x
        y += self.y
        return super().get_region(x, y, width, height)

class CompressedImageData(AbstractImage):
    """Compressed image data suitable for direct uploading to GPU."""

    _current_texture = None
    _current_mipmap_texture = None

    def __init__(self, width: int, height: int, gl_format: int, data: bytes,
                 extension: str | None = None,
                 decoder: Callable[[bytes, int, int], AbstractImage] | None = None) -> None:
        """Construct a CompressedImageData with the given compressed data.

        Args:
            width:
                The width of the image.
            height:
                The height of the image.
            gl_format:
                GL constant giving the format of the compressed data.
                For example: ``GL_COMPRESSED_RGBA_S3TC_DXT5_EXT``.
            data:
                An array of bytes containing the compressed image data.
            extension:
                If specified, gives the name of a GL extension to check for
                before creating a texture.
            decoder:
                An optional fallback function used to decode the compressed data.
                This function is called if the required extension is not present.
        """
        super().__init__(width, height)
        self.data = data
        self.gl_format = gl_format
        self.extension = extension
        self.decoder = decoder
        self.mipmap_data = []

    def set_mipmap_data(self, level: int, data: bytes) -> None:
        """Set compressed image data for a mipmap level.

        Supplied data gives a compressed image for the given mipmap level.
        This image data must be in the same format as was used in the
        constructor. The image data must also be of the correct dimensions for
        the level (i.e., width >> level, height >> level); but this is not checked.
        If *any* mipmap levels are specified, they are used; otherwise, mipmaps for
        ``mipmapped_texture`` are generated automatically.
        """
        # Extend mipmap_data list to required level
        self.mipmap_data += [None] * (level - len(self.mipmap_data))
        self.mipmap_data[level - 1] = data

    def _have_extension(self) -> bool:
        raise NotImplementedError

    def get_texture(self) -> TextureBase:
        raise NotImplementedError

    def get_mipmapped_texture(self) -> TextureBase:
        raise NotImplementedError

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        raise NotImplementedError

    def get_image_data(self) -> CompressedImageData:
        return self

    def get_region(self, x: int, y: int, width: int, height: int) -> AbstractImage:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit(self, x: int, y: int, z: int = 0) -> None:
        self.get_texture().blit(x, y, z)

    def blit_into(self, source, x: int, y: int, z: int) -> None:
        raise NotImplementedError(f"Not implemented for {self}")


class ImageGrid(AbstractImage, AbstractImageSequence):
    """An imaginary grid placed over an image allowing easy access to
    regular regions of that image.

    The grid can be accessed either as a complete image, or as a sequence
    of images. The most useful applications are to access the grid
    as a :py:class:`~pyglet.image.TextureGrid`::

        image_grid = ImageGrid(...)
        texture_grid = image_grid.get_texture_sequence()

    or as a :py:class:`~pyglet.image.Texture3D`::

        image_grid = ImageGrid(...)
        texture_3d = Texture3D.create_for_image_grid(image_grid)

    """

    _items: list
    _texture_grid: TextureGrid = None

    def __init__(self, image: AbstractImage, rows: int, columns: int, item_width: int | None = None,
                 item_height: int | None = None, row_padding: int = 0, column_padding: int = 0) -> None:
        """Construct a grid for the given image.

        You can specify parameters for the grid, for example setting
        the padding between cells.  Grids are always aligned to the
        bottom-left corner of the image.

        Args:
            image:
                Image over which to construct the grid.
            rows:
                Number of rows in the grid.
            columns:
                Number of columns in the grid.
            item_width:
                Width of each column.  If unspecified, is calculated such
                that the entire image width is used.
            item_height:
                Height of each row.  If unspecified, is calculated such that
                the entire image height is used.
            row_padding:
                Pixels separating adjacent rows.  The padding is only
                inserted between rows, not at the edges of the grid.
            column_padding:
                Pixels separating adjacent columns.  The padding is only
                inserted between columns, not at the edges of the grid.
        """
        super().__init__(image.width, image.height)
        self._items = []
        self.image = image
        self.rows = rows
        self.columns = columns
        self.item_width = item_width or (image.width - column_padding * (columns - 1)) // columns
        self.item_height = item_height or (image.height - row_padding * (rows - 1)) // rows
        self.row_padding = row_padding
        self.column_padding = column_padding

    def get_texture(self) -> TextureBase:
        return self.image.get_texture()

    def get_image_data(self) -> ImageData:
        return self.image.get_image_data()

    def get_texture_sequence(self) -> TextureGrid:
        if not self._texture_grid:
            self._texture_grid = TextureGrid(self)
        return self._texture_grid

    def get_mipmapped_texture(self) -> TextureBase:
        raise NotImplementedError(f"Not implemented for {self}.")

    def get_region(self, x: int, y: int, width: int, height: int) -> AbstractImage:
        raise NotImplementedError(f"Not implemented for {self}.")

    def blit(self, x: int, y: int, z: int = 0) -> None:
        raise NotImplementedError(f"Not implemented for {self}.")

    def blit_into(self, source, x: int, y: int, z: int) -> None:
        raise NotImplementedError(f"Not implemented for {self}.")

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        raise NotImplementedError(f"Not implemented for {self}.")

    def _update_items(self) -> None:
        if not self._items:
            y = 0
            for row in range(self.rows):
                x = 0
                for col in range(self.columns):
                    self._items.append(self.image.get_region(x, y, self.item_width, self.item_height))
                    x += self.item_width + self.column_padding
                y += self.item_height + self.row_padding

    def __getitem__(self, index) -> ImageDataRegion:
        self._update_items()
        if type(index) is tuple:
            row, column = index
            assert 0 <= row < self.rows and 0 <= column < self.columns
            return self._items[row * self.columns + column]
        else:
            return self._items[index]

    def __setitem__(self, index: int, value: AbstractImage):
        raise NotImplementedError

    def __len__(self) -> int:
        return self.rows * self.columns

    def __iter__(self) -> Iterator[ImageDataRegion]:
        self._update_items()
        return iter(self._items)




class TextureInternalFormat(NamedTuple):
    component: ComponentFormat | str
    depth: int | None = None
    data_type: type[float, int] | None = None


class TextureDescriptor:
    __slots__ = ("tex_type", "min_filter", "mag_filter", "address_mode", "internal_format", "pixel_format",
                 "anisotropic_level", "depth", "mipmap_levels")

    def __init__(self,
                 tex_type: TextureType = TextureType.TYPE_2D,
                 min_filter: TextureFilter = TextureFilter.LINEAR,
                 mag_filter: TextureFilter = TextureFilter.LINEAR,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 internal_format: TextureInternalFormat | None = None,
                 pixel_format: ComponentFormat = ComponentFormat.RGBA,
                 anisotropic_level: int = 0,
                 depth: int = 1,
                 mipmap_levels: int = 1):
        """Create a description of the texture.

        Args:
            tex_type:
                The default texture type. Defaults to TYPE_2D.
            min_filter:
                The default minification filter. Defaults to LINEAR.
            mag_filter:
                The default magnification filter. Defaults to LINEAR.
            address_mode:
                The border repeat mode for textures once values fall outside 0-1.
            internal_format:
                The internal pixel format of the intended texture. Defaults to RGBA 8bits per channel.
            pixel_format:
                The pixel format order of the data that will be written. Defaults to RGBA.
            anisotropic_level:
                The anisotropic filtering level, 0 is disabled. Not always supported.
        """
        self.tex_type = tex_type
        self.min_filter = min_filter
        self.mag_filter = mag_filter
        self.address_mode = address_mode
        self.internal_format = internal_format or TextureInternalFormat(ComponentFormat.RGBA, 8)
        self.pixel_format = pixel_format
        self.anisotropic_level = anisotropic_level

class TextureBase(AbstractImage):
    """An image loaded into GPU memory.

    Typically, you will get an instance of Texture by accessing calling
    the ``get_texture()`` method of any AbstractImage class (such as ImageData).
    """

    region_class: TextureRegionBase  # Set to TextureRegion after it's defined
    """The class to use when constructing regions of this texture.
     The class should be a subclass of TextureRegion.
    """

    tex_coords = (0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0)
    """12-tuple of float, named (u1, v1, r1, u2, v2, r2, ...).
    ``u, v, r`` give the 3D texture coordinates for vertices 1-4. The vertices
    are specified in the order bottom-left, bottom-right, top-right and top-left.
    """

    tex_coords_order: tuple[int, int, int, int] = (0, 1, 2, 3)
    """The default vertex winding order for a quad.
    This defaults to counter-clockwise, starting at the bottom-left.
    """

    target: int
    """The GL texture target (e.g., ``GL_TEXTURE_2D``)."""

    colors = (0, 0, 0, 0) * 4

    level: int = 0
    """The mipmap level of this texture."""

    images = 1

    x: int = 0
    y: int = 0
    z: int = 0

    # Default image descriptor used. This is a backend agnostic implementation.
    default_descriptor = TextureDescriptor(
        tex_type=TextureType.TYPE_2D,
        min_filter=TextureFilter.LINEAR,
        mag_filter=TextureFilter.LINEAR,
        address_mode=AddressMode.REPEAT,
        internal_format=TextureInternalFormat(ComponentFormat.RGBA, 8),
        pixel_format=ComponentFormat.RGBA,
    )

    def __init__(self, width: int, height: int, tex_id: int, descriptor: TextureDescriptor | None) -> None:
        super().__init__(width, height)
        self.id = tex_id
        self.descriptor = descriptor or self.default_descriptor

    def delete(self) -> None:
        """Delete this texture and the memory it occupies.

        Textures are invalid after deletion, and may no longer be used.
        """
        self.id = None

    #def __del__(self):
    #    raise NotImplementedError

    def bind(self, texture_unit: int = 0) -> None:
        """Bind to a specific Texture Unit by number."""
        raise NotImplementedError

    # def bind_image_texture(self, unit: int, level: int = 0, layered: bool = False,
    #                        layer: int = 0, access: int = GL_READ_WRITE, fmt: int = GL_RGBA32F):
    #     """Bind as an ImageTexture for use with a :py:class:`~pyglet.shader.ComputeShaderProgram`.
    #
    #     .. note:: OpenGL 4.3, or 4.2 with the GL_ARB_compute_shader extention is required.
    #     """
    #     raise NotImplementedError

    @classmethod
    def create(cls, width: int, height: int, descriptor: TextureDescriptor | None = None,
               blank_data: bool = True) -> TextureBase:
        """Create a Texture

        Create a Texture with the specified dimentions, target and format.
        On return, the texture will be bound.

        Args:
            width:
                Width of texture in pixels.
            height:
                Height of texture in pixels.
            descriptor:
                The descriptor information of the intended texture.
            blank_data:
                If True, initialize the texture data with all zeros. If False, do not pass initial data.
        """
        raise NotImplementedError

    def get_image_data(self, z: int = 0) -> ImageData:
        """Get the image data of this texture.

        Bind the texture, and read the pixel data back from the GPU.
        This can be a somewhat costly operation.

        Modifying the returned ImageData object has no effect on the
        texture itself. Uploading ImageData back to the GPU/texture
        can be done with the :py:meth:`~Texture.blit_into` method.

        Args:
            z:
                For 3D textures, the image slice to retrieve.
        """
        raise NotImplementedError

    def get_texture(self, rectangle: bool = False) -> TextureBase:
        return self

    def blit(self, x: int, y: int, z: int = 0, width: int | None = None, height: int | None = None) -> None:
        """Blit the texture to the screen.

        This is a costly operation, and should not be used for performance critical
        code. Blitting a texture requires binding it, setting up throwaway buffers,
        creating a VAO, uploading attribute data, and then making a single draw call.
        This is quite wasteful and slow, so blitting should not be used for more than
        a few images. This method is provided to assist with debugging, but not intended
        for drawing of multiple images.

        Instead, consider creating a :py:class:`~pyglet.sprite.Sprite` with the Texture,
        and drawing it as part of a larger :py:class:`~pyglet.graphics.Batch`.
        """
        raise NotImplementedError

    def get_mipmapped_texture(self) -> TextureBase:
        raise NotImplementedError(f"Not implemented for {self}.")

    def blit_into(self, source: AbstractImage, x: int, y: int, z: int):
        raise NotImplementedError

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        raise NotImplementedError(f"Not implemented for {self}")

    def get_region(self, x: int, y: int, width: int, height: int) -> TextureRegionBase:
        return self.region_class(x, y, 0, width, height, self)

    def get_transform(self, flip_x: bool = False, flip_y: bool = False,
                      rotate: Literal[0, 90, 180, 270, 360] = 0) -> TextureRegionBase:
        """Create a copy of this image applying a simple transformation.

        The transformation is applied to the texture coordinates only;
        :py:meth:`~pyglet.image.AbstractImage.get_image_data` will return the
        untransformed data. The transformation is applied around the anchor point.

        Args:
            flip_x:
                If True, the returned image will be flipped horizontally.
            flip_y:
                If True, the returned image will be flipped vertically.
            rotate:
                Degrees of clockwise rotation of the returned image.  Only
                90-degree increments are supported.
        """
        transform = self.get_region(0, 0, self.width, self.height)
        bl, br, tr, tl = 0, 1, 2, 3
        transform.anchor_x = self.anchor_x
        transform.anchor_y = self.anchor_y
        if flip_x:
            bl, br, tl, tr = br, bl, tr, tl
            transform.anchor_x = self.width - self.anchor_x
        if flip_y:
            bl, br, tl, tr = tl, tr, bl, br
            transform.anchor_y = self.height - self.anchor_y
        rotate %= 360
        if rotate < 0:
            rotate += 360
        if rotate == 0:
            pass
        elif rotate == 90:
            bl, br, tr, tl = br, tr, tl, bl
            transform.anchor_x, transform.anchor_y = transform.anchor_y, transform.width - transform.anchor_x
        elif rotate == 180:
            bl, br, tr, tl = tr, tl, bl, br
            transform.anchor_x = transform.width - transform.anchor_x
            transform.anchor_y = transform.height - transform.anchor_y
        elif rotate == 270:
            bl, br, tr, tl = tl, bl, br, tr
            transform.anchor_x, transform.anchor_y = transform.height - transform.anchor_y, transform.anchor_x
        else:
            raise ImageException("Only 90 degree rotations are supported.")
        if rotate in (90, 270):
            transform.width, transform.height = transform.height, transform.width
        transform._set_tex_coords_order(bl, br, tr, tl)
        return transform

    def _set_tex_coords_order(self, bl, br, tr, tl):
        tex_coords = (self.tex_coords[:3],
                      self.tex_coords[3:6],
                      self.tex_coords[6:9],
                      self.tex_coords[9:])
        self.tex_coords = tex_coords[bl] + tex_coords[br] + tex_coords[tr] + tex_coords[tl]

        order = self.tex_coords_order
        self.tex_coords_order = (order[bl], order[br], order[tr], order[tl])

    @property
    def uv(self) -> tuple[float, float, float, float]:
        """Tuple containing the left, bottom, right, top 2D texture coordinates."""
        tex_coords = self.tex_coords
        return tex_coords[0], tex_coords[1], tex_coords[3], tex_coords[7]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, size={self.width}x{self.height})"


class TextureRegionBase(TextureBase):
    """A rectangular region of a texture, presented as if it were a separate texture."""

    def __init__(self, x: int, y: int, z: int, width: int, height: int, owner: TextureBase):
        super().__init__(width, height, owner.id, owner.descriptor)

        self.x = x
        self.y = y
        self.z = z
        self._width = width
        self._height = height
        self.owner = owner
        owner_u1 = owner.tex_coords[0]
        owner_v1 = owner.tex_coords[1]
        owner_u2 = owner.tex_coords[3]
        owner_v2 = owner.tex_coords[7]
        scale_u = owner_u2 - owner_u1
        scale_v = owner_v2 - owner_v1
        u1 = x / owner.width * scale_u + owner_u1
        v1 = y / owner.height * scale_v + owner_v1
        u2 = (x + width) / owner.width * scale_u + owner_u1
        v2 = (y + height) / owner.height * scale_v + owner_v1
        r = z / owner.images + owner.tex_coords[2]
        self.tex_coords = (u1, v1, r, u2, v1, r, u2, v2, r, u1, v2, r)

    def get_image_data(self):
        image_data = self.owner.get_image_data(self.z)
        return image_data.get_region(self.x, self.y, self.width, self.height)

    def get_region(self, x: int, y: int, width: int, height: int) -> TextureRegionBase:
        x += self.x
        y += self.y
        region = self.region_class(x, y, self.z, width, height, self.owner)
        region._set_tex_coords_order(*self.tex_coords_order)
        return region

    def blit_into(self, source: AbstractImage, x: int, y: int, z: int) -> None:
        assert source.width <= self._width and source.height <= self._height, f"{source} is larger than {self}"
        self.owner.blit_into(source, x + self.x, y + self.y, z + self.z)

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(id={self.id},"
                f" size={self.width}x{self.height}, owner={self.owner.width}x{self.owner.height})")

    def delete(self) -> None:
        """Deleting a TextureRegion has no effect. Operate on the owning texture instead."""

    def __del__(self):
        pass


TextureBase.region_class = TextureRegionBase



class UniformTextureSequence(TextureSequence):
    """Interface for a sequence of textures, each with the same dimensions."""

class TextureArrayRegion(TextureRegionBase):
    """A region of a TextureArray, presented as if it were a separate texture."""

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, size={self.width}x{self.height}, layer={self.z})"

class TextureArray(TextureBase, UniformTextureSequence):
    default_descriptor = TextureDescriptor(
        tex_type=TextureType.TYPE_2D_ARRAY,
        min_filter=TextureFilter.LINEAR,
        mag_filter=TextureFilter.LINEAR,
    )
    def __init__(self, width, height, tex_id, max_depth, descriptor: TextureDescriptor | None = None):
        super().__init__(width, height, tex_id, descriptor or self.default_descriptor)
        self.max_depth = max_depth
        self.items = []

    @classmethod
    def create(cls, width: int, height: int, descriptor: TextureDescriptor | None = None, max_depth: int = 256) -> TextureArray:
        """Create an empty TextureArray.

        You may specify the maximum depth, or layers, the Texture Array should have. This defaults
        to 256, but will be hardware and driver dependent.

        Args:
            width:
                Width of the texture.
            height:
                Height of the texture.
            descriptor:
                Texture description.
            max_depth:
                The number of layers in the texture array.

        .. versionadded:: 2.0
        """
        raise NotImplementedError

    def _verify_size(self, image: AbstractImage) -> None:
        if image.width > self.width or image.height > self.height:
            raise TextureArraySizeExceeded(
                f'Image ({image.width}x{image.height}) exceeds the size of the TextureArray ({self.width}x'
                f'{self.height})')

    def add(self, image: ImageData) -> TextureArrayRegion:
        if len(self.items) >= self.max_depth:
            raise TextureArrayDepthExceeded("TextureArray is full.")

        self._verify_size(image)
        start_length = len(self.items)
        item = self.region_class(0, 0, start_length, image.width, image.height, self)

        self.blit_into(image, image.anchor_x, image.anchor_y, start_length)
        self.items.append(item)
        return item

    def allocate(self, *images: AbstractImage) -> list[TextureArrayRegion]:
        """Allocates multiple images at once."""
        raise NotImplementedError

    @classmethod
    def create_for_image_grid(cls, grid, descriptor: TextureDescriptor | None = None) -> TextureArray:
        texture_array = cls.create(grid[0].width, grid[0].height, descriptor, max_depth=len(grid))
        texture_array.allocate(*grid[:])
        return texture_array

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index) -> TextureArrayRegion:
        return self.items[index]

    def __setitem__(self, index, value) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[TextureRegionBase]:
        return iter(self.items)


TextureArray.region_class = TextureArrayRegion
TextureArrayRegion.region_class = TextureArrayRegion

class Texture3D(TextureBase, UniformTextureSequence):
    """A texture with more than one image slice.

    Use the :py:meth:`create_for_images` or :py:meth:`create_for_image_grid`
    classmethod to construct a Texture3D.
    """
    item_width: int = 0
    item_height: int = 0
    items: tuple
    default_descriptor = TextureDescriptor(
        tex_type=TextureType.TYPE_3D,
        min_filter=TextureFilter.LINEAR,
        mag_filter=TextureFilter.LINEAR,
    )

    @classmethod
    def create_for_images(cls, images, descriptor: TextureDescriptor | None = None, blank_data=True):
        raise NotImplementedError

    @classmethod
    def create_for_image_grid(cls, grid, descriptor: TextureDescriptor | None = None):
        return cls.create_for_images(grid[:], descriptor)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    def __setitem__(self, index, value):
        raise NotImplementedError

    def __iter__(self) -> Iterator[TextureRegionBase]:
        return iter(self.items)



class TileableTexture(TextureBase):
    """A texture that can be tiled efficiently.

    Use :py:class:`~pyglet.image.create_for_image` classmethod to construct.
    """

    def get_region(self, x: int, y: int, width: int, height: int):
        raise ImageException(f"Cannot get region of {self}")

    def blit_tiled(self, x: int, y: int, z: int, width: int, height: int) -> None:
        """Blit this texture tiled over the given area.

        The image will be tiled with the bottom-left corner of the destination
        rectangle aligned with the anchor point of this texture.
        """
        raise NotImplementedError

    @classmethod
    def create_for_image(cls, image: AbstractImage) -> TextureBase:
        raise NotImplementedError


class TextureGrid(TextureRegionBase, UniformTextureSequence):
    """A texture containing a regular grid of texture regions.

    To construct, create an :py:class:`~pyglet.image.ImageGrid` first::

        image_grid = ImageGrid(...)
        texture_grid = TextureGrid(image_grid)

    The texture grid can be accessed as a single texture, or as a sequence
    of :py:class:`~pyglet.image.TextureRegion`.  When accessing as a sequence, you can specify
    integer indexes, in which the images are arranged in rows from the
    bottom-left to the top-right::

        # assume the texture_grid is 3x3:
        current_texture = texture_grid[3] # get the middle-left image

    You can also specify tuples in the sequence methods, which are addressed
    as ``row, column``::

        # equivalent to the previous example:
        current_texture = texture_grid[1, 0]

    When using tuples in a slice, the returned sequence is over the
    rectangular region defined by the slice::

        # returns center, center-right, center-top, top-right images in that
        # order:
        images = texture_grid[(1,1):]
        # equivalent to
        images = texture_grid[(1,1):(3,3)]

    """
    items: list
    rows: int
    columns: int
    item_width: int
    item_height: int

    def __init__(self, grid: ImageGrid) -> None:
        image = grid.get_texture()
        if isinstance(image, TextureRegionBase):
            owner = image.owner
        else:
            owner = image

        super().__init__(image.x, image.y, image.z, image.width, image.height, owner)

        items = []
        y = 0
        for row in range(grid.rows):
            x = 0
            for col in range(grid.columns):
                items.append(self.get_region(x, y, grid.item_width, grid.item_height))
                x += grid.item_width + grid.column_padding
            y += grid.item_height + grid.row_padding

        self.items = items
        self.rows = grid.rows
        self.columns = grid.columns
        self.item_width = grid.item_width
        self.item_height = grid.item_height

    def get(self, row: int, column: int):
        return self[(row, column)]

    def __getitem__(self, index: int | tuple[int, int] | slice) -> TextureRegionBase | list[TextureRegionBase]:
        if type(index) is slice:
            if type(index.start) is not tuple and type(index.stop) is not tuple:
                return self.items[index]
            else:
                row1 = 0
                col1 = 0
                row2 = self.rows
                col2 = self.columns
                if type(index.start) is tuple:
                    row1, col1 = index.start
                elif type(index.start) is int:
                    row1 = index.start // self.columns
                    col1 = index.start % self.columns
                assert 0 <= row1 < self.rows and 0 <= col1 < self.columns

                if type(index.stop) is tuple:
                    row2, col2 = index.stop
                elif type(index.stop) is int:
                    row2 = index.stop // self.columns
                    col2 = index.stop % self.columns
                assert 0 <= row2 <= self.rows and 0 <= col2 <= self.columns

                result = []
                i = row1 * self.columns
                for row in range(row1, row2):
                    result += self.items[i + col1:i + col2]
                    i += self.columns
                return result
        else:
            if type(index) is tuple:
                row, column = index
                assert 0 <= row < self.rows and 0 <= column < self.columns
                return self.items[row * self.columns + column]
            elif type(index) is int:
                return self.items[index]

    def __setitem__(self, index: int | slice, value: AbstractImage | Sequence[AbstractImage]):
        if type(index) is slice:
            for region, image in zip(self[index], value):
                if image.width != self.item_width or image.height != self.item_height:
                    raise ImageException('Image has incorrect dimensions')
                image.blit_into(region, image.anchor_x, image.anchor_y, 0)
        else:
            image = value
            if image.width != self.item_width or image.height != self.item_height:
                raise ImageException('Image has incorrect dimensions')
            image.blit_into(self[index], image.anchor_x, image.anchor_y, 0)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[TextureRegionBase]:
        return iter(self.items)



# Default Framebuffer classes:
###############################################################


class BufferManager:
    """Manages the set of framebuffers for a context.

    Use :py:func:`~pyglet.image.get_buffer_manager` to obtain the instance
    of this class for the current context.
    """

    def __init__(self):
        self._color_buffer = None
        self._depth_buffer = None
        self.free_stencil_bits = None
        self._refs = []

    @staticmethod
    def get_viewport() -> tuple:
        """Get the current OpenGL viewport dimensions (left, bottom, right, top)."""
        raise NotImplementedError

    def get_color_buffer(self) -> ColorBufferImage:
        """Get the color buffer."""
        viewport = self.get_viewport()
        viewport_width = viewport[2]
        viewport_height = viewport[3]
        if (not self._color_buffer or
                viewport_width != self._color_buffer.width or
                viewport_height != self._color_buffer.height):
            self._color_buffer = ColorBufferImage(*viewport)
        return self._color_buffer

    def get_depth_buffer(self) -> DepthBufferImage:
        """Get the depth buffer."""
        viewport = self.get_viewport()
        viewport_width = viewport[2]
        viewport_height = viewport[3]
        if (not self._depth_buffer or
                viewport_width != self._depth_buffer.width or
                viewport_height != self._depth_buffer.height):
            self._depth_buffer = DepthBufferImage(*viewport)
        return self._depth_buffer

    def get_buffer_mask(self) -> BufferImageMask:
        """Get a free bitmask buffer.

        A bitmask buffer is a buffer referencing a single bit in the stencil
        buffer.  If no bits are free, ``ImageException`` is raised.  Bits are
        released when the bitmask buffer is garbage collected.
        """
        raise NotImplementedError


def get_buffer_manager() -> BufferManager:
    """Get the buffer manager for the current OpenGL context."""
    raise NotImplementedError


class BufferImage(AbstractImage):
    """An abstract "default" framebuffer."""

    #: The OpenGL read and write target for this buffer.
    #gl_buffer = GL_BACK

    #: The OpenGL format constant for image data.
    #gl_format = 0

    #: The format string used for image data.
    format = ''

    owner = None

    def __init__(self, x, y, width, height):
        super().__init__(width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_image_data(self) -> ImageData:
        raise NotImplementedError

    def get_region(self, x, y, width, height):
        if self.owner:
            return self.owner.get_region(x + self.x, y + self.y, width, height)

        region = self.__class__(x + self.x, y + self.y, width, height)
        #region.gl_buffer = self.gl_buffer
        region.owner = self
        return region

    def get_texture(self ) -> TextureBase:
        raise NotImplementedError(f"Not implemented for {self}")

    def get_mipmapped_texture(self) -> TextureBase:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit(self, x: int, y: int, z: int = 0) -> None:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit_into(self, source, x: int, y: int, z: int) -> None:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        raise NotImplementedError(f"Not implemented for {self}")


class ColorBufferImage(BufferImage):
    """A color framebuffer.

    This class is used to wrap the primary color buffer (i.e., the back
    buffer)
    """
    #gl_format = GL_RGBA
    #format = 'RGBA'

    def get_texture(self):
        texture = TextureBase.create(self.width, self.height, TextureDescriptor(), blank_data=False)
        self.blit_to_texture(texture.target, texture.level, self.anchor_x, self.anchor_y, 0)
        return texture

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        raise NotImplementedError


class DepthBufferImage(BufferImage):
    """The depth buffer.
    """
    #gl_format = GL_DEPTH_COMPONENT
    #format = 'R'

    def get_texture(self):
        image_data = self.get_image_data()
        return image_data.get_texture()

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        raise NotImplementedError


class BufferImageMask(BufferImage):
    """A single bit of the stencil buffer."""
    #gl_format = GL_STENCIL_INDEX
    #format = 'R'

    # TODO mask methods

