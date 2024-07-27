import ctypes
import io
from typing import TYPE_CHECKING, BinaryIO, List, Optional, Union

from pyglet.media.exceptions import MediaException, CannotSeekException
from pyglet.util import next_or_equal_power_of_two

if TYPE_CHECKING:
    from pyglet.image import AbstractImage
    from pyglet.image.animation import Animation
    from pyglet.media.codecs import MediaEncoder
    from pyglet.media.drivers.base import MediaEvent
    from pyglet.media.player import Player


class AudioFormat:
    """Audio details.

    An instance of this class is provided by sources with audio tracks.  You
    should not modify the fields, as they are used internally to describe the
    format of data provided by the source.

    Args:
        channels (int): The number of channels: 1 for mono or 2 for stereo
            (pyglet does not yet support surround-sound sources).
        sample_size (int): Bits per sample; only 8 or 16 are supported.
        sample_rate (int): Samples per second (in Hertz).
    """

    def __init__(self, channels: int, sample_size: int, sample_rate: int) -> None:
        self.channels = channels
        self.sample_size = sample_size
        self.sample_rate = sample_rate

        # Convenience

        self.bytes_per_frame = (sample_size // 8) * channels
        self.bytes_per_second = self.bytes_per_frame * sample_rate

        self.bytes_per_sample = self.bytes_per_frame
        """This attribute is kept for compatibility and should not be used due
        to a terminology error.
        This value contains the bytes per audio frame, and using
        `bytes_per_frame` should be preferred.
        For the actual amount of bytes per sample, divide `sample_size` by
        eight.
        """

    def align(self, num_bytes: int) -> int:
        """Align a given amount of bytes to the audio frame size of this
        audio format, downwards.
        """
        return num_bytes - (num_bytes % self.bytes_per_frame)

    def align_ceil(self, num_bytes: int) -> int:
        """Align a given amount of bytes to the audio frame size of this
        audio format, upwards.
        """
        return num_bytes + (-num_bytes % self.bytes_per_frame)

    def timestamp_to_bytes_aligned(self, timestamp: float) -> int:
        """Given a timestamp, return the amount of bytes that an emitter with
        this audio format would have to have played to reach it, aligned
        to the audio frame size.
        """
        return self.align(int(timestamp * self.bytes_per_second))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AudioFormat):
            return (self.channels == other.channels and
                    self.sample_size == other.sample_size and
                    self.sample_rate == other.sample_rate)
        return NotImplemented

    def __repr__(self) -> str:
        return '%s(channels=%d, sample_size=%d, sample_rate=%d)' % (
            self.__class__.__name__, self.channels, self.sample_size,
            self.sample_rate)


class VideoFormat:
    """Video details.

    An instance of this class is provided by sources with a video stream. You
    should not modify the fields.

    Note that the sample aspect has no relation to the aspect ratio of the
    video image.  For example, a video image of 640x480 with sample aspect 2.0
    should be displayed at 1280x480.  It is the responsibility of the
    application to perform this scaling.

    Args:
        width (int): Width of video image, in pixels.
        height (int): Height of video image, in pixels.
        sample_aspect (float): Aspect ratio (width over height) of a single
            video pixel.
        frame_rate (float): Frame rate (frames per second) of the video.

            .. versionadded:: 1.2
    """

    def __init__(self, width: int, height: int, sample_aspect: float = 1.0) -> None:
        self.width = width
        self.height = height
        self.sample_aspect = sample_aspect
        self.frame_rate = None

    def __eq__(self, other) -> bool:
        if isinstance(other, VideoFormat):
            return (self.width == other.width and
                    self.height == other.height and
                    self.sample_aspect == other.sample_aspect and
                    self.frame_rate == other.frame_rate)
        return False


class AudioData:
    """A single packet of audio data.

    This class is used internally by pyglet.

    Args:
        data (bytes, ctypes array, or supporting buffer protocol): Sample data.
        length (int): Size of sample data, in bytes.
        timestamp (float): Time of the first sample, in seconds.
        duration (float): Total data duration, in seconds.
        events (List[:class:`pyglet.media.drivers.base.MediaEvent`]): List of events
            contained within this packet. Events are timestamped relative to
            this audio packet.

    .. deprecated:: 2.0.10
            `timestamp` and `duration` are unused and will be removed eventually.
    """

    __slots__ = 'data', 'length', 'timestamp', 'duration', 'events', 'pointer'

    def __init__(self,
                 data: Union[bytes, ctypes.Array],
                 length: int,
                 timestamp: float = 0.0,
                 duration: float = 0.0,
                 events: Optional[List['MediaEvent']] = None) -> None:

        if isinstance(data, bytes):
            # bytes are treated specially by ctypes and can be cast to a void pointer, get
            # their content's address like this
            self.pointer = ctypes.cast(data, ctypes.c_void_p).value
        elif isinstance(data, ctypes.Array):
            self.pointer = ctypes.addressof(data)
        else:
            try:
                self.pointer = ctypes.addressof(ctypes.c_int.from_buffer(data))
            except TypeError:
                raise TypeError("Unsupported AudioData type.")

        self.data = data
        # In any case, `data` will support the buffer protocol by delivering at least
        # a readable buffer.

        self.length = length
        self.timestamp = timestamp
        self.duration = duration
        self.events = [] if events is None else events


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

    title = ''
    author = ''
    copyright = ''
    comment = ''
    album = ''
    year = 0
    track = 0
    genre = ''


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

            Check on a :py:class:`~pyglet.media.player.Player` if this source
            is the current source.
    """

    _duration = None
    _players: List['Player'] = []  # Players created through Source.play

    audio_format = None
    video_format = None
    info = None
    is_player_source = False

    @property
    def duration(self) -> float:
        """float: The length of the source, in seconds.

        Not all source durations can be determined; in this case the value
        is ``None``.

        Read-only.
        """
        return self._duration

    def play(self) -> 'Player':
        """Play the source.

        This is a convenience method which creates a Player for
        this source and plays it immediately.

        Returns:
            :class:`.Player`
        """
        from pyglet.media.player import Player  # XXX Nasty circular dependency
        player = Player()
        player.queue(self)
        player.play()
        Source._players.append(player)

        def _on_player_eos():
            Source._players.remove(player)
            # There is a closure on player. To break up that reference, delete this function.
            player.on_player_eos = None
            player.delete()

        player.on_player_eos = _on_player_eos
        return player

    def get_animation(self) -> 'Animation':
        """
        Import all video frames into memory.

        An empty animation will be returned if the source has no video.
        Otherwise, the animation will contain all unplayed video frames (the
        entire source, if it has not been queued on a player). After creating
        the animation, the source will be at EOS (end of stream).

        This method is unsuitable for videos running longer than a
        few seconds.

        .. versionadded:: 1.1

        Returns:
            :class:`pyglet.image.Animation`
        """
        from pyglet.image import Animation, AnimationFrame
        if not self.video_format:
            # XXX: This causes an assertion in the constructor of Animation
            return Animation([])
        else:
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

    def get_next_video_timestamp(self) -> Optional[float]:
        """Get the timestamp of the next video frame.

        .. versionadded:: 1.1

        Returns:
            float: The next timestamp, or ``None`` if there are no more video
            frames.
        """
        pass

    def get_next_video_frame(self) -> Optional['AbstractImage']:
        """Get the next video frame.

        .. versionadded:: 1.1

        Returns:
            :class:`pyglet.image.AbstractImage`: The next video frame image,
            or ``None`` if the video frame could not be decoded or there are
            no more video frames.
        """
        pass

    def save(self,
             filename: str,
             file: Optional[BinaryIO] = None,
             encoder: Optional['MediaEncoder'] = None) -> None:
        """Save this Source to a file.

        :Parameters:
            `filename` : str
                Used to set the file format, and to open the output file
                if `file` is unspecified.
            `file` : file-like object or None
                File to write audio data to.
            `encoder` : MediaEncoder or None
                If unspecified, all encoders matching the filename extension
                are tried.  If all fail, the exception from the first one
                attempted is raised.

        """
        if encoder:
            return encoder.encode(self, filename, file)
        else:
            import pyglet.media.codecs
            return pyglet.media.codecs.registry.encode(self, filename, file)

    # Internal methods that Player calls on the source:

    def is_precise(self) -> bool:
        """bool: Whether this source is considered precise.

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

        :Returns:
            bool: Whether the source is precise.
        """
        return False

    def seek(self, timestamp: float) -> None:
        """Seek to given timestamp.

        Args:
            timestamp (float): Time where to seek in the source. The
                ``timestamp`` will be clamped to the duration of the source.
        """
        raise CannotSeekException()

    def get_queue_source(self) -> 'Source':
        """Return the ``Source`` to be used as the queue source for a player.

        Default implementation returns ``self``.

        Returns:
            :class:`Source`
        """
        return self

    def get_audio_data(self, num_bytes: int, compensation_time=0.0) -> Optional[AudioData]:
        """Get next packet of audio data.

        Args:
            num_bytes (int): A size hint for the amount of bytes to return,
                but the returned amount may be lower or higher.
            compensation_time (float): Time in sec to compensate due to a
                difference between the master clock and the audio clock.

        .. deprecated:: 2.0.10
            compensation_time: Will always be given as ``0.0``.

        Returns:
            :class:`.AudioData`: Next packet of audio data, or ``None`` if
            there is no (more) data.
        """
        return None


class StreamingSource(Source):
    """A source that is decoded as it is being played.

    The source can only be played once at a time on any
    :class:`~pyglet.media.player.Player`.
    """

    def get_queue_source(self) -> 'StreamingSource':
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
        pass


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

    def get_queue_source(self) -> Optional['StaticMemorySource']:
        if self._data is not None:
            return StaticMemorySource(self._data, self.audio_format)
        return None

    def get_audio_data(self, num_bytes: float, compensation_time: float = 0.0) -> Optional[AudioData]:
        """The StaticSource does not provide audio data.

        When the StaticSource is queued on a
        :class:`~pyglet.media.player.Player`, it creates a
        :class:`.StaticMemorySource` containing its internal audio data and
        audio format.

        Raises:
            RuntimeError
        """
        raise RuntimeError('StaticSource cannot be queued.')


class StaticMemorySource(StaticSource):
    """
    Helper class for default implementation of :class:`.StaticSource`.

    Do not use directly. This class is used internally by pyglet.

    Args:
        data (readable buffer): The audio data.
        audio_format (AudioFormat): The audio format.
    """

    def __init__(self, data, audio_format: AudioFormat) -> None:
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

    def get_audio_data(self, num_bytes: float, compensation_time: float = 0.0) -> Optional[AudioData]:
        """Get next packet of audio data.

        Args:
            num_bytes (int): Maximum number of bytes of data to return.

        Returns:
            :class:`.AudioData`: Next packet of audio data, or ``None`` if
            there is no (more) data.
        """
        offset_before = self._file.tell()

        data = self._file.read(num_bytes)
        if not data:
            return None

        timestamp = float(offset_before) / self.audio_format.bytes_per_second
        duration = len(data) / self.audio_format.bytes_per_second
        return AudioData(data, len(data), timestamp, duration)


class SourceGroup:
    """Group of like sources to allow gapless playback.

    Seamlessly read data from a group of sources to allow for
    gapless playback. All sources must share the same audio format.
    The first source added sets the format.
    """

    def __init__(self) -> None:
        self.audio_format = None
        self.video_format = None
        self.info = None
        self.duration = 0.0
        self._timestamp_offset = 0.0
        self._dequeued_durations = []
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
        assert (source.audio_format == self.audio_format), "Sources must share the same audio format."
        self._sources.append(source)
        self.duration += source.duration

    def has_next(self) -> bool:
        return len(self._sources) > 1

    def get_queue_source(self) -> 'SourceGroup':
        return self

    def _advance(self) -> None:
        if self._sources:
            self._timestamp_offset += self._sources[0].duration
            self._dequeued_durations.insert(0, self._sources[0].duration)
            old_source = self._sources.pop(0)
            self.duration -= old_source.duration

            if isinstance(old_source, StreamingSource):
                old_source.delete()

    def get_audio_data(self, num_bytes: float, compensation_time=0.0) -> Optional[AudioData]:
        """Get next audio packet.

        :Parameters:
            `num_bytes` : int
                Hint for preferred size of audio packet; may be ignored.

        :rtype: `AudioData`
        :return: Audio data, or None if there is no more data.
        """

        if not self._sources:
            return None

        buffer = b""
        duration = 0.0
        timestamp = 0.0

        while len(buffer) < num_bytes and self._sources:
            audiodata = self._sources[0].get_audio_data(num_bytes)
            if audiodata:
                buffer += audiodata.data
                duration += audiodata.duration
                timestamp += self._timestamp_offset
            else:
                self._advance()

        return AudioData(buffer, len(buffer), timestamp, duration)
