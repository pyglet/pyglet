import weakref

from . import interface
from pyglet.util import debug_print
from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer, MediaEvent
from pyglet.media.mediathreads import PlayerWorkerThread
from pyglet.media.drivers.listener import AbstractListener

_debug = debug_print('debug_media')


class OpenALDriver(AbstractAudioDriver):
    def __init__(self, device_name=None):
        super().__init__()

        self.device = interface.OpenALDevice(device_name)
        self.context = self.device.create_context()
        self.context.make_current()

        self._listener = OpenALListener(self)

        self.worker = PlayerWorkerThread()
        self.worker.start()

    def __del__(self):
        assert _debug("Delete OpenALDriver")
        self.delete()

    def create_audio_player(self, source, player):
        assert self.device is not None, "Device was closed"
        return OpenALAudioPlayer(self, source, player)

    def delete(self):
        self.worker.stop()
        self.context = None

    def have_version(self, major, minor):
        return (major, minor) <= self.get_version()

    def get_version(self):
        assert self.device is not None, "Device was closed"
        return self.device.get_version()

    def get_extensions(self):
        assert self.device is not None, "Device was closed"
        return self.device.get_extensions()

    def have_extension(self, extension):
        return extension in self.get_extensions()

    def get_listener(self):
        return self._listener


class OpenALListener(AbstractListener):
    def __init__(self, driver):
        self._driver = weakref.proxy(driver)
        self._al_listener = interface.OpenALListener()

    def __del__(self):
        assert _debug("Delete OpenALListener")

    def _set_volume(self, volume):
        self._al_listener.gain = volume
        self._volume = volume

    def _set_position(self, position):
        self._al_listener.position = position
        self._position = position

    def _set_forward_orientation(self, orientation):
        self._al_listener.orientation = orientation + self._up_orientation
        self._forward_orientation = orientation

    def _set_up_orientation(self, orientation):
        self._al_listener.orientation = self._forward_orientation + orientation
        self._up_orientation = orientation


class OpenALAudioPlayer(AbstractAudioPlayer):
    #: Minimum size of an OpenAL buffer worth bothering with, in bytes
    min_buffer_size = 512

    #: Aggregate (desired) buffer size, in seconds
    _ideal_buffer_size = 1.0

    def __init__(self, driver, source, player):
        super(OpenALAudioPlayer, self).__init__(source, player)
        self.driver = driver
        self.alsource = driver.context.create_source()

        # Cursor positions, like DSound and Pulse drivers, refer to a
        # hypothetical infinite-length buffer.  Cursor units are in bytes.

        # Cursor position of current (head) AL buffer
        self._buffer_cursor = 0

        # Estimated playback cursor position (last seen)
        self._play_cursor = 0

        # Cursor position of end of queued AL buffer.
        self._write_cursor = 0

        # List of currently queued buffer sizes (in bytes)
        self._buffer_sizes = []

        # List of currently queued buffer timestamps
        self._buffer_timestamps = []

        # Timestamp at end of last written buffer (timestamp to return in case
        # of underrun)
        self._underrun_timestamp = None

        # List of (cursor, MediaEvent)
        self._events = []

        # Desired play state (True even if stopped due to underrun)
        self._playing = False

        # When clearing, the play cursor can be incorrect
        self._clearing = False

        # Up to one audio data may be buffered if too much data was received
        # from the source that could not be written immediately into the
        # buffer.  See _refill().
        self._audiodata_buffer = None

        self._refill(self.ideal_buffer_size)

    def __del__(self):
        self.delete()

    def delete(self):
        self.driver.worker.remove(self)
        self.alsource = None

    @property
    def ideal_buffer_size(self):
        return int(self._ideal_buffer_size * self.source.audio_format.bytes_per_second)

    def play(self):
        assert _debug('OpenALAudioPlayer.play()')

        assert self.driver is not None
        assert self.alsource is not None

        if not self.alsource.is_playing:
            self.alsource.play()
        self._playing = True
        self._clearing = False

        self.driver.worker.add(self)

    def stop(self):
        self.driver.worker.remove(self)
        assert _debug('OpenALAudioPlayer.stop()')
        assert self.driver is not None
        assert self.alsource is not None
        self.alsource.pause()
        self._playing = False

    def clear(self):
        assert _debug('OpenALAudioPlayer.clear()')

        assert self.driver is not None
        assert self.alsource is not None

        super().clear()
        self.alsource.stop()
        self._handle_processed_buffers()
        self.alsource.clear()
        self.alsource.byte_offset = 0
        self._playing = False
        self._clearing = True
        self._audiodata_buffer = None

        self._buffer_cursor = 0
        self._play_cursor = 0
        self._write_cursor = 0
        del self._events[:]
        del self._buffer_sizes[:]
        del self._buffer_timestamps[:]

    def _update_play_cursor(self):
        assert self.driver is not None
        assert self.alsource is not None

        self._handle_processed_buffers()

        # Update play cursor using buffer cursor + estimate into current buffer
        if self._clearing:
            self._play_cursor = self._buffer_cursor
        else:
            self._play_cursor = self._buffer_cursor + self.alsource.byte_offset
        assert self._check_cursors()

        self._dispatch_events()

    def _handle_processed_buffers(self):
        processed = self.alsource.unqueue_buffers()

        if processed > 0:
            if (len(self._buffer_timestamps) == processed
                    and self._buffer_timestamps[-1] is not None):
                assert _debug('OpenALAudioPlayer: Underrun')
                # Underrun, take note of timestamp.
                # We check that the timestamp is not None, because otherwise
                # our source could have been cleared.
                self._underrun_timestamp = self._buffer_timestamps[-1] + \
                    self._buffer_sizes[-1] / float(self.source.audio_format.bytes_per_second)
            self._update_buffer_cursor(processed)

        return processed

    def _update_buffer_cursor(self, processed):
        self._buffer_cursor += sum(self._buffer_sizes[:processed])
        del self._buffer_sizes[:processed]
        del self._buffer_timestamps[:processed]

    def _dispatch_events(self):
        while self._events and self._events[0][0] <= self._play_cursor:
            _, event = self._events.pop(0)
            event.sync_dispatch_to_player(self.player)

    def _get_write_size(self):
        self._update_play_cursor()
        buffer_size = int(self._write_cursor - self._play_cursor)

        # Only write when current buffer size is smaller than ideal
        write_size = max(self.ideal_buffer_size - buffer_size, 0)

        assert _debug("Write size {} bytes".format(write_size))
        return write_size

    def refill_buffer(self):
        write_size = self._get_write_size()
        if write_size > self.min_buffer_size:
            self._refill(write_size)
            return True
        return False

    def _refill(self, write_size):
        assert _debug('_refill', write_size)

        while write_size > self.min_buffer_size:
            audio_data = self._get_audiodata()

            if audio_data is None:
                break

            length = min(write_size, audio_data.length)
            if length == 0:
                assert _debug('Empty AudioData. Discard it.')

            else:
                assert _debug('Writing {} bytes'.format(length))
                self._queue_audio_data(audio_data, length)
                write_size -= length

        # Check for underrun stopping playback
        if self._playing and not self.alsource.is_playing:
            assert _debug('underrun')
            self.alsource.play()

    def _get_audiodata(self):
        if self._audiodata_buffer is None or self._audiodata_buffer.length == 0:
            self._get_new_audiodata()

        return self._audiodata_buffer

    def _get_new_audiodata(self):
        assert _debug('Getting new audio data buffer.')
        compensation_time = self.get_audio_time_diff()
        self._audiodata_buffer= self.source.get_audio_data(self.ideal_buffer_size, compensation_time)

        if self._audiodata_buffer is not None:
            assert _debug('New audio data available: {} bytes'.format(self._audiodata_buffer.length))
            self._queue_events(self._audiodata_buffer)
        else:
            assert _debug('No audio data left')
            if self._has_underrun():
                assert _debug('Underrun')
                MediaEvent('on_eos').sync_dispatch_to_player(self.player)

    def _queue_audio_data(self, audio_data, length):
        buf = self.alsource.get_buffer()
        buf.data(audio_data, self.source.audio_format, length)
        self.alsource.queue_buffer(buf)
        self._update_write_cursor(audio_data, length)

    def _update_write_cursor(self, audio_data, length):
        self._write_cursor += length
        self._buffer_sizes.append(length)
        self._buffer_timestamps.append(audio_data.timestamp)
        audio_data.consume(length, self.source.audio_format)
        assert self._check_cursors()

    def _queue_events(self, audio_data):
        for event in audio_data.events:
            cursor = self._write_cursor + event.timestamp * \
                self.source.audio_format.bytes_per_second
            self._events.append((cursor, event))

    def _has_underrun(self):
        return self.alsource.buffers_queued == 0

    def get_time(self):
        # Update first, might remove buffers
        self._update_play_cursor()

        if not self._buffer_timestamps:
            timestamp = self._underrun_timestamp
            assert _debug('OpenALAudioPlayer: Return underrun timestamp')
        else:
            timestamp = self._buffer_timestamps[0]
            assert _debug('OpenALAudioPlayer: Buffer timestamp: {}'.format(timestamp))

            if timestamp is not None:
                timestamp += ((self._play_cursor - self._buffer_cursor) /
                    float(self.source.audio_format.bytes_per_second))

        assert _debug('OpenALAudioPlayer: get_time = {}'.format(timestamp))

        return timestamp

    def _check_cursors(self):
        assert self._play_cursor >= 0
        assert self._buffer_cursor >= 0
        assert self._write_cursor >= 0
        assert self._buffer_cursor <= self._play_cursor
        assert self._play_cursor <= self._write_cursor
        assert _debug('Buffer[{}], Play[{}], Write[{}]'.format(self._buffer_cursor,
                                                                     self._play_cursor,
                                                                     self._write_cursor))
        return True  # Return true so it can be called in an assert (and optimized out)

    def set_volume(self, volume):
        self.alsource.gain = volume

    def set_position(self, position):
        self.alsource.position = position

    def set_min_distance(self, min_distance):
        self.alsource.reference_distance = min_distance

    def set_max_distance(self, max_distance):
        self.alsource.max_distance = max_distance

    def set_pitch(self, pitch):
        self.alsource.pitch = pitch

    def set_cone_orientation(self, cone_orientation):
        self.alsource.direction = cone_orientation

    def set_cone_inner_angle(self, cone_inner_angle):
        self.alsource.cone_inner_angle = cone_inner_angle

    def set_cone_outer_angle(self, cone_outer_angle):
        self.alsource.cone_outer_angle = cone_outer_angle

    def set_cone_outer_gain(self, cone_outer_gain):
        self.alsource.cone_outer_gain = cone_outer_gain

    def prefill_audio(self):
        write_size = self._get_write_size()
        self._refill(write_size)
