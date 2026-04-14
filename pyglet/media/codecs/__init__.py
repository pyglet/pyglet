import sys
import warnings

from typing import BinaryIO

from pyglet.util import CodecRegistry, Decoder, Encoder
from .base import *

import pyglet


_debug = pyglet.options['debug_media']

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

registry = CodecRegistry()
add_decoders = registry.add_decoders
add_encoders = registry.add_encoders
get_decoders = registry.get_decoders
get_encoders = registry.get_encoders


class MediaDecoder(Decoder):

    def decode(self, filename: str, file: BinaryIO | None, streaming: bool,
               audio_sample_format: str | None=None,
               audio_driver_sample_formats: list[str] | None=None,
               audio_sample_rate: int | None=None,
               audio_channels: int | None=None,
               audio_resample_hq: bool=False
    ) -> Source | StreamingSource:
        """Read the given file object and return an instance of `Source`
        or `StreamingSource`. Throws DecodeException if there is an error.
        `filename` can be a file type hint.

        Args:
        filename:
            Used to guess the media format, and to load the file if ``file``
            is unspecified.
        file:
            An optional file-like object containing the source data.
        streaming:
            If ``False``, a :class:`StaticSource` will be returned; otherwise
            a :class:`~pyglet.media.StreamingSource` is created.
        decoder:
            A specific decoder you wish to use, rather than relying on
            automatic detection. If specified, no other decoders are tried.
        audio_sample_format:
            A specific audio sample format you wish the decoder to ouput,
            rather than relying on automatic detection. For possible values see
            the AUDIO_SAMPLE_FORMAT_* constants.
            NOTE: currently only supported by FFmpegDecoder!
        audio_sample_rate:
            A specific audio sample rate (in Hz) you wish the decoder to
            output, rather than relying on automatic detection. For possible
            values see the AUDIO_SAMPLE_RATE_* constants.
            NOTE: currently only supported by FFmpegDecoder!
        audio_channels:
            A specific number of channels you wish the decoder to output,
            rather than relying on autimatic detection. For possible values see
            the AUDIO_CHANNELS_* constants.
            Note: currently only supported by FFmpegDecoder!
        audio_resample_hq:
            Whether to use high-quality resampling when resamplig is required
            (e.g. when a specific sample rate is requested), at the cost of
            increased CPU usage.
            Note: currently only supported by FFmpegDecoder!

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

        if not found and not _is_pyglet_doc_run:
            warnings.warn(f'FFmpeg release version not found. This may be a new or untested release. Unknown behavior may occur. Versions Loaded: {ffmpeg_lib.compat.versions}')

        return True

    except (ImportError, FileNotFoundError, AttributeError) as err:
        if _debug:
            print(f'FFmpeg not available: {err}')
        return False
