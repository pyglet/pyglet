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
import time

from pyglet.media.events import MediaEvent
from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer
from pyglet.media.threads import MediaThread

import pyglet
_debug = pyglet.options['debug_media']


class SilentAudioPacket(object):
    def __init__(self, timestamp, duration):
        self.timestamp = timestamp
        self.duration = duration

    def consume(self, dt):
        self.timestamp += dt
        self.duration -= dt


class SilentAudioPlayerPacketConsumer(AbstractAudioPlayer):
    # When playing video, length of audio (in secs) to buffer ahead.
    _buffer_time = 0.4

    # Minimum number of bytes to request from source
    _min_update_bytes = 1024

    # Maximum sleep time
    _max_sleep_time = 0.2

    def __init__(self, source_group, player):
        super(SilentAudioPlayerPacketConsumer, self).__init__(source_group, player)

        # System time of first timestamp
        self._last_system_time = None
        self._last_timestamp = 0.

        # Buffered audio data and events
        self._packets = []
        self._packets_duration = 0.
        self._events = []

        # Actual play state.
        self._playing = False
        self._eos = False

        # TODO Be nice to avoid creating this thread if user doesn't care
        #      about EOS events and there's no video format.
        # NOTE Use thread.condition as lock for all instance vars used by worker
        self._thread = MediaThread(target=self._worker_func)
        if source_group.audio_format:
            self._thread.start()

    def delete(self):
        if _debug:
            print 'SilentAudioPlayer.delete'
        self._thread.stop()
        with self._thread.condition:
            self._thread.condition.notify()

    def play(self):
        if _debug:
            print 'SilentAudioPlayer.play'

        with self._thread.condition:
            self._eos = False
            if not self._playing:
                self._playing = True
                self._last_system_time = time.time()
                self._thread.condition.notify()

    def stop(self):
        if _debug:
            print 'SilentAudioPlayer.stop'

        with self._thread.condition:
            if self._playing:
                self._consume_packets()
                self._playing = False

    def clear(self):
        if _debug:
            print 'SilentAudioPlayer.clear'

        with self._thread.condition:
            del self._packets[:]
            self._packets_duration = 0.
            del self._events[:]
            self._eos = False

    def get_time(self):
        with self._thread.condition:
            if self._playing:
                result = self._last_timestamp + self._calculate_offset()
            else:
                result = self._last_timestamp

        if _debug:
            print 'SilentAudioPlayer.get_time() -> ', result
        return result

    def _consume_packets(self):
        """Consume content of packets that should have been played back up to now."""
        with self._thread.condition:
            if self._playing:
                offset = self._calculate_offset()
                while self._packets:
                    current_packet = self._packets[0]
                    if offset > current_packet.duration:
                        del self._packets[0]
                        self._last_timestamp += current_packet.duration
                        offset -= current_packet.duration
                        self._packets_duration -= current_packet.duration
                    else:
                        current_packet.consume(offset)
                        self._packets_duration -= offset
                        self._last_timestamp += offset
                        result = current_packet.timestamp
                        break
                self._last_system_time = time.time()

    def _calculate_offset(self):
        """Calculate the current offset into the cached packages."""
        if self._last_system_time is None:
            return 0.

        offset = time.time() - self._last_system_time
        if offset > self._packets_duration:
            return self._packets_duration

        return offset

    def _buffer_data(self):
        """Read data from the audio source into the internal buffer."""
        with self._thread.condition:
            # Calculate how much data to request from source
            secs = self._buffer_time - self._packets_duration
            bytes_to_read = int(secs * self.source_group.audio_format.bytes_per_second)
            if _debug:
                print 'Trying to buffer %d bytes (%r secs)' % (bytes_to_read, secs)

            while bytes_to_read > self._min_update_bytes and not self._eos:
                # Pull audio data from source
                audio_data = self.source_group.get_audio_data(bytes_to_read)
                if not audio_data:
                    timestamp = self.get_time() + self._packets_duration
                    if _debug:
                        print('Soure group eos, adding events for {}'.format(timestamp))
                    self._events.append(MediaEvent(timestamp, 'on_eos'))
                    self._events.append(MediaEvent(timestamp, 'on_source_group_eos'))
                    self._eos = True
                    break
                else:
                    self._add_audio_data(audio_data)

                bytes_to_read -= audio_data.length

    def _add_audio_data(self, audio_data):
        """Add a package of audio data to the internal buffer. Update timestamps to reflect."""
        with self._thread.condition:
            if self._playing and not self._packets:
                # First packet, so need reference time
                self._timestamp_time = time.time()

            self._packets.append(SilentAudioPacket(audio_data.timestamp, audio_data.duration))
            self._packets_duration += audio_data.duration

            # Add events to internal list and adjust timestamp
            for event in audio_data.events:
                event.timestamp += audio_data.timestamp
                self._events.append(event)

    def _get_sleep_time(self):
        """Determine how long to sleep until next event or next batch of data needs to be read."""
        if not self._playing:
            # Not playing, so no need to wake up
            return None

        buffer_required = self._buffer_time - self._packets_duration
        if self._packets_duration < self._buffer_time/2 and not self._eos:
            # More buffering required
            return 0.

        if self._events and self._events[0].timestamp:
            time_to_next_event = self._events[0].timestamp - self.get_time()
            if time_to_next_event < self._max_sleep_time:
                return time_to_next_event

        if self._eos:
            # Nothing to read and no events to handle:
            return None

        # No buffering needed and not events soon, wake up after limited time
        return self._max_sleep_time

    def _dispatch_events(self):
        """Dispatch any events for the current timestamp."""
        timestamp = self.get_time()

        # Dispatch events
        while self._events and timestamp is not None:
            if (self._events[0].timestamp is None or
                self._events[0].timestamp <= timestamp):
                self._events[0]._sync_dispatch_to_player(self.player)
                del self._events[0]
            else:
                break

    # Worker func that consumes audio data and dispatches events
    def _worker_func(self):
        while True:
            with self._thread.condition:
                if self._thread.stopped:
                    break

                self._consume_packets()
                self._dispatch_events()
                self._buffer_data()

                sleep_time = self._get_sleep_time()
                if _debug:
                    print 'SilentAudioPlayer(Worker).sleep', sleep_time
                self._thread.sleep(sleep_time)


class SilentTimeAudioPlayer(AbstractAudioPlayer):
    # Note that when using this player (automatic if playing back video with
    # unsupported audio codec) no events are dispatched (because they are
    # normally encoded in the audio packet -- so no EOS events are delivered.
    # This is a design flaw.
    #
    # Also, seeking is broken because the timestamps aren't synchronized with
    # the source group.

    _time = 0.0
    _systime = None

    def play(self):
        self._systime = time.time()

    def stop(self):
        self._time = self.get_time()
        self._systime = None

    def delete(self):
        pass

    def clear(self):
        pass

    def get_time(self):
        if self._systime is None:
            return self._time
        else:
            return time.time() - self._systime + self._time

class SilentAudioDriver(AbstractAudioDriver):
    def create_audio_player(self, source_group, player):
        if source_group.audio_format:
            return SilentAudioPlayerPacketConsumer(source_group, player)
        else:
            return SilentTimeAudioPlayer(source_group, player)

    def get_listener(self):
        raise NotImplementedError('Silent audio driver does not support positional audio')

    def delete(self):
        pass

def create_audio_driver():
    return SilentAudioDriver()

