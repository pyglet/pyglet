from __future__ import print_function
from future import standard_library
standard_library.install_aliases()

import gc
import pytest
from tests import mock
import time
import unittest

import pyglet
_debug = False
pyglet.options['debug_media'] = _debug
pyglet.options['debug_media_buffers'] = _debug

from pyglet.media import Player
from pyglet.media.sources.procedural import Silence


class PlayerTest(Player):
    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.events = []
        super(PlayerTest, self).__init__()

    def dispatch_event(self, event_type, *args):
        super(PlayerTest, self).dispatch_event(event_type, *args)
        if _debug:
            print('PlayerTest: event {} received @ {}'.format(event_type, time.time()))
        self.events.append((event_type, args))
        self.event_loop.interrupt_event_loop()

    def wait_for_event(self, timeout, *event_types):
        end_time = time.time() + timeout

        while time.time() < end_time:
            if _debug:
                print('PlayerTest: run for {} sec @ {}'.format(end_time-time.time(),
                                                               time.time()))
            self.event_loop.run_event_loop(duration=end_time-time.time())
            if not self.events:
                continue
            event_type, args = self.events.pop()
            if event_type in event_types:
                return event_type, args
        return None, None

    def wait_for_all_events(self, timeout, *expected_events):
        if _debug:
            print('Wait for events @ {}'.format(time.time()))
        end_time = time.time() + timeout
        expected_events = list(expected_events)
        received_events = []
        while expected_events:
            event_type, args = self.wait_for_event(timeout, *expected_events)
            if _debug:
                print('PlayerTest: got event {} @ {}'.format(event_type, time.time()))
            if event_type is None and time.time() >= end_time:
                pytest.fail('Timeout before all events have been received. Still waiting for: '
                        + ','.join(expected_events))
            elif event_type is not None:
                if event_type in expected_events:
                    expected_events.remove(event_type)
                received_events.append((event_type, args))
        return received_events

    def wait(self, timeout):
        end_time = time.time() + timeout
        while time.time() < end_time:
            duration = max(.01, end_time-time.time())
            self.event_loop.run_event_loop(duration=duration)
        #assert time.time() - end_time < .1


@pytest.fixture
def player(event_loop):
    return PlayerTest(event_loop)

class SilentTestSource(Silence):
    def __init__(self, duration, sample_rate=44800, sample_size=16):
        super(Silence, self).__init__(duration, sample_rate, sample_size)
        self.bytes_read = 0

    def get_audio_data(self, nbytes, compensation_time=0.0):
        data = super(Silence, self).get_audio_data(nbytes, compensation_time)
        if data is not None:
            self.bytes_read += data.length
        return data

    def has_fully_played(self):
        return self.bytes_read == self._max_offset



def test_player_play(player):
    source = SilentTestSource(.1)
    player.queue(source)

    player.play()
    player.wait_for_all_events(1., 
        'on_eos', 'on_player_eos')
    assert source.has_fully_played(), 'Source not fully played'

def test_player_play_multiple(player):
    sources = (SilentTestSource(.1), SilentTestSource(.1))
    for source in sources:
        player.queue(source)

    player.play()
    player.wait_for_all_events(1., 
        'on_eos', 'on_player_next_source', 'on_eos', 'on_player_eos')
    for source in sources:
        assert source.has_fully_played(), 'Source not fully played'

