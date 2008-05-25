#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import sys

import lib_pulseaudio as pa

import pyglet
_debug = pyglet.options['debug_media']

from pyglet.media import AudioPlayer, Listener, MediaException

def check(result):
    if result < 0:
        error = pa.pa_context_errno(context)
        raise MediaException(pa.pa_strerror(error))
    return result

def check_not_null(value):
    if not value:
        error = pa.pa_context_errno(context)
        raise MediaException(pa.pa_strerror(error))
    return value

class PulseAudioListener(Listener):
    context = None
    def __init__(self):
        self.threaded_mainloop = pa.pa_threaded_mainloop_new()
        self.mainloop = pa.pa_threaded_mainloop_get_api(
            self.threaded_mainloop)

        pa.pa_threaded_mainloop_start(self.threaded_mainloop)
        
    def connect(self, server=None):
        '''Connect to pulseaudio server.
        
        :Parameters:
            `server` : str
                Server to connect to, or ``None`` for the default local
                server (which may be spawned as a daemon if no server is
                found).
                
        '''
        # TODO disconnect from old
        assert not self.context, 'Already connected'

        # Create context and connect
        app_name = self.get_app_name()

        self.lock()
        self.context = pa.pa_context_new(self.mainloop, app_name)
        check(
            pa.pa_context_connect(self.context, server, 0, None)
        )
        self.unlock()

    def lock(self):
        '''Lock the threaded mainloop against events.  Required for all
        calls into PA.'''
        pa.pa_threaded_mainloop_lock(self.threaded_mainloop)

    def unlock(self):
        '''Unlock the mainloop thread.'''
        pa.pa_threaded_mainloop_unlock(self.threaded_mainloop)

    def signal(self):
        '''Signal the mainloop thread to break from a wait.'''
        pa.pa_threaded_mainloop_signal(self.threaded_mainloop, 0)

    def wait(self):
        '''Wait for a signal.'''
        pa.pa_threaded_mainloop_wait(self.threaded_mainloop)

    def sync_operation(self, op):
        '''Wait for an operation to be done or cancelled, then release it.
        Uses a busy-loop -- make sure a callback is registered to 
        signal this listener.''' 
        while pa.pa_operation_get_state(op) == pa.PA_OPERATION_RUNNING:
            pa.pa_threaded_mainloop_wait(self.threaded_mainloop)
        pa.pa_operation_unref(op)

    def async_operation(self, op):
        '''Release the operation immediately without waiting for it to
        complete.'''
        pa.pa_operation_unref(op)

    def get_app_name(self):
        '''Get the application name as advertised to the pulseaudio server.'''
        # TODO move app name into pyglet.app (also useful for OS X menu bar?).
        import sys
        return sys.argv[0]

    def dump_debug_info(self):
        print 'Client version: ', pa.pa_get_library_version()

        print 'Server:         ', pa.pa_context_get_server(self.context)
        print 'Protocol:       ', pa.pa_context_get_protocol_version(
            self.context)
        print 'Server protocol:', pa.pa_context_get_server_protocol_version(
            self.context)
        print 'Local context:  ', (
            pa.pa_context_is_local(self.context) and 'Yes' or 'No')

    def delete(self):
        '''Completely shut down pulseaudio client.'''
        self.lock()
        pa.pa_context_unref(self.context)
        self.unlock()

        pa.pa_threaded_mainloop_stop(self.threaded_mainloop)
        pa.pa_threaded_mainloop_free(self.threaded_mainloop)
        self.threaded_mainloop = None
        self.mainloop = None

    # Listener API

    def _set_volume(self, volume):
        # TODO
        pass

    def _set_position(self, position):
        # TODO
        pass

    def _set_forward_orientation(self, orientation):
        # TODO
        pass

    def _set_up_orientation(self, orientation):
        # TODO
        pass

class PulseAudioPlayer(AudioPlayer):
    def __init__(self, audio_format):
        super(PulseAudioPlayer, self).__init__(audio_format)

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
        channel_map = None

        device = None
        buffer_attr = None
        flags = (pa.PA_STREAM_START_CORKED |
                 pa.PA_STREAM_INTERPOLATE_TIMING)
        volume = None

        # TODO should expose sync_stream, since soundspace example sounds
        # noticeably out of sync with PA.
        sync_stream = None

        try:
            driver_listener.lock()
            self.stream = pa.pa_stream_new(context, 
                                           str(id(self)),
                                           sample_spec,
                                           channel_map)
            check_not_null(self.stream)
            check(
                pa.pa_stream_connect_playback(self.stream, 
                                              device,
                                              buffer_attr, 
                                              flags,
                                              volume, 
                                              sync_stream)
            )
        finally:
            driver_listener.unlock()

        self._timestamps = [] # List of (pa_time, timestamp)
        self._write_time = 0.0
        self._timestamp = 0.0
        self._timestamp_pa_time = 0.0
        self._eos_count = 0
        self._ended = False
        self._ended_underflowed = False

        # Callback trampoline for success operations
        self._success_cb_func = pa.pa_stream_success_cb_t(self._success_cb)

        # Callback for underflow (to detect EOS when expected pa_timestamp
        # does not get reached).
        self._underflow_cb_func = pa.pa_stream_notify_cb_t(self._underflow_cb)
        pa.pa_stream_set_underflow_callback(self.stream,
                                            self._underflow_cb_func, None)

        # Wait for stream readiness
        self._state_cb_func = pa.pa_stream_notify_cb_t(self._state_cb)
        pa.pa_stream_set_state_callback(self.stream, self._state_cb_func, None)
        driver_listener.lock()
        while pa.pa_stream_get_state(self.stream) == pa.PA_STREAM_CREATING:
            driver_listener.wait()
        driver_listener.unlock()

        if _debug:
            print 'stream ready'

    def _state_cb(self, stream, data):
        driver_listener.signal()

    def _success_cb(self, stream, success, data):
        driver_listener.signal()

    def _underflow_cb(self, stream, data):
        # Force through final timestamps, since they have obviously been
        # fulfilled if underflowed.  (Main pump doesn't catch them because
        # PA stops incrementing time a little too early).
        for _, ts in self._timestamps:
            if ts is None:
                self._eos_count += 1
        self._timestamps = []

        if self._ended:
            self._ended_underflowed = True

    def _delete(self):   
        if _debug:
            print '_delete'
        driver_listener.lock()
        pa.pa_stream_disconnect(self.stream)
        driver_listener.unlock()
        pa.pa_stream_unref(self.stream)
        self.stream = None
        
    def get_write_size(self):
        driver_listener.lock()
        size = pa.pa_stream_writable_size(self.stream)
        driver_listener.unlock()
        if _debug:
            print 'get_write_size ->', size
        return size

    def write(self, audio_data):
        if _debug:
            print 'write', audio_data.length, 'bytes'

        driver_listener.lock()
        check(
            pa.pa_stream_write(self.stream,
                               audio_data.data,
                               audio_data.length,
                               pa.pa_free_cb_t(0),  # Data is copied
                               0,
                               pa.PA_SEEK_RELATIVE)
        )
        driver_listener.unlock()

        self._timestamps.append((self._write_time, audio_data.timestamp))
        self._write_time += audio_data.duration 
        self._ended = False

        audio_data.consume(audio_data.length, self.audio_format)

    def write_eos(self):
        if _debug:
            print 'write_eos'
        self._timestamps.append((self._write_time, None))

    def write_end(self):
        if _debug:
            print 'write_end'
        driver_listener.lock()
        driver_listener.sync_operation(
            pa.pa_stream_trigger(self.stream, self._success_cb_func, None)
        )
        driver_listener.unlock()
        self._ended = True

    def clear(self):
        if _debug:
            print 'clear'
        driver_listener.lock()
        driver_listener.sync_operation(
            pa.pa_stream_flush(self.stream, self._success_cb_func, None)
        )
        driver_listener.unlock()

        self._eos_count = 0
        self._timestamps = []
        self._timestamp = 0.0
        self._timestamp_pa_time = 0.0

        self._write_time = self._get_pa_time()

    def play(self):
        if _debug:
            print 'play'
        driver_listener.lock()
        driver_listener.async_operation(
             pa.pa_stream_cork(self.stream, 0, 
                               pa.pa_stream_success_cb_t(0), None)
        )
        if self._ended:
            driver_listener.async_operation(
                 pa.pa_stream_trigger(self.stream, 
                                      pa.pa_stream_success_cb_t(0), None)
             )
        driver_listener.unlock()

    def stop(self):
        if _debug:
            print 'stop'
        driver_listener.lock()
        driver_listener.async_operation(
             pa.pa_stream_cork(self.stream, 1, 
                               pa.pa_stream_success_cb_t(0), None)
        )
        driver_listener.unlock()
        
    def pump(self):
        # TODO ech.  Refactor media to use pull callbacks and threads for
        # drivers that support it (PulseAudio, DirectSound and ALSA,
        # probably).

        if self._ended_underflowed:
            self._delete()
            return

        pa_time = self._get_pa_time()

        try:
            ts_pa_time, ts = self._timestamps[0]
            if _debug:
                print 'pump: ts_pa_time =', ts_pa_time, ', pa_time =', pa_time
            while ts_pa_time <= pa_time:
                self._timestamps.pop(0)
                if ts is None:
                    self._eos_count += 1
                    if _debug:
                        print '_eos_count =', self._eos_count
                else:
                    self._timestamp_pa_time = ts_pa_time
                    self._timestamp = ts
                ts_pa_time, ts = self._timestamps[0]
        except IndexError:
            pass

    def _get_pa_time(self):
        time = pa.pa_usec_t()

        driver_listener.lock()
        driver_listener.sync_operation(
            pa.pa_stream_update_timing_info(self.stream, 
                                            self._success_cb_func, None)
        )
        check(
            pa.pa_stream_get_time(self.stream, time)
        )
        driver_listener.unlock()

        time = float(time.value) / 1000000.0

        if _debug:
            print '_get_pa_time ->', time
        return time 

    def get_time(self):
        pa_time = self._get_pa_time()
        time = self._timestamp + pa_time - self._timestamp_pa_time

        if _debug:
            print 'get_time ->', time
        return time

    def clear_eos(self):
        if _debug:
            if self._eos_count > 0:
                print 'clear_eos ->', True

        if self._eos_count > 0:
            self._eos_count -= 1
            return True
        return False

    def set_volume(self, volume):
        # XXX TODO
        pass

    def set_pitch(self, pitch):
        # XXX TODO (pa_stream_update_sample_rate)
        pass

def cleanup():
    # XXX Not part of pyglet.media API
    driver_listener.delete()

def driver_init():
    # Create default context
    global driver_listener
    global context

    driver_listener = PulseAudioListener()
    driver_listener.connect()
    context = driver_listener.context
    if _debug:
        driver_listener.dump_debug_info()

# pyglet.media interface
driver_audio_player_class = PulseAudioPlayer
driver_listener = None
