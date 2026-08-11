"""Base abstractions shared by media audio drivers."""

from __future__ import annotations

from collections import deque
import ctypes
import weakref
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Sequence

import pyglet
from pyglet.media.codecs import AudioData
from pyglet.util import debug_print, next_or_equal_power_of_two

if TYPE_CHECKING:
    from pyglet.media.codecs import Source
    from pyglet.media import AudioPlayer
    from pyglet.media.drivers.listener import AbstractListener


_debug = debug_print('debug_media')


class SourcePrecisionBuffer:
    """Wrap non-precise sources that may over- or undershoot.

    This class's purpose is to always return data whose length is equal or
    less than the requested size, where less hints at definite source
    exhaustion.

    """

    def __init__(self, source: Source) -> None:
        """Create a buffer for a non-precise source."""
        self._source = weakref.proxy(source)
        self._buffer = bytearray()
        self._exhausted = False

    def get_audio_data(self, requested_size: int) -> AudioData | None:
        if self._exhausted:
            return None

        if len(self._buffer) < requested_size:
            # Buffer is incapable of fulfilling request, get more

            # Reduce amount of required bytes by buffer length
            required_bytes = requested_size - len(self._buffer)

            # Don't bother with super-small requests to something that likely does some form of I/O
            # Also, intentionally overshoot since some sources may just barely undercut.
            base_attempt = next_or_equal_power_of_two(max(4096, required_bytes + 16))
            attempts = (base_attempt, base_attempt, base_attempt * 2, base_attempt * 8)
            cur_attempt_idx = 0
            # A malicious decoder could technically trap us by delivering empty AudioData, though
            # the argument that this is unnecessarily defensive programming is definitely valid.
            empty_bailout = 4

            while True:
                if cur_attempt_idx + 1 < 4:  # len(attempts)
                    cur_attempt_idx += 1
                res = self._source.get_audio_data(attempts[cur_attempt_idx])

                if res is None:
                    self._exhausted = True
                elif res.length == 0:
                    empty_bailout -= 1
                    if empty_bailout <= 0:
                        self._exhausted = True
                else:
                    empty_bailout = 4
                    self._buffer += res.data

                if len(self._buffer) >= requested_size or self._exhausted:
                    break

        res = self._buffer[:requested_size]
        if not res:
            return None

        del self._buffer[:requested_size]
        return AudioData(res, len(res))

    def set_source(self, source: Source) -> None:
        self._source = weakref.proxy(source)

    def reset(self) -> None:
        self._buffer.clear()
        self._exhausted = False


class AbstractAudioPlayer(metaclass=ABCMeta):
    """Base class for driver audio players.

    It relies on a thread to regularly call a `work` method in order to operate.
    """

    audio_sync_required_measurements = 8
    audio_desync_time_critical = 0.280
    audio_desync_time_minor = 0.030
    audio_minor_desync_correction_time = 0.012

    audio_buffer_length = 0.9

    def __init__(self, source: Source, player: AudioPlayer) -> None:
        """Create a new audio player.

        Args:
            source:
                Source to play from.
            player:
                Player to receive EOS and video frame sync events.

        """
        # We only keep weakref to the player and its source to avoid
        # circular references. It's the player who owns the source and
        # the audio_player
        self.source = weakref.proxy(source)
        self.player = weakref.proxy(player)

        self._precision_buffer = None if source.is_precise() else SourcePrecisionBuffer(source)

        afmt = source.audio_format
        # How much data should ideally be in memory ready to be played.
        self._buffered_data_ideal_size = max(
            32768,
            afmt.timestamp_to_bytes_aligned(self.audio_buffer_length),
        )

        # At which point a driver should try and refill data from the source
        self._buffered_data_comfortable_limit = int(self._buffered_data_ideal_size * (2 / 3))

        # Audio synchronization
        self.desync_bytes_critical = afmt.timestamp_to_bytes_aligned(self.audio_desync_time_critical)
        self.desync_bytes_minor = afmt.timestamp_to_bytes_aligned(self.audio_desync_time_minor)
        self.desync_correction_bytes_minor = afmt.timestamp_to_bytes_aligned(self.audio_minor_desync_correction_time)

        self.audio_sync_measurements = deque(maxlen=self.audio_sync_required_measurements)
        self.audio_sync_cumul_measurements = 0

        # Bytes that have been skipped or artificially added to compensate for audio
        # desync since initialization or the last call to `clear`.
        # Negative when data was skipped, positive if it was padded in.
        self._compensated_bytes = 0

    def on_driver_destroy(self) -> None:
        """Called before the audio driver is going to be destroyed (a planned destroy)."""
        return

    def on_driver_reset(self) -> None:
        """Called after the audio driver has been re-initialized."""
        return

    @property
    def can_dispatch_eos(self) -> bool:
        """Whether this backend can currently drive end-of-stream events.

        Backends which can temporarily lose their output device may override
        this while they wait for recovery.
        """
        return True

    def set_source(self, source: Source) -> None:
        """Change the player's source for a new one.

        It must be of the same audio format.
        Will clear the player, make sure you paused it beforehand.
        """
        assert self.source.audio_format == source.audio_format

        self.clear()
        self.source = weakref.proxy(source)

        if source.is_precise():
            self._precision_buffer = None
        elif self._precision_buffer is None:
            self._precision_buffer = SourcePrecisionBuffer(source)
        else:
            self._precision_buffer.set_source(source)

    @abstractmethod
    def prefill_audio(self) -> None:
        """Prefill the audio buffer with audio data.

        This method is called before the audio player starts in order to
        have it play as soon as possible.
        """
        # It is illegal to call this method while the player is playing.

    @abstractmethod
    def work(self) -> None:
        """Runs the regular worker-thread operation.

        This method should fill the player's buffers and dispatch necessary events.
        """
        # This method is tricky to implement. See "Media manual" in pyglet's
        # development guide.

    @abstractmethod
    def play(self) -> None:
        """Begin playback."""

    @abstractmethod
    def stop(self) -> None:
        """Stop (pause) playback."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all buffered data and prepare for replacement data.

        The player must be stopped before calling this method.
        """
        self._compensated_bytes = 0
        self.audio_sync_measurements.clear()
        self.audio_sync_cumul_measurements = 0
        if self._precision_buffer is not None:
            self._precision_buffer.reset()

    @abstractmethod
    def delete(self) -> None:
        """Stop playing and clean up all resources used by player."""
        # This may be called from high level Players on shutdown after the player's driver
        # has been deleted. AudioPlayer implementations must handle this.

    @abstractmethod
    def get_play_cursor(self) -> int | None:
        """Get this player's most recent play cursor, read index, or byte offset.

        The offset starts from the last clear operation or initialization.

        ``0`` is an acceptable return value when unavailable or unknown.
        """
        # This method should not/does not need to ask the audio backend for the
        # most recent play cursor position.
        # It is not supposed to be accurate; accurate play cursor info is always
        # passed into the corresponding methods from the implementation subclass.

    def get_time(self) -> float | None:
        """Retrieve the time in the current source the player is at, in seconds.

        By default, calculated using :meth:`get_play_cursor`, divided by the
        bytes per second played.
        """
        # See notes on `get_play_cursor` as well.
        return self._raw_play_cursor_to_time(self.get_play_cursor()) + self.player.last_seek_time

    def _raw_play_cursor_to_time(self, cursor: int | None) -> float | None:
        if cursor is None:
            return None
        return self._to_perceived_play_cursor(cursor) / self.source.audio_format.bytes_per_second

    def _to_perceived_play_cursor(self, play_cursor: int) -> int:
        return play_cursor - self._compensated_bytes

    def dispatch_eos(self) -> None:
        """Notify the high-level player that this source has finished.

        Audio backends may run on worker threads, so the notification must be
        posted through the platform event loop rather than dispatched directly.
        EOS is a driver lifecycle notification, not an audio-data packet.
        """
        pyglet.app.platform_event_loop.post_event(self.player, 'on_eos')

    def _play_group(self, audio_players: Sequence[AbstractAudioPlayer]) -> None:
        """Begin simultaneous playback on a list of audio players."""
        # This should be overridden by subclasses for better synchrony.
        for player in audio_players:
            player.play()

    def _stop_group(self, audio_players: Sequence[AbstractAudioPlayer]) -> None:
        """Stop simultaneous playback on a list of audio players."""
        # This should be overridden by subclasses for better synchrony.
        for player in audio_players:
            player.stop()

    def get_audio_time_diff(self, audio_time: float | None) -> tuple[int, bool]:
        """Query the difference between audio time and the player's master clock.

        The time difference returned is calculated as an average on previous
        audio time differences.

        Return a tuple of the bytes the player is off by, aligned to correspond
        to an integer number of audio frames, as well as bool designating
        whether the difference is extreme. If it is, it should be rectified
        immediately and all previous measurements will have been cleared.

        This method will return ``0, False`` if the difference is not
        significant or ``audio_time`` is ``None``.

        :rtype: int, bool
        """
        required_measurement_count = self.audio_sync_measurements.maxlen
        if audio_time is not None:
            p_time = self.player.time
            audio_time += self.player.last_seek_time

            diff_bytes = self.source.audio_format.timestamp_to_bytes_aligned(audio_time - p_time)

            if abs(diff_bytes) >= self.desync_bytes_critical:
                self.audio_sync_measurements.clear()
                self.audio_sync_cumul_measurements = 0
                return diff_bytes, True

            if len(self.audio_sync_measurements) == required_measurement_count:
                self.audio_sync_cumul_measurements -= self.audio_sync_measurements[0]
            self.audio_sync_measurements.append(diff_bytes)
            self.audio_sync_cumul_measurements += diff_bytes

        if len(self.audio_sync_measurements) == required_measurement_count:
            avg_diff = self.source.audio_format.align(self.audio_sync_cumul_measurements // required_measurement_count)

            # print(
            #     f"{diff_bytes:>6}, {avg_diff:>6} | "
            #     f"{(diff_bytes / self.source.audio_format.bytes_per_second):>9.6f}, "
            #     f"{(avg_diff / self.source.audio_format.bytes_per_second):>9.6f}"
            # )
            if abs(avg_diff) > self.desync_bytes_minor:
                return avg_diff, False
        # else:
        #     if audio_time is not None:
        #         print(
        #             f"{diff_bytes:>6}, | "
        #             f"{(diff_bytes / self.source.audio_format.bytes_per_second):>9.6f}, "
        #         )

        return 0, False

    def _get_audio_data(self, requested_size: int) -> AudioData | None:
        if self._precision_buffer is None:
            return self.source.get_audio_data(requested_size)
        return self._precision_buffer.get_audio_data(requested_size)

    def _get_and_compensate_audio_data(
        self,
        requested_size: int,
        audio_position: int | None = None,
    ) -> AudioData | None:
        """Retrieve a packet of `AudioData` of the given size."""
        audio_time = self._raw_play_cursor_to_time(audio_position)
        desync_bytes, extreme_desync = self.get_audio_time_diff(audio_time)

        if desync_bytes == 0:
            return self._get_audio_data(requested_size)

        compensated_bytes = 0
        afmt = self.source.audio_format

        assert _debug(f"Audio desync, {desync_bytes=}, {extreme_desync=}")
        assert desync_bytes % afmt.bytes_per_frame == 0

        if desync_bytes > 0:
            # Player running ahead
            # Request at most 12ms less or only enough to not undercut the request size by 1024
            # We can't do anything if this is a major desync (other than seeking backwards later),
            # but trying to avoid seeking behind the high level player's back)
            compensated_bytes = min(
                requested_size - afmt.align_ceil(1024),
                desync_bytes,
                self.desync_correction_bytes_minor,
            )

            audio_data = self._get_audio_data(requested_size - compensated_bytes)
            if audio_data is not None:
                if audio_data.length < afmt.bytes_per_frame:
                    raise RuntimeError("Partial audio frame returned?")

                first_frame = ctypes.string_at(audio_data.pointer, afmt.bytes_per_frame)
                ad = bytearray(audio_data.length + compensated_bytes)
                ad[0:compensated_bytes] = first_frame * (compensated_bytes // afmt.bytes_per_frame)
                ad[compensated_bytes:] = audio_data.data

                audio_data = AudioData(ad, len(ad))

        elif desync_bytes < 0:
            # Player falling behind
            # Skip at most 12ms if this is a minor desync, otherwise skip the entire
            # difference. this will be noticeable, but the desync is
            # likely already noticeable in context of whatever the application does.
            compensated_bytes = (
                -desync_bytes if extreme_desync else min(-desync_bytes, self.desync_correction_bytes_minor)
            )

            audio_data = self._get_audio_data(requested_size + compensated_bytes)
            if audio_data is not None:
                if audio_data.length <= compensated_bytes:
                    compensated_bytes = -audio_data.length
                    audio_data = None
                else:
                    audio_data = AudioData(
                        ctypes.string_at(
                            audio_data.pointer + compensated_bytes,
                            audio_data.length - compensated_bytes,
                        ),
                        audio_data.length - compensated_bytes,
                    )
                    compensated_bytes *= -1

        assert _debug(f"Compensated {compensated_bytes} after audio desync")
        self._compensated_bytes += compensated_bytes

        return audio_data

    def set_volume(self, volume: float) -> None:
        """See `Player.volume`."""
        return

    def set_position(self, position: tuple[float, float, float]) -> None:
        """See :py:attr:`~pyglet.media.AudioPlayer.position`."""
        return

    def set_min_distance(self, min_distance: float) -> None:
        """See `Player.min_distance`."""
        return

    def set_max_distance(self, max_distance: float) -> None:
        """See `Player.max_distance`."""
        return

    def set_pitch(self, pitch: float) -> None:
        """See :py:attr:`~pyglet.media.AudioPlayer.pitch`."""
        return

    def set_cone_orientation(self, cone_orientation: tuple[float, float, float]) -> None:
        """See `Player.cone_orientation`."""
        return

    def set_cone_inner_angle(self, cone_inner_angle: float) -> None:
        """See `Player.cone_inner_angle`."""
        return

    def set_cone_outer_angle(self, cone_outer_angle: float) -> None:
        """See `Player.cone_outer_angle`."""
        return

    def set_cone_outer_gain(self, cone_outer_gain: float) -> None:
        """See `Player.cone_outer_gain`."""
        return


class AbstractAudioDriver(metaclass=ABCMeta):
    """Base interface for audio-driver implementations."""

    @abstractmethod
    def create_audio_player(self, source: Source, player: AudioPlayer) -> AbstractAudioPlayer:
        """Create an audio player for a source and high-level player."""

    @abstractmethod
    def get_listener(self) -> AbstractListener:
        """Return the driver's listener."""

    @property
    @abstractmethod
    def sample_formats(self) -> Sequence[str]:
        """Get list of supported sample formats ("U8", "S16", "S32", "F32")."""

    @abstractmethod
    def delete(self) -> None:
        """Release the resources held by the driver."""
