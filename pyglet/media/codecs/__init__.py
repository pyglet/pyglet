from __future__ import annotations
import sys
import warnings
from typing import BinaryIO, Any, Literal, TYPE_CHECKING

from pyglet.util import CodecRegistry, Decoder, Encoder
from .base import *

import pyglet


_debug = pyglet.options.debug_media

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

registry = CodecRegistry()
add_decoders = registry.add_decoders
add_encoders = registry.add_encoders
get_decoders = registry.get_decoders
get_encoders = registry.get_encoders


class MediaDecoder(Decoder):
    def decode(self, filename: str, file: BinaryIO, streaming: bool) -> Any:
        """Read the given file object and return an instance of `Source` or `StreamingSource`.

        Throws DecodeException if there is an error.  `filename` can be a file type hint.
        """
        raise NotImplementedError


class MediaEncoder(Encoder):

    def encode(self, source: Any, filename: str, file: BinaryIO) -> None:
        """Encode the given source to the given file.

        `filename` provides a hint to the file format desired.  options are
        encoder-specific, and unknown options should be ignored or
        issue warnings.
        """
        raise NotImplementedError


def add_default_codecs() -> None:
    # Add all bundled codecs. These should be listed in order of
    # preference.  This is called automatically by pyglet.media.

    if pyglet.compat_platform == "emscripten":
        try:
            # Currently other codecs cannot retrieve files from pyodides path, as it exists in its own environment.
            # Will make this the only audio codec providers.
            # This could potentially be adjusted later, but the codec already handles all the major filetypes.
            from . import webaudio_pyodide  # noqa: PLC0415
            registry.add_decoders(webaudio_pyodide)
            return  # Return to prevent other codecs from handling file types.
        except ImportError:
            pass
    try:
        from . import wave  # noqa: PLC0415
        registry.add_decoders(wave)
        registry.add_encoders(wave)
    except ImportError:
        pass

    if pyglet.compat_platform.startswith('linux'):
        try:
            from . import gstreamer  # noqa: PLC0415
            registry.add_decoders(gstreamer)
        except ImportError:
            pass

    try:
        if pyglet.compat_platform in ('win32', 'cygwin'):
            from pyglet.libs.win32.constants import WINDOWS_VISTA_OR_GREATER  # noqa: PLC0415
            if WINDOWS_VISTA_OR_GREATER:  # Supports Vista and above.
                from . import wmf  # noqa: PLC0415
                registry.add_decoders(wmf)
    except ImportError:
        pass

    if pyglet.compat_platform.startswith("darwin"):
        try:
            from . import coreaudio  # noqa: PLC0415
            registry.add_decoders(coreaudio)
        except ImportError:
            pass

    try:
        from . import pyogg  # noqa: PLC0415
        registry.add_decoders(pyogg)
    except ImportError:
        pass

    try:
        if have_ffmpeg():
            from . import ffmpeg  # noqa: PLC0415
            registry.add_decoders(ffmpeg)
    except ImportError:
        pass



def have_ffmpeg() -> bool:
    """Check if FFmpeg library is available.

    Returns:
        bool: True if FFmpeg is found.

    .. versionadded:: 1.4
    """
    try:
        from . import ffmpeg_lib  # noqa: PLC0415
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
