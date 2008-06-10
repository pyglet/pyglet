#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import threading
import time

import mt_media

import pyglet
_debug = pyglet.options['debug_media']

class SilentAudioPlayer(mt_media.AbstractAudioPlayer):
    # When playing video, length of audio (in secs) to buffer ahead.
    _buffer_time = 0.4

    # Minimum number of bytes to request from source
    _min_update_bytes = 1024

    def __init__(self, source_group, player):
        super(SilentAudioPlayer, self).__init__(source_group, player)

        # Reference timestamp
        self._timestamp = 0.

        # System time of reference timestamp to interpolate from
        self._timestamp_time = time.time()

        # Last timestamp recorded by worker thread
        self._worker_timestamp = 0.

        # Queued events (used by worked exclusively except for clear).
        self._events = []

        # Lock required for changes to timestamp and events variables above.
        self._lock = threading.Lock()

        # Actual play state.
        self._playing = False

        # Be nice to avoid creating this thread if user doesn't care about EOS
        # events and there's no video format. XXX
        self._worker_thread = threading.Thread(target=self._worker_func)
        self._worker_thread.setDaemon(True)
        self._worker_thread.start()

    def delete(self):
        # TODO kill thread
        pass

    def play(self):
        if self._playing:
            return

        self._playing = True
        self._timestamp_time = time.time()

    def stop(self):
        if not self._playing:
            return

        self._timestamp = self.get_time()
        self._playing = False

    def seek(self, timestamp):
        self._lock.acquire()
        self._timestamp = timestamp
        self._worker_timestamp = timestamp
        self._timestamp_time = time.time()
        self._lock.release()

    def clear(self):
        self._lock.acquire()
        self._events = []
        self._lock.release()

    def get_time(self):
        if self._playing:
            return self._timestamp + (time.time() - self._timestamp_time)
        else:
            return self._timestamp

    def _worker_func(self):
        # Amount of audio data "buffered" (in secs)
        buffered_time = 0.

        self._lock.acquire()
        self._worker_timestamp = 0.0
        self._lock.release()

        while True:
            self._lock.acquire()

            # Use up "buffered" audio based on amount of time passed.
            timestamp = self.get_time()
            buffered_time -= timestamp - self._worker_timestamp
            self._worker_timestamp = timestamp

            if _debug:
                print 'timestamp: %f' % timestamp

            # Dispatch events
            events = self._events # local var ok within this lock
            while events and events[0].timestamp <= timestamp:
                events[0]._sync_dispatch_to_player(self.player)
                del events[0]

            if events:
                next_event_timestamp = events[0].timestamp
            else:
                next_event_timestamp = None

            self._lock.release()

            # Calculate how much data to request from source
            secs = self._buffer_time - buffered_time
            bytes = secs * self.source_group.audio_format.bytes_per_second
            if _debug:
                print 'need to get %d bytes (%f secs)' % (bytes, secs)

            # No need to get data, sleep until next event or buffer update
            # time instead.
            if bytes < self._min_update_bytes:
                sleep_time = buffered_time / 2
                if next_event_timestamp is not None:
                    sleep_time = min(sleep_time, 
                                     next_event_timestamp - timestamp)
                if _debug:
                    print 'sleeping for %f' % sleep_time
                time.sleep(sleep_time)
                continue

            # Pull audio data from source
            audio_data = self.source_group.get_audio_data(int(bytes))
            if not audio_data:
                mt_media.MediaEvent(timestamp,
                    'on_source_group_eos')._sync_dispatch_to_player(self.player)
                break

            # Pretend to buffer audio data, collect events.
            buffered_time += audio_data.duration
            self._lock.acquire()
            self._events.extend(audio_data.events)
            self._lock.release()

            if _debug:
                print 'got %s secs of audio data' % audio_data.duration
                print 'now buffered to %f' % buffered_time
                print 'events: %r' % events

class SilentAudioDriver(mt_media.AbstractAudioDriver):
    def create_audio_player(self, source_group, player):
        return SilentAudioPlayer(source_group, player)

def create_audio_driver():
    return SilentAudioDriver()

