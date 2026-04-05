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
from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO

from .drivers import get_audio_driver
from .player import Player, PlayerGroup
from .codecs import registry as _codec_registry
from .codecs import add_default_codecs as _add_default_codecs
from .codecs import Source, StaticSource, StreamingSource, SourceGroup, have_ffmpeg

from . import synthesis

if TYPE_CHECKING:
    from .codecs import MediaDecoder

__all__ = 'load', 'get_audio_driver', 'Player', 'PlayerGroup', 'SourceGroup', 'StaticSource', 'StreamingSource'


AUDIO_SAMPLE_FORMAT_U8 = "U8"
AUDIO_SAMPLE_FORMAT_S16 = "S16"
#AUDIO_SAMPLE_FORMAT_S24 = "S24"  # Could be considered as well
AUDIO_SAMPLE_FORMAT_S32 = "S32"
AUDIO_SAMPLE_FORMAT_F32 = "F32"

AUDIO_SAMPLE_RATE_22050 = 22050
AUDIO_SAMPLE_RATE_44100 = 44100
AUDIO_SAMPLE_RATE_48000 = 48000
AUDIO_SAMPLE_RATE_88200 = 88200
AUDIO_SAMPLE_RATE_96000 = 96000
AUDIO_SAMPLE_RATE_176400 = 176400
AUDIO_SAMPLE_RATE_192000 = 192000

AUDIO_CHANNELS_MONO = 1
AUDIO_CHANNELS_STEREO = 2
AUDIO_CHANNELS_DUAL_MONO = -2

_VALID_AUDIO_SAMPLE_FORMATS = (
    AUDIO_SAMPLE_FORMAT_U8,
    AUDIO_SAMPLE_FORMAT_S16,
    #AUDIO_SAMPLE_FORMAT_S24,  # Could be considered as well
    AUDIO_SAMPLE_FORMAT_S32,
    AUDIO_SAMPLE_FORMAT_F32,
)

_VALID_AUDIO_SAMPLE_RATES = (
    AUDIO_SAMPLE_RATE_22050,
    AUDIO_SAMPLE_RATE_44100,
    AUDIO_SAMPLE_RATE_48000,
    AUDIO_SAMPLE_RATE_88200,
    AUDIO_SAMPLE_RATE_96000,
    AUDIO_SAMPLE_RATE_176400,
    AUDIO_SAMPLE_RATE_192000,
)

_VALID_AUDIO_CHANNELS = (
    AUDIO_CHANNELS_MONO,
    AUDIO_CHANNELS_STEREO,
    AUDIO_CHANNELS_DUAL_MONO,
)

def load(filename: str, file: BinaryIO | None = None,
         streaming: bool = True, decoder: MediaDecoder | None = None,
         audio_sample_format: str | None = None,
         audio_sample_rate: int | None = None,
         audio_channels: int | None = None,
         audio_resample_hq: bool=False) -> Source | StreamingSource:
    """Load a Source from disk, or an opened file.

    All decoders that are registered for the filename extension are tried.
    If none succeed, the exception from the first decoder is raised.
    You can also specifically pass a decoder instance to use.

    Args:
        filename:
            Used to guess the media format, and to load the file if ``file``
            is unspecified.
        file:
            An optional file-like object containing the source data.
        streaming:
            If ``False``, a :class:`StaticSource` will be returned; otherwise
            (default) a :class:`~pyglet.media.StreamingSource` is created.
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

    audio_driver = get_audio_driver()
    if audio_sample_format is not None:
        if audio_sample_format not in _VALID_AUDIO_SAMPLE_FORMATS:
            raise ValueError(
                f"Invalid audio_sample_format '{audio_sample_format}'. "
                f"Expected one of: {', '.join(_VALID_AUDIO_SAMPLE_FORMATS)}")
        if audio_sample_format not in audio_driver.sample_formats:
            raise ValueError(
                f"Unsupported audio_sample_format '{audio_sample_format}'. "
                f"{type(audio_driver).__name__} is only compatible with: "
                f"{', '.join(audio_driver.sample_formats)}")

    if audio_sample_rate is not None:
        if audio_sample_rate not in _VALID_AUDIO_SAMPLE_RATES:
            raise ValueError(
                f"Invalid audio_sample_rate '{audio_sample_rate}'. "
                f"Expected one of: "
                f"{', '.join([str(x) for x in _VALID_AUDIO_SAMPLE_RATES])}")

    if audio_channels is not None:
        if audio_channels not in _VALID_AUDIO_CHANNELS:
            raise ValueError(
                f"Invalid audio_channels '{audio_channels}'. "
                f"Expected one of: "
                f"{', '.join([str(x) for x in _VALID_AUDIO_CHANNELS])}")

    if not isinstance(audio_resample_hq, bool):
        raise ValueError(
                f"Invalid audio_resample_hq '{audio_resample_hq}'. "
                f"Expected a boolean (True, False)")

    if decoder:
        if type(decoder).__name__ == "FFmpegDecoder":
            return decoder.decode(
                filename, file, streaming=streaming,
                audio_sample_format=audio_sample_format,
                audio_driver_sample_formats=audio_driver.sample_formats,
                audio_sample_rate=audio_sample_rate,
                audio_channels=audio_channels,
                audio_resample_hq=audio_resample_hq)
        else:
            return decoder.decode(filename, file, streaming=streaming)

    return _codec_registry.decode(filename, file, streaming=streaming)


_add_default_codecs()


__all__ = [
    'Player', 
    'PlayerGroup', 
    'Source', 
    'StaticSource', 
    'StreamingSource',
    'load', 
    'synthesis', 
    'get_audio_driver',
    'AUDIO_SAMPLE_FORMAT_U8',
    'AUDIO_SAMPLE_FORMAT_S16',
    #'AUDIO_SAMPLE_FORMAT_S24' # Could be considered as well
    'AUDIO_SAMPLE_FORMAT_S32',
    'AUDIO_SAMPLE_FORMAT_F32',
]
