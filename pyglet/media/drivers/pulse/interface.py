import ctypes
import sys
from typing import Any, Callable, Dict, Optional, Tuple, TYPE_CHECKING, TypeVar, Union
import weakref

from pyglet.media.drivers.pulse import lib_pulseaudio as pa
from pyglet.media.exceptions import MediaException
from pyglet.util import debug_print

if TYPE_CHECKING:
    from pyglet.media.codecs import AudioData, AudioFormat

T = TypeVar('T')
PulseAudioStreamSuccessCallback = Callable[[ctypes.POINTER(pa.pa_stream), int, Any], Any]
PulseAudioStreamRequestCallback = Callable[[ctypes.POINTER(pa.pa_stream), int, Any], Any]
PulseAudioStreamNotifyCallback = Callable[[ctypes.POINTER(pa.pa_stream), Any], Any]
PulseAudioContextSuccessCallback = Callable[[ctypes.POINTER(pa.pa_context), int, Any], Any]


_debug = debug_print('debug_media')


_UINT32_MAX = 0xFFFFFFFF
_SIZE_T_MAX = sys.maxsize*2 + 1
PA_INVALID_INDEX = _UINT32_MAX
PA_INVALID_WRITABLE_SIZE = _SIZE_T_MAX


def get_uint32_or_none(value: int) -> Optional[int]:
    if value == _UINT32_MAX:
        return None
    return value


def get_bool_or_none(value: int) -> Optional[bool]:
    if value < 0:
        return None
    elif value == 1:
        return True
    else:
        return False


def get_ascii_str_or_none(value: Optional[bytes]) -> Optional[str]:
    if value is not None:
        return value.decode('ascii')
    return None


class Proplist:
    def __init__(self, ini_data: Optional[Dict[str, Union[bytes, str]]] = None) -> None:
        self._pl = pa.pa_proplist_new()
        if not self._pl:
            raise PulseAudioException(0, 'Failed creating proplist.')
        if ini_data is not None:
            for k, v in ini_data:
                self[k] = v

    def __setitem__(self, k, v):
        if isinstance(v, bytes):
            r = pa.pa_proplist_set(self._pl, k.encode("utf-8"), v, len(v))
        else:
            r = pa.pa_proplist_sets(self._pl, k.encode("utf-8"), v.encode("utf-8"))
        if r != 0:
            raise PulseAudioException(0, 'Error setting proplist entry.')

    def __delitem__(self, k):
        if pa.pa_proplist_unset(k) != 0:
            raise PulseAudioException(0, 'Error unsetting proplist entry.')

    def delete(self) -> None:
        pa.pa_proplist_free(self._pl)
        self._pl = None


class PulseAudioException(MediaException):
    def __init__(self, error_code: int, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message

    def __str__(self):
        return f'{self.__class__.__name__}: [{self.error_code}] {self.message}'

    __repr__ = __str__


class _MainloopLock:
    def __init__(self, mainloop: 'PulseAudioMainloop') -> None:
        self.mainloop = mainloop

    def __enter__(self):
        self.mainloop.lock_()

    def __exit__(self, _exc_type, _ecx_value, _tb):
        self.mainloop.unlock()


class PulseAudioMainloop:
    def __init__(self) -> None:
        self._pa_threaded_mainloop = pa.pa_threaded_mainloop_new()
        self._pa_mainloop_vtab = pa.pa_threaded_mainloop_get_api(self._pa_threaded_mainloop)
        self.lock = _MainloopLock(self)

    def start(self) -> None:
        """Start running the mainloop."""
        result = pa.pa_threaded_mainloop_start(self._pa_threaded_mainloop)
        if result < 0:
            raise PulseAudioException(0, "Failed to start PulseAudio mainloop")
        assert _debug('PulseAudioMainloop: Started')

    def delete(self) -> None:
        """Clean up the mainloop."""
        if self._pa_threaded_mainloop is not None:
            assert _debug("Delete PulseAudioMainloop")
            pa.pa_threaded_mainloop_stop(self._pa_threaded_mainloop)
            pa.pa_threaded_mainloop_free(self._pa_threaded_mainloop)
            self._pa_threaded_mainloop = None
            self._pa_mainloop_vtab = None

    def lock_(self) -> None:
        """Lock the threaded mainloop against events.  Required for all
        calls into PA."""
        assert self._pa_threaded_mainloop is not None
        pa.pa_threaded_mainloop_lock(self._pa_threaded_mainloop)

    def unlock(self) -> None:
        """Unlock the mainloop thread."""
        assert self._pa_threaded_mainloop is not None
        pa.pa_threaded_mainloop_unlock(self._pa_threaded_mainloop)

    def signal(self) -> None:
        """Signal the mainloop thread to break from a wait."""
        assert self._pa_threaded_mainloop is not None
        pa.pa_threaded_mainloop_signal(self._pa_threaded_mainloop, 0)

    def wait(self) -> None:
        """Unlock and then Wait for a signal from the locked mainloop.
        It's important to note that the PA mainloop lock is reentrant, yet this method only
        releases one lock.
        Before returning, the lock is reacquired.
        """
        assert self._pa_threaded_mainloop is not None
        pa.pa_threaded_mainloop_wait(self._pa_threaded_mainloop)

    def create_context(self) -> 'PulseAudioContext':
        """Construct and return a new context in this mainloop.
        Will grab the lock.
        """
        assert self._pa_mainloop_vtab is not None
        app_name = self._get_app_name().encode("utf-8")
        with self.lock:
            return PulseAudioContext(self, app_name)

    def _get_app_name(self) -> str:
        """Get the application name as advertised to the pulseaudio server."""
        # TODO move app name into pyglet.app (also useful for OS X menu bar?).
        return sys.argv[0]


class PulseAudioMainloopChild:
    def __init__(self, mainloop: PulseAudioMainloop):
        assert mainloop is not None
        self.mainloop = mainloop


class PulseAudioContext(PulseAudioMainloopChild):
    """Basic object for a connection to a PulseAudio server."""
    _state_name = {pa.PA_CONTEXT_UNCONNECTED: 'Unconnected',
                   pa.PA_CONTEXT_CONNECTING: 'Connecting',
                   pa.PA_CONTEXT_AUTHORIZING: 'Authorizing',
                   pa.PA_CONTEXT_SETTING_NAME: 'Setting Name',
                   pa.PA_CONTEXT_READY: 'Ready',
                   pa.PA_CONTEXT_FAILED: 'Failed',
                   pa.PA_CONTEXT_TERMINATED: 'Terminated'}

    def __init__(self, mainloop: PulseAudioMainloop, name: bytes) -> None:
        super().__init__(mainloop)

        # TODO: Filling in stuff like language, IDs and icons is possible here
        # but gateways to get them down here don't really exist.
        # pl = Proplist({}); pl.delete()
        ctx = pa.pa_context_new_with_proplist(mainloop._pa_mainloop_vtab, name, None)
        self.check_ptr_not_null(ctx)

        self._pa_context = ctx
        self.state = None

        self._set_state_callback(self._state_callback)

    def delete(self) -> None:
        """Completely shut down pulseaudio client. Will lock."""
        if self._pa_context is not None:
            with self.mainloop.lock:
                assert _debug("PulseAudioContext.delete")
                if self.is_ready:
                    pa.pa_context_disconnect(self._pa_context)

                    while self.state is not None and not self.is_terminated:
                        self.mainloop.wait()

                self._set_state_callback(0)
                pa.pa_context_unref(self._pa_context)

            self._pa_context = None

    @property
    def is_ready(self) -> bool:
        return self.state == pa.PA_CONTEXT_READY

    @property
    def is_failed(self) -> bool:
        return self.state == pa.PA_CONTEXT_FAILED

    @property
    def is_terminated(self) -> bool:
        return self.state == pa.PA_CONTEXT_TERMINATED

    @property
    def server(self) -> Optional[str]:
        if self.is_ready:
            return get_ascii_str_or_none(pa.pa_context_get_server(self._pa_context))
        return None

    @property
    def protocol_version(self) -> Optional[str]:
        if self._pa_context is not None:
            return get_uint32_or_none(pa.pa_context_get_protocol_version(self._pa_context))
        return None

    @property
    def server_protocol_version(self) -> Optional[str]:
        if self._pa_context is not None:
            return get_uint32_or_none(pa.pa_context_get_server_protocol_version(self._pa_context))
        return None

    @property
    def is_local(self) -> Optional[bool]:
        if self._pa_context is not None:
            return get_bool_or_none(pa.pa_context_is_local(self._pa_context))
        return None

    def connect(self, server: Optional[bytes] = None) -> None:
        """Connect the context to a PulseAudio server.

        Will grab the mainloop lock.

        :Parameters:
            `server` : bytes
                Server to connect to, or ``None`` for the default local
                server (which may be spawned as a daemon if no server is
                found).
        """
        assert self._pa_context is not None
        self.state = None

        with self.mainloop.lock:
            self.check(
                pa.pa_context_connect(self._pa_context, server, 0, None)
            )
            while not self.is_failed and not self.is_ready:
                self.mainloop.wait()

            if self.is_failed:
                self.raise_error()

    def create_stream(self, audio_format: 'AudioFormat') -> 'PulseAudioStream':
        """
        Create a new audio stream.
        """
        assert self.is_ready

        return PulseAudioStream(self, audio_format)

    def set_input_volume(self, stream: 'PulseAudioStream', volume: float) -> 'PulseAudioOperation':
        """
        Set the volume for a stream.
        """
        cvolume = self._get_cvolume_from_linear(stream, volume)

        clump = PulseAudioContextSuccessCallbackLump(self)
        return PulseAudioOperation(
            clump,
            pa.pa_context_set_sink_input_volume(
                self._pa_context,
                stream.index,
                cvolume,
                clump.pa_callback,
                None,
            ),
        )

    def _get_cvolume_from_linear(self, stream: 'PulseAudioStream', volume: float) -> pa.pa_cvolume:
        cvolume = pa.pa_cvolume()
        volume = pa.pa_sw_volume_from_linear(volume)
        pa.pa_cvolume_set(cvolume, stream.get_sample_spec().channels, volume)
        return cvolume

    def _set_state_callback(
        self,
        py_callback: Optional[Callable[['PulseAudioContext', Any], Any]]
    ) -> None:
        if py_callback is None:
            self._pa_state_change_callback = None
        else:
            self._pa_state_change_callback = pa.pa_context_notify_cb_t(py_callback)
        pa.pa_context_set_state_callback(self._pa_context, self._pa_state_change_callback, None)

    def _state_callback(self, context: 'PulseAudioContext', _userdata) -> None:
        self.state = pa.pa_context_get_state(self._pa_context)
        assert _debug(f'PulseAudioContext: state changed to {self._state_name[self.state]}')
        self.mainloop.signal()

    def check(self, result: T) -> T:
        if result < 0:
            self.raise_error()
        return result

    def check_not_null(self, value: T) -> T:
        if value is None:
            self.raise_error()
        return value

    def check_ptr_not_null(self, value: T) -> T:
        if not value:
            self.raise_error()
        return value

    def raise_error(self) -> None:
        error = pa.pa_context_errno(self._pa_context)
        raise PulseAudioException(error, get_ascii_str_or_none(pa.pa_strerror(error)))


class PulseAudioStream(PulseAudioMainloopChild):
    """PulseAudio audio stream."""

    _state_name = {pa.PA_STREAM_UNCONNECTED: 'Unconnected',
                   pa.PA_STREAM_CREATING: 'Creating',
                   pa.PA_STREAM_READY: 'Ready',
                   pa.PA_STREAM_FAILED: 'Failed',
                   pa.PA_STREAM_TERMINATED: 'Terminated'}

    def __init__(self, context: PulseAudioContext, audio_format: 'AudioFormat') -> None:
        super().__init__(context.mainloop)

        self.state = None
        """The stream's state."""

        self.index = None
        """The stream's sink index."""

        self.context = weakref.ref(context)

        self._cb_write = pa.pa_stream_request_cb_t(0)
        self._cb_underflow = pa.pa_stream_notify_cb_t(0)
        self._cb_state = pa.pa_stream_notify_cb_t(self._state_callback)
        self._cb_moved = pa.pa_stream_notify_cb_t(self._moved_callback)

        self._pa_stream = pa.pa_stream_new_with_proplist(
            context._pa_context,
            f'{id(self):X}'.encode("utf-8"),
            self.create_sample_spec(audio_format),
            None,  # Default channel map
            None,  # No proplist to supply
        )
        context.check_not_null(self._pa_stream)

        pa.pa_stream_set_state_callback(self._pa_stream, self._cb_state, None)
        pa.pa_stream_set_moved_callback(self._pa_stream, self._cb_moved, None)
        self._refresh_state()

    def create_sample_spec(self, audio_format: 'AudioFormat') -> pa.pa_sample_spec:
        """
        Create a PulseAudio sample spec from pyglet audio format.
        """
        _FORMATS = {
            ('little', 8):  pa.PA_SAMPLE_U8,
            ('big', 8):     pa.PA_SAMPLE_U8,
            ('little', 16): pa.PA_SAMPLE_S16LE,
            ('big', 16):    pa.PA_SAMPLE_S16BE,
            ('little', 24): pa.PA_SAMPLE_S24LE,
            ('big', 24):    pa.PA_SAMPLE_S24BE,
        }
        fmt = (sys.byteorder, audio_format.sample_size) 
        if fmt not in _FORMATS:
            raise MediaException(f'Unsupported sample size/format: {fmt}')

        sample_spec = pa.pa_sample_spec()
        sample_spec.format = _FORMATS[fmt]
        sample_spec.rate = audio_format.sample_rate
        sample_spec.channels = audio_format.channels
        return sample_spec

    def delete(self) -> None:
        """If connected, disconnect, and delete the stream."""
        context = self.context()
        if context is None:
            assert _debug("No active context anymore. Cannot disconnect the stream")
            self._pa_stream = None
            return

        if self._pa_stream is None:
            assert _debug("No stream to delete.")
            return

        assert _debug("Delete PulseAudioStream")
        if not self.is_unconnected:
            assert _debug("PulseAudioStream: disconnecting")

            context.check(
                pa.pa_stream_disconnect(self._pa_stream)
            )
            while not (self.is_terminated or self.is_failed):
                self.mainloop.wait()

        self._disconnect_callbacks()
        pa.pa_stream_unref(self._pa_stream)
        self._pa_stream = None

    @property
    def is_unconnected(self) -> bool:
        return self.state == pa.PA_STREAM_UNCONNECTED

    @property
    def is_creating(self) -> bool:
        return self.state == pa.PA_STREAM_CREATING

    @property
    def is_ready(self) -> bool:
        return self.state == pa.PA_STREAM_READY

    @property
    def is_failed(self) -> bool:
        return self.state == pa.PA_STREAM_FAILED

    @property
    def is_terminated(self) -> bool:
        return self.state == pa.PA_STREAM_TERMINATED

    def get_writable_size(self) -> int:
        assert self._pa_stream is not None

        r = pa.pa_stream_writable_size(self._pa_stream)
        if r == PA_INVALID_WRITABLE_SIZE:
            self.context().raise_error()
        return r

    def is_corked(self) -> bool:
        assert self._pa_stream is not None

        r = pa.pa_stream_is_corked(self._pa_stream)
        self.context().check(r)
        return bool(r)

    def get_sample_spec(self) -> pa.pa_sample_spec:
        assert self._pa_stream is not None
        return pa.pa_stream_get_sample_spec(self._pa_stream)[0]

    def connect_playback(self, tlength: int = _UINT32_MAX, minreq: int = _UINT32_MAX) -> None:
        context = self.context()
        assert self._pa_stream is not None
        assert context is not None

        device = None

        buffer_attr = pa.pa_buffer_attr()
        buffer_attr.fragsize = _UINT32_MAX  # Irrelevant for playback
        buffer_attr.maxlength = _UINT32_MAX
        buffer_attr.tlength = tlength
        buffer_attr.prebuf = _UINT32_MAX
        buffer_attr.minreq = minreq

        flags = (pa.PA_STREAM_START_CORKED |
                 pa.PA_STREAM_INTERPOLATE_TIMING |
                 pa.PA_STREAM_VARIABLE_RATE)

        volume = None

        sync_stream = None  # TODO use this

        context.check(
            pa.pa_stream_connect_playback(self._pa_stream,
                                          device,
                                          buffer_attr,
                                          flags,
                                          volume,
                                          sync_stream)
        )

        while not self.is_ready and not self.is_failed:
            self.mainloop.wait()
        if not self.is_ready:
            context.raise_error()

        self._refresh_sink_index()
        # ba = pa.pa_stream_get_buffer_attr(self._pa_stream).contents
        # print(f"{ba.maxlength=}, {ba.tlength=}, {ba.prebuf=}, {ba.minreq=}, {ba.fragsize=}")

        assert _debug('PulseAudioStream: Playback connected')

    def begin_write(self, nbytes: Optional[int] = None) -> Tuple[ctypes.c_void_p, int]:
        context = self.context()
        assert context is not None

        addr = ctypes.c_void_p()
        nbytes_st = ctypes.c_size_t(_SIZE_T_MAX if nbytes is None else nbytes)

        context.check(
            pa.pa_stream_begin_write(self._pa_stream, ctypes.byref(addr), ctypes.byref(nbytes_st))
        )
        context.check_ptr_not_null(addr)

        assert _debug(f"PulseAudioStream: begin_write nbytes={nbytes} nbytes_n={nbytes_st.value}")

        return addr, nbytes_st.value

    def cancel_write(self) -> None:
        self.context().check(pa.pa_stream_cancel_write(self._pa_stream))

    def write(self, data, length: int, seek_mode=pa.PA_SEEK_RELATIVE) -> int:
        context = self.context()
        assert context is not None
        assert self._pa_stream is not None
        assert self.is_ready
        assert _debug(f'PulseAudioStream: writing {length} bytes')

        context.check(
            pa.pa_stream_write(self._pa_stream, data, length, pa.pa_free_cb_t(0), 0, seek_mode)
        )
        return length

    def update_timing_info(
        self,
        callback: Optional[PulseAudioContextSuccessCallback] = None,
    ) -> 'PulseAudioOperation':
        context = self.context()
        assert context is not None
        assert self._pa_stream is not None

        clump = PulseAudioStreamSuccessCallbackLump(context, callback)
        return PulseAudioOperation(
            clump,
            pa.pa_stream_update_timing_info(self._pa_stream, clump.pa_callback, None),
        )

    def get_timing_info(self) -> Optional[pa.pa_timing_info]:
        """
        Retrieves the stream's timing_info struct,
        or None if it does not exist.
        Note that ctypes creates a copy of the struct, meaning it will
        be safe to use with an unlocked mainloop.
        """
        context = self.context()
        assert context is not None
        assert self._pa_stream is not None
        timing_info = pa.pa_stream_get_timing_info(self._pa_stream)
        return timing_info.contents if timing_info else None

    def trigger(
        self,
        callback: Optional[PulseAudioContextSuccessCallback] = None,
    ) -> 'PulseAudioOperation':
        context = self.context()
        assert context is not None
        assert self._pa_stream is not None

        clump = PulseAudioStreamSuccessCallbackLump(context, callback)
        return PulseAudioOperation(
            clump,
            pa.pa_stream_trigger(self._pa_stream, clump.pa_callback, None),
        )

    def prebuf(
        self,
        callback: Optional[PulseAudioContextSuccessCallback] = None,
    ) -> 'PulseAudioOperation':
        context = self.context()
        assert context is not None
        assert self._pa_stream is not None

        clump = PulseAudioStreamSuccessCallbackLump(context, callback)
        return PulseAudioOperation(
            clump,
            pa.pa_stream_prebuf(self._pa_stream, clump.pa_callback, None),
        )

    def flush(
        self,
        callback: Optional[PulseAudioContextSuccessCallback] = None,
    ) -> 'PulseAudioOperation':
        context = self.context()
        assert context is not None
        assert self._pa_stream is not None

        clump = PulseAudioStreamSuccessCallbackLump(context, callback)
        return PulseAudioOperation(
            clump,
            pa.pa_stream_flush(self._pa_stream, clump.pa_callback, None),
        )

    def resume(
        self,
        callback: Optional[PulseAudioContextSuccessCallback] = None,
    ) -> 'PulseAudioOperation':
        return self._cork(False, callback)

    def pause(
        self,
        callback: Optional[PulseAudioContextSuccessCallback] = None,
    ) -> 'PulseAudioOperation':
        return self._cork(True, callback)

    def _cork(
        self,
        pause: Union[int, bool],
        callback: PulseAudioContextSuccessCallback,
    ) -> 'PulseAudioOperation':
        context = self.context()
        assert context is not None
        assert self._pa_stream is not None

        clump = PulseAudioStreamSuccessCallbackLump(context, callback)
        return PulseAudioOperation(
            clump,
            pa.pa_stream_cork(self._pa_stream, pause, clump.pa_callback, None),
        )

    def update_sample_rate(
        self,
        sample_rate: int,
        callback: Optional[PulseAudioContextSuccessCallback] = None,
    ) -> 'PulseAudioOperation':
        context = self.context()
        assert context is not None
        assert self._pa_stream is not None

        clump = PulseAudioStreamSuccessCallbackLump(context, callback)
        return PulseAudioOperation(
            clump,
            pa.pa_stream_update_sample_rate(
                self._pa_stream, sample_rate, clump.pa_callback, None
            ),
        )

    def set_write_callback(self, f: PulseAudioStreamRequestCallback) -> None:
        self._cb_write = pa.pa_stream_request_cb_t(f)
        pa.pa_stream_set_write_callback(self._pa_stream, self._cb_write, None)

    def set_underflow_callback(self, f: PulseAudioStreamNotifyCallback) -> None:
        self._cb_underflow = pa.pa_stream_notify_cb_t(f)
        pa.pa_stream_set_underflow_callback(self._pa_stream, self._cb_underflow, None)

    def _connect_callbacks(self) -> None:
        s = self._pa_stream
        pa.pa_stream_set_underflow_callback(s, self._cb_underflow, None)
        pa.pa_stream_set_write_callback(s, self._cb_write, None)
        pa.pa_stream_set_state_callback(s, self._cb_state, None)
        pa.pa_stream_set_moved_callback(s, self._cb_moved, None)

    def _disconnect_callbacks(self) -> None:
        s = self._pa_stream
        pa.pa_stream_set_underflow_callback(s, pa.pa_stream_notify_cb_t(0), None)
        pa.pa_stream_set_write_callback(s, pa.pa_stream_request_cb_t(0), None)
        pa.pa_stream_set_state_callback(s, pa.pa_stream_notify_cb_t(0), None)
        pa.pa_stream_set_moved_callback(s, pa.pa_stream_notify_cb_t(0), None)

    def _state_callback(self, _stream, _userdata) -> None:
        self._refresh_state()
        assert _debug(f"PulseAudioStream: state changed to {self._state_name[self.state]}")
        self.mainloop.signal()

    def _moved_callback(self, _stream, _userdata) -> None:
        self._refresh_sink_index()
        assert _debug(f"PulseAudioStream: moved to new index {self.index}")

    def _refresh_sink_index(self) -> None:
        self.index = pa.pa_stream_get_index(self._pa_stream)
        if self.index == PA_INVALID_INDEX:
            self.context().raise_error()

    def _refresh_state(self) -> None:
        self.state = pa.pa_stream_get_state(self._pa_stream)


class PulseAudioOperation(PulseAudioMainloopChild):
    """An asynchronous PulseAudio operation.
    Can be waited for, where it will run until completion or cancellation.
    Remember to `delete()` it with the mainloop lock held, otherwise
    it will be leaked.
    """

    _state_name = {pa.PA_OPERATION_RUNNING: 'Running',
                   pa.PA_OPERATION_DONE: 'Done',
                   pa.PA_OPERATION_CANCELLED: 'Cancelled'}

    def __init__(self, callback_lump, pa_operation: pa.pa_operation) -> None:
        context = callback_lump.context

        assert context.mainloop is not None
        assert pa_operation is not None
        context.check_ptr_not_null(pa_operation)

        super().__init__(context.mainloop)

        self.callback_lump = callback_lump
        self._pa_operation = pa_operation

    def _get_state(self) -> None:
        assert self._pa_operation is not None
        return pa.pa_operation_get_state(self._pa_operation)

    def delete(self) -> None:
        """Unref and delete the operation."""
        if self._pa_operation is not None:
            pa.pa_operation_unref(self._pa_operation)
            self._pa_operation = None
            self.callback_lump = None
            self.context = None

    def cancel(self):
        """Cancel the operation."""
        assert self._pa_operation is not None
        pa.pa_operation_cancel(self._pa_operation)
        return self

    def wait(self):
        """Wait until the operation is either done or cancelled."""
        while self.is_running:
            self.mainloop.wait()
        return self

    @property
    def is_running(self) -> bool:
        return self._get_state() == pa.PA_OPERATION_RUNNING

    @property
    def is_done(self) -> bool:
        return self._get_state() == pa.PA_OPERATION_DONE

    @property
    def is_cancelled(self) -> bool:
        return self._get_state() == pa.PA_OPERATION_CANCELLED


class PulseAudioContextSuccessCallbackLump:
    def __init__(
        self,
        context: PulseAudioContext,
        callback: Optional[PulseAudioContextSuccessCallback] = None,
    ) -> None:
        self.pa_callback = pa.pa_context_success_cb_t(self._success_callback)
        self.py_callback = callback
        self.context = context

    def _success_callback(self, context, success, userdata):
        if self.py_callback is not None:
            self.py_callback(context, success, userdata)
        self.context.mainloop.signal()


class PulseAudioStreamSuccessCallbackLump:
    def __init__(
        self,
        context: PulseAudioContext,
        callback: Optional[PulseAudioContextSuccessCallback] = None,
    ) -> None:
        self.pa_callback = pa.pa_stream_success_cb_t(self._success_callback)
        self.py_callback = callback
        self.context = context

    def _success_callback(self, stream, success, userdata):
        if self.py_callback is not None:
            self.py_callback(stream, success, userdata)
        self.context.mainloop.signal()
