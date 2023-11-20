"""Various utility functions used internally by pyglet
"""

import os
import math
import sys
from typing import Optional, Union, Callable

import pyglet
from pyglet.customtypes import Buffer


def asbytes(s: Union[str, Buffer]) -> bytes:
    if isinstance(s, bytes):
        return s
    elif isinstance(s, str):
        return bytes(ord(c) for c in s)
    else:
        return bytes(s)


def asstr(s: Optional[Union[str, Buffer]]) -> str:
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
        `pyglet_option_name` :
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
    if x <= 2:
        return 2
    if (x >> (x.bit_length() - 2)) & 1:
        return 1 << math.ceil(math.log2(x))
    else:
        return 1 << math.floor(math.log2(x))


def next_or_equal_power_of_two(x: int) -> int:
    if x <= 1:
        return 1
    return 1 << math.ceil(math.log2(x))


class CodecRegistry:
    """Utility class for handling adding and querying of codecs."""

    def __init__(self):
        self._decoders = []
        self._encoders = []
        self._decoder_extensions = {}   # Map str -> list of matching Decoders
        self._encoder_extensions = {}   # Map str -> list of matching Encoders

    def get_encoders(self, filename=None):
        """Get a list of all encoders. If a `filename` is provided, only
        encoders supporting that extension will be returned. An empty list
        will be return if no encoders for that extension are available.
        """
        if filename:
            root, ext = os.path.splitext(filename)
            extension = ext if ext else root        # If only ".ext" is provided
            return self._encoder_extensions.get(extension.lower(), [])
        return self._encoders

    def get_decoders(self, filename=None):
        """Get a list of all decoders. If a `filename` is provided, only
        decoders supporting that extension will be returned. An empty list
        will be return if no encoders for that extension are available.
        """
        if filename:
            root, ext = os.path.splitext(filename)
            extension = ext if ext else root        # If only ".ext" is provided
            return self._decoder_extensions.get(extension.lower(), [])
        return self._decoders

    def add_decoders(self, module):
        """Add a decoder module.  The module must define `get_decoders`.  Once
        added, the appropriate decoders defined in the codec will be returned by
        CodecRegistry.get_decoders.
        """
        for decoder in module.get_decoders():
            self._decoders.append(decoder)
            for extension in decoder.get_file_extensions():
                if extension not in self._decoder_extensions:
                    self._decoder_extensions[extension] = []
                self._decoder_extensions[extension].append(decoder)

    def add_encoders(self, module):
        """Add an encoder module.  The module must define `get_encoders`.  Once
        added, the appropriate encoders defined in the codec will be returned by
        CodecRegistry.get_encoders.
        """
        for encoder in module.get_encoders():
            self._encoders.append(encoder)
            for extension in encoder.get_file_extensions():
                if extension not in self._encoder_extensions:
                    self._encoder_extensions[extension] = []
                self._encoder_extensions[extension].append(encoder)

    def decode(self, filename, file, **kwargs):
        """Attempt to decode a file, using the available registered decoders.
        Any decoders that match the file extension will be tried first. If no
        decoders match the extension, all decoders will then be tried in order.
        """
        first_exception = None

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

    def encode(self, media, filename, file=None, **kwargs):
        """Attempt to encode a pyglet object to a specified format. All registered
        encoders that advertise support for the specific file extension will be tried.
        If no encoders are available, an EncodeException will be raised.
        """

        first_exception = None
        for encoder in self.get_encoders(filename):

            try:
                return encoder.encode(media, filename, file, **kwargs)
            except EncodeException as e:
                first_exception = first_exception or e

        if not first_exception:
            raise EncodeException(f"No Encoders are available for this extension: '{filename}'")
        raise first_exception


class Decoder:
    def get_file_extensions(self):
        """Return a list or tuple of accepted file extensions, e.g. ['.wav', '.ogg']
        Lower-case only.
        """
        raise NotImplementedError()

    def decode(self, *args, **kwargs):
        """Read and decode the given file object and return an approprite
        pyglet object. Throws DecodeException if there is an error.
        `filename` can be a file type hint.
        """
        raise NotImplementedError()

    def __hash__(self):
        return hash(self.__class__.__name__)

    def __eq__(self, other):
        return self.__class__.__name__ == other.__class__.__name__

    def __repr__(self):
        return "{0}{1}".format(self.__class__.__name__, self.get_file_extensions())


class Encoder:
    def get_file_extensions(self):
        """Return a list or tuple of accepted file extensions, e.g. ['.wav', '.ogg']
        Lower-case only.
        """
        raise NotImplementedError()

    def encode(self, media, filename, file):
        """Encode the given media type to the given file.  `filename`
        provides a hint to the file format desired.  options are
        encoder-specific, and unknown options should be ignored or
        issue warnings.
        """
        raise NotImplementedError()

    def __hash__(self):
        return hash(self.__class__.__name__)

    def __eq__(self, other):
        return self.__class__.__name__ == other.__class__.__name__

    def __repr__(self):
        return "{0}{1}".format(self.__class__.__name__, self.get_file_extensions())


class DecodeException(Exception):
    __module__ = "CodecRegistry"


class EncodeException(Exception):
    __module__ = "CodecRegistry"
