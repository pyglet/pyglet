"""Object-oriented wrappers around the PipeWire ctypes bindings.

These classes wrap the low-level bindings in a way that mirrors the
PulseAudio driver's ``interface`` module. All calls into PipeWire must be
made with the main-loop lock held (via ``mainloop.lock``), unless the
function is documented to be callable from any thread.
"""

from __future__ import annotations

import sys
import weakref

from ctypes import POINTER, byref, sizeof
from typing import Callable, Optional, TYPE_CHECKING

from pyglet.media.drivers.base import AbstractAudioPlayer
from pyglet.util import debug_print
from pyglet.media.drivers.pipewire import lib_pipewire as lib
from pyglet.media.exceptions import MediaException

if TYPE_CHECKING:
    from pyglet.media.codecs import AudioFormat

_debug = debug_print('debug_media')

StreamProcessCallback = Callable[[], None]
StreamStateChangedCallback = Callable[[int, int, Optional[bytes]], None]
StreamNewBufferCallback = Callable[[int], None]
DrainedCallback = Callable[[], None]


SAMPLE_FORMATS = {"U8": {"little": lib.SPA_AUDIO_FORMAT_U8, "big": lib.SPA_AUDIO_FORMAT_U8},
                  "S16": {"little": lib.SPA_AUDIO_FORMAT_S16_LE, "big": lib.SPA_AUDIO_FORMAT_S16_BE},
                  "S24": {"little": lib.SPA_AUDIO_FORMAT_S24_LE, "big": lib.SPA_AUDIO_FORMAT_S24_BE},
                  "S32": {"little": lib.SPA_AUDIO_FORMAT_S32_LE, "big": lib.SPA_AUDIO_FORMAT_S32_BE},
                  "F32": {"little": lib.SPA_AUDIO_FORMAT_F32_LE, "big": lib.SPA_AUDIO_FORMAT_F32_BE}}


class PipeWireException(MediaException):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.message}'


class _MainloopLock:
    def __init__(self, mainloop: 'PipeWireMainloop') -> None:
        self._mainloop = mainloop

    def __enter__(self) -> None:
        lib.pw_thread_loop_lock(self._mainloop.loop)

    def __exit__(self, _exc_type, _exc_value, _tb) -> None:
        lib.pw_thread_loop_unlock(self._mainloop.loop)


class PipeWireMainloop:
    """Wrapper around a ``pw_thread_loop``.

    The loop runs on a dedicated thread and its lock must be held whenever
    interacting with PipeWire from other threads. ``wait``/``signal`` are
    used to block until a state change has been processed.
    """

    _pw_initialized: bool = False

    def __init__(self) -> None:
        self._initialize()
        self.loop = lib.pw_thread_loop_new(b'pyglet', None)
        if not self.loop:
            raise PipeWireException('Could not create PipeWire main loop.')
        self.lock = _MainloopLock(self)

    @classmethod
    def _initialize(cls) -> None:
        """Call ``pw_init`` once per process."""
        if not cls._pw_initialized:
            lib.pw_init(None, None)
            cls._pw_initialized = True

    def start(self) -> None:
        """Start running the main loop on its own thread."""
        if lib.pw_thread_loop_start(self.loop) < 0:
            raise PipeWireException('Failed to start the PipeWire main loop.')
        assert _debug('PipeWireMainloop: Started')

    def create_context(self) -> 'PipeWireContext':
        """Construct and return a new context in this mainloop."""
        return PipeWireContext(self)

    def delete(self) -> None:
        """Stop the loop and clean up its resources."""
        if self.loop is not None:
            assert _debug('PipeWireMainloop: Deleting')
            lib.pw_thread_loop_stop(self.loop)
            lib.pw_thread_loop_destroy(self.loop)
            self.loop = None

    def signal(self) -> None:
        """Wake a thread waiting on ``wait``."""
        assert self.loop is not None
        lib.pw_thread_loop_signal(self.loop, False)

    def wait(self) -> None:
        """Release the lock and wait for a signal, then reacquire it.

        Must be called with the main-loop lock held.
        """
        assert self.loop is not None
        lib.pw_thread_loop_wait(self.loop)

    def timed_wait(self, max_sec: int) -> int:
        """Like ``wait`` but returns after ``max_sec`` seconds.

        Must be called with the main-loop lock held. Returns 0 when
        signaled, or a negative error code (e.g. ``-ETIMEDOUT``).
        """
        assert self.loop is not None
        return lib.pw_thread_loop_timed_wait(self.loop, max_sec)


class PipeWireContext:
    """A connection to a PipeWire daemon.

    The context is created on top of a main loop; the associated core
    represents the client's connection to the daemon.
    """

    def __init__(self, mainloop: PipeWireMainloop) -> None:
        self.mainloop = mainloop
        self._loop = lib.pw_thread_loop_get_loop(mainloop.loop)
        assert self._loop is not None
        self._context = lib.pw_context_new(self._loop, None, 0)
        if not self._context:
            raise PipeWireException('Could not create PipeWire context.')
        self._core = None

    def connect(self, properties: Optional[dict] = None) -> None:
        """Connect the context to a PipeWire daemon."""
        props = lib.make_properties(properties) if properties else None

        with self.mainloop.lock:
            self._core = lib.pw_context_connect(self._context, props, 0)
            if not self._core:
                if props:
                    lib.pw_properties_free(props)
                raise PipeWireException('Could not connect to the PipeWire daemon.')

        assert _debug('PipeWireContext: Connected')

    @property
    def is_connected(self) -> bool:
        return self._core is not None

    def create_stream(self, audio_format: AudioFormat) -> PipeWireStream:
        """Create a new playback stream for the given audio format."""
        assert self._core is not None
        return PipeWireStream(self, audio_format)

    def delete(self) -> None:
        """Disconnect and destroy the context."""
        if self._context is None:
            return
        if self._core is not None:
            lib.pw_core_disconnect(self._core)
            self._core = None
        lib.pw_context_destroy(self._context)
        self._context = None
        self._loop = None


class PipeWireStream:
    """A PipeWire audio playback stream.

    The stream is created inactive; callers activate it with
    ``set_active(True)`` when playback should start.
    """

    _state_name = {lib.PW_STREAM_STATE_ERROR: 'Error',
                   lib.PW_STREAM_STATE_UNCONNECTED: 'Unconnected',
                   lib.PW_STREAM_STATE_CONNECTING: 'Connecting',
                   lib.PW_STREAM_STATE_PAUSED: 'Paused',
                   lib.PW_STREAM_STATE_STREAMING: 'Streaming'}

    def __init__(self, context: PipeWireContext, audio_format: AudioFormat) -> None:
        self.context = weakref.proxy(context)
        self.state = lib.PW_STREAM_STATE_UNCONNECTED

        try:
            spa_format = SAMPLE_FORMATS[audio_format.sample_format][sys.byteorder]
        except KeyError:
            raise PipeWireException(
                f'PipeWire does not support '
                f"'{audio_format.channels}-channel, "
                f'{audio_format.sample_size}-bit '
                f"{audio_format.sample_type}' audio.")

        self._audio_format = audio_format
        self._spa_format = spa_format

        stream_name = f'pyglet-{id(self):X}'
        self._properties = lib.make_properties({
            'media.type': 'Audio',
            'media.category': 'Playback',
            'media.role': 'Music',
            'node.name': stream_name,
        })

        with self.context.mainloop.lock:
            self._stream = lib.pw_stream_new(context._core, stream_name.encode('utf-8'), self._properties)
            if not self._stream:
                raise PipeWireException('Could not create PipeWire stream.')
            self._properties = None  # Ownership transferred to the stream.

            self._listener = lib.struct_spa_hook()
            self._events = lib.struct_pw_stream_events()

            self._cb_destroy = lib._pw_stream_events_destroy_t(self._on_destroy)
            self._cb_state_changed = lib._pw_stream_events_state_changed_t(self._on_state_changed)
            self._cb_process = lib._pw_stream_events_process_t(self._on_process)
            self._cb_add_buffer = lib._pw_stream_events_add_buffer_t(self._on_add_buffer)
            self._cb_remove_buffer = lib._pw_stream_events_remove_buffer_t(self._on_remove_buffer)
            self._cb_drained = lib._pw_stream_events_drained_t(self._on_drained)

            self._events.version = lib.PW_VERSION_STREAM_EVENTS
            self._events.destroy = self._cb_destroy
            self._events.state_changed = self._cb_state_changed
            self._events.process = self._cb_process
            self._events.add_buffer = self._cb_add_buffer
            self._events.remove_buffer = self._cb_remove_buffer
            self._events.drained = self._cb_drained

            self._process_callback = None
            self._state_callback = None
            self._buffer_callback = None
            self._drained_callback = None

            lib.pw_stream_add_listener(self._stream, self._listener, self._events, None)

    @property
    def is_paused(self) -> bool:
        return self.state == lib.PW_STREAM_STATE_PAUSED

    @property
    def is_streaming(self) -> bool:
        return self.state == lib.PW_STREAM_STATE_STREAMING

    @property
    def is_ready(self) -> bool:
        return self.state >= lib.PW_STREAM_STATE_PAUSED

    def _on_destroy(self, _data) -> None:
        assert _debug('PipeWireStream: destroyed')

    def _on_state_changed(self, _data, old: int, state: int, error: Optional[bytes]) -> None:
        self.state = state
        assert _debug(f'PipeWireStream: state changed to {self._state_name.get(state, state)}')
        if state == lib.PW_STREAM_STATE_ERROR:
            error_msg = error.decode('utf-8') if error else 'unknown error'
            assert _debug(f'PipeWireStream: error: {error_msg}')
        callback = self._state_callback
        if callback is not None:
            callback(old, state, error)
        self.context.mainloop.signal()

    def _on_process(self, _data) -> None:
        callback = self._process_callback
        if callback is not None:
            callback()

    def _on_add_buffer(self, _data, buffer_ptr) -> None:
        callback = self._buffer_callback
        if callback is not None:
            callback(True)

    def _on_remove_buffer(self, _data, buffer_ptr) -> None:
        callback = self._buffer_callback
        if callback is not None:
            callback(False)

    def _on_drained(self, _data) -> None:
        callback = self._drained_callback
        if callback is not None:
            callback()

    def set_process_callback(self, callback: Optional[StreamProcessCallback]) -> None:
        self._process_callback = callback

    def set_state_callback(self, callback: Optional[StreamStateChangedCallback]) -> None:
        self._state_callback = callback

    def set_buffer_callback(self, callback: Optional[StreamNewBufferCallback]) -> None:
        self._buffer_callback = callback

    def set_drained_callback(self, callback: Optional[DrainedCallback]) -> None:
        self._drained_callback = callback

    def connect_playback(self, target_latency: Optional[float] = None) -> None:
        """Connect the stream for playback, negotiating a format with the
        server. The stream stays inactive until ``set_active(True)``."""
        assert self._stream is not None

        rate = self._audio_format.sample_rate
        channels = self._audio_format.channels

        self._pod_buffer, pod = lib.make_enum_format_pod(lib.SPA_MEDIA_SUBTYPE_raw, self._spa_format, rate, channels)
        self._params = (POINTER(lib.struct_spa_pod) * 1)(pod)

        flags = (lib.PW_STREAM_FLAG_AUTOCONNECT | lib.PW_STREAM_FLAG_INACTIVE | lib.PW_STREAM_FLAG_MAP_BUFFERS)

        with self.context.mainloop.lock:
            result = lib.pw_stream_connect(self._stream, lib.PW_DIRECTION_OUTPUT, lib.PW_ID_ANY, flags, self._params, 1)
            if result < 0:
                raise PipeWireException(f'Could not connect PipeWire stream: {result}')

            self._wait_until_ready()

    def _wait_until_ready(self, timeout: int = 10) -> None:
        """Wait until the stream is at least PAUSED (format negotiated),
        or has failed. Must be called with the main-loop lock held."""
        while True:
            if self.is_ready:
                return
            if self.state == lib.PW_STREAM_STATE_ERROR:
                raise PipeWireException('PipeWire stream entered the error state.')
            result = self.context.mainloop.timed_wait(1)
            if result != 0:
                timeout -= 1
                if timeout <= 0:
                    raise PipeWireException('Timed out waiting for the PipeWire stream.')

    def delete(self) -> None:
        """Disconnect and destroy the stream."""
        if self._stream is None:
            assert _debug('PipeWireStream: No stream to delete.')
            return

        assert _debug('PipeWireStream: Deleting')
        # pw_stream_destroy fully disconnects and tears down the stream,
        # including its listeners.
        with self.context.mainloop.lock:
            lib.pw_stream_destroy(self._stream)
        self._stream = None

    def get_state(self) -> int:
        assert self._stream is not None
        return lib.pw_stream_get_state(self._stream, None)

    def get_node_id(self) -> Optional[int]:
        assert self._stream is not None
        node_id = lib.pw_stream_get_node_id(self._stream)
        return node_id if node_id != lib.PW_ID_ANY else None

    def get_time(self) -> Optional[lib.struct_pw_time]:
        """Get a snapshot of the stream time info, or None if unavailable.

        Only valid in the STREAMING state. RT safe.
        """
        assert self._stream is not None
        time_info = lib.struct_pw_time()
        if lib.pw_stream_get_time_n(self._stream, byref(time_info), sizeof(time_info)) < 0:
            return None
        return time_info

    def get_nsec(self) -> int:
        """Get the current monotonic time (nanoseconds).

        ``struct_pw_time.now`` is reported on this clock, so it can be
        used to extrapolate stream positions between ``get_time`` snapshots.
        RT safe.
        """
        assert self._stream is not None
        return lib.pw_stream_get_nsec(self._stream)

    def dequeue_buffer(self) -> Optional[lib.struct_pw_buffer]:
        """Get a buffer to fill with data. RT safe."""
        assert self._stream is not None
        buffer = lib.pw_stream_dequeue_buffer(self._stream)
        return buffer.contents if buffer else None

    def queue_buffer(self, buffer: lib.struct_pw_buffer) -> None:
        """Queue a filled buffer. RT safe."""
        assert self._stream is not None
        result = lib.pw_stream_queue_buffer(self._stream, byref(buffer))
        assert _debug(f'PipeWireStream: queued buffer, result={result}')

    def return_buffer(self, buffer: lib.struct_pw_buffer) -> None:
        """Return an unused buffer to the stream. RT safe."""
        assert self._stream is not None
        result = lib.pw_stream_return_buffer(self._stream, byref(buffer))
        assert _debug(f'PipeWireStream: returned buffer, result={result}')

    def set_active(self, active: bool) -> None:
        """Start (``True``) or stop (``False``) streaming."""
        assert self._stream is not None
        result = lib.pw_stream_set_active(self._stream, active)
        assert _debug(f'PipeWireStream: set_active({active}), result={result}')

    def flush(self) -> None:
        """Flush all queued buffers. RT safe."""
        assert self._stream is not None
        lib.pw_stream_flush(self._stream, False)

    def drain(self) -> None:
        """Flush queued buffers and wait until they have all been played.

        The ``drained`` callback is invoked once the device has consumed
        every buffer queued so far. RT safe.
        """
        assert self._stream is not None
        lib.pw_stream_flush(self._stream, True)

    def set_rate(self, rate: float) -> int:
        """Adjust the adaptive resampler rate (1.0 is the default).

        Returns an error code when the stream has no resampler.
        """
        assert self._stream is not None
        return lib.pw_stream_set_rate(self._stream, rate)
