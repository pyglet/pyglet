from collections import deque
import math
import threading
from typing import Deque, Tuple, TYPE_CHECKING

from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer, MediaEvent
from pyglet.media.player_worker_thread import PlayerWorkerThread
from pyglet.media.drivers.listener import AbstractListener
from pyglet.util import debug_print
from . import interface

if TYPE_CHECKING:
    from pyglet.media.codecs import AudioData, AudioFormat, Source
    from pyglet.media.player import Player


_debug = debug_print('debug_media')


def _convert_coordinates(coordinates: Tuple[float, float, float]) -> Tuple[float, float, float]:
    x, y, z = coordinates
    return x, y, -z


class XAudio2Driver(AbstractAudioDriver):
    def __init__(self) -> None:
        self._xa2_driver = interface.XAudio2Driver()
        self._xa2_listener = self._xa2_driver.create_listener()
        self._listener = XAudio2Listener(self._xa2_listener, self._xa2_driver)

        self.worker = PlayerWorkerThread()
        self.worker.start()

    def get_performance(self) -> interface.lib.XAUDIO2_PERFORMANCE_DATA:
        assert self._xa2_driver is not None
        return self._xa2_driver.get_performance()

    def create_audio_player(self, source: 'Source', player: 'Player') -> 'XAudio2AudioPlayer':
        assert self._xa2_driver is not None
        return XAudio2AudioPlayer(self, source, player)

    def get_listener(self) -> 'XAudio2Listener':
        return self._listener

    def delete(self) -> None:
        if self._xa2_driver is not None:
            self.worker.stop()
            self.worker = None
            self._xa2_driver._delete_driver()
            self._xa2_driver = None
            self._xa2_listener = None


class XAudio2Listener(AbstractListener):
    def __init__(self, xa2_listener, xa2_driver) -> None:
        self._xa2_listener = xa2_listener
        self._xa2_driver = xa2_driver

    def _set_volume(self, volume: float) -> None:
        self._volume = volume
        self._xa2_driver.volume = volume

    def _set_position(self, position: Tuple[float, float, float]) -> None:
        self._position = position
        self._xa2_listener.position = _convert_coordinates(position)

    def _set_forward_orientation(self, orientation: Tuple[float, float, float]) -> None:
        self._forward_orientation = orientation
        self._set_orientation()

    def _set_up_orientation(self, orientation: Tuple[float, float, float]) -> None:
        self._up_orientation = orientation
        self._set_orientation()

    def _set_orientation(self) -> None:
        self._xa2_listener.orientation = (
            _convert_coordinates(self._forward_orientation) +
            _convert_coordinates(self._up_orientation))


class XAudio2AudioPlayer(AbstractAudioPlayer):
    def __init__(self, driver: 'XAudio2Driver', source: 'Source', player: 'Player') -> None:
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

        self._audio_data_in_use: Deque['AudioData'] = deque()
        self._pyglet_source_exhausted = False

        # A lock to be held whenever modifying things relating to the in-use audio data.
        # Ensures that the XAudio2 callbacks will not interfere with the
        # player operations.
        self._audio_data_lock = threading.Lock()

        self._xa2_source_voice = self.driver._xa2_driver.get_source_voice(source.audio_format, self)

    def on_driver_destroy(self) -> None:
        self.stop()
        self._xa2_source_voice = None

    def on_driver_reset(self) -> None:
        self._xa2_source_voice = self.driver._xa2_driver.get_source_voice(self.source.audio_format, self)

        # Queue up any buffers that are still in queue but weren't deleted. This does not
        # pickup where the last sample played, only where the last buffer was submitted.
        # As such, audio will be replayed.
        # TODO: Make best effort by using XAUDIO2_BUFFER.PlayBegin in conjunction
        # with last playback sample
        for audio_data in self._audio_data_in_use:
            xa2_buffer = interface.create_xa2_buffer(audio_data)
            self._xa2_source_voice.submit_buffer(xa2_buffer)

    def delete(self) -> None:
        if self.driver._xa2_driver is None:
            assert _debug("Xaudio2: Player deleted, driver is gone")
            # Driver was deleted, voice is gone; just break up some references and return
            self.driver = None
            self._xa2_source_voice = None
            self._audio_data_in_use.clear()
            return

        assert _debug("XAudio2: Player deleted, returning voice")

        self.stop()
        self.driver._xa2_driver.return_voice(self._xa2_source_voice, self._audio_data_in_use)
        self.driver = None
        self._xa2_source_voice = None

    def play(self) -> None:
        assert _debug(f'XAudio2 play: {self._playing=}')

        if not self._playing:
            self._playing = True
            self._xa2_source_voice.play()
            self.driver.worker.add(self)

        assert _debug('return XAudio2 play')

    def stop(self) -> None:
        assert _debug('XAudio2 stop')

        if self._playing:
            self.driver.worker.remove(self)
            # no callback could possibly be running after this lock is released.
            with self.driver._xa2_driver.lock:
                self._xa2_source_voice.stop()
            self._playing = False

        assert _debug('return XAudio2 stop')

    def clear(self) -> None:
        assert _debug('XAudio2 clear')
        super().clear()
        self._play_cursor = 0
        self._write_cursor = 0
        self._pyglet_source_exhausted = False
        self.driver._xa2_driver.return_voice(self._xa2_source_voice, self._audio_data_in_use)
        self._audio_data_in_use = deque()

        self._xa2_source_voice = self.driver._xa2_driver.get_source_voice(self.source.audio_format, self)
        self._xa2_source_voice.volume = self.player.volume
        self._xa2_source_voice.frequency = self.player.pitch
        if self._xa2_source_voice.is_emitter:
            self._xa2_source_voice.position = _convert_coordinates(self.player.position)
            self._xa2_source_voice.distance_scaler = self.player.min_distance
            self._xa2_source_voice.cone_orientation = _convert_coordinates(self.player.cone_orientation)
            self._xa2_source_voice.cone_outside_volume = self.player.cone_outer_gain
            self._set_cone_angles()
            self.driver._xa2_driver.apply3d(self._xa2_source_voice)

    def on_buffer_end(self, buffer_context_ptr: int) -> None:
        # Called from the XAudio2 thread.
        # A buffer stopped being played by the voice, it should by all means be the first one
        with self._audio_data_lock:
            assert self._audio_data_in_use
            self._audio_data_in_use.popleft()
            # This should cause the AudioData to lose all its references and be gc'd

            if self._audio_data_in_use:
                assert _debug(f"Buffer ended, others remain: {len(self._audio_data_in_use)=}")
                return

            assert self._xa2_source_voice.buffers_queued == 0

            if self._pyglet_source_exhausted:
                # Last buffer ran out naturally, out of AudioData; voice will now fall silent
                assert _debug("Last buffer ended normally, dispatching eos")
                MediaEvent('on_eos').sync_dispatch_to_player(self.player)
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

        self._audio_data_lock.release()
        audio_data = self._get_and_compensate_audio_data(refill_size, self._play_cursor)
        self._audio_data_lock.acquire()

        if audio_data is None:
            assert _debug(f"XAudio2: Source is out of data")
            self._pyglet_source_exhausted = True
            if not self._audio_data_in_use:
                MediaEvent('on_eos').sync_dispatch_to_player(self.player)
            return

        xa2_buffer = interface.create_xa2_buffer(audio_data)
        self._audio_data_in_use.append(audio_data)
        self._xa2_source_voice.submit_buffer(xa2_buffer)
        assert _debug(f"XAudio2: Submitted buffer of size {audio_data.length}B")

        self.append_events(self._write_cursor, audio_data.events)
        self._write_cursor += audio_data.length

    def _update_play_cursor(self) -> None:
        voice = self._xa2_source_voice
        self._play_cursor = (
            (voice.samples_played - voice.samples_played_at_last_recycle) *
            self.source.audio_format.bytes_per_frame
        )

    def get_play_cursor(self) -> int:
        return self._play_cursor

    def work(self) -> None:
        with self._audio_data_lock:
            self._update_play_cursor()
            self.dispatch_media_events(self._play_cursor)
            self._maybe_refill()

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
        with self._audio_data_lock:
            self._maybe_refill()

    def set_volume(self, volume: float) -> None:
        self._xa2_source_voice.volume = volume

    def set_position(self, position: Tuple[float, float, float]) -> None:
        if self._xa2_source_voice.is_emitter:
            self._xa2_source_voice.position = _convert_coordinates(position)

    def set_min_distance(self, min_distance: float) -> None:
        """Not a true min distance, but similar effect. Changes CurveDistanceScaler default is 1."""
        if self._xa2_source_voice.is_emitter:
            self._xa2_source_voice.distance_scaler = min_distance

    def set_max_distance(self, max_distance: float) -> None:
        """No such thing built into xaudio2"""
        return

    def set_pitch(self, pitch: float) -> None:
        self._xa2_source_voice.frequency = pitch

    def set_cone_orientation(self, cone_orientation: Tuple[float, float, float]) -> None:
        if self._xa2_source_voice.is_emitter:
            self._xa2_source_voice.cone_orientation = _convert_coordinates(cone_orientation)

    def set_cone_inner_angle(self, cone_inner_angle: float) -> None:
        if self._xa2_source_voice.is_emitter:
            self._cone_inner_angle = int(cone_inner_angle)
            self._set_cone_angles()

    def set_cone_outer_angle(self, cone_outer_angle: float) -> None:
        if self._xa2_source_voice.is_emitter:
            self._cone_outer_angle = int(cone_outer_angle)
            self._set_cone_angles()

    def _set_cone_angles(self) -> None:
        inner = min(self._cone_inner_angle, self._cone_outer_angle)
        outer = max(self._cone_inner_angle, self._cone_outer_angle)
        self._xa2_source_voice.set_cone_angles(math.radians(inner), math.radians(outer))

    def set_cone_outer_gain(self, cone_outer_gain: float) -> None:
        if self._xa2_source_voice.is_emitter:
            self._xa2_source_voice.cone_outside_volume = cone_outer_gain
