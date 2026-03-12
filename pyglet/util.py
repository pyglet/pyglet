"""Various utility functions used internally by pyglet."""
from __future__ import annotations

import os
import math
from typing import Optional, Callable, Any, BinaryIO, Sequence, Protocol, ClassVar, TYPE_CHECKING

import pyglet

if TYPE_CHECKING:
    from pyglet.customtypes import Buffer


def asbytes(s: str | Buffer) -> bytes:
    """Return ``s`` as bytes."""
    if isinstance(s, bytes):
        return s
    if isinstance(s, str):
        return bytes(ord(c) for c in s)
    return bytes(s)


def asstr(s: str | Buffer | None) -> str:
    """Return ``s`` as a UTF-8 string, or an empty string for ``None``."""
    if s is None:
        return ''
    if isinstance(s, str):
        return s
    return s.decode("utf-8")  # type: ignore


# Keep these outside of the function since we don't need to re-define
# the function each time we make a call since no state is persisted.
def _debug_print_real(arg: str) -> bool:
    print(arg)
    return True


def _debug_print_dummy(arg: str) -> bool:
    return True


def debug_print(pyglet_option_name: str = 'debug') -> Callable[[str], bool]:
    """Get a debug printer controlled by the given ``pyglet.options`` name.

    This allows repurposing ``assert`` to write cleaner, more efficient
    debug output:

    #. Debug printers fit into a one-line ``assert`` statements instead
       of longer, slower key-lookup ``if`` statements
    #. Running Python with the ``-O`` flag makes pyglet run faster by
       skipping all ``assert`` statements

    Usage example::

        from pyglet.util import debug_print


        _debug_media = debug_print('debug_media')


        def some_func():
            # Python will skip the line below when run with -O
            assert _debug_media('My debug statement')

            # The rest of the function will run as normal
            ...

    For more information, please see `the Python command line
    documentation <https://docs.python.org/3/using/cmdline.html#cmdoption-O>`_.

    Args:
        pyglet_option_name:
            The name of a key in :attr:`pyglet.options` to read the
            debug flag's value from.

    Returns:
        A callable which prints a passed string and returns ``True``
        to allow auto-removal when running with ``-O``.

    """
    enabled = pyglet.options.get(pyglet_option_name, False)
    if enabled:
        return _debug_print_real
    return _debug_print_dummy


# Based on: https://stackoverflow.com/a/56225940
def closest_power_of_two(x: int) -> int:
    """Return the power of two closest to ``x``."""
    if x <= 2:
        return 2
    if (x >> (x.bit_length() - 2)) & 1:
        return 1 << math.ceil(math.log2(x))
    return 1 << math.floor(math.log2(x))


def next_or_equal_power_of_two(x: int) -> int:
    """Return the next power of two greater than or equal to ``x``."""
    if x <= 1:
        return 1
    return 1 << math.ceil(math.log2(x))


class CodecRegistry:
    """Utility class for handling adding and querying of codecs."""

    def __init__(self) -> None:
        """Initialize empty codec registries."""
        self._decoders: list[Decoder] = []
        self._encoders: list[Encoder] = []
        self._decoder_extensions: dict[str, list[Decoder]] = {}  # Map str -> list of matching Decoders
        self._encoder_extensions: dict[str, list[Encoder]] = {}  # Map str -> list of matching Encoders

    def get_encoders(self, filename: Optional[str] = None) -> list[Encoder]:
        """Get a list of all encoders.

        If a `filename` is provided, only
        encoders supporting that extension will be returned. An empty list
        will be return if no encoders for that extension are available.
        """
        if filename:
            root, ext = os.path.splitext(filename)
            extension = ext or root  # If only ".ext" is provided
            return self._encoder_extensions.get(extension.lower(), [])
        return self._encoders

    def get_decoders(self, filename: str | None = None) -> list[Decoder]:
        """Get a list of all decoders.

        If a `filename` is provided, only
        decoders supporting that extension will be returned. An empty list
        will be return if no encoders for that extension are available.
        """
        if filename:
            root, ext = os.path.splitext(filename)
            extension = ext or root  # If only ".ext" is provided
            return self._decoder_extensions.get(extension.lower(), [])
        return self._decoders

    def add_decoders(self, module: _DecodersModule) -> None:
        """Add a decoder module.

        The module must define `get_decoders`. Once
        added, the appropriate decoders defined in the codec will be returned by
        CodecRegistry.get_decoders.
        """
        for decoder in module.get_decoders():
            self._decoders.append(decoder)
            for extension in decoder.get_file_extensions():
                if extension not in self._decoder_extensions:
                    self._decoder_extensions[extension] = []
                self._decoder_extensions[extension].append(decoder)

    def add_encoders(self, module: _EncodersModule) -> None:
        """Add an encoder module.

        The module must define `get_encoders`. Once
        added, the appropriate encoders defined in the codec will be returned by
        CodecRegistry.get_encoders.
        """
        for encoder in module.get_encoders():
            self._encoders.append(encoder)
            for extension in encoder.get_file_extensions():
                if extension not in self._encoder_extensions:
                    self._encoder_extensions[extension] = []
                self._encoder_extensions[extension].append(encoder)

    def decode(self, filename: str, file: Optional[BinaryIO], **kwargs: Any) -> Any:
        """Attempt to decode a file using the available registered decoders.

        Any decoders that match the file extension will be tried first. If no
        decoders match the extension, all decoders will then be tried in order.
        """
        first_exception: Optional[DecodeException] = None

        for decoder in self.get_decoders(filename):
            try:
                return decoder.decode(filename, file, **kwargs)
            except DecodeException as e:
                if not first_exception:
                    first_exception = e
                if file:
                    file.seek(0)

        for decoder in self.get_decoders():
            try:
                return decoder.decode(filename, file, **kwargs)
            except DecodeException:
                if file:
                    file.seek(0)

        if not first_exception:
            raise DecodeException(f"No decoders available for this file type: {filename}")
        raise first_exception

    def encode(self, media: Any, filename: str, file: Optional[BinaryIO] = None, **kwargs: Any) -> Any:
        """Attempt to encode a pyglet object to a specified format.

        All registered
        encoders that advertise support for the specific file extension will be tried.
        If no encoders are available, an EncodeException will be raised.
        """
        first_exception: EncodeException | None = None
        for encoder in self.get_encoders(filename):
            try:
                return encoder.encode(media, filename, file, **kwargs)
            except EncodeException as e:
                first_exception = first_exception or e

        if not first_exception:
            raise EncodeException(f"No Encoders are available for this extension: '{filename}'")
        raise first_exception


class Decoder:
    """Interface for media decoders."""

    def get_file_extensions(self) -> Sequence[str]:
        """Return accepted file extensions, e.g. ['.wav', '.ogg'].

        Lower-case only.
        """
        raise NotImplementedError

    def decode(self, *args: Any, **kwargs: Any) -> Any:
        """Decode the given file object and return an appropriate pyglet object.

        pyglet object. Throws DecodeException if there is an error.
        `filename` can be a file type hint.
        """
        raise NotImplementedError

    def __hash__(self) -> int:
        """Return a hash based on decoder class name."""
        return hash(self.__class__.__name__)

    def __eq__(self, other: object) -> bool:
        """Return whether two decoders are of the same class name."""
        return self.__class__.__name__ == other.__class__.__name__

    def __repr__(self) -> str:
        """Return a developer-friendly decoder representation."""
        return f"{self.__class__.__name__}{self.get_file_extensions()}"


class Encoder:
    """Interface for media encoders."""

    def get_file_extensions(self) -> Sequence[str]:
        """Return accepted file extensions, e.g. ['.wav', '.ogg'].

        Lower-case only.
        """
        raise NotImplementedError

    def encode(self, media: Any, filename: str, file: BinaryIO | None) -> Any:
        """Encode media to the given file.

        `filename`
        provides a hint to the file format desired.  options are
        encoder-specific, and unknown options should be ignored or
        issue warnings.
        """
        raise NotImplementedError

    def __hash__(self) -> int:
        """Return a hash based on encoder class name."""
        return hash(self.__class__.__name__)

    def __eq__(self, other: object) -> bool:
        """Return whether two encoders are of the same class name."""
        return self.__class__.__name__ == other.__class__.__name__

    def __repr__(self) -> str:
        """Return a developer-friendly encoder representation."""
        return f"{self.__class__.__name__}{self.get_file_extensions()}"


class DecodeException(Exception):
    """Raised when decoding fails."""

    __module__: ClassVar[str] = "CodecRegistry"


class EncodeException(Exception):
    """Raised when encoding fails."""

    __module__: ClassVar[str] = "CodecRegistry"


class _DecodersModule(Protocol):
    def get_decoders(self) -> Sequence[Decoder]: ...


class _EncodersModule(Protocol):
    def get_encoders(self) -> Sequence[Encoder]: ...
