"""Various utility functions used internally by pyglet
"""

import os
import sys

import pyglet


def asbytes(s):
    if isinstance(s, bytes):
        return s
    elif isinstance(s, str):
        return bytes(ord(c) for c in s)
    else:
        return bytes(s)


def asbytes_filename(s):
    if isinstance(s, bytes):
        return s
    elif isinstance(s, str):
        return s.encode(encoding=sys.getfilesystemencoding())


def asstr(s):
    if s is None:
        return ''
    if isinstance(s, str):
        return s
    return s.decode("utf-8")


def with_metaclass(meta, *bases):
    """
    Function from jinja2/_compat.py. License: BSD.
    Use it like this::
        class BaseForm:
            pass
        class FormType(type):
            pass
        class Form(with_metaclass(FormType, BaseForm)):
            pass
    This requires a bit of explanation: the basic idea is to make a
    dummy metaclass for one level of class instantiation that replaces
    itself with the actual metaclass.  Because of internal type checks
    we also need to make sure that we downgrade the custom metaclass
    for one level to something closer to type (that's why __call__ and
    __init__ comes back from type etc.).
    This has the advantage over six.with_metaclass of not introducing
    dummy classes into the final MRO.
    """
    class MetaClass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)

    return MetaClass('temporary_class', None, {})


def debug_print(enabled_or_option='debug'):
    """Get a debug printer that is enabled based on a boolean input or a pyglet option.
    The debug print function returned should be used in an assert. This way it can be
    optimized out when running python with the -O flag.

    Usage example::

        from pyglet.debug import debug_print
        _debug_media = debug_print('debug_media')

        def some_func():
            assert _debug_media('My debug statement')

    :parameters:
        `enabled_or_options` : bool or str
            If a bool is passed, debug printing is enabled if it is True. If str is passed
            debug printing is enabled if the pyglet option with that name is True.

    :returns: Function for debug printing.
    """
    if isinstance(enabled_or_option, bool):
        enabled = enabled_or_option
    else:
        enabled = pyglet.options.get(enabled_or_option, False)

    if enabled:
        def _debug_print(*args, **kwargs):
            print(*args, **kwargs)
            return True

    else:
        def _debug_print(*args, **kwargs):
            return True

    return _debug_print


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
            extension = os.path.splitext(filename)[1].lower()
            return self._encoder_extensions.get(extension, [])
        return self._encoders

    def get_decoders(self, filename=None):
        """Get a list of all decoders. If a `filename` is provided, only
        decoders supporting that extension will be returned. An empty list
        will be return if no encoders for that extension are available.
        """
        if filename:
            extension = os.path.splitext(filename)[1].lower()
            return self._decoder_extensions.get(extension, [])
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
