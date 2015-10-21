from __future__ import print_function
from __future__ import absolute_import
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
# $Id$

import ctypes
import heapq
import threading
import time
import Queue
import atexit

from . import lib_openal as al
from . import lib_alc as alc
from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer
from pyglet.media.events import MediaEvent
from pyglet.media.exceptions import MediaException
from pyglet.media.listener import AbstractListener
from pyglet.media.threads import MediaThread

import pyglet
_debug = pyglet.options['debug_media']
_debug_buffers = pyglet.options.get('debug_media_buffers', False)

class OpenALException(MediaException):
    pass

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
    return filter(None, [ss.strip() for ss in s.split('\0')])

format_map = {
    (1,  8): al.AL_FORMAT_MONO8,
    (1, 16): al.AL_FORMAT_MONO16,
    (2,  8): al.AL_FORMAT_STEREO8,
    (2, 16): al.AL_FORMAT_STEREO16,
}

class OpenALWorker(MediaThread):
    # Minimum size to bother refilling (bytes)
    _min_write_size = 512

    # Time to wait if there are players, but they're all full.
    _nap_time = 0.05

    # Time to wait if there are no players.
    _sleep_time = None

    def __init__(self):
        super(OpenALWorker, self).__init__()
        self.players = set()

    def run(self):
        while True:
            # This is a big lock, but ensures a player is not deleted while
            # we're processing it -- this saves on extra checks in the
            # player's methods that would otherwise have to check that it's
            # still alive.
            with self.condition:
                if self.stopped:
                    break
                sleep_time = -1

                # Refill player with least write_size
                if self.players:
                    player = None
                    write_size = 0
                    for p in self.players:
                        s = p.get_write_size()
                        if s > write_size:
                            player = p
                            write_size = s

                    if write_size > self._min_write_size:
                        player.refill(write_size)
                    else:
                        sleep_time = self._nap_time
                else:
                    sleep_time = self._sleep_time

            if sleep_time != -1:
                self.sleep(sleep_time)
            else:
                # We MUST sleep, or we will starve pyglet's main loop.  It
                # also looks like if we don't sleep enough, we'll starve out
                # various updates that stop us from properly removing players
                # that should be removed.
                time.sleep(self._nap_time)

    def add(self, player):
        with self.condition:
            self.players.add(player)
            self.condition.notify()

    def remove(self, player):
        with self.condition:
            if player in self.players:
                self.players.remove(player)
            self.condition.notify()


class OpenALBufferPool(object):
    """At least Mac OS X doesn't free buffers when a source is deleted; it just
    detaches them from the source.  So keep our own recycled queue.
    """
    def __init__(self):
        self._buffers = [] # list of free buffer names
        self._sources = {} # { sourceId : [ buffer names used ] }

    def getBuffer(self, alSource):
        """Convenience for returning one buffer name"""
        return self.getBuffers(alSource, 1)[0]

    def getBuffers(self, alSource, i):
        """Returns an array containing i buffer names.  The returned list must
        not be modified in any way, and may get changed by subsequent calls to
        getBuffers.
        """
        assert context.lock.locked()
        buffs = []
        try:
            while i > 0:
                b = self._buffers.pop()
                if not al.alIsBuffer(b):
                    # Protect against implementations that DO free buffers
                    # when they delete a source - carry on.
                    if _debug_buffers:
                        print("Found a bad buffer")
                    continue
                buffs.append(b)
                i -= 1
        except IndexError:
            while i > 0:
                buffer_name = al.ALuint()
                al.alGenBuffers(1, buffer_name)
                if _debug_buffers:
                    error = al.alGetError()
                    if error != 0:
                        print("GEN BUFFERS: " + str(error))
                buffs.append(buffer_name)
                i -= 1

        alSourceVal = alSource.value
        if alSourceVal not in self._sources:
            self._sources[alSourceVal] = buffs
        else:
            self._sources[alSourceVal].extend(buffs)

        return buffs

    def deleteSource(self, alSource):
        """Delete a source pointer (self._al_source) and free its buffers"""
        assert context.lock.locked()
        if alSource.value in self._sources:
            for buffer in self._sources.pop(alSource.value):
                self._buffers.append(buffer)

    def dequeueBuffer(self, alSource, buffer):
        """A buffer has finished playing, free it."""
        assert context.lock.locked()
        sourceBuffs = self._sources[alSource.value]
        for i, b in enumerate(sourceBuffs):
            if buffer == b.value:
                self._buffers.append(sourceBuffs.pop(i))
                break
                
        else:
            # If no such buffer exists, should not happen anyway.
            if _debug_buffers:
                print("Bad buffer: " + str(buffer))

    def delete(self):
        """Delete all sources and free all buffers"""
        assert context.lock.locked()
        for source, buffers in self._sources.items():
            al.alDeleteSources(1, ctypes.byref(ctypes.c_uint(source)))
            for b in buffers:
                if not al.alIsBuffer(b):
                    # Protect against implementations that DO free buffers
                    # when they delete a source - carry on.
                    if _debug_buffers:
                        print("Found a bad buffer")
                    continue
                al.alDeleteBuffers(1, ctypes.byref(b))
        for b in self._buffers:
            al.alDeleteBuffers(1, ctypes.byref(b))
        self._buffers = []
        self._sources = {}

bufferPool = OpenALBufferPool()

class OpenALAudioPlayer(AbstractAudioPlayer):
    #: Minimum size of an OpenAL buffer worth bothering with, in bytes
    _min_buffer_size = 512

    #: Aggregate (desired) buffer size, in bytes
    _ideal_buffer_size = 44800

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

        # Lock policy: lock all instance vars (except constants).  (AL calls
        # are locked on context).
        self._lock = threading.RLock()

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

        # Has source group EOS been seen (and hence, event added to queue)?
        self._eos = False

        # OpenAL 1.0 timestamp interpolation: system time of current buffer
        # playback (best guess)
        if not context.have_1_1:
            self._buffer_system_time = time.time()

        self.refill(self._ideal_buffer_size)

    def __del__(self):
        try:
            self.delete()
        except:
            pass

    def delete(self):
        if _debug:
            print('OpenALAudioPlayer.delete()')

        if not self._al_source:
            return

        context.worker.remove(self)

        with self._lock:
            with context.lock:
                al.alDeleteSources(1, self._al_source)
                bufferPool.deleteSource(self._al_source)
                if _debug_buffers:
                    error = al.alGetError()
                    if error != 0:
                        print("DELETE ERROR: " + str(error))
            self._al_source = None

    def play(self):
        if self._playing:
            return

        if _debug:
            print('OpenALAudioPlayer.play()')
        self._playing = True
        self._al_play()
        if not context.have_1_1:
            self._buffer_system_time = time.time()

        context.worker.add(self)

    def _al_play(self):
        if _debug:
            print('OpenALAudioPlayer._al_play()')
        with context.lock:
            state = al.ALint()
            al.alGetSourcei(self._al_source, al.AL_SOURCE_STATE, state)
            if state.value != al.AL_PLAYING:
                al.alSourcePlay(self._al_source)

    def stop(self):
        if not self._playing:
            return

        if _debug:
            print('OpenALAudioPlayer.stop()')
        self._pause_timestamp = self.get_time()
        with context.lock:
            al.alSourcePause(self._al_source)
        self._playing = False

        context.worker.remove(self)

    def clear(self):
        if _debug:
            print('OpenALAudioPlayer.clear()')

        with self._lock:
            with context.lock:
                al.alSourceStop(self._al_source)
                self._playing = False

                del self._events[:]
                self._underrun_timestamp = None
                self._buffer_timestamps = [None for _ in self._buffer_timestamps]

    def _update_play_cursor(self):
        if not self._al_source:
            return

        with self._lock:
            with context.lock:

                # Release spent buffers
                processed = al.ALint()
                al.alGetSourcei(self._al_source, al.AL_BUFFERS_PROCESSED, processed)
                processed = processed.value
                if _debug_buffers:
                    print(("Processed buffer count:", processed))
                if processed:
                    buffers = (al.ALuint * processed)()
                    al.alSourceUnqueueBuffers(self._al_source, len(buffers), buffers)
                    error = al.alGetError()
                    if error != 0:
                        if _debug_buffers:
                            print("Source unqueue error: " + str(error))
                    else:
                        for b in buffers:
                            bufferPool.dequeueBuffer(self._al_source, b)

            if processed:
                if (len(self._buffer_timestamps) == processed
                        and self._buffer_timestamps[-1] is not None):
                    # Underrun, take note of timestamp.
                    # We check that the timestamp is not None, because otherwise
                    # our source could have been cleared.
                    self._underrun_timestamp = \
                        self._buffer_timestamps[-1] + \
                        self._buffer_sizes[-1] / \
                            float(self.source_group.audio_format.bytes_per_second)
                self._buffer_cursor += sum(self._buffer_sizes[:processed])
                del self._buffer_sizes[:processed]
                del self._buffer_timestamps[:processed]

                if not context.have_1_1:
                    self._buffer_system_time = time.time()

            # Update play cursor using buffer cursor + estimate into current
            # buffer
            if context.have_1_1:
                byte_offset = al.ALint()
                with context.lock:
                    al.alGetSourcei(self._al_source, al.AL_BYTE_OFFSET, byte_offset)
                if _debug:
                    print('Current offset in bytes:', byte_offset.value)
                self._play_cursor = self._buffer_cursor + byte_offset.value
            else:
                # Interpolate system time past buffer timestamp
                self._play_cursor = \
                    self._buffer_cursor + int(
                        (time.time() - self._buffer_system_time) * \
                            self.source_group.audio_format.bytes_per_second)

            # Process events
            while self._events and self._events[0][0] < self._play_cursor:
                _, event = self._events.pop(0)
                event._sync_dispatch_to_player(self.player)

    def get_write_size(self):
        with self._lock:
            self._update_play_cursor()
            write_size = self._ideal_buffer_size - \
                (self._write_cursor - self._play_cursor)
            if self._eos:
                write_size = 0

        if _debug:
            print("Write size {} bytes".format(write_size))
        return write_size

    def refill(self, write_size):
        if _debug:
            print('refill', write_size)

        with self._lock:

            while write_size > self._min_buffer_size:
                audio_data = self.source_group.get_audio_data(write_size)
                if not audio_data:
                    self._eos = True
                    self._events.append(
                        (self._write_cursor, MediaEvent(0, 'on_eos')))
                    self._events.append(
                        (self._write_cursor, MediaEvent(0, 'on_source_group_eos')))
                    break

                for event in audio_data.events:
                    cursor = self._write_cursor + event.timestamp * \
                        self.source_group.audio_format.bytes_per_second
                    self._events.append((cursor, event))

                with context.lock:
                    buffer_name = bufferPool.getBuffer(self._al_source)
                    al.alBufferData(buffer_name,
                                    self._al_format,
                                    audio_data.data,
                                    audio_data.length,
                                    self.source_group.audio_format.sample_rate)
                    if _debug_buffers:
                        error = al.alGetError()
                        if error != 0:
                            print("BUFFER DATA ERROR: " + str(error))
                    al.alSourceQueueBuffers(self._al_source, 1, ctypes.byref(buffer_name))
                    if _debug_buffers:
                        error = al.alGetError()
                        if error != 0:
                            print("QUEUE BUFFER ERROR: " + str(error))

                self._write_cursor += audio_data.length
                self._buffer_sizes.append(audio_data.length)
                self._buffer_timestamps.append(audio_data.timestamp)
                write_size -= audio_data.length

            # Check for underrun stopping playback
            if self._playing:
                state = al.ALint()
                with context.lock:
                    al.alGetSourcei(self._al_source, al.AL_SOURCE_STATE, state)
                    if state.value != al.AL_PLAYING:
                        if _debug:
                            print('underrun')
                        al.alSourcePlay(self._al_source)

    def get_time(self):
        try:
            buffer_timestamp = self._buffer_timestamps[0]
        except IndexError:
            return self._underrun_timestamp

        if buffer_timestamp is None:
            return None

        return buffer_timestamp + \
            (self._play_cursor - self._buffer_cursor) / \
                float(self.source_group.audio_format.bytes_per_second)

    def set_volume(self, volume):
        volume = float(volume)
        with context.lock:
            al.alSourcef(self._al_source, al.AL_GAIN, max(0., volume))

    def set_position(self, position):
        x, y, z = map(float, position)
        with context.lock:
            al.alSource3f(self._al_source, al.AL_POSITION, x, y, z)

    def set_min_distance(self, min_distance):
        min_distance = float(min_distance)
        with context.lock:
            al.alSourcef(self._al_source, al.AL_REFERENCE_DISTANCE, min_distance)

    def set_max_distance(self, max_distance):
        max_distance = float(max_distance)
        with context.lock:
            al.alSourcef(self._al_source, al.AL_MAX_DISTANCE, max_distance)

    def set_pitch(self, pitch):
        pitch = float(pitch)
        with context.lock:
            al.alSourcef(self._al_source, al.AL_PITCH, max(0., pitch))

    def set_cone_orientation(self, cone_orientation):
        x, y, z = map(float, cone_orientation)
        with context.lock:
            al.alSource3f(self._al_source, al.AL_DIRECTION, x, y, z)

    def set_cone_inner_angle(self, cone_inner_angle):
        cone_inner_angle = float(cone_inner_angle)
        with context.lock:
            al.alSourcef(self._al_source, al.AL_CONE_INNER_ANGLE, cone_inner_angle)

    def set_cone_outer_angle(self, cone_outer_angle):
        cone_outer_angle = float(cone_outer_angle)
        with context.lock:
            al.alSourcef(self._al_source, al.AL_CONE_OUTER_ANGLE, cone_outer_angle)

    def set_cone_outer_gain(self, cone_outer_gain):
        cone_outer_gain = float(cone_outer_gain)
        with context.lock:
            al.alSourcef(self._al_source, al.AL_CONE_OUTER_GAIN, cone_outer_gain)

class OpenALDriver(AbstractAudioDriver):
    _forward_orientation = (0, 0, -1)
    _up_orientation = (0, 1, 0)

    def __init__(self, device_name=None):
        super(OpenALDriver, self).__init__()

        # TODO devices must be enumerated on Windows, otherwise 1.0 context is
        # returned.

        self._device = alc.alcOpenDevice(device_name)
        if not self._device:
            raise Exception('No OpenAL device.')

        self._context = alc.alcCreateContext(self._device, None)
        alc.alcMakeContextCurrent(self._context)

        self.have_1_1 = self.have_version(1, 1) and False

        self.lock = threading.Lock()

        self._listener = OpenALListener(self)

        # Start worker thread
        self.worker = OpenALWorker()
        self.worker.start()

    def create_audio_player(self, source_group, player):
        assert self._device is not None, "Device was closed"
        return OpenALAudioPlayer(source_group, player)

    def delete(self):
        self.worker.stop()
        with self.lock:
            alc.alcMakeContextCurrent(None)
            alc.alcDestroyContext(self._context)
            alc.alcCloseDevice(self._device)
            self._device = None

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

    def get_extensions(self):
        extensions = alc.alcGetString(self._device, alc.ALC_EXTENSIONS)
        if pyglet.compat_platform == 'darwin' or pyglet.compat_platform.startswith('linux'):
            return ctypes.cast(extensions, ctypes.c_char_p).value.split(' ')
        else:
            return _split_nul_strings(extensions)

    def have_extension(self, extension):
        return extension in self.get_extensions()

    def get_listener(self):
        return self._listener


class OpenALListener(AbstractListener):
    def __init__(self, driver):
        self._driver = driver

    def _set_volume(self, volume):
        volume = float(volume)
        with self._driver.lock:
            al.alListenerf(al.AL_GAIN, volume)
        self._volume = volume

    def _set_position(self, position):
        x, y, z = map(float, position)
        with self._driver.lock:
            al.alListener3f(al.AL_POSITION, x, y, z)
        self._position = position

    def _set_forward_orientation(self, orientation):
        val = (al.ALfloat * 6)(*map(float, (orientation + self._up_orientation)))
        with self._driver.lock:
            al.alListenerfv(al.AL_ORIENTATION, val)
        self._forward_orientation = orientation

    def _set_up_orientation(self, orientation):
        val = (al.ALfloat * 6)(*map(float, (self._forward_orientation + orientation)))
        with self._driver.lock:
            al.alListenerfv(al.AL_ORIENTATION, val)
        self._up_orientation = orientation

context = None

def create_audio_driver(device_name=None):
    global context
    context = OpenALDriver(device_name)
    if _debug:
        print('OpenAL', context.get_version())
    return context

def cleanup_audio_driver():
    global context

    if _debug:
        print("Cleaning up audio driver")

    if context:
        with context.lock:
            bufferPool.delete()

        context.delete()
        context = None

    if _debug:
        print("Cleaning done")

atexit.register(cleanup_audio_driver)

