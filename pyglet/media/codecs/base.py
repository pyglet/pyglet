"""Base data types and source abstractions for media codecs."""

from __future__ import annotations

import ctypes
import io
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, BinaryIO, ClassVar

from pyglet.media.exceptions import MediaException, CannotSeekException

if TYPE_CHECKING:
    from pyglet.graphics import Texture
    from pyglet.image.animation import Animation
    from pyglet.media.codecs import MediaEncoder
    from pyglet.media.player import AudioPlayer


class SampleType(str, Enum):
    """The numeric representation used by audio samples."""

    INT = "int"
    UINT = "uint"
    FLOAT = "float"


@dataclass
class AudioFormat:
    """Audio details.

    An instance of this class is provided by sources with audio tracks.  You
    should not modify the fields, as they are used internally to describe the
    format of data provided by the source.
    """

    #: The number of channels: 1 for mono or 2 for stereo
    #: (pyglet does not yet support surround-sound sources).
    channels: int

    #: Bits per sample; only 8 or 16 are supported.
    sample_size: int

    #: Samples per second (in Hertz).
    sample_rate: int

    #: The sample type, such as int, unit, or float.
    sample_type: SampleType | None = None
    sample_format: str = field(init=False, compare=False)
    bytes_per_frame: int = field(init=False, compare=False)
    bytes_per_second: int = field(init=False, compare=False)
    bytes_per_sample: int = field(init=False, compare=False)

    def __post_init__(self) -> None:
        if self.sample_type is None:
            if self.sample_size == 8:
                self.sample_type = SampleType.UINT
            else:
                self.sample_type = SampleType.INT
        else:
            self.sample_type = SampleType(self.sample_type)

        # Convenience
        prefixes = {SampleType.INT: "S", SampleType.UINT: "U", SampleType.FLOAT: "F"}
        self.sample_format = f"{prefixes[self.sample_type]}{self.sample_size}"

        self.bytes_per_frame = (self.sample_size // 8) * self.channels
        self.bytes_per_second = self.bytes_per_frame * self.sample_rate

        self.bytes_per_sample = self.bytes_per_frame
        """This attribute is kept for compatibility and should not be used due
        to a terminology error.
        This value contains the bytes per audio frame, and using
        `bytes_per_frame` should be preferred.
        For the actual amount of bytes per sample, divide `sample_size` by
        eight.
        """

    def align(self, num_bytes: int) -> int:
        """Align a given amount of bytes to the audio frame size.

        Align downwards.
        """
        return num_bytes - (num_bytes % self.bytes_per_frame)

    def align_ceil(self, num_bytes: int) -> int:
        """Align a given amount of bytes to the audio frame size.

        Align upwards.
        """
        return num_bytes + (-num_bytes % self.bytes_per_frame)

    def timestamp_to_bytes_aligned(self, timestamp: float) -> int:
        """Convert a timestamp to a frame-aligned byte offset.

        The returned offset corresponds to playback at the given timestamp.
        """
        return self.align(int(timestamp * self.bytes_per_second))

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(channels={self.channels}, "
            f"sample_size={self.sample_size}, sample_rate={self.sample_rate}, "
            f"sample_type={self.sample_type.value})"
        )


@dataclass
class VideoFormat:
    """Video details.

    An instance of this class is provided by sources with a video stream. You
    should not modify the fields.

    Note that the sample aspect has no relation to the aspect ratio of the
    video image.  For example, a video image of 640x480 with sample aspect 2.0
    should be displayed at 1280x480.  It is the responsibility of the
    application to perform this scaling.

    Args:
            width:
                Width of video image, in pixels.
            height:
                Height of video image, in pixels.
            sample_aspect:
                Aspect ratio (width over height) of a single video pixel.
            frame_rate:
                Frame rate (frames per second) of the video or ``None`` if not known.

            .. versionadded:: 1.2
    """

    width: int
    height: int
    sample_aspect: float = 0.0
    frame_rate: float | None = None


class AudioData:
    """A single packet of audio data.

    This class is used internally by pyglet.
    """

    __slots__ = 'data', 'length', 'pointer'

    def __init__(
        self,
        data: bytes | ctypes.Array,
        length: int,
    ) -> None:
        """Create an audio packet.

        Args:
            data:
                Sample data.
            length:
                Size of sample data, in bytes.
        """
        if isinstance(data, bytes):
            # bytes are treated specially by ctypes and can be cast to a void pointer, get
            # their content's address like this
            self.pointer = ctypes.cast(data, ctypes.c_void_p).value
        elif isinstance(data, ctypes.Array):
            self.pointer = ctypes.addressof(data)
        else:
            try:
                self.pointer = ctypes.addressof(ctypes.c_int.from_buffer(data))
            except TypeError as err:
                raise TypeError("Unsupported AudioData type.") from err

        self.data = data
        # In any case, `data` will support the buffer protocol by delivering at least
        # a readable buffer.

        self.length = length


@dataclass
class SourceInfo:
    """Source metadata information.

    Fields are the empty string or zero if the information is not available.

    Args:
        title (str): Title
        author (str): Author
        copyright (str): Copyright statement
        comment (str): Comment
        album (str): Album name
        year (int): Year
        track (int): Track number
        genre (str): Genre

    .. versionadded:: 1.2
    """

    title: str = ''
    author: str = ''
    copyright: str = ''
    comment: str = ''
    album: str = ''
    year: int = 0
    track: int = 0
    genre: str = ''


class Source:
    """An audio and/or video source.

    Args:
        audio_format (:class:`.AudioFormat`): Format of the audio in this
            source, or ``None`` if the source is silent.
        video_format (:class:`.VideoFormat`): Format of the video in this
            source, or ``None`` if there is no video.
        info (:class:`.SourceInfo`): Source metadata such as title, artist,
            etc; or ``None`` if the` information is not available.

            .. versionadded:: 1.2

    Attributes:
        is_player_source (bool): Determine if this source is a player
            current source.

            Check on a :py:class:`~pyglet.media.player.AudioPlayer` if this source
            is the current source.
    """

    _duration: float = 0.0
    _players: ClassVar[list[AudioPlayer]] = []  # Players created through Source.play

    audio_format: AudioFormat | None = None
    video_format: VideoFormat | None = None
    info: SourceInfo | None = None
    is_player_source: bool = False

    @property
    def duration(self) -> float:
        """The length of the source, in seconds.

        Not all source durations can be determined; in this case the value
        is ``None``.

        Read-only.
        """
        return self._duration

    def play(self) -> AudioPlayer:
        """Play the source.

        This is a convenience method which creates a Player for
        this source and plays it immediately.

        Returns:
            :class:`.Player`
        """
        from pyglet.media.player import AudioPlayer  # noqa: PLC0415

        player = AudioPlayer()
        player.queue(self)
        player.play()
        Source._players.append(player)

        def _on_player_eos() -> None:
            Source._players.remove(player)
            # There is a closure on player. To break up that reference, delete this function.
            player.on_player_eos = None
            player.delete()

        player.on_player_eos = _on_player_eos
        return player

    def get_animation(self) -> Animation:
        """Import all video frames into memory.

        An empty animation will be returned if the source has no video.
        Otherwise, the animation will contain all unplayed video frames (the
        entire source, if it has not been queued on a player). After creating
        the animation, the source will be at EOS (end of stream).

        This method is unsuitable for videos running longer than a
        few seconds.

        .. versionadded:: 1.1
        """
        from pyglet.image import Animation, AnimationFrame  # noqa: PLC0415

        if not self.video_format:
            # Animation requires at least one frame.
            return Animation([])
        frames = []
        last_ts = 0
        next_ts = self.get_next_video_timestamp()
        while next_ts is not None:
            image = self.get_next_video_frame()
            if image is not None:
                delay = next_ts - last_ts
                frames.append(AnimationFrame(image, delay))
                last_ts = next_ts
            next_ts = self.get_next_video_timestamp()
        return Animation(frames)

    def get_next_video_timestamp(self) -> float | None:
        """Get the timestamp of the next video frame.

        .. versionadded:: 1.1

        Returns:
            float: The next timestamp, or ``None`` if there are no more video
            frames.
        """

    def get_next_video_frame(self) -> Texture | None:
        """Get the next video frame.

        Returns:
            The next video frame image, or ``None`` if the video frame could not be decoded or there are
            no more video frames.

        .. versionadded:: 1.1
        """

    def save(self, filename: str, file: BinaryIO | None = None, encoder: MediaEncoder | None = None) -> None:
        """Save this Source to a file.

        Args:
            filename:
                Used to set the file format, and to open the output file
                if `file` is unspecified.
            file:
                File to write audio data to.
            encoder:
                If unspecified, all encoders matching the filename extension
                are tried.  If all fail, the exception from the first one
                attempted is raised.

        """
        if encoder:
            return encoder.encode(self, filename, file)
        import pyglet.media.codecs  # noqa: PLC0415

        return pyglet.media.codecs.registry.encode(self, filename, file)

    # Internal methods that Player calls on the source:

    def is_precise(self) -> bool:
        r"""Whether this source is considered precise.

        ``x`` bytes on source ``s`` are considered aligned if
        ``x % s.audio_format.bytes_per_frame == 0``, so there'd be no partial
        audio frame in the returned data.

        A source is precise if - for an aligned request of ``x`` bytes - it
        returns:\\

          - If ``x`` or more bytes are available, ``x`` bytes.
          - If not enough bytes are available anymore, ``r`` bytes where
            ``r < x`` and ``r`` is aligned.

        A source is **not** precise if it does any of these:

          - Return less than ``x`` bytes for an aligned request of ``x``
            bytes although data still remains so that an additional request
            would return additional :class:`.AudioData` / not ``None``.
          - Return more bytes than requested.
          - Return an unaligned amount of bytes for an aligned request.

        pyglet's internals are guaranteed to never make unaligned
        requests, or requests of less than 1024 bytes.

        If this method returns ``False``, pyglet will wrap the source in an
        alignment-forcing buffer creating additional overhead.

        If this method is overridden to return ``True`` although the source
        does not comply with the requirements above, audio playback may be
        negatively impacted at best and memory access violations occur at
        worst.

        Returns:
            Whether the source is precise.
        """
        return False

    def seek(self, timestamp: float) -> None:
        """Seek to given timestamp.

        Args:
            timestamp (float): Time where to seek in the source. The
                ``timestamp`` will be clamped to the duration of the source.
        """
        del timestamp
        raise CannotSeekException

    def get_queue_source(self) -> Source:
        """Return the ``Source`` to be used as the queue source for a player.

        Default implementation returns ``self``.

        Returns:
            :class:`Source`
        """
        return self

    def get_audio_data(self, num_bytes: int) -> AudioData | None:
        """Get next packet of audio data.

        Args:
            num_bytes (int): A size hint for the amount of bytes to return,
                but the returned amount may be lower or higher.

        Returns:
            :class:`.AudioData`: Next packet of audio data, or ``None`` if
            there is no (more) data.
        """
        del num_bytes
        return None


class StreamingSource(Source):
    """A source that is decoded as it is being played.

    The source can only be played once at a time on any
    :class:`~pyglet.media.player.AudioPlayer`.
    """

    def get_queue_source(self) -> StreamingSource:
        """Return the ``Source`` to be used as the source for a player.

        Default implementation returns self.

        Returns:
            :class:`.Source`
        """
        if self.is_player_source:
            raise MediaException('This source is already queued on a player.')
        self.is_player_source = True
        return super().get_queue_source()

    def delete(self) -> None:
        """Release the resources held by this StreamingSource."""


class StaticSource(Source):
    """A source that has been completely decoded in memory.

    This source can be queued onto multiple players any number of times.

    Construct a :py:class:`~pyglet.media.StaticSource` for the data in
    ``source``.

    Args:
        source (Source):  The source to read and decode audio and video data
            from.
    """

    def __init__(self, source: Source) -> None:
        """Read a source into an in-memory buffer."""
        source = source.get_queue_source()
        if source.video_format:
            raise NotImplementedError('Static sources not supported for video.')

        self.audio_format = source.audio_format
        if self.audio_format is None:
            self._data = None
            self._duration = 0.0
            return

        # Arbitrary: number of bytes to request at a time.
        buffer_size = 1 << 20  # 1 MB

        # Naive implementation.  Driver-specific implementations may override
        # to load static audio data into device (or at least driver) memory.
        data = io.BytesIO()
        while True:
            audio_data = source.get_audio_data(buffer_size)
            if audio_data is None:
                break
            data.write(audio_data.data)
        self._data = data.getvalue()

        self._duration = len(self._data) / self.audio_format.bytes_per_second

    def get_queue_source(self) -> StaticMemorySource | None:
        if self._data is not None:
            return StaticMemorySource(self._data, self.audio_format)
        return None

    def get_audio_data(self, num_bytes: int) -> AudioData | None:
        """The StaticSource does not provide audio data.

        When the StaticSource is queued on a
        :class:`~pyglet.media.player.AudioPlayer`, it creates a
        :class:`.StaticMemorySource` containing its internal audio data and
        audio format.

        Raises:
            RuntimeError
        """
        del num_bytes
        raise RuntimeError('StaticSource cannot be queued.')


class StaticMemorySource(StaticSource):
    """Helper class for default implementation of :class:`.StaticSource`.

    Do not use directly. This class is used internally by pyglet.

    Args:
        data (readable buffer): The audio data.
        audio_format (AudioFormat): The audio format.
    """

    def __init__(self, data: bytes | bytearray | memoryview, audio_format: AudioFormat) -> None:
        """Construct a memory source over the given data buffer."""
        self._file = io.BytesIO(data)
        self._max_offset = len(data)
        self.audio_format = audio_format
        self._duration = len(data) / float(audio_format.bytes_per_second)

    def is_precise(self) -> bool:
        return True

    def seek(self, timestamp: float) -> None:
        """Seek to given timestamp.

        Args:
            timestamp (float): Time where to seek in the source.
        """
        offset = int(timestamp * self.audio_format.bytes_per_second)
        # Align to audio frame to not corrupt audio data.
        self._file.seek(self.audio_format.align(offset))

    def get_audio_data(self, num_bytes: int) -> AudioData | None:
        """Get next packet of audio data.

        Args:
            num_bytes (int): Maximum number of bytes of data to return.

        Returns:
            :class:`.AudioData`: Next packet of audio data, or ``None`` if
            there is no (more) data.
        """
        data = self._file.read(num_bytes)
        if not data:
            return None

        return AudioData(data, len(data))


class SourceGroup:
    """Group of like sources to allow gapless playback.

    Seamlessly read data from a group of sources to allow for
    gapless playback. All sources must share the same audio format.
    The first source added sets the format.
    """

    def __init__(self) -> None:
        """Create an empty source group."""
        self.audio_format = None
        self.video_format = None
        self.info = None
        self.duration = 0.0
        self._sources = []
        self.is_player_source = False

    def is_precise(self) -> bool:
        return False

    def seek(self, time: float) -> None:
        if self._sources:
            self._sources[0].seek(time)

    def add(self, source: Source) -> None:
        self.audio_format = self.audio_format or source.audio_format
        self.info = self.info or source.info
        source = source.get_queue_source()
        if source.audio_format != self.audio_format:
            raise MediaException("Sources must share the same audio format.")
        self._sources.append(source)
        if self.duration is not None:
            self.duration = None if source.duration is None else self.duration + source.duration

    def has_next(self) -> bool:
        return len(self._sources) > 1

    def get_queue_source(self) -> SourceGroup:
        return self

    def _advance(self) -> None:
        if self._sources:
            old_source = self._sources.pop(0)
            if old_source.duration is not None and self.duration is not None:
                self.duration -= old_source.duration

            if isinstance(old_source, StreamingSource):
                old_source.delete()

    def get_audio_data(self, num_bytes: int) -> AudioData | None:
        """Get next audio packet.

        Args:
            num_bytes:
                Hint for preferred size of audio packet; may be ignored.

        Returns:
            Audio data, or ``None`` if there is no more data.
        """
        if not self._sources:
            return None

        buffer = b""

        while len(buffer) < num_bytes and self._sources:
            audiodata = self._sources[0].get_audio_data(num_bytes - len(buffer))
            if audiodata:
                buffer += audiodata.data
            else:
                self._advance()

        if not buffer:
            return None
        return AudioData(buffer, len(buffer))
