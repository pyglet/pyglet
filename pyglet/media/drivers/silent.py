#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import time

from pyglet.media import AbstractAudioPlayer, AbstractAudioDriver, \
                         MediaThread, MediaEvent

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
    _sleep_time = 0.2

    def __init__(self, source_group, player):
        super(SilentAudioPlayerPacketConsumer, self).__init__(source_group, player)

        # System time of first timestamp
        self._timestamp_time = None

        # List of buffered SilentAudioPacket
        self._packets = []
        self._packets_duration = 0
        self._events = []

        # Actual play state.
        self._playing = False

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

    def play(self):
        if _debug: 
            print 'SilentAudioPlayer.play'

        self._thread.condition.acquire()
        if not self._playing:
            self._playing = True
            self._timestamp_time = time.time()
            self._thread.condition.notify()
        self._thread.condition.release()

    def stop(self):
        if _debug:
            print 'SilentAudioPlayer.stop'

        self._thread.condition.acquire()
        if self._playing:
            timestamp = self.get_time()
            if self._packets:
                packet = self._packets[0]
                self._packets_duration -= timestamp - packet.timestamp
                packet.consume(timestamp - packet.timestamp)
            self._playing = False
        self._thread.condition.release()

    def clear(self):
        if _debug:
            print 'SilentAudioPlayer.clear'

        self._thread.condition.acquire()
        del self._packets[:]
        self._packets_duration = 0
        del self._events[:]
        self._thread.condition.release()

    def get_time(self):
        if _debug:
            print 'SilentAudioPlayer.get_time()'
        self._thread.condition.acquire()

        packets = self._packets

        if self._playing:
            # Consume timestamps
            result = None
            offset = time.time() - self._timestamp_time
            while packets:
                packet = packets[0]
                if offset > packet.duration:
                    del packets[0]
                    self._timestamp_time += packet.duration
                    offset -= packet.duration
                    self._packets_duration -= packet.duration
                else:
                    packet.consume(offset)
                    self._packets_duration -= offset
                    self._timestamp_time += offset
                    result = packet.timestamp
                    break
        else:
            # Paused
            if packets:
                result = packets[0].timestamp
            else:
                result = None

        self._thread.condition.release()

        if _debug:
            print 'SilentAudioPlayer.get_time() -> ', result
        return result

    # Worker func that consumes audio data and dispatches events
    def _worker_func(self):
        thread = self._thread
        #buffered_time = 0
        eos = False
        events = self._events

        while True:
            thread.condition.acquire()
            if thread.stopped or (eos and not events):
                thread.condition.release()
                break

            # Use up "buffered" audio based on amount of time passed.
            timestamp = self.get_time()
            if _debug:
                print 'timestamp: %r' % timestamp

            # Dispatch events
            while events and events[0].timestamp <= timestamp:
                events[0]._sync_dispatch_to_player(self.player)
                del events[0]

            # Calculate how much data to request from source
            secs = self._buffer_time - self._packets_duration
            bytes = secs * self.source_group.audio_format.bytes_per_second
            if _debug:
                print 'Trying to buffer %d bytes (%r secs)' % (bytes, secs)

            while bytes > self._min_update_bytes and not eos:
                # Pull audio data from source
                audio_data = self.source_group.get_audio_data(int(bytes))
                if not audio_data and not eos:
                    events.append(MediaEvent(timestamp, 'on_eos'))
                    events.append(MediaEvent(timestamp, 'on_source_group_eos'))
                    eos = True
                    break
    
                # Pretend to buffer audio data, collect events.
                if self._playing and not self._packets:
                    self._timestamp_time = time.time()
                self._packets.append(SilentAudioPacket(audio_data.timestamp,
                                                       audio_data.duration))
                self._packets_duration += audio_data.duration
                for event in audio_data.events:
                    event.timestamp += audio_data.timestamp
                    events.append(event)
                events.extend(audio_data.events)
                bytes -= audio_data.length

            sleep_time = self._sleep_time
            if not self._playing:
                sleep_time = None
            elif events and events[0].timestamp and timestamp:
                sleep_time = min(sleep_time, events[0].timestamp - timestamp)

            if _debug:
                print 'SilentAudioPlayer(Worker).sleep', sleep_time
            thread.sleep(sleep_time)
            
            thread.condition.release()

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

def create_audio_driver():
    return SilentAudioDriver()

