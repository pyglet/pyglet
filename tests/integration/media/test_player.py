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
from pyglet.media.procedural import Silence
from .mock_player import MockPlayer


class PlayerTest(MockPlayer, Player):
    pass


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


def test_multiple_fire_and_forget_players():
    """
    Test an issue where the driver crashed when starting multiple players, but not keeping a
    reference to these players.
    """
    for _ in range(10):
        Silence(1).play()
    time.sleep(1)
