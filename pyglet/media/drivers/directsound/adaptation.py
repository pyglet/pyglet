import math
import ctypes

from . import interface
from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer, MediaEvent
from pyglet.media.drivers.listener import AbstractListener
from pyglet.media.player_worker_thread import PlayerWorkerThread
from pyglet.util import debug_print

_debug = debug_print('debug_media')


def _convert_coordinates(coordinates):
    x, y, z = coordinates
    return x, y, -z


def _gain2db(gain):
    """
    Convert linear gain in range [0.0, 1.0] to 100ths of dB.

    Power gain = P1/P2
    dB = 2 log(P1/P2)
    dB * 100 = 1000 * log(power gain)
    """
    if gain <= 0:
        return -10000
    return max(-10000, min(int(1000 * math.log2(min(gain, 1))), 0))


def _db2gain(db):
    """Convert 100ths of dB to linear gain."""
    return math.pow(10.0, float(db)/1000.0)


class DirectSoundDriver(AbstractAudioDriver):
    def __init__(self):
        self._ds_driver = interface.DirectSoundDriver()
        self._ds_listener = self._ds_driver.create_listener()
        self._listener = DirectSoundListener(self._ds_listener, self._ds_driver.primary_buffer)

        assert self._ds_driver is not None
        assert self._ds_listener is not None

        self.worker = PlayerWorkerThread()
        self.worker.start()

    def create_audio_player(self, source, player):
        assert self._ds_driver is not None
        return DirectSoundAudioPlayer(self, source, player)

    def get_listener(self):
        assert self._ds_driver is not None
        assert self._ds_listener is not None
        return self._listener

    def delete(self):
        if self._ds_listener is None:
            assert _debug("DirectSoundDriver.delete() on deleted driver, ignoring")
            return

        assert _debug("Deleting DirectSoundDriver")
        self.worker.stop()
        # Destroy listener before destroying driver
        self._ds_listener.delete()
        self._ds_listener = None
        self._ds_driver.delete()
        self._ds_driver = None
        assert _debug("DirectSoundDriver deleted.")


class DirectSoundListener(AbstractListener):
    def __init__(self, ds_listener, ds_primary_buffer):
        self._ds_listener = ds_listener
        self._ds_primary_buffer = ds_primary_buffer

    def _set_volume(self, volume):
        self._volume = volume
        self._ds_primary_buffer.volume = _gain2db(volume)

    def _set_position(self, position):
        self._position = position
        self._ds_listener.position = _convert_coordinates(position)

    def _set_forward_orientation(self, orientation):
        self._forward_orientation = orientation
        self._set_orientation()

    def _set_up_orientation(self, orientation):
        self._up_orientation = orientation
        self._set_orientation()

    def _set_orientation(self):
        self._ds_listener.orientation = (_convert_coordinates(self._forward_orientation)
                                         + _convert_coordinates(self._up_orientation))


class DirectSoundAudioPlayer(AbstractAudioPlayer):
    def __init__(self, driver, source, player):
        super().__init__(source, player)

        # We keep here a strong reference because the AudioDriver is anyway
        # a singleton object which will only be deleted when the application
        # shuts down. The AudioDriver does not keep a ref to the AudioPlayer.
        self.driver = driver

        # Desired play state. As the DS Buffer is just a circular buffer, it is
        # not possible to have it stop at an exact position if the source
        # should lag behind and cause it to underrun.
        self._playing = False

        # Need to cache these because pyglet API allows update separately, but
        # DSound requires both to be set at once.
        self._cone_inner_angle = 360
        self._cone_outer_angle = 360

        # Actual cursors for the circular DSBuffer. Will never exceed
        # `self._buffer_size`.
        self._play_cursor_ring = 0
        self._write_cursor_ring = 0

        # Theoretical write and play cursors for an infinite buffer.  play
        # cursor is always <= write cursor (when equal, underrun is
        # happening).
        self._write_cursor = 0
        self._play_cursor = 0

        # Cursor position of where the source ran out.
        # We are done once the play cursor crosses it.
        self._eos_cursor = None

        # Always set to just after the most recently written audio data; so
        # either undefined data or silence. The eos cursor is set to it once
        # the source is confirmed to have run out.
        self._possible_eos_cursor = 0

        # Whether the source has hit its end; protect against duplicate
        # dispatch of on_eos events.
        self._has_underrun = False

        # DSound buffer
        self._buffer_size = self._buffered_data_ideal_size
        self._ds_buffer = self.driver._ds_driver.create_buffer(source.audio_format, self._buffer_size)
        self._ds_buffer.current_position = 0

        assert self._ds_buffer.buffer_size == self._buffer_size

    def delete(self):
        if self.driver._ds_driver is not None:
            self.driver.worker.remove(self)
            self._ds_buffer.delete()

    def play(self):
        assert _debug('DirectSound play')

        if not self._playing:
            self._playing = True
            self._ds_buffer.play()

        self.driver.worker.add(self)
        assert _debug('return DirectSound play')

    def stop(self):
        assert _debug('DirectSound stop')
        self.driver.worker.remove(self)

        if self._playing:
            self._playing = False
            self._ds_buffer.stop()

        assert _debug('return DirectSound stop')

    def clear(self):
        assert _debug('DirectSound clear')
        super().clear()
        self._ds_buffer.current_position = 0
        self._play_cursor_ring = self._write_cursor_ring = 0
        self._play_cursor = self._write_cursor = 0
        self._eos_cursor = None
        self._possible_eos_cursor = 0
        self._has_underrun = False

    def get_play_cursor(self):
        return self._play_cursor

    def work(self):
        assert self._playing

        self._update_play_cursor()
        self.dispatch_media_events(self._play_cursor)

        if self._eos_cursor is None:
            self._maybe_fill()
            return

        # Source exhausted, check whether we hit the end
        if not self._has_underrun and self._play_cursor > self._eos_cursor:
            self._has_underrun = True
            assert _debug('DirectSoundAudioPlayer: Dispatching eos')
            MediaEvent('on_eos').sync_dispatch_to_player(self.player)

        # While we are still playing / waiting for the on_eos to be dispatched for
        # the player to stop, the buffer continues playing. Ensure that silence is
        # filled.
        if (used := self._get_used_buffer_space()) < self._buffered_data_comfortable_limit:
            self._write(None, self._buffer_size - used)

    def _maybe_fill(self):
        if (used := self._get_used_buffer_space()) < self._buffered_data_comfortable_limit:
            self._refill(self.source.audio_format.align(self._buffer_size - used))

    def _refill(self, size):
        """Refill the next `size` bytes in the buffer using the source.
        `size` must be aligned.
        """
        audio_data = self._get_and_compensate_audio_data(size, self._play_cursor)
        if audio_data is None:
            assert _debug('DirectSoundAudioPlayer: Out of audio data')
            if self._eos_cursor is None:
                self._eos_cursor = self._possible_eos_cursor
            self._write(None, size)

        else:
            assert _debug(f'DirectSoundAudioPlayer: Got {audio_data.length} bytes of audio data')
            self.append_events(self._write_cursor, audio_data.events)
            self._write(audio_data, size)

    def _update_play_cursor(self):
        play_cursor_ring = self._ds_buffer.current_position.play_cursor
        if play_cursor_ring < self._play_cursor_ring:
            # Wrapped around
            self._play_cursor += self._buffer_size - self._play_cursor_ring
            self._play_cursor += play_cursor_ring
        else:
            self._play_cursor += play_cursor_ring - self._play_cursor_ring
        self._play_cursor_ring = play_cursor_ring

    def _get_used_buffer_space(self):
        return max(self._write_cursor - self._play_cursor, 0)

    def _write(self, audio_data, region_size):
        """Write data into the circular DSBuffer, starting at _write_cursor_ring.
        May supply None as audio_data to only write silence.
        If the audio data is not sufficient, will fill silence afterwards.
        If too much audio data is supplied, will write as much as fits.
        """
        if region_size == 0:
            return

        if audio_data is None:
            audio_size = 0
        else:
            audio_size = min(region_size, audio_data.length)
            self._possible_eos_cursor = self._write_cursor + audio_size
            audio_ptr = audio_data.pointer

        assert _debug(f'Writing {region_size}B ({audio_size}B data, {region_size - audio_size}B silence)')

        write_ptr = self._ds_buffer.lock(self._write_cursor_ring, region_size)

        a1_size = write_ptr.audio_length_1.value
        a2_size = write_ptr.audio_length_2.value

        assert 0 < region_size <= self._buffer_size
        assert region_size == a1_size + a2_size

        a2_silence = a2_size
        s = 0x80 if self.source.audio_format.sample_size == 8 else 0

        if audio_size < a1_size:
            if audio_size > 0:
                ctypes.memmove(write_ptr.audio_ptr_1, audio_ptr, audio_size)
            ctypes.memset(write_ptr.audio_ptr_1.value + audio_size, s, a1_size - audio_size)
        else:
            if a1_size > 0:
                ctypes.memmove(write_ptr.audio_ptr_1, audio_ptr, a1_size)
            if write_ptr.audio_ptr_2 and (a2_audio := (audio_size - a1_size)) > 0:
                ctypes.memmove(write_ptr.audio_ptr_2, audio_ptr + a1_size, a2_audio)
                a2_silence -= a2_audio
        if write_ptr.audio_ptr_2 and a2_silence > 0:
            ctypes.memset(write_ptr.audio_ptr_2.value + (a2_size - a2_silence), s, a2_silence)

        self._ds_buffer.unlock(write_ptr)

        self._write_cursor += region_size
        self._write_cursor_ring += region_size
        self._write_cursor_ring %= self._buffer_size

    def set_volume(self, volume):
        self._ds_buffer.volume = _gain2db(volume)

    def set_position(self, position):
        if self._ds_buffer.is3d:
            self._ds_buffer.position = _convert_coordinates(position)

    def set_min_distance(self, min_distance):
        if self._ds_buffer.is3d:
            self._ds_buffer.min_distance = min_distance

    def set_max_distance(self, max_distance):
        if self._ds_buffer.is3d:
            self._ds_buffer.max_distance = max_distance

    def set_pitch(self, pitch):
        frequency = int(pitch * self.source.audio_format.sample_rate)
        self._ds_buffer.frequency = frequency

    def set_cone_orientation(self, cone_orientation):
        if self._ds_buffer.is3d:
            self._ds_buffer.cone_orientation = _convert_coordinates(cone_orientation)

    def set_cone_inner_angle(self, cone_inner_angle):
        if self._ds_buffer.is3d:
            self._cone_inner_angle = int(cone_inner_angle)
            self._set_cone_angles()

    def set_cone_outer_angle(self, cone_outer_angle):
        if self._ds_buffer.is3d:
            self._cone_outer_angle = int(cone_outer_angle)
            self._set_cone_angles()

    def _set_cone_angles(self):
        inner = min(self._cone_inner_angle, self._cone_outer_angle)
        outer = max(self._cone_inner_angle, self._cone_outer_angle)
        self._ds_buffer.set_cone_angles(inner, outer)

    def set_cone_outer_gain(self, cone_outer_gain):
        if self._ds_buffer.is3d:
            volume = _gain2db(cone_outer_gain)
            self._ds_buffer.cone_outside_volume = volume

    def prefill_audio(self):
        self._maybe_fill()
