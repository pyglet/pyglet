import math
import ctypes

from . import interface
from pyglet.util import debug_print
from pyglet.media.mediathreads import PlayerWorkerThread
from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer, MediaEvent
from pyglet.media.drivers.listener import AbstractListener

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


class DirectSoundAudioPlayer(AbstractAudioPlayer):
    # Need to cache these because pyglet API allows update separately, but
    # DSound requires both to be set at once.
    _cone_inner_angle = 360
    _cone_outer_angle = 360

    min_buffer_size = 9600

    def __init__(self, driver, ds_driver, source, player):
        super(DirectSoundAudioPlayer, self).__init__(source, player)

        # We keep here a strong reference because the AudioDriver is anyway
        # a singleton object which will only be deleted when the application
        # shuts down. The AudioDriver does not keep a ref to the AudioPlayer.
        self.driver = driver
        self._ds_driver = ds_driver

        # Desired play state (may be actually paused due to underrun -- not
        # implemented yet).
        self._playing = False

        # Up to one audio data may be buffered if too much data was received
        # from the source that could not be written immediately into the
        # buffer.  See _refill().
        self._audiodata_buffer = None

        # Theoretical write and play cursors for an infinite buffer.  play
        # cursor is always <= write cursor (when equal, underrun is
        # happening).
        self._write_cursor = 0
        self._play_cursor = 0

        # Cursor position of end of data.  Silence is written after
        # eos for one buffer size.
        self._eos_cursor = None

        # Whether the source has hit its end; protect against duplicate
        # dispatch of on_eos events.
        self._has_underrun = False

        # Indexes into DSound circular buffer.  Complications ensue wrt each
        # other to avoid writing over the play cursor.  See _get_write_size and
        # write().
        self._play_cursor_ring = 0
        self._write_cursor_ring = 0

        # List of (play_cursor, MediaEvent), in sort order
        self._events = []

        # List of (cursor, timestamp), in sort order (cursor gives expiry
        # place of the timestamp)
        self._timestamps = []

        audio_format = source.audio_format

        # DSound buffer
        self._ds_buffer = self._ds_driver.create_buffer(audio_format)
        self._buffer_size = self._ds_buffer.buffer_size

        self._ds_buffer.current_position = 0

        self._refill(self._buffer_size)

    def __del__(self):
        # We decrease the IDirectSound refcount
        self.driver._ds_driver._native_dsound.Release()

    def delete(self):
        self.driver.worker.remove(self)

    def play(self):
        assert _debug('DirectSound play')

        if not self._playing:
            self._playing = True
            self._get_audiodata()  # prebuffer if needed
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
        super(DirectSoundAudioPlayer, self).clear()
        self._ds_buffer.current_position = 0
        self._play_cursor_ring = self._write_cursor_ring = 0
        self._play_cursor = self._write_cursor
        self._eos_cursor = None
        self._audiodata_buffer = None
        self._has_underrun = False
        del self._events[:]
        del self._timestamps[:]

    def refill_buffer(self):
        write_size = self._get_write_size()
        if write_size > self.min_buffer_size:
            self._refill(write_size)
            return True
        return False

    def _refill(self, write_size):
        while write_size > 0:
            assert _debug('_refill, write_size =', write_size)
            audio_data = self._get_audiodata()

            if audio_data is not None:
                assert _debug('write', audio_data.length)
                length = min(write_size, audio_data.length)
                self.write(audio_data, length)
                write_size -= length
            else:
                assert _debug('write silence')
                self.write(None, write_size)
                write_size = 0

    def _dispatch_new_event(self, event_name):
        MediaEvent(event_name).sync_dispatch_to_player(self.player)

    def _get_audiodata(self):
        if self._audiodata_buffer is None or self._audiodata_buffer.length == 0:
            self._get_new_audiodata()

        return self._audiodata_buffer

    def _get_new_audiodata(self):
        assert _debug('Getting new audio data buffer.')
        # Pass a reference of ourself to allow the audio decoding to get time
        # information for synchronization.
        compensation_time = self.get_audio_time_diff()
        self._audiodata_buffer = self.source.get_audio_data(self._buffer_size, compensation_time)

        if self._audiodata_buffer is not None:
            assert _debug('New audio data available: {} bytes'.format(self._audiodata_buffer.length))

            if self._eos_cursor is not None:
                self._move_write_cursor_after_eos()

            self._add_audiodata_events(self._audiodata_buffer)
            self._add_audiodata_timestamp(self._audiodata_buffer)
            self._eos_cursor = None
        elif self._eos_cursor is None:
            assert _debug('No more audio data.')
            self._eos_cursor = self._write_cursor

    def _move_write_cursor_after_eos(self):
        # Set the write cursor back to eos_cursor or play_cursor to prevent gaps
        if self._play_cursor < self._eos_cursor:
            cursor_diff = self._write_cursor - self._eos_cursor
            assert _debug('Moving cursor back', cursor_diff)
            self._write_cursor = self._eos_cursor
            self._write_cursor_ring -= cursor_diff
            self._write_cursor_ring %= self._buffer_size

        else:
            cursor_diff = self._play_cursor - self._eos_cursor
            assert _debug('Moving cursor back', cursor_diff)
            self._write_cursor = self._play_cursor
            self._write_cursor_ring -= cursor_diff
            self._write_cursor_ring %= self._buffer_size

    def _add_audiodata_events(self, audio_data):
        for event in audio_data.events:
            event_cursor = self._write_cursor + event.timestamp * \
                           self.source.audio_format.bytes_per_second
            assert _debug('Adding event', event, 'at', event_cursor)
            self._events.append((event_cursor, event))

    def _add_audiodata_timestamp(self, audio_data):
        ts_cursor = self._write_cursor + audio_data.length
        self._timestamps.append(
            (ts_cursor, audio_data.timestamp + audio_data.duration))

    def update_play_cursor(self):
        play_cursor_ring = self._ds_buffer.current_position.play_cursor
        if play_cursor_ring < self._play_cursor_ring:
            # Wrapped around
            self._play_cursor += self._buffer_size - self._play_cursor_ring
            self._play_cursor_ring = 0
        self._play_cursor += play_cursor_ring - self._play_cursor_ring
        self._play_cursor_ring = play_cursor_ring

        self._dispatch_pending_events()
        self._cleanup_timestamps()
        self._check_underrun()

    def _dispatch_pending_events(self):
        pending_events = []
        while self._events and self._events[0][0] <= self._play_cursor:
            _, event = self._events.pop(0)
            pending_events.append(event)
        assert _debug('Dispatching pending events: {}'.format(pending_events))
        assert _debug('Remaining events: {}'.format(self._events))

        for event in pending_events:
            event.sync_dispatch_to_player(self.player)

    def _cleanup_timestamps(self):
        while self._timestamps and self._timestamps[0][0] < self._play_cursor:
            del self._timestamps[0]

    def _check_underrun(self):
        if (
            not self._has_underrun and
            self._playing and
            (self._eos_cursor is not None and self._play_cursor > self._eos_cursor)
        ):
            assert _debug('underrun, stopping')
            self._has_underrun = True
            self._dispatch_new_event('on_eos')

    def _get_write_size(self):
        self.update_play_cursor()

        play_cursor = self._play_cursor
        write_cursor = self._write_cursor

        return self._buffer_size - max(write_cursor - play_cursor, 0)

    def write(self, audio_data, length):
        # Pass audio_data=None to write silence
        if length == 0:
            return 0

        write_ptr = self._ds_buffer.lock(self._write_cursor_ring, length)
        assert 0 < length <= self._buffer_size
        assert length == write_ptr.audio_length_1.value + write_ptr.audio_length_2.value

        if audio_data:
            ctypes.memmove(write_ptr.audio_ptr_1, audio_data.data, write_ptr.audio_length_1.value)
            audio_data.consume(write_ptr.audio_length_1.value, self.source.audio_format)
            if write_ptr.audio_length_2.value > 0:
                ctypes.memmove(write_ptr.audio_ptr_2, audio_data.data, write_ptr.audio_length_2.value)
                audio_data.consume(write_ptr.audio_length_2.value, self.source.audio_format)
        else:
            if self.source.audio_format.sample_size == 8:
                c = 0x80
            else:
                c = 0
            ctypes.memset(write_ptr.audio_ptr_1, c, write_ptr.audio_length_1.value)
            if write_ptr.audio_length_2.value > 0:
                ctypes.memset(write_ptr.audio_ptr_2, c, write_ptr.audio_length_2.value)
        self._ds_buffer.unlock(write_ptr)

        self._write_cursor += length
        self._write_cursor_ring += length
        self._write_cursor_ring %= self._buffer_size

    def get_time(self):
        self.update_play_cursor()
        if self._timestamps:
            cursor, ts = self._timestamps[0]
            result = ts + (self._play_cursor - cursor) / float(self.source.audio_format.bytes_per_second)
        else:
            result = None

        return result

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
        write_size = self._get_write_size()
        self._refill(write_size)


class DirectSoundDriver(AbstractAudioDriver):
    def __init__(self):
        self._ds_driver = interface.DirectSoundDriver()
        self._ds_listener = self._ds_driver.create_listener()

        assert self._ds_driver is not None
        assert self._ds_listener is not None

        self.worker = PlayerWorkerThread()
        self.worker.start()

    def __del__(self):
        self.delete()

    def create_audio_player(self, source, player):
        assert self._ds_driver is not None
        # We increase IDirectSound refcount for each AudioPlayer instantiated
        # This makes sure the AudioPlayer still has a valid _native_dsound to
        # clean-up itself during tear-down.
        self._ds_driver._native_dsound.AddRef()
        return DirectSoundAudioPlayer(self, self._ds_driver, source, player)

    def get_listener(self):
        assert self._ds_driver is not None
        assert self._ds_listener is not None
        return DirectSoundListener(self._ds_listener, self._ds_driver.primary_buffer)

    def delete(self):
        if hasattr(self, 'worker'):
            self.worker.stop()
        # Make sure the _ds_listener is deleted before the _ds_driver
        self._ds_listener = None


class DirectSoundListener(AbstractListener):
    def __init__(self, ds_listener, ds_buffer):
        self._ds_listener = ds_listener
        self._ds_buffer = ds_buffer

    def _set_volume(self, volume):
        self._volume = volume
        self._ds_buffer.volume = _gain2db(volume)

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
