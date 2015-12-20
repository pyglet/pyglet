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

import threading
import time

from . import interface
from pyglet.app import WeakSet
from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer
from pyglet.media.events import MediaEvent
from pyglet.media.exceptions import MediaException
from pyglet.media.listener import AbstractListener
from pyglet.media.threads import MediaThread

import pyglet
_debug = pyglet.options['debug_media']


class OpenALWorker(MediaThread):
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
                if _debug:
                    print('OpenALWorker: woke up@{}'.format(time.time()))
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

                    if write_size > 0 and write_size > player.min_buffer_size:
                        player.refill(write_size)
                    else:
                        sleep_time = self._nap_time
                else:
                    if _debug:
                        print('OpenALWorker: No active players')
                    sleep_time = self._sleep_time

                if sleep_time != -1:
                    self.sleep(sleep_time)
                else:
                    # We MUST sleep, or we will starve pyglet's main loop.  It
                    # also looks like if we don't sleep enough, we'll starve out
                    # various updates that stop us from properly removing players
                    # that should be removed.
                    self.sleep(self._nap_time)

    def add(self, player):
        assert player is not None
        if _debug:
            print('OpenALWorker: player added')
        with self.condition:
            self.players.add(player)
            self.condition.notify()

    def remove(self, player):
        if _debug:
            print('OpenALWorker: player removed')
        with self.condition:
            if player in self.players:
                self.players.remove(player)
            self.condition.notify()


class OpenALDriver(AbstractAudioDriver):
    def __init__(self, device_name=None):
        super(OpenALDriver, self).__init__()

        # TODO devices must be enumerated on Windows, otherwise 1.0 context is
        # returned.

        self.device = interface.OpenALDevice(device_name)
        self.context = self.device.create_context()
        self.context.make_current()

        self.have_1_1 = self.have_version(1, 1) and False

        self.lock = threading.Lock()

        self._listener = OpenALListener(self)
        self._players = WeakSet()

        # Start worker thread
        self.worker = OpenALWorker()
        self.worker.start()

    def create_audio_player(self, source_group, player):
        assert self.device is not None, "Device was closed"
        if self.have_1_1:
            player = OpenALAudioPlayer11(self, source_group, player)
        else:
            player = OpenALAudioPlayer10(self, source_group, player)
        self._players.add(player)
        return player

    def delete(self):
        self.worker.stop()
        for player in self._players:
            player.delete()
        with self.lock:
            if self.context is not None:
                self.context.delete()
                self.context = None
            if self.device is not None:
                self.device.delete()
                self.device = None

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

    def __enter__(self):
        self.lock.acquire()

    def __exit__(self, exc_type, exc_value, traceback):
        self.lock.release()


class OpenALListener(AbstractListener):
    def __init__(self, driver):
        self._driver = driver
        self._al_listener = interface.OpenALListener()

    def _set_volume(self, volume):
        with self._driver:
            self._al_listener.gain = volume
        self._volume = volume

    def _set_position(self, position):
        with self._driver:
            self._al_listener.position = position
        self._position = position

    def _set_forward_orientation(self, orientation):
        with self._driver:
            self._al_listener = orientation + self._up_orientation
        self._forward_orientation = orientation

    def _set_up_orientation(self, orientation):
        with self._driver:
            self._al_listener.orientation = self._forward_orientation + orientation
        self._up_orientation = orientation


class OpenALAudioPlayer11(AbstractAudioPlayer):
    #: Minimum size of an OpenAL buffer worth bothering with, in bytes
    min_buffer_size = 512

    #: Aggregate (desired) buffer size, in seconds
    _ideal_buffer_size = 1.

    def __init__(self, driver, source_group, player):
        super(OpenALAudioPlayer11, self).__init__(source_group, player)
        self.driver = driver
        self.source = driver.context.create_source()

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

        self.refill(self.ideal_buffer_size)

    def __del__(self):
        try:
            self.delete()
        except:
            pass

    def delete(self):
        if _debug:
            print('OpenALAudioPlayer.delete()')

        if not self.source:
            return

        self.driver.worker.remove(self)

        with self._lock:
            with self.driver.lock:
                self.source.delete()
            self.source = None

    @property
    def ideal_buffer_size(self):
        return int(self._ideal_buffer_size * self.source_group.audio_format.bytes_per_second)

    def play(self):
        if _debug:
            print('OpenALAudioPlayer.play()')

        assert self.driver is not None
        assert self.source is not None

        with self.driver:
            if not self.source.is_playing:
                self.source.play()
        self._playing = True

        self.driver.worker.add(self)

    def stop(self):
        if _debug:
            print('OpenALAudioPlayer.stop()')

        assert self.driver is not None
        assert self.source is not None

        self._pause_timestamp = self.get_time()

        with self.driver:
            self.source.pause()
        self._playing = False

        self.driver.worker.remove(self)

    def clear(self):
        if _debug:
            print('OpenALAudioPlayer.clear()')

        assert self.driver is not None
        assert self.source is not None

        with self._lock:
            with self.driver:
                self.source.stop()
                self._playing = False

                del self._events[:]
                self._underrun_timestamp = None
                self._buffer_timestamps = [None for _ in self._buffer_timestamps]

    def _update_play_cursor(self):
        assert self.driver is not None
        assert self.source is not None

        with self._lock:
            self._handle_processed_buffers()

            # Update play cursor using buffer cursor + estimate into current
            # buffer
            with self.driver:
                self._play_cursor = self._buffer_cursor + self.source.byte_offset

            self._dispatch_events()

    def _handle_processed_buffers(self):
        with self._lock:
            with self.driver:
                processed = self.source.unqueue_buffers()

            if processed > 0:
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

        return processed

    def _dispatch_events(self):
        with self._lock:
            while self._events and self._events[0][0] <= self._play_cursor:
                _, event = self._events.pop(0)
                event._sync_dispatch_to_player(self.player)

    def get_write_size(self):
        with self._lock:
            self._update_play_cursor()
            write_size = self.ideal_buffer_size - \
                (self._write_cursor - self._play_cursor)

        if _debug:
            print("Write size {} bytes".format(write_size))
        assert write_size >= 0
        return write_size

    def refill(self, write_size):
        if _debug:
            print('refill', write_size)

        with self._lock:

            while write_size > self.min_buffer_size:
                audio_data = self.source_group.get_audio_data(write_size)
                if not audio_data:
                    if _debug:
                        print('No audio data left')
                    if self._has_underrun():
                        if _debug:
                            print('Underrun')
                        MediaEvent(0, 'on_eos')._sync_dispatch_to_player(self.player)
                        MediaEvent(0, 'on_source_group_eos')._sync_dispatch_to_player(self.player)
                    break

                if _debug:
                    print('Writing {} bytes'.format(audio_data.length))
                self._queue_events(audio_data)
                self._queue_audio_data(audio_data)
                write_size -= audio_data.length

            # Check for underrun stopping playback
            with self.driver:
                if self._playing and not self.source.is_playing:
                    if _debug:
                        print('underrun')
                    self.source.play()

    def _queue_audio_data(self, audio_data):
        with self.driver:
            buf = self.driver.context.buffer_pool.get_buffer()
            buf.data(audio_data, self.source_group.audio_format)
            self.source.queue_buffer(buf)

        self._write_cursor += audio_data.length
        self._buffer_sizes.append(audio_data.length)
        self._buffer_timestamps.append(audio_data.timestamp)

    def _queue_events(self, audio_data):
        for event in audio_data.events:
            cursor = self._write_cursor + event.timestamp * \
                self.source_group.audio_format.bytes_per_second
            self._events.append((cursor, event))

    def _has_underrun(self):
        with self.driver:
            return self.source.buffers_queued == 0

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
        with self.driver:
            self.source.gain = volume

    def set_position(self, position):
        with self.driver:
            self.source.position = position

    def set_min_distance(self, min_distance):
        with self.driver:
            self.source.reference_distance = min_distance

    def set_max_distance(self, max_distance):
        with self.driver:
            self.source.max_distance = max_distance

    def set_pitch(self, pitch):
        with self.driver:
            self.source.pitch = pitch

    def set_cone_orientation(self, cone_orientation):
        with self.driver:
            self.source.direction = cone_orientation

    def set_cone_inner_angle(self, cone_inner_angle):
        with self.driver:
            self.source.cone_inner_angle = cone_inner_angle

    def set_cone_outer_angle(self, cone_outer_angle):
        with self.driver:
            self.source.cone_outer_angle = cone_outer_angle

    def set_cone_outer_gain(self, cone_outer_gain):
        with self.driver:
            self.source.cone_outer_gain = cone_outer_gain


class OpenALAudioPlayer10(OpenALAudioPlayer11):
    """Player compatible with OpenAL version 1.0. This version needs to interpolate
    timestamps."""
    def __init__(self, driver, source_group, player):
        super(OpenALAudioPlayer10, self).__init__(driver, source_group, player)

        # OpenAL 1.0 timestamp interpolation: system time of current buffer
        # playback (best guess)
        self._buffer_system_time = time.time()

    def play(self):
        super(OpenALAudioPlayer10, self).play()
        self._buffer_system_time = time.time()

    def _update_play_cursor(self):
        assert self.driver is not None
        assert self.source is not None

        with self._lock:
            self._handle_processed_buffers()

            # Interpolate system time past buffer timestamp
            self._play_cursor = \
                self._buffer_cursor + int(
                    (time.time() - self._buffer_system_time) * \
                        self.source_group.audio_format.bytes_per_second)

            if _debug:
                print('Play cursor at {} bytes'.format(self._play_cursor))

            self._dispatch_events()

    def _handle_processed_buffers(self):
        with self._lock:
            processed = super(OpenALAudioPlayer10, self)._handle_processed_buffers()
            if processed > 0:
                self._buffer_system_time = time.time()

