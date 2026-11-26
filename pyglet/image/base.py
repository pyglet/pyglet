from __future__ import annotations

import re
import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING, Any, BinaryIO, ClassVar, Generic, Protocol, TypeVar, Union, cast, overload,
)

from pyglet.image.animation import Animation
from pyglet.image.codecs import ImageEncoder
from pyglet.image.codecs import registry as _codec_registry
from pyglet.util import asbytes

if TYPE_CHECKING:
    from ctypes import Array

    from pyglet.customtypes import RGBAColor
    from pyglet.customtypes import DataTypes
    from pyglet.graphics.api.base import SurfaceContextT
    from pyglet.graphics.texture import CompressedTexture, Texture, TextureGrid, TextureSequence


class ImagePattern(ABC):
    """Abstract image creation class."""

    @abstractmethod
    def create_image(self, width: int, height: int) -> ImageData:
        """Create an image of the given size."""
        raise NotImplementedError('method must be defined in subclass')


def _color_as_bytes(color: RGBAColor) -> bytes:
    if len(color) != 4:
        raise TypeError("color is expected to have 4 components")
    return bytes(color)


class ImageException(Exception):
    pass


class _AbstractImage(ABC):
    """Abstract class representing an image."""

    def __init__(self, width: int, height: int) -> None:
        """Initialized in subclass."""
        self.width = width
        self.height = height

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(size={self.width}x{self.height})"

    @abstractmethod
    def get_image_data(self) -> _AbstractImage:
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
        owns_file = file is None
        if owns_file:
            assert filename is not None, "Either filename or file must be specified."
            file = open(filename, 'wb')

        try:
            if encoder is not None:
                encoder.encode(self, filename, file)
            else:
                _codec_registry.encode(self, filename or '', file)
        finally:
            if owns_file:
                file.close()


T = TypeVar('T', bound=_AbstractImage)


class _AbstractImageSequence(ABC, Generic[T]):
    """Abstract sequence of images.

    Image sequence are useful for storing image animations or slices of a volume.
    The class implements the sequence interface (``__len__``, ``__getitem__``,
    ``__setitem__``).
    """

    @abstractmethod
    def get_texture_sequence(self) -> TextureSequence | TextureGrid:
        """Get a TextureSequence.

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
        return Animation.from_image_sequence(self.get_texture_sequence(), period, loop)

    @overload
    def __getitem__(self, item: int) -> T: ...

    @overload
    def __getitem__(self, item: slice) -> Sequence[T]: ...

    @abstractmethod
    def __getitem__(self, item: int | slice) -> T | Sequence[T]:
        """Retrieve one or more images by index."""

    @overload
    def __setitem__(self, item: int, image: ImageData) -> None: ...

    @overload
    def __setitem__(self, item: slice, image: Sequence[ImageData]) -> None: ...

    @abstractmethod
    def __setitem__(self, item: int | slice, image: ImageData | Sequence[ImageData]) -> None:
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
    def __iter__(self) -> Iterator[T]:
        """Iterate over the images in sequence."""


class ImageData(_AbstractImage):
    """An image represented as bytes or a ctypes array of pixel data."""

    _swap1_pattern: ClassVar[re.Pattern[bytes]] = re.compile(asbytes('(.)'), re.DOTALL)
    _swap2_pattern: ClassVar[re.Pattern[bytes]] = re.compile(asbytes('(.)(.)'), re.DOTALL)
    _swap3_pattern: ClassVar[re.Pattern[bytes]] = re.compile(asbytes('(.)(.)(.)'), re.DOTALL)
    _swap4_pattern: ClassVar[re.Pattern[bytes]] = re.compile(asbytes('(.)(.)(.)(.)'), re.DOTALL)

    _current_texture: Texture | None = None
    _current_format: str
    _desired_format: str
    _data_type: DataTypes
    _current_pitch: int
    _current_data: bytes | Array[Any]
    pitch: int

    def __init__(self, width: int, height: int, fmt: str, data: bytes | Array[Any], pitch: int | None = None,
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
                Bytes or a ctypes array containing the raw image data. The
                supplied object is retained until a conversion requires bytes.
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

    def __getstate__(self) -> dict[str, int | str | bytes]:
        return {
            'width': self.width,
            'height': self.height,
            '_current_data': bytes(self.get_bytes(self._current_format, self._current_pitch)),
            '_current_format': self._current_format,
            '_desired_format': self._desired_format,
            '_current_pitch': self._current_pitch,
            '_data_type': self._data_type,
            'pitch': self.pitch,
        }

    @property
    def data_type(self) -> DataTypes:
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

    def get_bytes(self, fmt: str | None = None, pitch: int | None = None) -> bytes | Array[Any]:
        """Get the byte data of the image.

        This method returns the raw byte data of the image, with optional conversion.
        If no conversion is needed, the original bytes or ctypes array is returned.
        To convert the data into another format, you can provide ``fmt`` and ``pitch``
        arguments. For example, if the image format is ``RGBA``, and you wish to get
        the byte data in ``RGB`` format::

            rgb_pitch = my_image.width * len('RGB')
            rgb_img_bytes = my_image.get_bytes(fmt='RGB', pitch=rgb_pitch)

        The image ``pitch`` may be negative, so be sure to check that when converting
        to another format. Switching the sign of the ``pitch`` will cause the image
        to appear "upside-down".

        When converting RGB or BGR data to a format with alpha, the added
        alpha is 255 (opaque). Other missing components copy the first source
        component, including alpha when expanding single-channel data.

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

    def set_bytes(self, fmt: str, pitch: int, data: bytes | Array[Any]) -> None:
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
                Image data as bytes or a ctypes array.
        """
        self._current_format = fmt
        self._current_pitch = pitch
        self._current_data = data
        self._current_texture = None

    def create_texture(self, cls: type[Texture]) -> Texture:
        """Given a texture class, create a texture containing this image."""
        return cls.create_from_image(self)

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

    def convert(self, fmt: str, pitch: int) -> bytes | Array[Any]:
        """Convert data to the desired format.

        This method does not alter this instance's current format or pitch.

        Can be expensive depending on the size of the image and kind of re-ordering.
        If no conversion is needed, the original bytes or ctypes array is returned.
        """
        if fmt == self._current_format and pitch == self._current_pitch:
            return self._current_data

        self._ensure_bytes()
        data = cast(bytes, self._current_data)
        current_pitch = self._current_pitch
        current_format = self._current_format
        sign_pitch = -1 if current_pitch < 0 else 1
        if fmt != self._current_format:
            # Create replacement string, e.g. r'\4\1\2\3' to convert RGBA to ARGB
            repl = asbytes('')
            for c in fmt:
                try:
                    idx = current_format.index(c) + 1
                except ValueError:
                    if c == 'A' and current_format in ('RGB', 'BGR'):
                        repl += b'\xff'
                        continue
                    idx = 1
                repl += asbytes(fr'\{idx:d}')

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
            # Re-pack per source row when changing row width and/or sign.
            old_pitch = abs(current_pitch)
            new_pitch = abs(pitch)
            rows = [data[row * old_pitch : (row + 1) * old_pitch] for row in range(self.height)]

            if new_pitch < old_pitch:
                # New pitch is shorter than old pitch, chop bytes off each row.
                rows = [row[:new_pitch] for row in rows]
            elif new_pitch > old_pitch:
                # New pitch is longer than old pitch, add '0' bytes to each row.
                padding = bytes(new_pitch - old_pitch)
                rows = [row + padding for row in rows]

            if current_pitch * pitch < 0:
                # Pitch differs in sign, swap row order.
                rows.reverse()

            data = b''.join(rows)

        return data

    def _ensure_bytes(self) -> None:
        if type(self._current_data) is not bytes:
            self._current_data = asbytes(self._current_data)


class ImageDataRegion(ImageData):
    """A region of image data taken from an existing ImageData or region."""

    x: int
    y: int
    _source_height: int

    def __init__(self, x: int, y: int, width: int, height: int, image_data: ImageData) -> None:  # noqa: D107
        super().__init__(width, height,
                         image_data._current_format, image_data._current_data, image_data._current_pitch,  # noqa: SLF001
                         image_data._data_type)  # noqa: SLF001
        self.x = x
        self.y = y
        if isinstance(image_data, ImageDataRegion):
            self._source_height = image_data._source_height  # noqa: SLF001
        else:
            self._source_height = image_data.height

    def __getstate__(self) -> dict[str, int | str | bytes]:
        data = bytes(self.get_bytes(self._current_format))
        return {
            'width': self.width,
            'height': self.height,
            '_current_data': data,
            '_current_format': self._current_format,
            '_desired_format': self._desired_format,
            '_current_pitch': self._current_pitch,
            '_data_type': self._data_type,
            'pitch': self.pitch,
            'x': self.x,
            'y': self.y,
            '_source_height': self._source_height,
        }

    def get_bytes(self, fmt: str | None = None, pitch: int | None = None) -> bytes:
        x1 = len(self._current_format) * self.x
        x2 = len(self._current_format) * (self.x + self.width)

        self._ensure_bytes()
        data = cast(bytes, self._current_data)
        new_pitch = abs(self._current_pitch)
        # Reverse the complete source before applying logical region coordinates.
        rows = [data[i * new_pitch : (i + 1) * new_pitch] for i in range(self._source_height)]
        if self._current_pitch < 0:
            rows.reverse()
        rows = [row[x1:x2] for row in rows[self.y : self.y + self.height]]
        self._current_data = b''.join(rows)
        self._source_height = self.height
        self._current_pitch = self.width * len(self._current_format)
        self._current_texture = None
        self.x = 0
        self.y = 0

        fmt = fmt or self._desired_format
        pitch = pitch or self._current_pitch
        return cast(bytes, super().get_bytes(fmt, pitch))

    def set_bytes(self, fmt: str, pitch: int, data: bytes | Array[Any]) -> None:
        self._source_height = self.height
        self.x = 0
        self.y = 0
        super().set_bytes(fmt, pitch, data)

    def get_region(self, x: int, y: int, width: int, height: int) -> ImageDataRegion:
        x += self.x
        y += self.y
        return super().get_region(x, y, width, height)


@dataclass(frozen=True)
class CompressionFormat:
    """Immutable description of a compressed image's pixel format.

    Legacy DDS formats use a FourCC directly. DX10 DDS and KTX2 images use
    a container tag together with a DXGI or Vulkan format identifier, which
    the graphics backend maps to its native compressed texture format.
    """

    fmt: bytes
    """FourCC or container tag, such as b'DXT1', b'DX10', or b'KTX2'."""

    alpha: bool
    """Whether the image declares an alpha channel."""

    dxgi_format: int = 0
    """DXGI format identifier for DX10 DDS images, or zero when unused."""

    vk_format: int = 0
    """Vulkan format identifier for KTX2 images, or zero when unused."""

    def __str__(self) -> str:
        """Return the format tag, active identifiers, and alpha flag."""
        parts = [self.fmt.decode("ascii", errors="backslashreplace").strip()]
        if self.dxgi_format:
            parts.append(f"DXGI={self.dxgi_format}")
        if self.vk_format:
            parts.append(f"Vulkan={self.vk_format}")
        return f"{', '.join(parts)} (alpha={self.alpha})"


class CompressedImageDecoder(Protocol):
    """Decode one compressed mipmap level into uncompressed pixel data.

    The callback must understand the image's compression format and return an
    ImageData with the requested dimensions. Functions and callable objects
    can implement this protocol; no inheritance is required.
    """

    def __call__(self, data: bytes, width: int, height: int, /) -> ImageData:
        """Decode compressed bytes for a level of the given size."""
        ...


class CompressedImageData(_AbstractImage):
    """Compressed image data suitable for direct uploading to GPU.

    If the active backend cannot upload the compression format, an optional
    :class:`CompressedImageDecoder` can decode each supplied mipmap level into
    ordinary :class:`ImageData`. The resulting texture is cached as usual.
    Pyglet does not supply a software decoder; the application must provide one
    that understands this image's compression format.

    Attach the decoder before requesting a texture. For example, given an
    application-provided ``decode_bc7(data, width, height)`` function::

        image = pyglet.resource.image("terrain.dds")
        if isinstance(image, pyglet.image.CompressedImageData):
            image.decoder = decode_bc7
        texture = image.get_texture()

    Native compressed uploads take priority, so the callback only runs when
    the backend does not support the format. Without a callback, an unsupported
    format raises :class:`~pyglet.graphics.UnsupportedCompressedTextureError`.

    .. note::
        ``pyglet.resource.texture()`` loads the source internally and currently
        has no argument for supplying this fallback decoder. It also loads
        independently of the ``pyglet.resource.image()`` cache. Configuring the
        cached image's decoder therefore does not configure subsequent
        ``resource.texture()`` calls. Use the image's ``get_texture()`` method
        as shown above to select the native upload or software fallback path.
    """

    _current_texture: Texture | CompressedTexture | None = None

    def __init__(
        self,
        width: int,
        height: int,
        fmt: CompressionFormat,
        data: bytes,
        decoder: CompressedImageDecoder | None = None,
    ) -> None:
        """Construct a CompressedImageData with the given compressed data.

        Args:
            width:
                The width of the image.
            height:
                The height of the image.
            fmt:
                Compression format understood by the backend and any supplied decoder.
            data:
                An array of bytes containing the compressed image data.
            decoder:
                Optional software decoder for this compression format, called
                as ``decoder(data, width, height)`` when the backend cannot
                upload it directly. Must return ImageData of the given size.
                Supplied mipmap levels are decoded separately.
        """
        super().__init__(width, height)
        self.data = data
        self.fmt = fmt
        self.decoder = decoder
        self.data_type = "B"
        self.mipmap_data: list[bytes | None] = []

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

    def create_texture(
        self, cls: type[CompressedTexture[SurfaceContextT]], *, context: SurfaceContextT | None = None,
    ) -> Texture[SurfaceContextT] | CompressedTexture[SurfaceContextT]:
        """Upload compressed data, or use the supplied software decoder.

        Capability is checked before allocating a GPU texture.

        Args:
            cls:
                Backend compressed texture class used for direct uploads.
            context:
                Context to use for either upload path, or None for the current context.
        """
        if cls.supports_format(self.fmt, context=context):
            return cls.create_from_image(self, context=context)
        if self.decoder is None:
            from pyglet.graphics import UnsupportedCompressedTextureError  # noqa: PLC0415

            msg = f"Unsupported compressed texture format {self.fmt!r}; no software decoder supplied."
            raise UnsupportedCompressedTextureError(msg)

        from pyglet.graphics.texture import Texture  # noqa: PLC0415

        images: list[ImageData] = []
        for level, data in enumerate([self.data, *self.mipmap_data]):
            if data is None:
                msg = f"Compressed texture mipmap level {level} has no data."
                raise ImageException(msg)
            width, height = max(1, self.width >> level), max(1, self.height >> level)
            image = self.decoder(data, width, height)
            if not isinstance(image, ImageData) or (image.width, image.height) != (width, height):
                msg = f"Software decoder must return ImageData of size {width}x{height}."
                raise ImageException(msg)
            images.append(image)

        texture = Texture.create_from_image(images[0], context=context)
        try:
            if len(images) > 1:
                texture.init_mipmaps(levels=len(images), blank_data=False)
                texture.bind()
                for level, image in enumerate(images[1:], start=1):
                    texture.upload(image, 0, 0, 0, level=level)
        except Exception:
            texture.delete()
            raise
        return texture

    def get_texture(self) -> Texture | CompressedTexture:
        if self._current_texture is None:
            from pyglet.graphics.texture import CompressedTexture  # noqa: PLC0415

            self._current_texture = self.create_texture(cast("type[CompressedTexture]", CompressedTexture))
        return self._current_texture

    def get_image_data(self) -> CompressedImageData:
        return self

    def get_region(self, x: int, y: int, width: int, height: int) -> _AbstractImage:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit(self, x: int, y: int, z: int = 0) -> None:
        raise NotImplementedError


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
    @overload
    def __getitem__(self, index: int) -> T: ...
    @overload
    def __getitem__(self, index: tuple[int, int]) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> list[T]: ...

    def __getitem__(self, index: int | tuple[int, int] | slice) -> list[T] | T | None:
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

    @overload
    def __setitem__(self, index: int, value: T) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Sequence[T]) -> None: ...

    def __setitem__(self, index: int | slice, value: T | Sequence[T]) -> None:
        """Replace cells, requiring one correctly sized image per selected cell.

        Slice length and image dimensions are checked before any cells change.
        """
        if isinstance(index, slice):
            if not isinstance(value, Sequence):
                raise TypeError("Slice assignment requires a sequence of images.")
            selected = self[index]
            replacements = list(value)
            if len(replacements) != len(selected):
                msg = f'Slice selects {len(selected)} cells, but received {len(replacements)} images.'
                raise ValueError(msg)
            for new_item in replacements:
                if new_item.width != self.item_width or new_item.height != self.item_height:
                    msg = (
                        f'Dimensions of new item does not match existing.\n'
                        f'Expected {self.item_width}x{self.item_height}, Received {new_item.width}x{new_item.height}'
                    )
                    raise ImageException(msg)
            for existing_item, new_item in zip(selected, replacements, strict=True):
                self._update_item(existing_item, new_item)
        else:
            if isinstance(value, Sequence):
                raise TypeError("Single-item assignment requires an image.")
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


class ImageGrid(_AbstractGrid[Union[ImageData, ImageDataRegion]], _AbstractImageSequence[ImageData | ImageDataRegion]):
    """An imaginary grid placed over an image allowing easy access to regular regions of that image.

    The grid can be accessed either as a complete image, or as a sequence of images.

    Any :py:class:`~pyglet.graphics.texture.TextureGrid` generated via the method below will create
    a separate texture resource::

        image_grid = ImageGrid(...)
        texture_grid = image_grid.get_texture_sequence()

    For existing Texture's, it is recommended to use :py:class:`~pyglet.graphics.texture.TextureGrid` directly.
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
        assert item_width is not None
        assert item_height is not None
        super().__init__(rows, columns, item_width, item_height, row_padding, column_padding)
        self.image = image

    def _create_item(self, x: int, y: int, width: int, height: int) -> ImageDataRegion:
        return self.image.get_region(x, y, width, height)

    def _update_item(self, existing_item: ImageData | ImageDataRegion,
                     new_item: ImageData | ImageDataRegion) -> None:
        new_item_bytes = new_item.get_bytes(existing_item.format, existing_item.pitch)
        existing_item.set_bytes(existing_item.format, existing_item.pitch, new_item_bytes)

    def get_texture(self) -> Texture:
        """Create a new Texture resource from the underlying image data."""
        return self.image.get_texture()

    def get_image_data(self) -> _AbstractImage:
        """Retrieve the underlying image data the grid is based upon."""
        return self.image.get_image_data()

    def get_texture_sequence(self) -> TextureGrid:
        """Create a :py:class:`~pyglet.graphics.texture.TextureGrid` resource from the underlying image data.

        It is recommended to use :py:class:`~pyglet.graphics.texture.TextureGrid` directly.
        """
        warnings.warn("Use pyglet.graphics.TextureGrid instead", DeprecationWarning)
        if not self._texture_grid:
            from pyglet.graphics.texture import TextureGrid  # noqa: PLC0415
            self._texture_grid = TextureGrid.from_image_grid(self)
        return self._texture_grid

