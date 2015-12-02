# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------
from __future__ import print_function
from __future__ import absolute_import

import ctypes
import sys

from . import lib_pulseaudio as pa
from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer
from pyglet.media.events import MediaEvent
from pyglet.media.exceptions import MediaException
from pyglet.media.listener import AbstractListener

import pyglet
_debug = pyglet.options['debug_media']


def get_uint32_or_none(value):
    # Check for max uint32
    if value is None or value == 4294967295:
        return None
    return value


def get_bool_or_none(value):
    if value < 0:
        return None
    elif value == 1:
        return True
    else:
        return False


def get_ascii_str_or_none(value):
    if value is not None:
        return value.decode('ascii')
    return None


def to_void_pointer(obj):
    if obj is None:
        return None
    return ctypes.byref(ctypes.py_object(obj))

def from_void_pointer(ptr):
    if not ptr:
        return None
    return ctypes.cast(ptr, ctypes.py_object).value


class PulseAudioException(MediaException):
    def __init__(self, error_code, message):
        super(PulseAudioException, self).__init__(message)
        self.error_code = error_code
        self.message = message

    def __str__(self):
        return '{}: [{}] {}'.format(self.__class__.__name__,
                                    self.error_code,
                                    self.message)

    __repr__ = __str__


class PulseAudioMainLoop(object):
    def __init__(self):
        self._pa_threaded_mainloop = pa.pa_threaded_mainloop_new()
        self._pa_mainloop = pa.pa_threaded_mainloop_get_api(
            self._pa_threaded_mainloop)

    def __del__(self):
        self.delete()

    def start(self):
        """Start running the mainloop."""
        with self:
            result = pa.pa_threaded_mainloop_start(self._pa_threaded_mainloop)
            if result < 0:
                raise PulseAudioException(0, "Failed to start PulseAudio mainloop")
            if _debug:
                print('PulseAudioMainLoop: Started')

    def delete(self):
        """Clean up the mainloop."""
        if self._pa_threaded_mainloop is not None:
            if _debug:
                print("PulseAudioMainLoop.delete")
            pa.pa_threaded_mainloop_stop(self._pa_threaded_mainloop)
            pa.pa_threaded_mainloop_free(self._pa_threaded_mainloop)
            self._pa_threaded_mainloop = None
            self._pa_mainloop = None

    def lock(self):
        """Lock the threaded mainloop against events.  Required for all
        calls into PA."""
        assert self._pa_threaded_mainloop is not None
        pa.pa_threaded_mainloop_lock(self._pa_threaded_mainloop)

    def unlock(self):
        """Unlock the mainloop thread."""
        assert self._pa_threaded_mainloop is not None
        pa.pa_threaded_mainloop_unlock(self._pa_threaded_mainloop)

    def signal(self):
        """Signal the mainloop thread to break from a wait."""
        assert self._pa_threaded_mainloop is not None
        pa.pa_threaded_mainloop_signal(self._pa_threaded_mainloop, 0)

    def wait(self):
        """Wait for a signal."""
        assert self._pa_threaded_mainloop is not None
        pa.pa_threaded_mainloop_wait(self._pa_threaded_mainloop)

    def create_context(self):
        return PulseAudioContext(self, self._context_new())

    def _context_new(self):
        """Construct a new context in this mainloop."""
        assert self._pa_mainloop is not None
        app_name = self._get_app_name()
        return pa.pa_context_new(self._pa_mainloop, app_name.encode('ASCII'))

    def _get_app_name(self):
        """Get the application name as advertised to the pulseaudio server."""
        # TODO move app name into pyglet.app (also useful for OS X menu bar?).
        return sys.argv[0]

    def __enter__(self):
        self.lock()

    def __exit__(self, exc_type, exc_value, traceback):
        self.unlock()


class PulseAudioLockable(object):
    def __init__(self, mainloop):
        assert mainloop is not None
        self.mainloop = mainloop

    def lock(self):
        """Lock the threaded mainloop against events.  Required for all
        calls into PA."""
        self.mainloop.lock()

    def unlock(self):
        """Unlock the mainloop thread."""
        self.mainloop.unlock()

    def signal(self):
        """Signal the mainloop thread to break from a wait."""
        self.mainloop.signal()

    def wait(self):
        """Wait for a signal."""
        self.mainloop.wait()

    def __enter__(self):
        self.lock()

    def __exit__(self, exc_type, exc_value, traceback):
        self.unlock()


class PulseAudioContext(PulseAudioLockable):
    """Basic object for a connection to a PulseAudio server."""
    _state_name = {pa.PA_CONTEXT_UNCONNECTED: 'Unconnected',
                   pa.PA_CONTEXT_CONNECTING: 'Connecting',
                   pa.PA_CONTEXT_AUTHORIZING: 'Authorizing',
                   pa.PA_CONTEXT_SETTING_NAME: 'Setting Name',
                   pa.PA_CONTEXT_READY: 'Ready',
                   pa.PA_CONTEXT_FAILED: 'Failed',
                   pa.PA_CONTEXT_TERMINATED: 'Terminated'}

    def __init__(self, mainloop, pa_context):
        super(PulseAudioContext, self).__init__(mainloop)
        self._pa_context = pa_context
        self.state = None

        self._connect_callbacks()

    def __del__(self):
        if self._pa_context is not None:
            with self:
                self.delete()

    def delete(self):
        """Completely shut down pulseaudio client."""
        if self._pa_context is not None:
            if _debug:
                print("PulseAudioContext.delete")
            pa.pa_context_disconnect(self._pa_context)
            pa.pa_context_unref(self._pa_context)
            while self.state is not None and not self.is_terminated:
                self.mainloop.wait()
            self._pa_context = None

    @property
    def is_ready(self):
        return self.state == pa.PA_CONTEXT_READY

    @property
    def is_failed(self):
        return self.state == pa.PA_CONTEXT_FAILED

    @property
    def is_terminated(self):
        return self.state == pa.PA_CONTEXT_TERMINATED

    @property
    def server(self):
        if self.is_ready:
            return get_ascii_str_or_none(pa.pa_context_get_server(self._pa_context))
        else:
            return None

    @property
    def protocol_version(self):
        if self._pa_context is not None:
            return get_uint32_or_none(pa.pa_context_get_protocol_version(self._pa_context))

    @property
    def server_protocol_version(self):
        if self._pa_context is not None:
            return get_uint32_or_none(pa.pa_context_get_server_protocol_version(self._pa_context))

    @property
    def is_local(self):
        if self._pa_context is not None:
            return get_bool_or_none(pa.pa_context_is_local(self._pa_context))

    def connect(self, server=None):
        """Connect the context to a PulseAudio server.

        :Parameters:
            `server` : str
                Server to connect to, or ``None`` for the default local
                server (which may be spawned as a daemon if no server is
                found).
        """
        assert self._pa_context is not None
        self.state = None
        self.check(
            pa.pa_context_connect(self._pa_context, server, 0, None)
        )

        while not self.is_failed and not self.is_ready:
            self.wait()
        if self.is_failed:
            self.raise_error()


    def create_stream(self, audio_format):
        """
        Create a new audio stream.
        """
        assert self.is_ready

        sample_spec = self.create_sample_spec(audio_format)
        channel_map = None

        # TODO It is now recommended to use pa_stream_new_with_proplist()
        stream = pa.pa_stream_new(self._pa_context,
                                  str(id(self)).encode('ASCII'),
                                  sample_spec,
                                  channel_map)
        self.check_not_null(stream)
        return PulseAudioStream(self.mainloop, self, stream)

    def create_sample_spec(self, audio_format):
        """
        Create a PulseAudio sample spec from pyglet audio format.
        """
        sample_spec = pa.pa_sample_spec()
        if audio_format.sample_size == 8:
            sample_spec.format = pa.PA_SAMPLE_U8
        elif audio_format.sample_size == 16:
            if sys.byteorder == 'little':
                sample_spec.format = pa.PA_SAMPLE_S16LE
            else:
                sample_spec.format = pa.PA_SAMPLE_S16BE
        else:
            raise MediaException('Unsupported sample size')
        sample_spec.rate = audio_format.sample_rate
        sample_spec.channels = audio_format.channels
        return sample_spec

    def set_input_volume(self, stream, volume):
        """
        Set the volume for a stream.
        """
        cvolume = self._get_cvolume_from_linear(stream, volume)
        with self:
            idx = stream.index
            op = pa.pa_context_set_sink_volume(self._pa_context,
                                               idx,
                                               cvolume,
                                               self._success_cb_func,
                                               None)
        return op

    def _get_cvolume_from_linear(self, stream, volume):
        cvolume = pa.pa_cvolume()
        volume = pa.pa_sw_volume_from_linear(volume)
        pa.pa_cvolume_set(cvolume,
                          stream.audio_format.channels,
                          volume)
        return cvolume

    def _connect_callbacks(self):
        self._state_cb_func = pa.pa_context_notify_cb_t(self._state_callback)
        pa.pa_context_set_state_callback(self._pa_context,
                                        self._state_cb_func, None)

    def _state_callback(self, context, userdata):
        self.state = pa.pa_context_get_state(self._pa_context)
        if _debug:
            print('PulseAudioContext: state changed to {}'.format(self._state_name[self.state]))
        self.signal()

    def check(self, result):
        if result < 0:
            self.raise_error()
        return result

    def check_not_null(self, value):
        if value is None:
            self.raise_error()
        return value

    def check_ptr_not_null(self, value):
        if not value:
            self.raise_error()
        return value

    def raise_error(self):
        error = pa.pa_context_errno(self._pa_context)
        raise PulseAudioException(error, get_ascii_str_or_none(pa.pa_strerror(error)))


class PulseAudioStream(PulseAudioLockable, pyglet.event.EventDispatcher):
    """PulseAudio audio stream."""

    _state_name = {pa.PA_STREAM_UNCONNECTED: 'Unconnected',
                   pa.PA_STREAM_CREATING: 'Creating',
                   pa.PA_STREAM_READY: 'Ready',
                   pa.PA_STREAM_FAILED: 'Failed',
                   pa.PA_STREAM_TERMINATED: 'Terminated'}

    def __init__(self, mainloop, context, pa_stream):
        PulseAudioLockable.__init__(self, mainloop)
        self._pa_stream = pa_stream
        self.context = context
        self.state = None
        self.underflow = False

        pa.pa_stream_ref(self._pa_stream)
        self._connect_callbacks()
        self._refresh_state()

    def __del__(self):
        if self._pa_stream is not None:
            with self:
                self.delete()

    def delete(self):
        if self._pa_stream is not None:
            if _debug:
                print("PulseAudioStream.delete")
                print('PulseAudioStream: writable_size {}'.format(self.writable_size))
            if not self.is_unconnected:
                self.context.check(
                    pa.pa_stream_disconnect(self._pa_stream)
                    )
                while not self.is_terminated:
                    self.wait()

            pa_stream = self._pa_stream
            self._pa_stream = None
            pa.pa_stream_unref(pa_stream)

    @property
    def is_unconnected(self):
        return self.state == pa.PA_STREAM_UNCONNECTED

    @property
    def is_creating(self):
        return self.state == pa.PA_STREAM_CREATING

    @property
    def is_ready(self):
        return self.state == pa.PA_STREAM_READY

    @property
    def is_failed(self):
        return self.state == pa.PA_STREAM_FAILED

    @property
    def is_terminated(self):
        return self.state == pa.PA_STREAM_TERMINATED

    @property
    def writable_size(self):
        assert self._pa_stream is not None
        return pa.pa_stream_writable_size(self._pa_stream)

    @property
    def index(self):
        assert self._pa_stream is not None
        return pa.pa_stream_get_index(self._pa_stream)

    @property
    def is_corked(self):
        assert self._pa_stream is not None
        return get_bool_or_none(pa.pa_stream_is_corked(self._pa_stream))

    def connect_playback(self):
        assert self._pa_stream is not None
        device = None
        buffer_attr = None
        flags = (pa.PA_STREAM_START_CORKED |
                 pa.PA_STREAM_INTERPOLATE_TIMING |
                 pa.PA_STREAM_VARIABLE_RATE)
        volume = None
        sync_stream = None  # TODO use this
        self.context.check(
            pa.pa_stream_connect_playback(self._pa_stream,
                                          device,
                                          buffer_attr,
                                          flags,
                                          volume,
                                          sync_stream)
        )

        while not self.is_ready and not self.is_failed:
            self.wait()
        if not self.is_ready:
            self.context.raise_error()
        if _debug:
            print('PulseAudioStream: Playback connected')

    def write(self, audio_data, length=None, seek_mode=pa.PA_SEEK_RELATIVE):
        assert self._pa_stream is not None
        assert self.is_ready
        if length is None:
            length = min(audio_data.length, self.writable_size)
        if _debug:
            print('PulseAudioStream: writing {} bytes'.format(length))
            print('PulseAudioStream: writable size before write {} bytes'.format(self.writable_size))
        self.context.check(
                pa.pa_stream_write(self._pa_stream,
                                   audio_data.data,
                                   length,
                                   pa.pa_free_cb_t(0),  # Data is copied
                                   0,
                                   seek_mode)
                )
        if _debug:
            print('PulseAudioStream: writable size after write {} bytes'.format(self.writable_size))
        self.underflow = False
        return length

    def update_timing_info(self, callback=None):
        assert self._pa_stream is not None
        op = PulseAudioOperation(self.context, callback)
        op.execute(
                pa.pa_stream_update_timing_info(self._pa_stream,
                                                op.pa_callback,
                                                None)
                )
        return op

    def get_timing_info(self):
        assert self._pa_stream is not None
        timing_info = self.context.check_ptr_not_null(
                pa.pa_stream_get_timing_info(self._pa_stream)
                )
        return timing_info.contents

    def trigger(self, callback=None):
        assert self._pa_stream is not None
        op = PulseAudioOperation(self.context)
        op.execute(
                pa.pa_stream_trigger(self._pa_stream,
                                     op.pa_callback,
                                     None)
                )
        return op

    def prebuf(self, callback=None):
        assert self._pa_stream is not None
        op = PulseAudioOperation(self.context)
        op.execute(
                pa.pa_stream_prebuf(self._pa_stream,
                                    op.pa_callback,
                                    None)
                )
        return op

    def resume(self, callback=None):
        return self._cork(False, callback)

    def pause(self, callback=None):
        return self._cork(True, callback)

    def update_sample_rate(self, sample_rate, callback=None):
        assert self._pa_stream is not None
        op = PulseAudioOperation(self.context)
        op.execute(
                pa.pa_stream_update_sample_rate(self._pa_stream,
                                                int(sample_rate),
                                                op.pa_callback,
                                                None)
                )
        return op

    def _cork(self, pause, callback):
        assert self._pa_stream is not None
        op = PulseAudioOperation(self.context)
        op.execute(
            pa.pa_stream_cork(self._pa_stream,
                              1 if pause else 0,
                              op.pa_callback,
                              None)
            )
        return op

    def _connect_callbacks(self):
        self._cb_underflow = pa.pa_stream_notify_cb_t(self._underflow_callback)
        self._cb_write = pa.pa_stream_request_cb_t(self._write_callback)
        self._cb_state = pa.pa_stream_notify_cb_t(self._state_callback)

        pa.pa_stream_set_underflow_callback(self._pa_stream, self._cb_underflow, None)
        pa.pa_stream_set_write_callback(self._pa_stream, self._cb_write, None)
        pa.pa_stream_set_state_callback(self._pa_stream, self._cb_state, None)

    def _underflow_callback(self, stream, userdata):
        if _debug:
            print("PulseAudioStream: underflow")
        self.underflow = True
        self._write_needed()
        self.signal()

    def _write_callback(self, stream, nbytes, userdata):
        if _debug:
            print("PulseAudioStream: write requested")
        self._write_needed(nbytes)
        self.signal()

    def _state_callback(self, stream, userdata):
        self._refresh_state()
        if _debug:
            print("PulseAudioStream: state changed to {}".format(self._state_name[self.state]))
        self.signal()

    def _refresh_state(self):
        if self._pa_stream is not None:
            self.state = pa.pa_stream_get_state(self._pa_stream)

    def _write_needed(self, nbytes=None):
        if nbytes is None:
            nbytes = self.writable_size
        ret = self.dispatch_event('on_write_needed', nbytes, self.underflow)

    def on_write_needed(self, nbytes, underflow):
        """A write is requested from PulseAudio.
        Called from the PulseAudio mainloop, so no locking required.

        :event:
        """

PulseAudioStream.register_event_type('on_write_needed')


class PulseAudioOperation(PulseAudioLockable):
    """Asynchronous PulseAudio operation"""

    _state_name = {pa.PA_OPERATION_RUNNING: 'Running',
                   pa.PA_OPERATION_DONE: 'Done',
                   pa.PA_OPERATION_CANCELLED: 'Cancelled'}

    def __init__(self, context, callback=None, pa_operation=None):
        PulseAudioLockable.__init__(self, context.mainloop)
        self.context = context
        self._callback = callback
        self.pa_callback = pa.pa_stream_success_cb_t(self._success_callback)
        if pa_operation is not None:
            self.execute(pa_operation)
        else:
            self._pa_operation = None

    def __del__(self):
        if self._pa_operation is not None:
            with self:
                self.delete()

    def delete(self):
        if self._pa_operation is not None:
            if _debug:
                print("PulseAudioOperation.delete({})".format(id(self)))
            pa.pa_operation_unref(self._pa_operation)
            self._pa_operation = None

    def execute(self, pa_operation):
        self.context.check_ptr_not_null(pa_operation)
        if _debug:
            print("PulseAudioOperation.execute({})".format(id(self)))
        self._pa_operation = pa_operation
        self._get_state()
        return self

    def cancel(self):
        assert self._pa_operation is not None
        pa.pa_operation_cancel(self._pa_operation)
        return self

    @property
    def is_running(self):
        return self._get_state() == pa.PA_OPERATION_RUNNING

    @property
    def is_done(self):
        return self._get_state() == pa.PA_OPERATION_DONE

    @property
    def is_cancelled(self):
        return self._get_state() == pa.PA_OPERATION_CANCELLED

    def wait(self):
        """Wait until operation is either done or cancelled."""
        while self.is_running:
            super(PulseAudioOperation, self).wait()
        return self

    def _get_state(self):
        assert self._pa_operation is not None
        return pa.pa_operation_get_state(self._pa_operation)

    def _success_callback(self, stream, success, userdata):
        if self._callback:
            self._callback()
        self.signal()


class PulseAudioDriver(AbstractAudioDriver):
    def __init__(self):
        self.mainloop = PulseAudioMainLoop()
        self.mainloop.start()
        self.lock = self.mainloop
        self.context = None

        self._players = pyglet.app.WeakSet()
        self._listener = PulseAudioListener(self)

    def create_audio_player(self, source_group, player):
        assert self.context is not None
        player = PulseAudioPlayer(source_group, player, self)
        self._players.add(player)
        return player

    def connect(self, server=None):
        """Connect to pulseaudio server.

        :Parameters:
            `server` : str
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

    def delete(self):
        """Completely shut down pulseaudio client."""
        #TODO: Delete players
        self.context.delete()
        self.context = None

        self.mainloop.delete()
        self.mainloop = None
        self.lock = None

    def get_listener(self):
        return self._listener


class PulseAudioListener(AbstractListener):
    def __init__(self, driver):
        self.driver = driver

    def _set_volume(self, volume):
        self._volume = volume
        for player in self.driver._players:
            player.set_volume(player._volume)

    def _set_position(self, position):
        self._position = position

    def _set_forward_orientation(self, orientation):
        self._forward_orientation = orientation

    def _set_up_orientation(self, orientation):
        self._up_orientation = orientation


class PulseAudioPlayer(AbstractAudioPlayer):
    _volume = 1.0

    def __init__(self, source_group, player, driver):
        super(PulseAudioPlayer, self).__init__(source_group, player)
        self.driver = driver
        self.context = driver.context

        self._events = []
        self._timestamps = []  # List of (ref_time, timestamp)
        self._write_index = 0  # Current write index (tracked manually)
        self._read_index_valid = False # True only if buffer has non-stale data

        self._clear_write = False
        self._buffered_audio_data = None
        self._playing = False

        self._current_audio_data = None

        self._time_sync_operation = None

        audio_format = source_group.audio_format
        assert audio_format

        with self.context.mainloop:
            self.stream = self.context.create_stream(audio_format)
            self.stream.push_handlers(self)
            self.stream.connect_playback()
            assert self.stream.is_ready

        if _debug:
            print('PulseAudioPlayer: __init__ finished')

    def on_write_needed(self, nbytes, underflow):
        if underflow:
            self._handle_underflow()
        else:
            self._write_to_stream(nbytes)

        # Asynchronously update time
        if self._events:
            if self._time_sync_operation is not None and self._time_sync_operation.is_done:
                self._time_sync_operation.delete()
                self._time_sync_operation = None
            if self._time_sync_operation is None:
                if _debug:
                    print('PulseAudioPlayer: trigger timing info update')
                self._time_sync_operation = self.stream.update_timing_info(self._process_events)

    def _get_audio_data(self, nbytes=None):
        if self._current_audio_data is None and self.source_group is not None:
            # Always try to buffer at least 1 second of audio data
            min_bytes = 1 * self.source_group.audio_format.bytes_per_second
            if nbytes is None:
                nbytes = min_bytes
            else:
                nbytes = min(min_bytes, nbytes)
            if _debug:
                print('PulseAudioPlayer: Try to get {} bytes of audio data'.format(nbytes))
            self._current_audio_data = self.source_group.get_audio_data(nbytes)
            self._schedule_events()
        if _debug:
            if self._current_audio_data is None:
                print('PulseAudioPlayer: No audio data available')
            else:
                print('PulseAudioPlayer: Got {} bytes of audio data'.format(self._current_audio_data.length))
        return self._current_audio_data

    def _has_audio_data(self):
        return self._get_audio_data() is not None

    def _consume_audio_data(self, nbytes):
        if self._current_audio_data is not None:
            if nbytes == self._current_audio_data.length:
                self._current_audio_data = None
            else:
                self._current_audio_data.consume(nbytes, self.source_group.audio_format)

    def _schedule_events(self):
        if self._current_audio_data is not None:
            for event in self._current_audio_data.events:
                event_index = self._write_index + event.timestamp * \
                    self.source_group.audio_format.bytes_per_second
                if _debug:
                    print('PulseAudioPlayer: Schedule event at index {}'.format(event_index))
                self._events.append((event_index, event))

    def _write_to_stream(self, nbytes=None):
        if nbytes is None:
            nbytes = self.stream.writable_size
        if _debug:
            print('PulseAudioPlayer: Requested to write %d bytes to stream' % nbytes)

        seek_mode = pa.PA_SEEK_RELATIVE
        if self._clear_write:
            seek_mode = pa.PA_SEEK_RELATIVE_ON_READ
            self._clear_write = False
            if _debug:
                print('PulseAudioPlayer: Clear buffer')

        while self._has_audio_data() and nbytes > 0:
            audio_data = self._get_audio_data()

            write_length = min(nbytes, audio_data.length)
            consumption = self.stream.write(audio_data, write_length, seek_mode)

            seek_mode = pa.PA_SEEK_RELATIVE
            self._read_index_valid = True
            self._timestamps.append((self._write_index, audio_data.timestamp))
            self._write_index += consumption

            if _debug:
                print('PulseAudioPlayer: Actually wrote %d bytes to stream' % consumption)
            self._consume_audio_data(consumption)

            nbytes -= consumption

        if not self._has_audio_data():
            # In case the source group wasn't long enough to prebuffer stream
            # to PA's satisfaction, trigger immediate playback (has no effect
            # if stream is already playing).
            if self._playing:
                op = self.stream.trigger()
                op.delete()  # Explicit delete to prevent locking

    def _handle_underflow(self):
        if _debug:
            print('Player: underflow')
        if self._has_audio_data():
            self._write_to_stream()
        else:
            self._add_event_at_write_index('on_eos')
            self._add_event_at_write_index('on_source_group_eos')

    def _process_events(self):
        if _debug:
            print('PulseAudioPlayer: Process events')
        if not self._events:
            if _debug:
                print('PulseAudioPlayer: No events')
            return

        # Assume this is called after time sync
        timing_info = self.stream.get_timing_info()
        if not timing_info:
            if _debug:
                print('PulseAudioPlayer: No timing info to process events')
            return

        read_index = timing_info.read_index
        if _debug:
            print('PulseAudioPlayer: Dispatch events at index {}'.format(read_index))

        while self._events and self._events[0][0] <= read_index:
            _, event = self._events.pop(0)
            if _debug:
                print('PulseAudioPlayer: Dispatch event', event)
            event._sync_dispatch_to_player(self.player)

    def _add_event_at_write_index(self, event_name):
        if _debug:
            print('PulseAudioPlayer: Add event at index {}'.format(self._write_index))
        self._events.append((self._write_index, MediaEvent(0., event_name)))


    def __del__(self):
        try:
            self.delete()
        except:
            pass

    def delete(self):
        if _debug:
            print('PulseAudioPlayer.delete')

        if self._time_sync_operation is not None:
            with self._time_sync_operation:
                self._time_sync_operation.delete()
            self._time_sync_operation = None

        if self.stream is not None:
            with self.stream:
                self.stream.delete()
            self.stream = None

    def clear(self):
        if _debug:
            print('PulseAudioPlayer.clear')

        self._clear_write = True
        self._write_index = self._get_read_index()
        self._timestamps = []
        self._events = []

        with self.stream:
            self._read_index_valid = False
            self.stream.prebuf().wait()

    def play(self):
        if _debug:
            print('PulseAudioPlayer.play')

        with self.stream:
            if self.stream.is_corked:
                self.stream.resume().wait().delete()
                if _debug:
                    print('PulseAudioPlayer: Resumed playback')
            if self.stream.underflow:
                self._write_to_stream()
            if not self._has_audio_data():
                self.stream.trigger().wait().delete()
                if _debug:
                    print('PulseAudioPlayer: Triggered stream for immediate playback')
            assert not self.stream.is_corked

        self._playing = True

    def stop(self):
        if _debug:
            print('PulseAudioPlayer.stop')

        with self.stream:
            if not self.stream.is_corked:
                self.stream.pause().wait().delete()

        self._playing = False

    def _get_read_index(self):
        with self.stream:
            self.stream.update_timing_info().wait().delete()

        timing_info = self.stream.get_timing_info()
        if timing_info:
            read_index = timing_info.read_index
        else:
            read_index = 0

        if _debug:
            print('_get_read_index ->', read_index)
        return read_index

    def _get_write_index(self):
        timing_info = self.stream.get_timing_info()
        if timing_info:
            write_index = timing_info.write_index
        else:
            write_index = 0

        if _debug:
            print('_get_write_index ->', write_index)
        return write_index

    def get_time(self):
        if not self._read_index_valid:
            if _debug:
                print('get_time <_read_index_valid = False> -> None')
            return

        read_index = self._get_read_index()

        write_index = 0
        timestamp = 0.0

        try:
            write_index, timestamp = self._timestamps[0]
            write_index, timestamp = self._timestamps[1]
            while read_index >= write_index:
                del self._timestamps[0]
                write_index, timestamp = self._timestamps[1]
        except IndexError:
            pass

        bytes_per_second = self.source_group.audio_format.bytes_per_second
        time = timestamp + (read_index - write_index) / float(bytes_per_second)

        if _debug:
            print('get_time ->', time)
        return time

    def set_volume(self, volume):
        self._volume = volume

        if self.stream:
            volume *= self.driver._listener._volume
            with self.context:
                self.context.set_input_volume(self.stream, volume).wait()

    def set_pitch(self, pitch):
        with self.stream:
            self.stream.update_sample_rate(int(pitch * self.sample_rate)).wait()


def create_audio_driver():
    driver = PulseAudioDriver()
    driver.connect()
    if _debug:
        driver.dump_debug_info()
    return driver
