"""Collection of image encoders and decoders.

Modules must subclass ImageDecoder and ImageEncoder for each method of
decoding/encoding they support.

Modules must also implement the two functions::

    def get_decoders():
        # Return a list of ImageDecoder instances or []
        return []

    def get_encoders():
        # Return a list of ImageEncoder instances or []
        return []

"""
from __future__ import annotations

import os.path

from pyglet.util import CodecRegistry, Decoder, Encoder, DecodeException, EncodeException
from pyglet import compat_platform


class _ImageCodecRegistry(CodecRegistry):
    """Subclass of CodecRegistry that adds support for animation methods."""

    def __init__(self):
        self._decoder_animation_extensions = {}
        super().__init__()

    def add_decoders(self, module):
        """Override the default method to also add animation decoders."""
        super().add_decoders(module)
        for decoder in module.get_decoders():
            for extension in decoder.get_animation_file_extensions():
                if extension not in self._decoder_animation_extensions:
                    self._decoder_animation_extensions[extension] = []
                self._decoder_animation_extensions[extension].append(decoder)

    def get_animation_decoders(self, filename=None):
        """Get a list of animation decoders. If a `filename` is provided, only
           decoders supporting that extension will be returned. An empty list
           will be return if no encoders for that extension are available.
        """
        if filename:
            extension = os.path.splitext(filename)[1].lower()
            return self._decoder_animation_extensions.get(extension, [])
        return self._decoders

    def decode_animation(self, filename, file, **kwargs):
        first_exception = None

        for decoder in self.get_animation_decoders(filename):
            try:
                return decoder.decode_animation(filename, file, **kwargs)
            except DecodeException as e:
                if not first_exception:
                    first_exception = e
                if file:
                    file.seek(0)

        for decoder in self.get_animation_decoders():   # Try ALL codecs
            try:
                return decoder.decode_animation(filename, file, **kwargs)
            except DecodeException:
                if file:
                    file.seek(0)

        if not first_exception:
            msg = f"No decoders available for this file type: {filename}"
            raise DecodeException(msg)
        raise first_exception


registry = _ImageCodecRegistry()
add_decoders = registry.add_decoders
add_encoders = registry.add_encoders
get_animation_decoders = registry.get_animation_decoders
get_decoders = registry.get_decoders
get_encoders = registry.get_encoders


class ImageDecodeException(DecodeException):
    pass


class ImageEncodeException(EncodeException):
    pass


class ImageDecoder(Decoder):

    def get_animation_file_extensions(self) -> list[str]:
        """Return a list of accepted file extensions, e.g. ['.gif', '.flc']
        Lower-case only.
        """
        return []

    def decode(self, filename, file):
        """Decode the given file object and return an instance of `Image`.
        Throws ImageDecodeException if there is an error.  filename
        can be a file type hint.
        """
        raise NotImplementedError()

    def decode_animation(self, filename, file):
        """Decode the given file object and return an instance of :py:class:`~pyglet.image.Animation`.
        Throws ImageDecodeException if there is an error.  filename
        can be a file type hint.
        """
        raise ImageDecodeException('This decoder cannot decode animations.')

    def __repr__(self) -> str:
        return "{}{}".format(self.__class__.__name__,
                               self.get_animation_file_extensions() +
                               self.get_file_extensions())


class ImageEncoder(Encoder):

    def encode(self, image, filename, file):
        """Encode the given image to the given file.  filename
        provides a hint to the file format desired.
        """
        raise NotImplementedError()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self.get_file_extensions()}"


def add_default_codecs():
    # Add the codecs we know about.  These should be listed in order of
    # preference.  This is called automatically by pyglet.image.

    # Compressed texture in DDS format
    try:
        from pyglet.image.codecs import dds
        registry.add_encoders(dds)
        registry.add_decoders(dds)
    except ImportError:
        pass

    # Mac OS X default: Quartz
    if compat_platform == 'darwin':
        try:
            from pyglet.image.codecs import quartz
            registry.add_encoders(quartz)
            registry.add_decoders(quartz)
        except ImportError:
            pass

    # Windows 7 default: Windows Imaging Component
    if compat_platform in ('win32', 'cygwin'):
        from pyglet.libs.win32.constants import WINDOWS_7_OR_GREATER
        if WINDOWS_7_OR_GREATER:  # Supports Vista and above.
            try:
                from pyglet.image.codecs import wic
                registry.add_encoders(wic)
                registry.add_decoders(wic)
            except ImportError:
                pass

    # Windows XP default: GDI+
    if compat_platform in ('win32', 'cygwin'):
        try:
            from pyglet.image.codecs import gdiplus
            registry.add_encoders(gdiplus)
            registry.add_decoders(gdiplus)
        except ImportError:
            pass

    # Linux default: GdkPixbuf 2.0
    if compat_platform.startswith('linux'):
        try:
            from pyglet.image.codecs import gdkpixbuf2
            registry.add_encoders(gdkpixbuf2)
            registry.add_decoders(gdkpixbuf2)
        except ImportError:
            pass

    # Fallback: PIL
    try:
        from pyglet.image.codecs import pil
        registry.add_encoders(pil)
        registry.add_decoders(pil)
    except ImportError:
        pass

    # Fallback: PNG loader (slow)
    try:
        from pyglet.image.codecs import png
        registry.add_encoders(png)
        registry.add_decoders(png)
    except ImportError:
        pass

    # Fallback: BMP loader (slow)
    try:
        from pyglet.image.codecs import bmp
        registry.add_encoders(bmp)
        registry.add_decoders(bmp)
    except ImportError:
        pass
