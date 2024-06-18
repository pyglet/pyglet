from collections import deque
import ctypes
import threading
from typing import Deque, Optional, TYPE_CHECKING
import weakref

from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer, MediaEvent
from pyglet.media.drivers.listener import AbstractListener
from pyglet.media.player_worker_thread import PlayerWorkerThread
from pyglet.util import debug_print

from . import lib_pulseaudio as pa
from .interface import PulseAudioMainloop

if TYPE_CHECKING:
    from pyglet.media.codecs import AudioData, AudioFormat, Source
    from pyglet.media.player import Player


_debug = debug_print('debug_media')


class PulseAudioDriver(AbstractAudioDriver):
    def __init__(self) -> None:
        self.mainloop = PulseAudioMainloop()
        self.mainloop.start()
        self.context = None

        self.worker = PlayerWorkerThread()
        self.worker.start()
        self._players = weakref.WeakSet()
        self._listener = PulseAudioListener(self)

    def create_audio_player(self, source: 'Source', player: 'Player') -> 'PulseAudioPlayer':
        assert self.context is not None
        player = PulseAudioPlayer(source, player, self)
        self._players.add(player)
        return player

    def connect(self, server: Optional[bytes] = None) -> None:
        """Connect to pulseaudio server.

        :Parameters:
            `server` : bytes
                Server to connect to, or ``None`` for the default local
                server (which may be spawned as a daemon if no server is
                found).
        """
        # TODO disconnect from old
        assert not self.context, 'Already connected'

        self.context = self.mainloop.create_context()
        self.context.connect(server)

    def dump_debug_info(self):
        print('Client version: ', pa.pa_get_library_version())
        print('Server:         ', self.context.server)
        print('Protocol:       ', self.context.protocol_version)
        print('Server protocol:', self.context.server_protocol_version)
        print('Local context:  ', self.context.is_local and 'Yes' or 'No')

    def delete(self) -> None:
        """Completely shut down pulseaudio client."""
        if self.mainloop is None:
            return

        self.worker.stop()

        with self.mainloop.lock:
            if self.context is not None:
                self.context.delete()
                self.context = None

        self.mainloop.delete()
        self.mainloop = None

    def get_listener(self) -> 'PulseAudioListener':
        return self._listener


class PulseAudioListener(AbstractListener):
    def __init__(self, driver: 'PulseAudioDriver') -> None:
        self.driver = weakref.proxy(driver)

    def _set_volume(self, volume: float) -> None:
        self._volume = volume
        for player in self.driver._players:
            player.set_volume(player._volume)

    def _set_position(self, position):
        self._position = position

    def _set_forward_orientation(self, orientation):
        self._forward_orientation = orientation

    def _set_up_orientation(self, orientation):
        self._up_orientation = orientation


class _AudioDataBuffer:
    def __init__(self, ideal_size: int, comfortable_limit: int) -> None:
        self.available = 0
        self.virtual_write_index = 0
        self._ideal_size = ideal_size
        self._comfortable_limit = comfortable_limit
        self._data: Deque['AudioData'] = deque()
        self._first_read_offset = 0

    def clear(self) -> None:
        self.available = 0
        self.virtual_write_index = 0
        self._data.clear()
        self._first_read_offset = 0

    def get_ideal_refill_size(self, virtual_required: int = 0) -> int:
        virtual_available = self.available - virtual_required
        if virtual_available < self._comfortable_limit:
            return self._ideal_size - virtual_available
        return 0

    def add_data(self, d: 'AudioData') -> None:
        self._data.append(d)
        self.available += d.length
        self.virtual_write_index += d.length

    def memmove(self, target_pointer: int, num_bytes: int) -> int:
        bytes_written = 0
        bytes_remaining = num_bytes
        while bytes_remaining > 0 and self._data:
            cur_audio_data = self._data[0]
            cur_len = cur_audio_data.length - self._first_read_offset
            packet_used = cur_len <= bytes_remaining
            cur_write = min(bytes_remaining, cur_len)
            ctypes.memmove(target_pointer + bytes_written,
                           cur_audio_data.pointer + self._first_read_offset,
                           cur_write)
            bytes_written += cur_write
            bytes_remaining -= cur_write
            if packet_used:
                self._data.popleft()
                self._first_read_offset = 0
            else:
                self._first_read_offset += cur_write

        self.available -= bytes_written

        return bytes_written


class PulseAudioPlayer(AbstractAudioPlayer):
    def __init__(self, source: 'Source', player: 'Player', driver: 'PulseAudioDriver') -> None:
        super().__init__(source, player)
        self.driver = driver

        self._volume = 1.0

        audio_format = source.audio_format
        assert audio_format

        self._latest_timing_info = None
        self._last_clear_read_index = 0

        self._pyglet_source_exhausted = False
        self._pending_bytes = 0

        # PA has a playback buffer it makes requests for via callbacks, but those callbacks
        # can not decode data. The decoding happens in a PlayerWorkerThread as usual, and the
        # result is kept in an _AudioDataBuffer, splitting up the ideal size between
        # them. The data is copied when the PulseAudio buffer runs low, at which point the
        # thread will ensure refilling of the _AudioDataBuffer.
        ideal_size = audio_format.align_ceil(self._buffered_data_ideal_size // 2)
        comf_limit = audio_format.align_ceil(self._buffered_data_comfortable_limit // 2)

        self._audio_data_buffer = _AudioDataBuffer(ideal_size, comf_limit)

        # A lock that should be held whenever the audio data buffer is accessed, or
        # any variables really, if they are shared between PA callbacks and the rest of
        # implemented methods.
        # Should prevent The PA callback from interfering with the work method.
        # Don't ever acquire the PA mainloop lock when this is held, might risk a deadlock
        # if a callback runs at an unfortunate time.
        self._audio_data_lock = threading.Lock()

        self._has_underrun = False

        with driver.mainloop.lock:
            self.stream = driver.context.create_stream(audio_format)
            self.stream.set_write_callback(self._write_callback)
            self.stream.set_underflow_callback(self._underflow_callback)
            self.stream.connect_playback(ideal_size, comf_limit)
            assert self.stream.is_ready

        assert _debug('PulseAudioPlayer: __init__ finished')

    def _write_callback(self, _stream, nbytes: int, _userdata) -> None:
        # Called from within PA thread
        assert _debug(f'PulseAudioPlayer: Write requested, {nbytes}B')
        assert self.source.audio_format.align(nbytes) == nbytes

        with self._audio_data_lock:
            if self._audio_data_buffer.available > 0:
                written = self._write_to_stream(nbytes)
                if (unfulfilled := nbytes - written) > 0:
                    self._pending_bytes = unfulfilled
            else:
                self._pending_bytes = nbytes

        self.stream.mainloop.signal()

    def _underflow_callback(self, _stream, _userdata) -> None:
        # Called from within PA thread
        assert _debug('PulseAudioPlayer: underflow')
        with self._audio_data_lock:
            if self._pyglet_source_exhausted and self._audio_data_buffer.available == 0:
                MediaEvent('on_eos').sync_dispatch_to_player(self.player)
            self._has_underrun = True
        self.stream.mainloop.signal()

    def _maybe_fill_audio_data_buffer(self) -> None:
        # PA as opposed to the other backends works on requests which are relatively small (or on a
        # polling model not used here which also requires the client to adjust to an ideal remaining
        # space), so this chops up AudioData in an attempt of not hitting source.get_audio_data too
        # often.
        # Hold the audio_data_lock when calling this.
        if self._pyglet_source_exhausted:
            return

        refill_size = self._audio_data_buffer.get_ideal_refill_size(self._pending_bytes)
        if refill_size == 0:
            return

        self._audio_data_lock.release()

        refill_size = self.source.audio_format.align(refill_size)
        assert _debug(f'PulseAudioPlayer: Getting {refill_size}B of audio data')
        new_data = self._get_and_compensate_audio_data(refill_size, self._get_read_index())

        self._audio_data_lock.acquire()

        if new_data is None:
            self._pyglet_source_exhausted = True
            if self._has_underrun:
                MediaEvent('on_eos').sync_dispatch_to_player(self.player)
        else:
            self._audio_data_buffer.add_data(new_data)
            self.append_events(self._audio_data_buffer.virtual_write_index, new_data.events)

    def _write_to_stream(self, nbytes: int) -> int:
        data_ptr, bytes_accepted = self.stream.begin_write(nbytes)

        bytes_written = self._audio_data_buffer.memmove(data_ptr.value, bytes_accepted)

        if bytes_written == 0:
            self.stream.cancel_write()
        else: # elif bytes_written <= bytes_accepted:
            self.stream.write(data_ptr, bytes_written, pa.PA_SEEK_RELATIVE)

        assert _debug(f'PulseAudioPlayer: Wrote {bytes_written}/{nbytes}')
        return bytes_written

    def _update_and_get_timing_info(self) -> Optional[pa.pa_timing_info]:
        self.stream.update_timing_info().wait().delete()
        return self.stream.get_timing_info()

    def _maybe_write_pending(self) -> None:
        with self._audio_data_lock:
            if self._pending_bytes == 0 or self._audio_data_buffer.available == 0:
                return

            written = self._write_to_stream(self._pending_bytes)
            self._pending_bytes -= written
            if not self._has_underrun:
                return

            self._has_underrun = False

        # If the stream has underrun, trigger it again for immediate playback.
        # Unsure whether this is really needed, but better be safe.
        # Make sure to not hold the audio data lock, as `wait` reenters the PA loop.
        self.stream.trigger().wait().delete()

    def work(self) -> None:
        with self.driver.mainloop.lock:
            self._maybe_write_pending()
            self._latest_timing_info = self._update_and_get_timing_info()

        self.dispatch_media_events(self._get_read_index())
        with self._audio_data_lock:
            self._maybe_fill_audio_data_buffer()
        with self.driver.mainloop.lock:
            self._maybe_write_pending()

    def delete(self) -> None:
        assert _debug('PulseAudioPlayer.delete')
        self.driver.worker.remove(self)

        if self.driver.mainloop is None:
            assert _debug('PulseAudioPlayer.delete: PulseAudioDriver already deleted.')
            # This is fine otherwise. If the mainloop's gone, the context is gone too,
            # having cleaned up all its streams.
        else:
            with self.driver.mainloop.lock:
                self.stream.delete()
                self.stream = None

    def clear(self) -> None:
        assert _debug('PulseAudioPlayer.clear')
        super().clear()

        # Do not reset pending_bytes as PA doesn't always seem to issue new write
        # requests despite being flushed. Should still end up fine since PA replies with
        # how many bytes it actually accepts in `_write_to_stream`.
        # self._pending_bytes = 0
        self._pyglet_source_exhausted = False
        self._audio_data_buffer.clear()
        self._has_underrun = False

        with self.stream.mainloop.lock:
            # Just hope that the read index is frozen while we're paused.
            ti = self._update_and_get_timing_info()
            assert not ti.read_index_corrupt
            self._last_clear_read_index = ti.read_index
            self.stream.flush().wait().delete()
            self.stream.prebuf().wait().delete()

    def play(self) -> None:
        assert _debug('PulseAudioPlayer.play')

        with self.stream.mainloop.lock:
            if self.stream.is_corked():
                self.stream.resume().wait().delete()
            assert not self.stream.is_corked()

        self.driver.worker.add(self)

    def stop(self) -> None:
        assert _debug('PulseAudioPlayer.stop')
        self.driver.worker.remove(self)

        with self.stream.mainloop.lock:
            self.stream.pause().wait().delete()

    def get_play_cursor(self) -> int:
        return self._get_read_index()

    def _get_read_index(self) -> int:
        if (t_info := self._latest_timing_info) is None:
            return 0

        read_idx = t_info.read_index - self._last_clear_read_index
        # bps = self.source.audio_format.bytes_per_second
        # (t_info.transport_usec / 1000000.0) * bps -
        # (t_info.sink_usec / 1000000.0) * bps

        assert _debug(f'_get_read_index -> {read_idx}')
        return read_idx

    def set_volume(self, volume: float) -> None:
        self._volume = volume

        if self.stream:
            driver = self.driver
            volume *= driver._listener._volume
            with driver.context.mainloop.lock:
                driver.context.set_input_volume(self.stream, volume).wait().delete()

    def set_pitch(self, pitch):
        with self.stream.mainloop.lock:
            sample_rate = self.stream.get_sample_spec().rate
            self.stream.update_sample_rate(int(pitch * sample_rate)).wait().delete()

    def prefill_audio(self):
        self.work()
