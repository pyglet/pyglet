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
# $Id: __init__.py 2088 2008-05-29 12:44:43Z Alex.Holkner $

import ctypes
import heapq
import sys
import threading
import time
import Queue

import pyglet
_debug = pyglet.options['debug_media']

import mt_media

import lib_openal as al
import lib_alc as alc

class OpenALException(mt_media.MediaException):
    pass

# From Python Cookbook, 2nd ed.
class PriorityQueue(Queue.Queue):
    def _init(self, maxsize):
        self.maxsize = maxsize
        self.queue = []

    def _put(self, item):
        heapq.heappush(self.queue, item)

    def _get(self):
        return heapq.heappop(self.queue)

# TODO move functions into context/driver?

def _split_nul_strings(s):
    # NUL-separated list of strings, double-NUL-terminated.
    nul = False
    i = 0
    while True:
        if s[i] == '\0':
            if nul:
                break
            else:
                nul = True
        else:
            nul = False
        i += 1
    s = s[:i - 1]
    return s.split('\0')

def get_extensions():
    extensions = alc.alcGetString(context._device, alc.ALC_EXTENSIONS)
    if sys.platform == 'darwin':
        return ctypes.cast(extensions, ctypes.c_char_p).value.split(' ')
    else:
        return _split_nul_strings(extensions)

def have_extension(extension):
    return extension in get_extensions()

format_map = {
    (1,  8): al.AL_FORMAT_MONO8,
    (1, 16): al.AL_FORMAT_MONO16,
    (2,  8): al.AL_FORMAT_STEREO8,
    (2, 16): al.AL_FORMAT_STEREO16,
}

class OpenALAudioPlayer(mt_media.AbstractAudioPlayer):
    #: Seconds ahead to buffer audio.  Keep small for low latency, but large
    #: enough to avoid underruns. (0.05 is the minimum for my 2.2 GHz Linux)
    _update_buffer_time = 0.2

    #: Minimum size of an OpenAL buffer worth bothering with
    _min_buffer_size = 512

    #: Maximum size of an OpenAL buffer, in bytes.  TODO: use OpenAL maximum
    _max_buffer_size = 65536

    UPDATE_PERIOD = 0.05

    def __init__(self, source_group, player):
        super(OpenALAudioPlayer, self).__init__(source_group, player)
        audio_format = source_group.audio_format

        try:
            self._al_format = format_map[(audio_format.channels,
                                          audio_format.sample_size)]
        except KeyError:
            raise OpenALException('Unsupported audio format.')

        self._al_source = al.ALuint()
        al.alGenSources(1, self._al_source)

        # Seconds of audio currently queued not processed (estimate)
        self._buffered_time = 0.0

        # List of (timestamp, duration) corresponding to currently queued AL
        # buffers
        self._timestamps = []
        self._events = []

        self._lock = threading.Lock()

        # OpenAL 1.0 timestamp interpolation
        if not context.have_1_1:
            self._timestamp_system_time = time.time()

        # Desired play state (True even if stopped due to underrun)
        self._playing = False

        # Timestamp when paused
        self._pause_timestamp = 0.0

        self._pump()

    def __del__(self):
        try:
            self.delete()
        except:
            pass

    def delete(self):
        return
        # XXX TODO crashes
        context.lock()
        al.alDeleteSources(1, self._al_source)
        context.unlock()
        self._al_source = None

    def play(self):
        if self._playing:
            return

        self._playing = True
        self._al_play()
        if not context.have_1_1:
            self._timestamp_system_time = time.time()

    def _al_play(self):
        if not self._timestamps:
            return
        state = al.ALint()

        context.lock()
        al.alGetSourcei(self._al_source, al.AL_SOURCE_STATE, state)
        if state.value != al.AL_PLAYING:
            al.alSourcePlay(self._al_source)
        context.unlock()

    def stop(self):
        if not self._playing:
            return

        self._pause_timestamp = self.get_time()
        al.alSourcePause(self._al_source)
        self._playing = False

    def clear(self):
    
        self._lock.acquire()
        context.lock()

        al.alSourceStop(self._al_source)
        self._playing = False

        del self._events[:]

        '''
        # XXX what's the point of this?  need to dequeue unprocessed buffers
        # as well as processed ones.  clearing timestamps list confuses pump,
        # serves no purpose.

        processed = al.ALint()
        al.alGetSourcei(self._al_source, al.AL_BUFFERS_PROCESSED, processed)
        if processed.value:
            buffers = (al.ALuint * processed.value)()
            al.alSourceUnqueueBuffers(self._al_source, len(buffers), buffers)
            al.alDeleteBuffers(len(buffers), buffers)


        self._pause_timestamp = 0.0
        self._buffered_time = 0.0
        self._timestamps = []
        '''
        context.unlock()
        self._lock.release()

    def _get_current_buffer_time(self):
        # Estimate how far into current buffer
        if context.have_1_1:
            samples = al.ALint()
            context.lock()
            al.alGetSourcei(self._al_source, al.AL_SAMPLE_OFFSET, samples)
            context.unlock()
            return samples.value / \
                float(self.source_group.audio_format.sample_rate)
        else:
            # Interpolate system time past buffer timestamp
            return time.time() - self._timestamp_system_time

    def _pump(self):
        if _debug:
            print 'pump'

        if not self._al_source:
            # Deleted.
            return

        self._lock.acquire()

        # Release spent buffers
        processed = al.ALint()
        context.lock()
        al.alGetSourcei(self._al_source, al.AL_BUFFERS_PROCESSED, processed)
        processed = processed.value
        if processed:
            buffers = (al.ALuint * processed)()
            al.alSourceUnqueueBuffers(self._al_source, len(buffers), buffers)
            al.alDeleteBuffers(len(buffers), buffers)
        context.unlock()

        # Pop timestamps
        while processed:
            if not context.have_1_1:
                self._timestamp_system_time = time.time()
            _, duration = self._timestamps.pop(0)
            self._buffered_time -= duration
            processed -= 1

        current_buffer_time = self._get_current_buffer_time()

        repump = True

        # Refill buffers
        refill_time = \
            self._update_buffer_time - self._buffered_time + \
            current_buffer_time
        refill_bytes = \
            int(refill_time * self.source_group.audio_format.bytes_per_second)
        while refill_bytes > self._min_buffer_size:
            audio_data = self.source_group.get_audio_data(refill_bytes)
            if not audio_data:
                repump = False
                break

            self._events.extend(audio_data.events)

            buffer = al.ALuint()
            context.lock()
            al.alGenBuffers(1, buffer)
            al.alBufferData(buffer, 
                            self._al_format,
                            audio_data.data,
                            audio_data.length,
                            self.source_group.audio_format.sample_rate)
            al.alSourceQueueBuffers(self._al_source, 1, ctypes.byref(buffer)) 
            context.unlock()

            self._buffered_time += audio_data.duration
            self._timestamps.append((audio_data.timestamp, audio_data.duration))
            refill_bytes -= audio_data.length

        # Check for underrun stopping playback
        if self._playing:
            state = al.ALint()
            context.lock()
            al.alGetSourcei(self._al_source, al.AL_SOURCE_STATE, state)
            if state.value != al.AL_PLAYING:
                al.alSourcePlay(self._al_source)
            context.unlock()

        # Process events
        self._process_events()

        update_period = self.UPDATE_PERIOD
        if self._events:
            repump = True # ech, stupid flag
            timestamp, _ = self._events[0]
            # XXX avoid call to get_time()
            update_period = min(update_period, timestamp - self.get_time())

        # Schedule future pump
        if repump:
            context.post_job(update_period, self._pump)
        else:
            # End of source group XXX wrong, wait for underrun
            self._sync_dispatch_player_event('on_eos')
            self._sync_dispatch_player_event('on_source_group_eos')

        self._lock.release()

    # TODO consolidate with other drivers
    # XXX not locked
    def _process_events(self):
        if not self._events:
            return

        time = self.get_time()

        timestamp, event = self._events[0]
        try:
            while time >= timestamp:
                if event == 'on_video_frame': #XXX HACK
                    self._sync_dispatch_player_event(event, timestamp)
                else:
                    self._sync_dispatch_player_event(event)
                del self._events[0]
                timestamp, event = self._events[0]
        except IndexError:
            pass

    # TODO consolidate with other drivers
    def _sync_dispatch_player_event(self, event, *args):
        # TODO if EventLoop not being used, hook into
        #      pyglet.media.dispatch_events.
        if pyglet.app.event_loop:
            pyglet.app.event_loop.post_event(self.player, event, *args)

    def get_time(self):
        # Assumes pump has been called recently.
        state = al.ALint()
        context.lock()
        al.alGetSourcei(self._al_source, al.AL_SOURCE_STATE, state)
        context.unlock()

        if not self._playing:
            return self._pause_timestamp

        try:
            ts, _ = self._timestamps[0]
        except IndexError:
            return self._pause_timestamp

        current_buffer_time = self._get_current_buffer_time()
        return ts + current_buffer_time

    def set_volume(self, volume):
        self.lock()
        al.alSourcef(self._al_source, al.AL_GAIN, max(0, volume))
        self.unlock()

    def set_position(self, position):
        x, y, z = position
        self.lock()
        al.alSource3f(self._al_source, al.AL_POSITION, x, y, z)
        self.unlock()

    def set_min_distance(self, min_distance):
        self.lock()
        al.alSourcef(self._al_source, al.AL_REFERENCE_DISTANCE, min_distance)
        self.unlock()

    def set_max_distance(self, max_distance):
        self.lock()
        al.alSourcef(self._al_source, al.AL_MAX_DISTANCE, max_distance)
        self.unlock()

    def set_pitch(self, pitch):
        self.lock()
        al.alSourcef(self._al_source, al.AL_PITCH, max(0, pitch))
        self.unlock()

    def set_cone_orientation(self, cone_orientation):
        x, y, z = cone_orientation
        self.lock()
        al.alSource3f(self._al_source, al.AL_DIRECTION, x, y, z)
        self.unlock()

    def set_cone_inner_angle(self, cone_inner_angle):
        self.lock()
        al.alSourcef(self._al_source, al.AL_CONE_INNER_ANGLE, cone_inner_angle)
        self.unlock()

    def set_cone_outer_angle(self, cone_outer_angle):
        self.lock()
        al.alSourcef(self._al_source, al.AL_CONE_OUTER_ANGLE, cone_outer_angle)
        self.unlock()

    def set_cone_outer_gain(self, cone_outer_gain):
        self.lock()
        al.alSourcef(self._al_source, al.AL_CONE_OUTER_GAIN, cone_outer_gain)
        self.unlock()

class OpenALDriver(mt_media.AbstractAudioDriver):
    def __init__(self, device_name=None):
        # TODO devices must be enumerated on Windows, otherwise 1.0 context is
        # returned.

        self._device = alc.alcOpenDevice(device_name)
        if not self._device:
            raise Exception('No OpenAL device.')

        alcontext = alc.alcCreateContext(self._device, None)
        alc.alcMakeContextCurrent(alcontext)

        self.have_1_1 = self.have_version(1, 1) and False

        self._lock = threading.Lock()

        # Start worker thread
        self._work_queue = PriorityQueue()
        self._worker_thread = threading.Thread(target=self._worker_thread_func)
        self._worker_thread.setDaemon(True)
        self._worker_thread.start()

    def create_audio_player(self, source_group, player):
        return OpenALAudioPlayer(source_group, player)

    def delete(self):
        pass

    def lock(self):
        self._lock.acquire()

    def unlock(self):
        self._lock.release()

    def post_job(self, delay, job):
        self._work_queue.put((delay + time.time(), job))

    def _worker_thread_func(self):
        while True:
            target_time, job = self._work_queue.get()
            wait_time = target_time - time.time()
            while wait_time > 0:
                if _debug:
                    print 'worker sleep', wait_time
                time.sleep(wait_time)
                wait_time = target_time - time.time()
            if _debug:
                print 'worker job', job
            job()

    def have_version(self, major, minor):
        return (major, minor) <= self.get_version()

    def get_version(self):
        major = alc.ALCint()
        minor = alc.ALCint()
        alc.alcGetIntegerv(self._device, alc.ALC_MAJOR_VERSION, 
                           ctypes.sizeof(major), major)
        alc.alcGetIntegerv(self._device, alc.ALC_MINOR_VERSION, 
                           ctypes.sizeof(minor), minor)
        return major.value, minor.value


    # Listener API

    def _set_volume(self, volume):
        self.lock()
        al.alListenerf(al.AL_GAIN, volume)
        self.unlock()
        self._volume = volume

    def _set_position(self, position):
        x, y, z = position
        self.lock()
        al.alListener3f(al.AL_POSITION, x, y, z)
        self.unlock()
        self._position = position 

    def _set_forward_orientation(self, orientation):
        val = (al.ALfloat * 6)(*(orientation + self._up_orientation))
        self.lock()
        al.alListenerfv(al.AL_ORIENTATION, val)
        self.unlock()
        self._forward_orientation = orientation

    def _set_up_orientation(self, orientation):
        val = (al.ALfloat * 6)(*(self._forward_orientation + orientation))
        self.lock()
        al.alListenerfv(al.AL_ORIENTATION, val)
        self.unlock()
        self._up_orientation = orientation

context = None

def create_audio_driver(device_name=None):
    global context
    context = OpenALDriver(device_name)
    if _debug:
        print 'OpenAL', context.get_version()
    return context
