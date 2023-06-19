"""Audio and video playback.

pyglet can play WAV files, and if FFmpeg is installed, many other audio and
video formats.

Playback is handled by the :class:`.Player` class, which reads raw data from
:class:`Source` objects and provides methods for pausing, seeking, adjusting
the volume, and so on. The :class:`.Player` class implements the best
available audio device. ::

    player = Player()

A :class:`Source` is used to decode arbitrary audio and video files. It is
associated with a single player by "queueing" it::

    source = load('background_music.mp3')
    player.queue(source)

Use the :class:`.Player` to control playback.

If the source contains video, the :py:meth:`Source.video_format` attribute
will be non-None, and the :py:attr:`Player.texture` attribute will contain the
current video image synchronised to the audio.

Decoding sounds can be processor-intensive and may introduce latency,
particularly for short sounds that must be played quickly, such as bullets or
explosions. You can force such sounds to be decoded and retained in memory
rather than streamed from disk by wrapping the source in a
:class:`StaticSource`::

    bullet_sound = StaticSource(load('bullet.wav'))

The other advantage of a :class:`StaticSource` is that it can be queued on
any number of players, and so played many times simultaneously.

Pyglet relies on Python's garbage collector to release resources when a player
has finished playing a source. In this way some operations that could affect
the application performance can be delayed.

The player provides a :py:meth:`Player.delete` method that can be used to
release resources immediately.
"""
from .drivers import get_audio_driver
from .player import Player, PlayerGroup
from .codecs import registry as _codec_registry
from .codecs import add_default_codecs as _add_default_codecs
from .codecs import Source, StaticSource, StreamingSource, SourceGroup, have_ffmpeg

from . import synthesis


__all__ = 'load', 'get_audio_driver', 'Player', 'PlayerGroup', 'SourceGroup', 'StaticSource', 'StreamingSource'


def load(filename, file=None, streaming=True, decoder=None):
    """Load a Source from a file.

    All decoders that are registered for the filename extension are tried.
    If none succeed, the exception from the first decoder is raised.
    You can also specifically pass a decoder to use.

    :Parameters:
        `filename` : str
            Used to guess the media format, and to load the file if `file` is
            unspecified.
        `file` : file-like object or None
            Source of media data in any supported format.
        `streaming` : bool
            If `False`, a :class:`StaticSource` will be returned; otherwise
            (default) a :class:`~pyglet.media.StreamingSource` is created.
        `decoder` : MediaDecoder or None
            A specific decoder you wish to use, rather than relying on
            automatic detection. If specified, no other decoders are tried.

    :rtype: StreamingSource or Source
    """
    if decoder:
        return decoder.decode(filename, file, streaming=streaming)
    else:
        return _codec_registry.decode(filename, file, streaming=streaming)


_add_default_codecs()
