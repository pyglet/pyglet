# ruff: noqa: SLF001

from __future__ import annotations
from collections import deque
import math
import threading
from typing import TYPE_CHECKING

from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer
from pyglet.media.player_worker_thread import PlayerWorkerThread
from pyglet.media.drivers.listener import AbstractListener
from pyglet.util import debug_print
from . import interface

if TYPE_CHECKING:
    from pyglet.media.codecs import AudioData, Source
    from pyglet.media.player import AudioPlayer


_debug = debug_print('debug_media')


def _convert_coordinates(coordinates: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = coordinates
    return x, y, -z


class XAudio2Driver(AbstractAudioDriver):
    def __init__(self) -> None:
        self._xa2_driver = interface.XAudio2Driver()
        self._xa2_listener = self._xa2_driver.create_listener()
        self._listener = XAudio2Listener(self._xa2_listener, self._xa2_driver)

        self.worker = PlayerWorkerThread()
        self.worker.start()

    @property
    def sample_formats(self) -> tuple[str, ...]:
        return tuple(interface.SAMPLE_FORMATS.keys())

    def get_performance(self) -> interface.lib.XAUDIO2_PERFORMANCE_DATA:
        assert self._xa2_driver is not None
        return self._xa2_driver.get_performance()

    def create_audio_player(self, source: Source, player: AudioPlayer) -> XAudio2AudioPlayer:
        assert self._xa2_driver is not None
        return XAudio2AudioPlayer(self, source, player)

    def get_listener(self) -> XAudio2Listener:
        return self._listener

    def delete(self) -> None:
        if self._xa2_driver is not None:
            self.worker.stop()
            self.worker = None
            self._xa2_driver.delete()
            self._xa2_driver = None
            self._xa2_listener = None


class XAudio2Listener(AbstractListener):
    def __init__(self, xa2_listener: interface.XAudio2Listener, xa2_driver: interface.XAudio2Driver) -> None:
        self._xa2_listener = xa2_listener
        self._xa2_driver = xa2_driver

    def _set_volume(self, volume: float) -> None:
        self._volume = volume
        self._xa2_driver.volume = volume

    def _set_position(self, position: tuple[float, float, float]) -> None:
        self._position = position
        self._xa2_listener.position = _convert_coordinates(position)

    def _set_forward_orientation(self, orientation: tuple[float, float, float]) -> None:
        self._forward_orientation = orientation
        self._set_orientation()

    def _set_up_orientation(self, orientation: tuple[float, float, float]) -> None:
        self._up_orientation = orientation
        self._set_orientation()

    def _set_orientation(self) -> None:
        self._xa2_listener.orientation = _convert_coordinates(self._forward_orientation) + _convert_coordinates(
            self._up_orientation,
        )


class XAudio2AudioPlayer(AbstractAudioPlayer):
    # The voice is absent after a critical error and after player deletion.
    # It is recreated by on_driver_reset once an output endpoint returns.
    _xa2_source_voice: interface.XA2SourceVoice | None

    def __init__(self, driver: XAudio2Driver, source: Source, player: AudioPlayer) -> None:
        super().__init__(source, player)
        # We keep here a strong reference because the AudioDriver is anyway
        # a singleton object which will only be deleted when the application
        # shuts down. The AudioDriver does not keep a ref to the AudioPlayer.
        self.driver = driver

        # Need to cache these because pyglet API allows update separately, but
        # XAudio2 requires both to be set at once.
        self._cone_inner_angle = 360
        self._cone_outer_angle = 360

        # Desired play state. (`True` doesn't necessarily mean the player is playing.
        # It may be silent due to either underrun or because a flush is in progress.)
        self._playing = False

        # Theoretical write and play cursors for an infinite buffer.  play
        # cursor is always <= write cursor (when equal, underrun is
        # happening).
        self._write_cursor = 0
        self._play_cursor = 0

        self._audio_data_in_use: deque[AudioData] = deque()
        self._pyglet_source_exhausted = False

        # Keeps the source voice and its playback data in sync when the audio
        # worker or an XAudio2 callback runs at the same time. This includes
        # queued buffers, playback position, resets, and deletion.
        self._audio_state_lock = threading.RLock()
        self._play_cursor_base = 0
        self._deleted = False

        # This can start as None if no default output device is available on startup.
        self._xa2_source_voice = self.driver._xa2_driver.get_source_voice(source.audio_format, self)

    def on_driver_destroy(self) -> None:
        # Stop worker access first. A critical engine error means voice methods
        # may already fail, so cursor capture and Stop are best-effort.
        was_playing = self._playing
        if was_playing:
            self.driver.worker.remove(self)

        with self._audio_state_lock:
            voice = self._xa2_source_voice
            if voice is not None:
                try:
                    self._update_play_cursor()
                    voice.stop()
                except OSError:
                    pass
            self._play_cursor_base = self._play_cursor
            self._xa2_source_voice = None

        # FFmpeg only fills its queues while both the audio and
        # video queues have room. Have worker make this voice keep consuming audio.
        if was_playing and self.source.video_format is not None:
            self.driver.worker.add(self)

    @property
    def can_dispatch_eos(self) -> bool:
        return self._playing and self._xa2_source_voice is not None

    def on_driver_reset(self) -> None:
        # A video player may be using the worker to consume audio
        # while no output device exists.
        if self._playing:
            self.driver.worker.remove(self)

        with self._audio_state_lock:
            if self._deleted:
                return

            # The high-level Player will call play after this event if playback
            # is still desired. Reset this even if play was requested while the
            # device was unavailable, so that call starts the new voice.
            self._playing = False
            if not self._get_and_configure_voice():
                return

            # Drop buffers that finished before the old engine stopped, and
            # begin the first remaining buffer at the last known play cursor.
            skip_bytes = max(
                0,
                self._play_cursor_base - (self._write_cursor - sum(data.length for data in self._audio_data_in_use)),
            )
            while self._audio_data_in_use and skip_bytes >= self._audio_data_in_use[0].length:
                skip_bytes -= self._audio_data_in_use.popleft().length

            for index, audio_data in enumerate(self._audio_data_in_use):
                xa2_buffer = interface.create_xa2_buffer(audio_data)
                if index == 0 and skip_bytes:
                    bytes_per_frame = self.source.audio_format.bytes_per_frame
                    xa2_buffer.PlayBegin = skip_bytes // bytes_per_frame
                    xa2_buffer.PlayLength = audio_data.length // bytes_per_frame - xa2_buffer.PlayBegin
                self._xa2_source_voice.submit_buffer(xa2_buffer)

    def delete(self) -> None:
        if self.driver is None:
            return

        # Driver shutdown stops and removes the shared worker before players
        # are deleted.  In that state the driver voices are
        # already gone, so there is nothing left for stop() to access.
        if self.driver.worker is not None:
            self.stop()
        else:
            self._playing = False

        with self._audio_state_lock:
            self._deleted = True
            xa2_driver = self.driver._xa2_driver
            if xa2_driver is None or self._xa2_source_voice is None:
                assert _debug("Xaudio2: Player deleted, driver or voice is gone")
                if xa2_driver is not None:
                    with xa2_driver.lock:
                        xa2_driver._players.discard(self)
                # Driver was deleted, voice is gone; just break up some references and return.
                self.driver = None
                self._xa2_source_voice = None
                self._audio_data_in_use.clear()
                return

            assert _debug("XAudio2: Player deleted, returning voice")

            xa2_driver.return_voice(self._xa2_source_voice, self._audio_data_in_use)
            self.driver = None
            self._xa2_source_voice = None

    def play(self) -> None:
        assert _debug(f'XAudio2 play: {self._playing=}')

        if not self._playing:
            self._playing = True
            with self._audio_state_lock:
                if self._xa2_source_voice is not None:
                    self._xa2_source_voice.play()

                needs_worker = self._xa2_source_voice is not None or self.source.video_format is not None

            if needs_worker:
                self.driver.worker.add(self)

        assert _debug('return XAudio2 play')

    def stop(self) -> None:
        assert _debug('XAudio2 stop')

        if self._playing:
            self.driver.worker.remove(self)
            with self._audio_state_lock:
                if self._xa2_source_voice is not None:
                    self._xa2_source_voice.stop()
            self._playing = False

        assert _debug('return XAudio2 stop')

    def clear(self) -> None:
        assert _debug('XAudio2 clear')
        super().clear()
        self._play_cursor = 0
        self._play_cursor_base = 0
        self._write_cursor = 0
        self._pyglet_source_exhausted = False
        with self._audio_state_lock:
            if self._xa2_source_voice is None:
                self._audio_data_in_use.clear()
                return

            self.driver._xa2_driver.return_voice(self._xa2_source_voice, self._audio_data_in_use)
            self._audio_data_in_use = deque()
            self._get_and_configure_voice()

    def _get_and_configure_voice(self) -> bool:
        voice = self.driver._xa2_driver.get_source_voice(self.source.audio_format, self)
        if voice is None:
            return False

        self._xa2_source_voice = voice
        voice.volume = self.player.volume
        voice.frequency = self.player.pitch
        if voice.is_emitter:
            voice.position = _convert_coordinates(self.player.position)
            voice.min_distance = self.player.min_distance
            voice.cone_orientation = _convert_coordinates(self.player.cone_orientation)
            voice.cone_outside_volume = self.player.cone_outer_gain
            self._set_cone_angles()
            self.driver._xa2_driver.apply3d(voice)
        return True

    def on_buffer_end(self, _buffer_context_ptr: int) -> None:
        # Called from the XAudio2 thread.
        # A buffer stopped being played by the voice, it should by all means be the first one
        with self._audio_state_lock:
            if self._deleted or self._xa2_source_voice is None:
                return
            if not self._audio_data_in_use:
                return
            self._audio_data_in_use.popleft()
            # This should cause the AudioData to lose all its references and be gc'd

            if self._audio_data_in_use:
                assert _debug(f"Buffer ended, others remain: {len(self._audio_data_in_use)=}")
                return

            assert self._xa2_source_voice.buffers_queued == 0

            if self._pyglet_source_exhausted:
                # Last buffer ran out naturally, out of AudioData; voice will now fall silent
                assert _debug("Last buffer ended normally, dispatching eos")
                self.dispatch_eos()
            else:
                # Shouldn't have ran out; supplier is running behind
                # All we can do is wait; as long as voices are not stopped via `Stop`, they will
                # immediately continue playing the new buffer once it arrives
                assert _debug("Last buffer ended normally, source is lagging behind")

    def _refill(self, refill_size: int) -> None:
        """Get one piece of AudioData and submit it to the voice.

        This method will release the lock around the call to `get_audio_data`,
        so make sure it's held upon calling.
        """
        assert _debug(f"XAudio2: Retrieving new buffer of {refill_size}B")

        self._audio_state_lock.release()
        try:
            audio_data = self._get_and_compensate_audio_data(refill_size, self._play_cursor)
        finally:  # Release lock incase decoding fails.
            self._audio_state_lock.acquire()

        if audio_data is None:
            assert _debug("XAudio2: Source is out of data")
            self._pyglet_source_exhausted = True
            if not self._audio_data_in_use:
                self.dispatch_eos()
            return

        xa2_buffer = interface.create_xa2_buffer(audio_data)
        self._audio_data_in_use.append(audio_data)
        self._xa2_source_voice.submit_buffer(xa2_buffer)
        assert _debug(f"XAudio2: Submitted buffer of size {audio_data.length}B")

        self._write_cursor += audio_data.length

    def _update_play_cursor(self) -> None:
        voice = self._xa2_source_voice
        if voice is None:
            return
        self._play_cursor = (
            self._play_cursor_base + (
                (voice.samples_played - voice.samples_played_at_last_recycle) *
                self.source.audio_format.bytes_per_frame
            )
        )

    def get_play_cursor(self) -> int:
        return self._play_cursor

    def work(self) -> None:
        with self._audio_state_lock:
            if self._xa2_source_voice is None:
                self._consume_audio_for_video()
                return
            self._update_play_cursor()
            self._maybe_refill()

    def _consume_audio_for_video(self) -> None:
        """Consume interleaved audio while video advances without an output device.

        This keeps FFmpeg able to refill the video queue still. Uses the timing of the player.
        """
        if self.source.video_format is None or self._pyglet_source_exhausted:
            return

        audio_format = self.source.audio_format
        elapsed = max(0.0, self.player.time - self.player.last_seek_time)
        self._play_cursor = audio_format.timestamp_to_bytes_aligned(elapsed)
        remaining_bytes = max(0, self._write_cursor - self._play_cursor)
        if remaining_bytes >= self._buffered_data_comfortable_limit:
            return

        requested_size = audio_format.align_ceil(self._buffered_data_ideal_size - remaining_bytes)
        self._audio_state_lock.release()
        try:
            audio_data = self._get_audio_data(requested_size)
        finally:
            self._audio_state_lock.acquire()

        if audio_data is None:
            self._pyglet_source_exhausted = True
        else:
            self._write_cursor += audio_data.length

    def _maybe_refill(self) -> bool:
        if self._pyglet_source_exhausted:
            return False

        remaining_bytes = self._write_cursor - self._play_cursor
        if remaining_bytes >= self._buffered_data_comfortable_limit:
            return False

        missing_bytes = self._buffered_data_ideal_size - remaining_bytes
        self._refill(self.source.audio_format.align_ceil(missing_bytes))
        return True

    def prefill_audio(self) -> None:
        with self._audio_state_lock:
            if self._xa2_source_voice is not None:
                self._maybe_refill()

    def set_volume(self, volume: float) -> None:
        if self._xa2_source_voice is not None:
            self._xa2_source_voice.volume = volume

    def set_position(self, position: tuple[float, float, float]) -> None:
        if self._xa2_source_voice is not None and self._xa2_source_voice.is_emitter:
            self._xa2_source_voice.position = _convert_coordinates(position)

    def set_min_distance(self, min_distance: float) -> None:
        """Not a true min distance, but similar effect. Changes CurveDistanceScaler default is 1."""
        if self._xa2_source_voice is not None and self._xa2_source_voice.is_emitter:
            self._xa2_source_voice.min_distance = min_distance

    def set_max_distance(self, _max_distance: float) -> None:
        """No such thing built into xaudio2."""
        return

    def set_pitch(self, pitch: float) -> None:
        if self._xa2_source_voice is not None:
            self._xa2_source_voice.frequency = pitch

    def set_cone_orientation(self, cone_orientation: tuple[float, float, float]) -> None:
        if self._xa2_source_voice is not None and self._xa2_source_voice.is_emitter:
            self._xa2_source_voice.cone_orientation = _convert_coordinates(cone_orientation)

    def set_cone_inner_angle(self, cone_inner_angle: float) -> None:
        if self._xa2_source_voice is not None and self._xa2_source_voice.is_emitter:
            self._cone_inner_angle = int(cone_inner_angle)
            self._set_cone_angles()

    def set_cone_outer_angle(self, cone_outer_angle: float) -> None:
        if self._xa2_source_voice is not None and self._xa2_source_voice.is_emitter:
            self._cone_outer_angle = int(cone_outer_angle)
            self._set_cone_angles()

    def _set_cone_angles(self) -> None:
        if self._xa2_source_voice is None:
            return
        inner = min(self._cone_inner_angle, self._cone_outer_angle)
        outer = max(self._cone_inner_angle, self._cone_outer_angle)
        self._xa2_source_voice.set_cone_angles(math.radians(inner), math.radians(outer))

    def set_cone_outer_gain(self, cone_outer_gain: float) -> None:
        if self._xa2_source_voice is not None and self._xa2_source_voice.is_emitter:
            self._xa2_source_voice.cone_outside_volume = cone_outer_gain
