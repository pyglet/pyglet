
import pytest
from tests import mock
import time

import pyglet
_debug = False
pyglet.options['debug_media'] = _debug

from pyglet.media import Player
from pyglet.media.synthesis import Silence
from .mock_player import MockPlayer


class PlayerTest(MockPlayer, Player):
    pass


@pytest.fixture
def player(event_loop):
    return PlayerTest(event_loop)


class SilentTestSource(Silence):
    def __init__(self, duration, frequency=440, sample_rate=44800, envelope=None):
        super().__init__(duration, frequency, sample_rate, envelope)
        self.bytes_read = 0

    def get_audio_data(self, nbytes):
        data = super().get_audio_data(nbytes)
        if data is not None:
            self.bytes_read += data.length
        return data

    @property
    def max_offset(self):
        return self._max_offset


def test_player_play(player):
    source = SilentTestSource(.1)
    player.queue(source)

    player.play()
    player.wait_for_all_events(
        1.,
        'on_eos',
        'on_player_eos'
    )
    assert source.bytes_read == source.max_offset, 'Source not fully played'


def test_player_play_multiple(player):
    sources = (SilentTestSource(.1), SilentTestSource(.1))
    for source in sources:
        player.queue(source)

    player.play()
    player.wait_for_all_events(
        1.,
        'on_eos',
        'on_player_next_source',
        'on_eos',
        'on_player_eos'
    )
    for source in sources:
        assert source.bytes_read == source.max_offset, 'Source not fully played'


def test_multiple_fire_and_forget_players():
    """
    Test an issue where the driver crashed when starting multiple players, but not
    keeping a reference to these players.
    """
    for _ in range(10):
        Silence(1).play()
    time.sleep(1)


def test_player_silent_audio_driver(player):
    with mock.patch('pyglet.media.player.get_audio_driver') as get_audio_driver_mock:
        get_audio_driver_mock.return_value = None
        source = SilentTestSource(.1)
        player.queue(source)
        player.play()

        player.wait_for_all_events(
            1.,
            'on_eos',
            'on_player_eos')
