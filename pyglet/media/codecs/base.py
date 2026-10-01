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
            self.pointer = ctypes.cast(data, ctypes.c_void_p).value  # type: ignore[arg-type]
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
        last_ts = 0.0
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
        raise CannotSeekException

    def seek_to_frame(self, frame: int) -> None:
        """Seek to a decoded PCM frame.

        The default implementation preserves the historical, timestamp-based
        seek API.  Decoders which can seek sample-accurately should override
        this method.  Consumers that need an exact loop boundary should use
        this method instead of converting a frame index back to a float.

        Args:
            frame: Zero-based PCM frame index.
        """
        if self.audio_format is None:
            raise CannotSeekException
        self.seek(frame / self.audio_format.sample_rate)

    def get_queue_source(self) -> Source | None:
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
        return super().get_queue_source()  # type: ignore[return-value]

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

    def get_queue_source(self) -> Source | None:
        if self._data is not None:
            assert self.audio_format is not None
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

    def seek_to_frame(self, frame: int) -> None:
        """Seek directly to a PCM frame without a floating-point conversion."""
        frame = max(0, frame)
        self._file.seek(min(frame * self.audio_format.bytes_per_frame, self._max_offset))

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


class LoopingSource(Source):
    """Wrap an audio source with a repeatable region.

    Audio before ``loop_start`` is played once. The interval
    ``[loop_start, loop_end]`` is then repeated ``loop_count`` additional
    times before playback continues with the audio after ``loop_end``.
    A loop count of ``-1`` repeats indefinitely, while ``0`` disables further
    repeats. Changing :attr:`loop_count` during playback takes effect when the
    source next reaches the loop end.

    Loop points are expressed in seconds. Use :meth:`from_frames` when loop
    metadata is expressed as PCM frame indexes.
    """

    def __init__(self, source: Source, loop_start: float, loop_end: float, loop_count: int = -1) -> None:
        """Initialize a loop source object.

        Args:
            source:
                A frame-seekable, audio-only source.  The looping source has the
                same queueing behavior as this source: wrapping a
                :class:`StaticSource` creates an independent looping cursor for
                each player, while a streaming source remains single-use.
            loop_start:
                Start of the loop region in seconds.
            loop_end:
                Exclusive end of the loop region in seconds.
            loop_count:
                Number of additional times to play the loop region, or ``-1``
                for infinite looping.
        """
        if source.audio_format is None:
            raise ValueError("LoopingSource requires a source with audio.")
        if source.video_format is not None:
            raise ValueError("LoopingSource does not support video sources.")
        if loop_start < 0:
            raise ValueError("loop_start must be greater than or equal to zero.")
        if loop_end <= loop_start:
            raise ValueError("loop_end must be greater than loop_start.")
        if source.duration is not None and loop_end > source.duration:
            raise ValueError("loop_end must not exceed the source duration.")

        self.audio_format = source.audio_format
        self.video_format = None
        self.info = source.info
        self._source_template = source
        self._source = None
        self._is_player_source = False

        self._loop_start = self.audio_format.timestamp_to_bytes_aligned(loop_start)
        self._loop_end = self.audio_format.timestamp_to_bytes_aligned(loop_end)
        if self._loop_end <= self._loop_start:
            raise ValueError("Loop points must contain at least one complete audio frame.")

        self._cursor = 0
        self._loop_boundary_pending = False
        self._loop_count = 0
        self._remaining_loop_count = 0
        self.loop_count = loop_count

    @property
    def is_player_source(self) -> bool:
        return self._is_player_source

    @is_player_source.setter
    def is_player_source(self, value: bool) -> None:
        self._is_player_source = value
        if not value and self._source is not None:
            self._source.is_player_source = False

    @classmethod
    def from_frames(
        cls,
        source: Source,
        loop_start: int,
        loop_end: int,
        loop_count: int = -1,
    ) -> LoopingSource:
        """Create a looping source using PCM frame indexes as loop points."""
        if source.audio_format is None:
            raise ValueError("LoopingSource requires a source with audio.")
        if not isinstance(loop_start, int) or not isinstance(loop_end, int):
            raise TypeError("Frame loop points must be integers.")
        sample_rate = source.audio_format.sample_rate
        looping_source = cls(source, loop_start / sample_rate, loop_end / sample_rate, loop_count)
        # Preserve the caller's exact frame indexes
        looping_source._loop_start = loop_start * source.audio_format.bytes_per_frame
        looping_source._loop_end = loop_end * source.audio_format.bytes_per_frame
        return looping_source

    @property
    def loop_start(self) -> float:
        """Start of the loop region in seconds."""
        return self._loop_start / self.audio_format.bytes_per_second

    @property
    def loop_end(self) -> float:
        """Exclusive end of the loop region in seconds."""
        return self._loop_end / self.audio_format.bytes_per_second

    @property
    def loop_count(self) -> int:
        """Configured number of additional repeats, or ``-1`` for infinite."""
        return self._loop_count

    @loop_count.setter
    def loop_count(self, value: int) -> None:
        assert isinstance(value, int), "loop_count must be an integer."
        if value < -1:
            raise ValueError("loop_count must be -1 or greater.")
        self._loop_count = value
        self._remaining_loop_count = value

    def set_loop_count(self, value: int) -> None:
        """Set the number of repeats to make after the next loop boundary.

        The current pass through the loop region is never interrupted.  For
        example, setting this to ``0`` while an infinite loop is playing lets
        that pass finish and then continues with the outro.
        """
        self.loop_count = value

    @property
    def duration(self) -> float | None:
        """The duration including finite loop repetitions, if known."""
        source_duration = self._source_template.duration
        if source_duration is None or self._loop_count == -1:
            return None
        loop_duration = (self._loop_end - self._loop_start) / self.audio_format.bytes_per_second
        return source_duration + self._loop_count * loop_duration

    @property
    def remaining_loop_count(self) -> int:
        """Number of repeats remaining, or ``-1`` for infinite."""
        return self._remaining_loop_count

    def get_queue_source(self) -> LoopingSource:
        if isinstance(self._source_template, StreamingSource) and self.is_player_source:
            raise MediaException('This source is already queued on a player.')

        source = self._source_template.get_queue_source()
        if isinstance(self._source_template, StreamingSource):
            # The wrapped stream owns its one-shot queueing restriction.
            self._source = source
            self.is_player_source = True
            self._cursor = 0
            self._loop_boundary_pending = False
            self._remaining_loop_count = self._loop_count
            return self

        # Static sources return a new playable source for every player. Keep
        # the loop state independent as well, and retain the exact frame
        # positions instead of round-tripping through seconds.
        queue_source = type(self).from_frames(
            self._source_template,
            self._loop_start // self.audio_format.bytes_per_frame,
            self._loop_end // self.audio_format.bytes_per_frame,
            self._loop_count,
        )
        queue_source._source = source
        return queue_source

    def is_precise(self) -> bool:
        return self._source is not None and self._source.is_precise()

    def seek(self, timestamp: float) -> None:
        if self._source is None:
            raise RuntimeError("LoopingSource must be queued before it can be seeked.")
        timestamp = max(0.0, timestamp)
        if self.duration is not None:
            timestamp = min(timestamp, self.duration)

        requested_frame = int(timestamp * self.audio_format.sample_rate)
        loop_start_frame = self._loop_start // self.audio_format.bytes_per_frame
        loop_end_frame = self._loop_end // self.audio_format.bytes_per_frame
        loop_length = loop_end_frame - loop_start_frame

        if requested_frame < loop_start_frame:
            source_frame = requested_frame
            self._remaining_loop_count = self._loop_count
        elif self._loop_count == -1:
            source_frame = loop_start_frame + (requested_frame - loop_start_frame) % loop_length
            self._remaining_loop_count = -1
        else:
            final_loop_end = loop_start_frame + (self._loop_count + 1) * loop_length
            if requested_frame < final_loop_end:
                iteration = (requested_frame - loop_start_frame) // loop_length
                source_frame = loop_start_frame + (requested_frame - loop_start_frame) % loop_length
                self._remaining_loop_count = self._loop_count - iteration
            else:
                source_frame = loop_end_frame + (requested_frame - final_loop_end)
                self._remaining_loop_count = 0

        self._source.seek_to_frame(source_frame)
        self._cursor = source_frame * self.audio_format.bytes_per_frame
        self._loop_boundary_pending = False

    def get_audio_data(self, num_bytes: int, compensation_time: float = 0.0) -> AudioData | None:
        assert self._source
        requested_size = self.audio_format.align(num_bytes)
        if requested_size <= 0:
            return None

        chunks = []
        remaining_size = requested_size
        while remaining_size:
            if self._loop_boundary_pending:
                if self._remaining_loop_count == -1 or self._remaining_loop_count > 0:
                    if self._remaining_loop_count > 0:
                        self._remaining_loop_count -= 1
                    self._source.seek_to_frame(self._loop_start // self.audio_format.bytes_per_frame)
                    self._cursor = self._loop_start
                self._loop_boundary_pending = False

            request_size = remaining_size
            if self._cursor < self._loop_end:
                request_size = min(request_size, self._loop_end - self._cursor)

            audio_data = self._source.get_audio_data(request_size)
            if audio_data is None:
                break

            length = self.audio_format.align(min(audio_data.length, request_size))
            if length <= 0:
                break

            chunks.append(ctypes.string_at(audio_data.pointer, length))
            self._cursor += length
            remaining_size -= length

            if length != audio_data.length:
                # An imprecise decoder may have advanced beyond the requested
                # boundary.  Return it to the precise output position before
                # continuing at the loop point or in the outro.
                self._source.seek_to_frame(self._cursor // self.audio_format.bytes_per_frame)

            if self._cursor == self._loop_end:
                self._loop_boundary_pending = True

        if not chunks:
            return None
        data = b''.join(chunks)
        return AudioData(data, len(data))

    def delete(self) -> None:
        if isinstance(self._source, StreamingSource):
            self._source.delete()
        self.is_player_source = False
