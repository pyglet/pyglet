#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import sys

import lib_pulseaudio as pa

import pyglet
_debug = pyglet.options['debug_media']

import mt_media

def check(result):
    if result < 0:
        error = pa.pa_context_errno(context._context)
        raise MediaException(pa.pa_strerror(error))
    return result

def check_not_null(value):
    if not value:
        error = pa.pa_context_errno(context._context)
        raise MediaException(pa.pa_strerror(error))
    return value

class PulseAudioDriver(mt_media.AbstractAudioDriver):
    _context = None
    def __init__(self):
        self.threaded_mainloop = pa.pa_threaded_mainloop_new()
        self.mainloop = pa.pa_threaded_mainloop_get_api(
            self.threaded_mainloop)


    def create_audio_player(self, source_group, player):
        return PulseAudioPlayer(source_group, player)
        
    def connect(self, server=None):
        '''Connect to pulseaudio server.
        
        :Parameters:
            `server` : str
                Server to connect to, or ``None`` for the default local
                server (which may be spawned as a daemon if no server is
                found).
                
        '''
        # TODO disconnect from old
        assert not self._context, 'Already connected'

        # Create context
        app_name = self.get_app_name()
        self._context = pa.pa_context_new(self.mainloop, app_name)

        # Context state callback 
        self._state_cb_func = pa.pa_context_notify_cb_t(self._state_cb)
        pa.pa_context_set_state_callback(self._context, 
                                         self._state_cb_func, None)

        # Connect
        check(
            pa.pa_context_connect(self._context, server, 0, None)
        )


        self.lock()
        check(
            pa.pa_threaded_mainloop_start(self.threaded_mainloop)
        )
        try:
            # Wait for context ready.
            self.wait()
            if pa.pa_context_get_state(self._context) != pa.PA_CONTEXT_READY:
                check(-1)
        finally:
            self.unlock()

    def _state_cb(self, context, userdata):
        if _debug:
            print 'context state cb'
        state = pa.pa_context_get_state(self._context)
        if state in (pa.PA_CONTEXT_READY, 
                     pa.PA_CONTEXT_TERMINATED,
                     pa.PA_CONTEXT_FAILED):
            self.signal()

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

        print 'Server:         ', pa.pa_context_get_server(self._context)
        print 'Protocol:       ', pa.pa_context_get_protocol_version(
            self._context)
        print 'Server protocol:', pa.pa_context_get_server_protocol_version(
            self._context)
        print 'Local context:  ', (
            pa.pa_context_is_local(self._context) and 'Yes' or 'No')

    def delete(self):
        '''Completely shut down pulseaudio client.'''
        self.lock()
        pa.pa_context_unref(self._context)
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

class PulseAudioPlayer(mt_media.AbstractAudioPlayer):
    def __init__(self, source_group, player):
        super(PulseAudioPlayer, self).__init__(source_group, player)

        self._events = []
        self._timestamps = []  # List of (ref_time, timestamp)
        self._write_index = 0  # Current write index (tracked manually)

        self._clear_write = False
        self._buffered_audio_data = None
        self._underflow_is_eos = False
        self._playing = False

        audio_format = source_group.audio_format
        assert audio_format

        # Create sample_spec
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

        try:
            context.lock()
            # Create stream
            self.stream = pa.pa_stream_new(context._context, 
                                           str(id(self)),
                                           sample_spec,
                                           channel_map)
            check_not_null(self.stream)

            # Callback trampoline for success operations
            self._success_cb_func = pa.pa_stream_success_cb_t(self._success_cb)

            # Callback for underflow (to detect EOS when expected pa_timestamp
            # does not get reached).
            self._underflow_cb_func = \
                pa.pa_stream_notify_cb_t(self._underflow_cb)
            pa.pa_stream_set_underflow_callback(self.stream,
                                                self._underflow_cb_func, None)

            # Callback for data write
            self._write_cb_func = pa.pa_stream_request_cb_t(self._write_cb)
            pa.pa_stream_set_write_callback(self.stream,
                                            self._write_cb_func, None)

            # Connect to sink
            device = None
            buffer_attr = None
            flags = (pa.PA_STREAM_START_CORKED |
                     pa.PA_STREAM_INTERPOLATE_TIMING)
            volume = None
            sync_stream = None  # TODO use this
            check(
                pa.pa_stream_connect_playback(self.stream, 
                                              device,
                                              buffer_attr, 
                                              flags,
                                              volume, 
                                              sync_stream)
            )

            # Wait for stream readiness
            self._state_cb_func = pa.pa_stream_notify_cb_t(self._state_cb)
            pa.pa_stream_set_state_callback(self.stream, 
                                            self._state_cb_func, None)
            while pa.pa_stream_get_state(self.stream) == pa.PA_STREAM_CREATING:
                context.wait()

            if pa.pa_stream_get_state(self.stream) != pa.PA_STREAM_READY:
                check(-1)
        finally:
            context.unlock()

        if _debug:
            print 'stream ready'

    def _state_cb(self, stream, data):
        context.signal()

    def _success_cb(self, stream, success, data):
        context.signal()

    def _write_cb(self, stream, bytes, data):
        if _debug:
            print 'write callback: %d bytes' % bytes

        # Asynchronously update time
        if self._events:
            context.async_operation(
                pa.pa_stream_update_timing_info(self.stream, 
                                                self._success_cb_func, None)
            )

        # Grab next audio packet, or leftovers from last callback.
        if self._buffered_audio_data:
            audio_data = self._buffered_audio_data
            self._buffered_audio_data = None
        else:
            audio_data = self.source_group.get_audio_data(bytes)

        seek_flag = pa.PA_SEEK_RELATIVE
        if self._clear_write:
            if _debug:
                print 'seek PA_SEEK_RELATIVE_ON_READ'
            seek_flag = pa.PA_SEEK_RELATIVE_ON_READ
            self._clear_write = False

        # Keep writing packets until `bytes` is depleted
        while audio_data and bytes > 0:
            if _debug:
                print 'packet', audio_data.timestamp
            if _debug and audio_data.events:
                print 'events', audio_data.events
            for event in audio_data.events:
                event_index = self._write_index + event.timestamp * \
                    self.source_group.audio_format.bytes_per_second
                self._events.append((event_index, event))

            consumption = min(bytes, audio_data.length)
            
            check(
                pa.pa_stream_write(self.stream,
                                   audio_data.data,
                                   consumption,
                                   pa.pa_free_cb_t(0),  # Data is copied
                                   0,
                                   seek_flag)
            )

            seek_flag = pa.PA_SEEK_RELATIVE
            self._timestamps.append((self._write_index, audio_data.timestamp))
            self._write_index += consumption
            self._underflow_is_eos = False

            if _debug:
                print 'write', consumption
            if consumption < audio_data.length:
                audio_data.consume(consumption, self.source_group.audio_format)
                self._buffered_audio_data = audio_data
                break

            bytes -= consumption
            if bytes > 0:
                audio_data = self.source_group.get_audio_data(bytes) #XXX name change

        if not audio_data:
            # Whole source group has been written.  Any underflow encountered
            # after now is the EOS.
            self._underflow_is_eos = True
            
            # In case the source group wasn't long enough to prebuffer stream
            # to PA's satisfaction, trigger immediate playback (has no effect
            # if stream is already playing).
            if self._playing:
                context.async_operation(
                     pa.pa_stream_trigger(self.stream, 
                                          pa.pa_stream_success_cb_t(0), None)
                )

        self._process_events()

    def _underflow_cb(self, stream, data):
        self._process_events()

        if self._underflow_is_eos:
            self._sync_dispatch_player_event('on_eos')
            self._sync_dispatch_player_event('on_source_group_eos')
            self._underflow_is_eos = False
            if _debug:
                print 'eos'
        else:
            if _debug:
                print 'underflow'
            # TODO: does PA automatically restart stream when buffered again?
            # XXX: sometimes receive an underflow after EOS... need to filter?

    def _process_events(self):
        if not self._events:
            return

        timing_info = pa.pa_stream_get_timing_info(self.stream)
        if not timing_info:
            if _debug:
                print 'abort _process_events'
            return

        read_index = timing_info.contents.read_index

        while self._events and self._events[0][0] < read_index:
            _, event = self._events.pop(0)
            if _debug:
                print 'dispatch event', event
            event._sync_dispatch_to_player(self.player)

    def _sync_dispatch_player_event(self, event, *args):
        # TODO if EventLoop not being used, hook into
        #      pyglet.media.dispatch_events.
        if pyglet.app.event_loop:
            pyglet.app.event_loop.post_event(self.player, event, *args)

    def __del__(self):
        try:
            self.delete()
        except:
            pass
        
    def delete(self):   
        if _debug:
            print 'delete'
        if not self.stream:
            return

        context.lock()
        pa.pa_stream_disconnect(self.stream)
        context.unlock()
        pa.pa_stream_unref(self.stream)
        self.stream = None

    def clear(self):
        if _debug:
            print 'clear'

        self._clear_write = True
        self._write_index = self._get_read_index()
        self._timestamps = []
        self._events = []

        context.lock()
        context.sync_operation(
            pa.pa_stream_prebuf(self.stream, self._success_cb_func, None)
        )
        context.unlock()

    def play(self):
        if _debug:
            print 'play'
        context.lock()
        context.async_operation(
             pa.pa_stream_cork(self.stream, 0, 
                               pa.pa_stream_success_cb_t(0), None)
        )

        # If whole stream has already been written, trigger immediate
        # playback.        
        if self._underflow_is_eos:
            context.async_operation(
                 pa.pa_stream_trigger(self.stream, 
                                      pa.pa_stream_success_cb_t(0), None)
            )
        context.unlock()

        self._playing = True

    def stop(self):
        if _debug:
            print 'stop'
        context.lock()
        context.async_operation(
             pa.pa_stream_cork(self.stream, 1, 
                               pa.pa_stream_success_cb_t(0), None)
        )
        context.unlock()

        self._playing = False

    def _get_read_index(self):
        time = pa.pa_usec_t()

        context.lock()
        context.sync_operation(
            pa.pa_stream_update_timing_info(self.stream, 
                                            self._success_cb_func, None)
        )
        context.unlock()

        timing_info = pa.pa_stream_get_timing_info(self.stream)
        if timing_info:
            read_index = timing_info.contents.read_index
        else:
            read_index = 0

        if _debug:
            print '_get_read_index ->', read_index
        return read_index

    def _get_write_index(self):
        timing_info = pa.pa_stream_get_timing_info(self.stream)
        if timing_info:
            write_index = timing_info.contents.write_index
        else:
            write_index = 0

        if _debug:
            print '_get_write_index ->', write_index
        return write_index

    def get_time(self, read_index=None):
        if read_index is None:
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
            print 'get_time ->', time
        return time

    def set_volume(self, volume):
        # XXX TODO
        pass

    def set_pitch(self, pitch):
        # XXX TODO (pa_stream_update_sample_rate)
        pass

def create_audio_driver():
    global context
    context = PulseAudioDriver()
    context.connect()
    if _debug:
        context.dump_debug_info()
    return context
