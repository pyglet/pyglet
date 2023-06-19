import warnings

from pyglet.util import CodecRegistry, Decoder, Encoder
from .base import *

import pyglet


_debug = pyglet.options['debug_media']

registry = CodecRegistry()
add_decoders = registry.add_decoders
add_encoders = registry.add_encoders
get_decoders = registry.get_decoders
get_encoders = registry.get_encoders


class MediaDecoder(Decoder):

    def decode(self, filename, file, streaming):
        """Read the given file object and return an instance of `Source`
        or `StreamingSource`. 
        Throws DecodeException if there is an error.  `filename`
        can be a file type hint.
        """
        raise NotImplementedError()


class MediaEncoder(Encoder):

    def encode(self, source, filename, file):
        """Encode the given source to the given file.  `filename`
        provides a hint to the file format desired.  options are
        encoder-specific, and unknown options should be ignored or
        issue warnings.
        """
        raise NotImplementedError()


def add_default_codecs():
    # Add all bundled codecs. These should be listed in order of
    # preference.  This is called automatically by pyglet.media.

    try:
        from . import wave
        registry.add_decoders(wave)
        registry.add_encoders(wave)
    except ImportError:
        pass

    if pyglet.compat_platform.startswith('linux'):
        try:
            from . import gstreamer
            registry.add_decoders(gstreamer)
        except ImportError:
            pass

    try:
        if pyglet.compat_platform in ('win32', 'cygwin'):
            from pyglet.libs.win32.constants import WINDOWS_VISTA_OR_GREATER
            if WINDOWS_VISTA_OR_GREATER:  # Supports Vista and above.
                from . import wmf
                registry.add_decoders(wmf)
    except ImportError:
        pass

    try:
        if have_ffmpeg():
            from . import ffmpeg
            registry.add_decoders(ffmpeg)
    except ImportError:
        pass

    try:
        from . import pyogg
        registry.add_decoders(pyogg)
    except ImportError:
        pass

    if pyglet.compat_platform.startswith("darwin"):
        try:
            from . import coreaudio
            registry.add_decoders(coreaudio)
        except ImportError:
            pass


def have_ffmpeg():
    """Check if FFmpeg library is available.

    Returns:
        bool: True if FFmpeg is found.

    .. versionadded:: 1.4
    """
    try:
        from . import ffmpeg_lib
        if _debug:
            print('FFmpeg available, using to load media files.')

        found = False
        for release_versions, build_versions in ffmpeg_lib.release_versions.items():
            if ffmpeg_lib.compat.versions == build_versions:
                if _debug:
                    print(f'FFMpeg Release Version: {release_versions}. Versions Loaded: {ffmpeg_lib.compat.versions}')
                found = True
                break

        if not found:
            warnings.warn(f'FFmpeg release version not found. This may be a new or untested release. Unknown behavior may occur. Versions Loaded: {ffmpeg_lib.compat.versions}')

        return True

    except (ImportError, FileNotFoundError, AttributeError) as err:
        if _debug:
            print(f'FFmpeg not available: {err}')
        return False
