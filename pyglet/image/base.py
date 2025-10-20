from __future__ import annotations

import re
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, BinaryIO, Callable, Generic, Iterator, Sequence, TypeVar, Union

from pyglet.customtypes import DataTypes
from pyglet.image.animation import Animation
from pyglet.image.codecs import ImageEncoder
from pyglet.image.codecs import registry as _codec_registry
from pyglet.util import asbytes

if TYPE_CHECKING:
    from pyglet.graphics.texture import CompressedTexture, Texture, TextureGrid, TextureSequence


class ImagePattern(ABC):
    """Abstract image creation class."""

    @abstractmethod
    def create_image(self, width: int, height: int) -> _AbstractImage:
        """Create an image of the given size."""
        raise NotImplementedError('method must be defined in subclass')


def _color_as_bytes(color: Sequence[int, int, int, int]) -> bytes:
    if len(color) != 4:
        raise TypeError("color is expected to have 4 components")
    return bytes(color)


class ImageException(Exception):
    pass


class _AbstractImage(ABC):
    """Abstract class representing an image."""

    anchor_x: int = 0
    """X coordinate of anchor, relative to left edge of image data."""

    anchor_y: int = 0
    """Y coordinate of anchor, relative to bottom edge of image data."""

    def __init__(self, width: int, height: int) -> None:
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
    def get_region(self, x: int, y: int, width: int, height: int) -> _AbstractImage:
        """Retrieve a rectangular region of this image."""

    def save(
        self, filename: str | None = None, file: BinaryIO | None = None, encoder: ImageEncoder | None = None,
    ) -> None:
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


class _AbstractImageSequence(ABC):
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
        """Create an animation over this image sequence for the given constant framerate.

        Args:
            period:
                Number of seconds to display each frame.
            loop:
                If True, the animation will loop continuously.
        """
        return Animation.from_image_sequence(self, period, loop)

    @abstractmethod
    def __getitem__(self, item) -> _AbstractImage:
        """Retrieve one or more images by index."""

    @abstractmethod
    def __setitem__(self, item, image: _AbstractImage) -> _AbstractImage:
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
    def __iter__(self) -> Iterator[_AbstractImage]:
        """Iterate over the images in sequence."""


class ImageData(_AbstractImage):
    """An image represented as a string of unsigned bytes."""

    _swap1_pattern = re.compile(asbytes('(.)'), re.DOTALL)
    _swap2_pattern = re.compile(asbytes('(.)(.)'), re.DOTALL)
    _swap3_pattern = re.compile(asbytes('(.)(.)(.)'), re.DOTALL)
    _swap4_pattern = re.compile(asbytes('(.)(.)(.)(.)'), re.DOTALL)

    _current_texture = None

    def __init__(self, width: int, height: int, fmt: str, data: bytes, pitch: int | None = None,
                 data_type: DataTypes = "B") -> None:
        """Initialize image data.

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
                indicate a top-to-bottom arrangement.  Defaults to ``width * len(format)``.
            data_type:
                The data type of the underlying data. Defaults to unsigned bytes.
        """
        super().__init__(width, height)

        self._current_format = self._desired_format = fmt.upper()
        self._data_type = data_type
        self._current_data = data
        self.pitch = pitch or width * len(fmt)
        self._current_pitch = self.pitch

    def __getstate__(self) -> dict:
        return {
            'width': self.width,
            'height': self.height,
            '_current_data': self.get_bytes(self._current_format, self._current_pitch),
            '_current_format': self._current_format,
            '_desired_format': self._desired_format,
            '_current_pitch': self._current_pitch,
            '_data_type': self._data_type,
            'pitch': self.pitch,
        }

    @property
    def data_type(self) -> str:
        return self._data_type

    def get_image_data(self) -> ImageData:
        return self

    @property
    def format(self) -> str:
        """Format string of the data. Read-write."""
        return self._desired_format

    @format.setter
    def format(self, fmt: str) -> None:
        self._desired_format = fmt.upper()
        self._current_texture = None

    def get_bytes(self, fmt: str | None = None, pitch: int | None = None) -> bytes:
        """Get the byte data of the image.

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
        return self.convert(fmt, pitch)

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

    def get_data(self, fmt: str | None = None, pitch: int | None = None) -> NotImplementedError:
        """Get the byte data of the image.

        Warning:
            This method is deprecated and will be removed in the next version.
            Use :py:meth:`~get_bytes` instead.
        """
        raise NotImplementedError("Removed. Use `get_bytes` instead.")

    def set_data(self, fmt: str, pitch: int, data: bytes) -> NotImplementedError:
        """Set the byte data of the image.

        Warning:
            This method is deprecated and will be removed in the next version.
            Use :py:meth:`~set_bytes` instead.
        """
        raise NotImplementedError("Removed. Use `set_bytes` instead.")

    def create_texture(self, cls: type[Texture]) -> Texture:
        """Given a texture class, create a texture containing this image."""
        texture = cls.create_from_image(self)

        if self.anchor_x or self.anchor_y:
            texture.anchor_x = self.anchor_x
            texture.anchor_y = self.anchor_y

        return texture

    def get_texture(self) -> Texture:
        if not self._current_texture:
            from pyglet.graphics.texture import Texture

            self._current_texture = self.create_texture(Texture)
        return self._current_texture

    def get_region(self, x: int, y: int, width: int, height: int) -> ImageDataRegion:
        """Retrieve a rectangular region of this image data."""
        return ImageDataRegion(x, y, width, height, self)

    def blit(self, x: int, y: int, z: int = 0, width: int | None = None, height: int | None = None) -> None:
        raise NotImplementedError("This is no longer supported. Check documentation for 3.0 migration.")

    def convert(self, fmt: str, pitch: int) -> bytes:
        """Convert data to the desired format.

        This method does not alter this instance's current format or pitch.

        Can be expensive depending on the size of the image and kind of re-ordering.
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
                rows = [data[i : i + new_pitch] for i in range(0, len(data), new_pitch)]
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
                rows = [data[i : i + new_pitch - diff] for i in range(0, len(data), new_pitch)]
                data = b''.join(rows)

            elif diff < 0:
                # New pitch is longer than old pitch, add '0' bytes to each row
                new_pitch = abs(current_pitch)
                padding = bytes(1) * -diff
                rows = [data[i : i + new_pitch] + padding for i in range(0, len(data), new_pitch)]
                data = b''.join(rows)

            if current_pitch * pitch < 0:
                # Pitch differs in sign, swap row order
                new_pitch = abs(pitch)
                rows = [data[i : i + new_pitch] for i in range(0, len(data), new_pitch)]
                rows.reverse()
                data = b''.join(rows)

        return data

    def _ensure_bytes(self) -> None:
        if type(self._current_data) is not bytes:
            self._current_data = asbytes(self._current_data)


class ImageDataRegion(ImageData):
    """A region of image data taken from an existing ImageData or region."""

    def __init__(self, x: int, y: int, width: int, height: int, image_data: ImageData) -> None:  # noqa: D107
        super().__init__(width, height, image_data._current_format, image_data._current_data, image_data._current_pitch)  # noqa: SLF001
        self.x = x
        self.y = y

    def __getstate__(self) -> dict:
        return {
            'width': self.width,
            'height': self.height,
            '_current_data': self.get_bytes(self._current_format, self._current_pitch),
            '_current_format': self._current_format,
            '_desired_format': self._desired_format,
            '_current_pitch': self._current_pitch,
            'pitch': self.pitch,
            'x': self.x,
            'y': self.y,
        }

    def get_bytes(self, fmt: str | None = None, pitch: int | None = None) -> bytes:
        x1 = len(self._current_format) * self.x
        x2 = len(self._current_format) * (self.x + self.width)

        self._ensure_bytes()
        data = self.convert(self._current_format, abs(self._current_pitch))
        new_pitch = abs(self._current_pitch)
        rows = [data[i : i + new_pitch] for i in range(0, len(data), new_pitch)]
        rows = [row[x1:x2] for row in rows[self.y : self.y + self.height]]
        self._current_data = b''.join(rows)
        self._current_pitch = self.width * len(self._current_format)
        self._current_texture = None
        self.x = 0
        self.y = 0

        fmt = fmt or self._desired_format
        pitch = pitch or self._current_pitch
        return super().get_bytes(fmt, pitch)

    def set_bytes(self, fmt: str, pitch: int, data: bytes) -> None:
        self.x = 0
        self.y = 0
        super().set_bytes(fmt, pitch, data)

    def get_region(self, x: int, y: int, width: int, height: int) -> ImageDataRegion:
        x += self.x
        y += self.y
        return super().get_region(x, y, width, height)


@dataclass(frozen=True)
class CompressionFormat:
    fmt: bytes
    alpha: bool
    dxgi_format: int = 0
    vk_format: int = 0

class CompressedImageData(_AbstractImage):
    """Compressed image data suitable for direct uploading to GPU."""

    _current_texture = None

    def __init__(
        self,
        width: int,
        height: int,
        fmt: CompressionFormat,
        data: bytes,
        extension: str | None = None,
        decoder: Callable[[bytes, int, int], _AbstractImage] | None = None,
    ) -> None:
        """Construct a CompressedImageData with the given compressed data.

        Args:
            width:
                The width of the image.
            height:
                The height of the image.
            data:
                An array of bytes containing the compressed image data.
            extension:
                If specified, gives the name of the extension to check for
                before creating a texture.
            decoder:
                An optional fallback function used to decode the compressed data.
                This function is called if the required extension is not present.
        """
        super().__init__(width, height)
        self.data = data
        self.fmt = fmt
        self.extension = extension
        self.decoder = decoder
        self.data_type = "B"
        self.mipmap_data: list[bytes | None] = []

    def _have_extension(self) -> bool:
        raise NotImplementedError

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

    def create_texture(self, cls: type[CompressedTexture]) -> Texture:
        """Given a texture class, create a texture containing this image."""
        texture = cls.create_from_image(self)

        if self.anchor_x or self.anchor_y:
            texture.anchor_x = self.anchor_x
            texture.anchor_y = self.anchor_y

        return texture

    def get_texture(self) -> CompressedTexture:
        if not self._current_texture:
            from pyglet.graphics.texture import CompressedTexture

            self._current_texture = self.create_texture(CompressedTexture)
        return self._current_texture

    def get_image_data(self) -> CompressedImageData:
        return self

    def get_region(self, x: int, y: int, width: int, height: int) -> _AbstractImage:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit(self, x: int, y: int, z: int = 0) -> None:
        raise NotImplementedError


T = TypeVar('T', bound=_AbstractImage)


class _AbstractGrid(ABC, Generic[T]):
    column_padding: int
    row_padding: int
    columns: int
    rows: int
    item_width: int
    item_height: int
    _height: int
    _width: int
    _items: list[T] | None = None

    def __init__(
        self, rows: int, columns: int, item_width: int, item_height: int, row_padding: int = 0, column_padding: int = 0,
    ) -> None:
        self.rows = rows
        self.columns = columns
        self.item_width = item_width
        self.item_height = item_height
        self.row_padding = row_padding
        self.column_padding = column_padding
        self._items = None
        self._width = (item_width * columns) + (column_padding * columns)
        self._height = (item_height * rows) + (row_padding * rows)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def _generate_items(self) -> list[T]:
        if self._items is None:
            self._items = []
            y = 0
            for row in range(self.rows):
                x = 0
                for col in range(self.columns):
                    self._items.append(self._create_item(x, y, self.item_width, self.item_height))
                    x += self.item_width + self.column_padding
                y += self.item_height + self.row_padding
        return self._items

    @abstractmethod
    def _create_item(self, x: int, y: int, width: int, height: int) -> T:
        """Factory method to create a grid item.

        Must be implemented by subclasses.
        """

    @abstractmethod
    def _update_item(self, existing_item: T, new_item: T) -> None:
        """Factory method to update an existing grid item.

        Must be implemented by subclasses, even if it does not change the data.
        """

    def __getitem__(self, index: int | tuple[int, int] | slice) -> list[Any] | None | Any:
        items = self._generate_items()
        if isinstance(index, slice):
            if type(index.start) is not tuple and type(index.stop) is not tuple:
                return items[index]
            row1 = 0
            col1 = 0
            row2 = self.rows
            col2 = self.columns
            if type(index.start) is tuple:
                row1, col1 = index.start
            elif type(index.start) is int:
                row1 = index.start // self.columns
                col1 = index.start % self.columns
            assert 0 <= row1 < self.rows and 0 <= col1 < self.columns, "Grid index out of range"  # noqa: PT018

            if type(index.stop) is tuple:
                row2, col2 = index.stop
            elif type(index.stop) is int:
                row2 = index.stop // self.columns
                col2 = index.stop % self.columns
            assert 0 <= row2 <= self.rows and 0 <= col2 <= self.columns, "Grid index out of range"  # noqa: PT018

            result = []
            i = row1 * self.columns
            for row in range(row1, row2):
                result += items[i + col1 : i + col2]
                i += self.columns
            return result
        if isinstance(index, tuple):
            row, column = index
            assert 0 <= row < self.rows and 0 <= column < self.columns, "Grid index out of range"  # noqa: PT018
            return items[row * self.columns + column]

        return items[index]

    def __setitem__(self, index: int | slice, value: T | Sequence[T]) -> None:
        if isinstance(value, slice):
            for existing_item, new_item in zip(self[index], value):
                if new_item.width != self.item_width or new_item.height != self.item_height:
                    msg = (
                        f'Dimensions of new item does not match existing.\n'
                        f'Expected {self.item_width}x{self.item_height}, Received {new_item.width}x{new_item.height}'
                    )
                    raise ImageException(msg)
                self._update_item(existing_item, new_item)
        else:
            new_item = value
            if new_item.width != self.item_width or new_item.height != self.item_height:
                msg = (
                    f'Dimensions of new item does not match existing.\n'
                    f'Expected {self.item_width}x{self.item_height}, Received {new_item.width}x{new_item.height}'
                )
                raise ImageException(msg)
            self._update_item(self[index], new_item)

    def __iter__(self) -> Iterator[T]:
        return iter(self._generate_items())

    def __len__(self) -> int:
        return self.rows * self.columns


class ImageGrid(_AbstractGrid[Union[ImageData, ImageDataRegion]], _AbstractImageSequence):
    """An imaginary grid placed over an image allowing easy access to regular regions of that image.

    The grid can be accessed either as a complete image, or as a sequence of images.

    Any :py:class:`~pyglet.graphics.TextureGrid` generated via the method below will create
    a separate texture resource::

        image_grid = ImageGrid(...)
        texture_grid = image_grid.get_texture_sequence()

    For existing Texture's, it is recommended to use :py:class:`~pyglet.graphics.TextureGrid` directly.
    """

    _texture_grid: TextureGrid | None = None

    def __init__(
        self,
        image: ImageData | ImageDataRegion,
        rows: int,
        columns: int,
        item_width: int | None = None,
        item_height: int | None = None,
        row_padding: int = 0,
        column_padding: int = 0,
    ) -> None:
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
        item_width = item_width or (image.width - column_padding * (columns - 1)) // columns
        item_height = item_height or (image.height - row_padding * (rows - 1)) // rows
        super().__init__(rows, columns, item_width, item_height, row_padding, column_padding)
        self.image = image

    def _create_item(self, x: int, y: int, width: int, height: int) -> ImageDataRegion:
        return self.image.get_region(x, y, width, height)

    def _update_item(self, existing_item: ImageDataRegion, new_item: ImageData | ImageDataRegion) -> None:
        new_item_bytes = new_item.get_bytes(existing_item.format, existing_item.pitch)
        existing_item.set_data(existing_item.format, existing_item.pitch, new_item_bytes)

    def get_texture(self) -> Texture:
        """Create a new Texture resource from the underlying image data."""
        return self.image.get_texture()

    def get_image_data(self) -> ImageData:
        """Retrieve the underlying image data the grid is based upon."""
        return self.image.get_image_data()

    def get_texture_sequence(self) -> TextureGrid:
        """Create a :py:class:`~pyglet.graphics.TextureGrid` resource from the underlying image data.

        It is recommended to use :py:class:`~pyglet.graphics.TextureGrid` directly.
        """
        warnings.warn("Use pyglet.graphics.TextureGrid instead", DeprecationWarning)
        if not self._texture_grid:
            from pyglet.graphics.texture import TextureGrid
            self._texture_grid = TextureGrid.from_image_grid(self)
        return self._texture_grid

