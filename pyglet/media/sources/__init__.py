"""Sources for media playback."""

import pyglet

from .base import AudioFormat, VideoFormat, AudioData, SourceInfo
from .base import Source, StreamingSource, StaticSource, PlayList
# help the docs figure out where these are supposed to live (they live here)
__all__ = [
    'have_ffmpeg',
    'AudioFormat',
    'VideoFormat',
    'AudioData',
    'SourceInfo',
    'Source',
    'StreamingSource',
    'StaticSource',
    'PlayList',
]


_debug = pyglet.options['debug_media']


def have_ffmpeg():
    """Check if FFmpeg library is available.

    Returns:
        bool: True if FFmpeg is found.

    .. versionadded:: 1.4
    """
    global _have_ffmpeg
    if _have_ffmpeg is None:
        try:
            from . import ffmpeg_lib
            _have_ffmpeg = True
            if _debug:
                print('FFmpeg available, using to load media files.')
        except ImportError:
            _have_ffmpeg = False
            if _debug:
                print('FFmpeg not available.')
    return _have_ffmpeg


_have_ffmpeg = None
