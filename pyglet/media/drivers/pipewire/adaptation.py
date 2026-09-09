"""PipeWire audio driver for pyglet.

This driver mirrors the PulseAudio driver's design:

* A ``_AudioDataBuffer`` holds decoded audio data, filled by the worker
  thread and drained by the PipeWire ``process`` callback on the main-loop
  thread.

* The PipeWire stream is created inactive and is only activated once
  playback starts (``play()``), in the same spirit as PulseAudio's corked
  streams.

Because PipeWire runs a thread loop of its own, all interactions with the
stream must hold the main-loop lock, with the notable exception of the
buffer queueing/dequeueing functions which are safe to call from the
processing thread.
"""

from __future__ import annotations

from collections import deque
import ctypes
import threading
import weakref
from typing import TYPE_CHECKING

from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer
from pyglet.media.drivers.listener import AbstractListener
from pyglet.media.player_worker_thread import PlayerWorkerThread
from pyglet.util import debug_print

from pyglet.media.drivers.pipewire import lib_pipewire as lib
from pyglet.media.drivers.pipewire.interface import PipeWireMainloop, SAMPLE_FORMATS

if TYPE_CHECKING:
    from pyglet.media.codecs import AudioData, AudioFormat, Source
    from pyglet.media.player import AudioPlayer

_debug = debug_print('debug_media')


class PipeWireDriver(AbstractAudioDriver):
    def __init__(self) -> None:
        self.mainloop = PipeWireMainloop()
        self.mainloop.start()
        self.context = None

        self.worker = PlayerWorkerThread()
        self.worker.start()
        self._players = weakref.WeakSet()
        self._listener = PipeWireListener(self)

    @property
    def sample_formats(self):
        return tuple(SAMPLE_FORMATS.keys())

    def create_audio_player(self, source: 'Source', player: 'AudioPlayer') -> 'PipeWirePlayer':
        assert self.context is not None
        player = PipeWirePlayer(source, player, self)
        self._players.add(player)
        return player

    def connect(self) -> None:
        """Connect to the local PipeWire daemon."""
        assert not self.context, 'Already connected'

        self.context = self.mainloop.create_context()
        self.context.connect()

    @staticmethod
    def dump_debug_info():
        print('Client version: ', lib.pw_get_library_version())

    def delete(self) -> None:
        """Completely shut down the PipeWire client."""
        if self.mainloop is None:
            return

        self.worker.stop()

        with self.mainloop.lock:
            if self.context is not None:
                self.context.delete()
                self.context = None

        self.mainloop.delete()
        self.mainloop = None

    def get_listener(self) -> 'PipeWireListener':
        return self._listener


class PipeWireListener(AbstractListener):
    def __init__(self, driver: 'PipeWireDriver') -> None:
        self.driver = weakref.proxy(driver)

    def _set_volume(self, volume: float) -> None:
        self._volume = volume
        for player in self.driver._players:
            player.set_volume(player._volume)

    def _set_position(self, position) -> None:
        self._position = position

    def _set_forward_orientation(self, orientation) -> None:
        self._forward_orientation = orientation

    def _set_up_orientation(self, orientation) -> None:
        self._up_orientation = orientation


class _AudioDataBuffer:
    def __init__(self, ideal_size: int, comfortable_limit: int) -> None:
        self.available = 0
        self.virtual_write_index = 0
        self._ideal_size = ideal_size
        self._comfortable_limit = comfortable_limit
        self._data: deque = deque()
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
            ctypes.memmove(target_pointer + bytes_written, cur_audio_data.pointer + self._first_read_offset, cur_write)
            bytes_written += cur_write
            bytes_remaining -= cur_write
            if packet_used:
                self._data.popleft()
                self._first_read_offset = 0
            else:
                self._first_read_offset += cur_write

        self.available -= bytes_written

        return bytes_written


class PipeWirePlayer(AbstractAudioPlayer):
    def __init__(self, source: 'Source', player: 'AudioPlayer', driver: 'PipeWireDriver') -> None:
        super().__init__(source, player)
        self.driver = driver

        self._volume = 1.0
        self._pitch = 1.0

        audio_format = source.audio_format
        assert audio_format
        self._bytes_per_frame = audio_format.bytes_per_frame

        self._latest_time = None
        self._written_frames = 0

        self._pyglet_source_exhausted = False
        self._pending_bytes = 0
        self._eos_dispatched = False
        self._draining = False

        # Only half of the ideal buffer size is kept in Python land, the
        # rest is spread across the PipeWire stream's queued buffers.
        ideal_size = audio_format.align_ceil(self._buffered_data_ideal_size // 2)
        comf_limit = audio_format.align_ceil(self._buffered_data_comfortable_limit // 2)

        self._audio_data_buffer = _AudioDataBuffer(ideal_size, comf_limit)

        # A lock that should be held whenever the audio data buffer is
        # accessed, or the shared variables, if they are shared between the
        # PipeWire process callback and the rest of the methods.
        self._audio_data_lock = threading.Lock()

        with driver.mainloop.lock:
            self.stream = driver.context.create_stream(audio_format)

        # State-change and process callbacks fire from the PipeWire main-loop thread.
        # Handlers must be attached before connect_playback() because the connect state
        # change is dispatched while it waits.
        self.stream.push_handlers(on_process=self.on_process,
                                  on_state_changed=self.on_state_changed,
                                  on_drained=self.on_drained)

        # connect_playback() manages the main-loop lock itself; it must not be called while
        # already holding it, because it waits on the thread-loop condition variable while the
        # loop dispatches the state-change handler (holding the lock again would keep the loop
        # thread from running).
        self.stream.connect_playback()
        assert _debug('PipeWirePlayer: __init__ finished')

    def on_state_changed(self, old: int, state: int, error) -> None:
        assert _debug(f'PipeWirePlayer: stream state = {self.stream._state_name.get(state, state)}')

    def on_process(self) -> None:
        # Called from the PipeWire main-loop thread.
        assert _debug('PipeWirePlayer: process')
        with self._audio_data_lock:
            self._write_buffers()

    def _write_buffers(self) -> None:
        """Fill and queue as many buffers as the stream has available."""
        if self._draining:
            # The source is exhausted and the stream is flushing its queued
            # buffers out to the device; do not hand it any more data.
            return
        while True:
            buffer = self.stream.dequeue_buffer()
            if buffer is None:
                return

            data = None
            if buffer.buffer.contents.n_datas > 0:
                data = buffer.buffer.contents.datas[0]

            if data is None:
                self.stream.return_buffer(buffer)
                continue

            maxsize = data.maxsize
            if buffer.requested > 0:
                request_size = min(buffer.requested * self._bytes_per_frame, maxsize)
            else:
                request_size = maxsize

            write_size = min(request_size, self._audio_data_buffer.available)
            if write_size > 0:
                written = self._audio_data_buffer.memmove(data.data, write_size)

                chunk = data.chunk.contents
                chunk.offset = 0
                chunk.stride = self._bytes_per_frame
                chunk.size = written

                buffer.size = written // self._bytes_per_frame
                self._written_frames += buffer.size
                self._pending_bytes = request_size - written

                self.stream.queue_buffer(buffer)
            else:
                self.stream.return_buffer(buffer)
                self._pending_bytes = request_size
                if self._pyglet_source_exhausted:
                    self._request_drain()
                return

    def _request_drain(self) -> None:
        """Flush the queued tail out to the device before ending playback.

        Dispatching EOS as soon as the source is exhausted makes the player
        pause and destroy the stream while the audio still queued in the
        graph is in flight, truncating it with an audible click. Instead the
        stream signals ``drained`` once the device has consumed that tail,
        and EOS is dispatched from there.
        """
        assert _debug('PipeWirePlayer: requesting drain')
        self._draining = True
        self.stream.drain()

    def on_drained(self) -> None:
        # Called from the PipeWire main-loop thread.
        assert _debug('PipeWirePlayer: drained')
        self._dispatch_eos()

    def _dispatch_eos(self) -> None:
        if not self._eos_dispatched:
            assert _debug('PipeWirePlayer: EOS')
            self._eos_dispatched = True
            self.dispatch_eos()

    def _maybe_fill_audio_data_buffer(self) -> None:
        # Hold the audio_data_lock when calling this.
        if self._pyglet_source_exhausted:
            return

        refill_size = self._audio_data_buffer.get_ideal_refill_size(self._pending_bytes)
        if refill_size == 0:
            return

        self._audio_data_lock.release()

        refill_size = self.source.audio_format.align(refill_size)
        assert _debug(f'PipeWirePlayer: Getting {refill_size}B of audio data')
        new_data = self._get_and_compensate_audio_data(refill_size, self._get_read_index())

        self._audio_data_lock.acquire()

        if new_data is None:
            self._pyglet_source_exhausted = True
            # The drained event dispatches EOS once the tail has played out.
        else:
            self._audio_data_buffer.add_data(new_data)

    def _update_time_info(self) -> None:
        # RT safe; safe to call from the worker thread.
        if self.stream is None:
            return
        time_info = self.stream.get_time()
        if time_info is not None:
            self._latest_time = time_info

    def work(self) -> None:
        # Called from the worker thread.
        self._update_time_info()

        with self._audio_data_lock:
            self._maybe_fill_audio_data_buffer()

    def delete(self) -> None:
        assert _debug('PipeWirePlayer.delete')
        self.driver.worker.remove(self)

        if self.driver.mainloop is None:
            assert _debug('PipeWirePlayer.delete: PipeWireDriver already deleted.')
        else:
            with self.driver.mainloop.lock:
                self.stream.delete()
                self.stream = None

    def clear(self) -> None:
        assert _debug('PipeWirePlayer.clear')
        super().clear()

        self._pyglet_source_exhausted = False
        self._eos_dispatched = False
        self._draining = False
        self._pending_bytes = 0
        self._latest_time = None

        with self._audio_data_lock:
            self._audio_data_buffer.clear()
            self._written_frames = 0

        with self.driver.mainloop.lock:
            self.stream.flush()

    def play(self) -> None:
        assert _debug('PipeWirePlayer.play')

        with self.driver.mainloop.lock:
            self.stream.set_active(True)

        self.driver.worker.add(self)

    def stop(self) -> None:
        assert _debug('PipeWirePlayer.stop')
        self.driver.worker.remove(self)

        with self.driver.mainloop.lock:
            self.stream.set_active(False)

    def get_play_cursor(self) -> int:
        return self._get_read_index()

    def _get_read_index(self) -> int:
        """Estimate the source byte offset currently presented by the DAC.

        ``struct_pw_time.ticks`` is the position the remote end of the graph
        is reading/writing, expressed in ``struct_pw_time.rate`` units (the
        graph clock, e.g. 1/48000 on a 48 kHz sink). ``ticks`` only updates
        once per graph cycle, so the position is extrapolated to the present
        with the wall clock (``pw_stream_get_nsec``), which the report's
        ``now`` is measured on; ``delay`` is subtracted since a sample only
        reaches the listener ``delay`` ns after the graph reads it.
        """
        time_info = self._latest_time
        if time_info is None or self.stream is None:
            return 0

        rate = time_info.rate
        if rate.num <= 0 or rate.denom <= 0:
            return 0

        ns_per_unit = 1e9 * rate.num / rate.denom
        if time_info.ticks == 0 and time_info.now == 0:
            return 0

        elapsed_units = (time_info.ticks
                         + (self.stream.get_nsec() - time_info.now) / ns_per_unit
                         - max(0, time_info.delay) / ns_per_unit)
        if elapsed_units <= 0:
            return 0

        # Never report a position ahead of the audio data delivered to the
        # stream (stream frames converted into graph-clock units).
        frames_delivered = self._written_frames / self.source.audio_format.sample_rate
        max_units = frames_delivered * rate.denom / rate.num
        elapsed_units = min(elapsed_units, max_units)

        seconds = elapsed_units * ns_per_unit / 1e9
        return max(0, int(seconds * self.source.audio_format.bytes_per_second))

    def set_volume(self, volume: float) -> None:
        self._volume = volume

        # The volume is applied by the graph mixer via the stream control,
        # multiplied by the master (listener) volume.
        if self.stream is not None:
            with self.driver.mainloop.lock:
                self.stream.set_control_volume(volume * self.driver._listener._volume)

    def set_pitch(self, pitch: float) -> None:
        if pitch == self._pitch:
            return
        self._pitch = pitch

        # The adaptive resampler needs to be active for this to work. When
        # it is not, the pitch simply isn't applied.
        if self.stream is not None:
            with self.driver.mainloop.lock:
                result = self.stream.set_rate(pitch)
                assert _debug(f'PipeWirePlayer: set_rate({pitch}) = {result}')

    def prefill_audio(self) -> None:
        self.work()
