"""Test a specific audio driver for platform. Only checks the use of the
interface. Any playback is silent."""

import pytest
import time

import pyglet
_debug = False
pyglet.options['debug_media'] = _debug
pyglet.options['debug_media_buffers'] = _debug

import pyglet.app
from pyglet.media.synthesis import Silence

from .mock_player import MockPlayer


class MockPlayerWithMockTime(MockPlayer):

    @property
    def time(self):
        return 0


@pytest.fixture
def player(event_loop):
    return MockPlayerWithMockTime(event_loop)


class SilentTestSource(Silence):
    def __init__(self, duration, frequency=440, sample_rate=44800, envelope=None):
        super().__init__(duration, frequency, sample_rate, envelope)
        self.bytes_read = 0

    def get_audio_data(self, nbytes, compensation_time=0.0):
        data = super(Silence, self).get_audio_data(nbytes, compensation_time)
        if data is not None:
            self.bytes_read += data.length
        return data

    def has_fully_played(self):
        return self.bytes_read == self._max_offset


def get_drivers():
    drivers = []
    ids = []

    try:
        from pyglet.media.drivers import silent
        drivers.append(silent)
        ids.append('Silent')
    except:
        pass

    try:
        from pyglet.media.drivers import pulse
        drivers.append(pulse)
        ids.append('PulseAudio')
    except:
        pass

    try:
        from pyglet.media.drivers import openal
        drivers.append(openal)
        ids.append('OpenAL')
    except:
        pass

    try:
        from pyglet.media.drivers import directsound
        drivers.append(directsound)
        ids.append('DirectSound')
    except:
        pass

    try:
        from pyglet.media.drivers import xaudio2
        drivers.append(xaudio2)
        ids.append('XAudio2')
    except:
        pass


    return {'params': drivers, 'ids': ids}


@pytest.fixture(**get_drivers())
def driver(request):
    if _debug:
        print('Create driver @ {}'.format(time.time()))
    driver = request.param.create_audio_driver()
    assert driver is not None
    def fin():
        driver.delete()
    request.addfinalizer(fin)
    return driver


def test_create_destroy(driver):
    driver.delete()


def test_create_audio_player(driver, player):
    source = Silence(1.)
    audio_player = driver.create_audio_player(source, player)
    audio_player.delete()


def test_audio_player_clear(driver, player):
    """Test clearing all buffered data."""
    source = SilentTestSource(10.)

    audio_player = driver.create_audio_player(source, player)
    try:
        audio_player.play()
        player.wait(.5)
        assert 0. < audio_player.get_time() < 5.

        audio_player.stop()
        source.seek(5.)
        audio_player.clear()
        audio_player.play()
        player.wait(.3)
        assert 5. <= audio_player.get_time() < 10.

    finally:
        audio_player.delete()


def test_audio_player_time(driver, player):
    """Test retrieving current timestamp from player."""
    source = SilentTestSource(10.)

    audio_player = driver.create_audio_player(source, player)
    try:
        audio_player.play()
        last_time = audio_player.get_time()
        # Needs to run until at least the initial buffer is processed. Ideal time is 1 sec, so run
        # more than 1 sec.
        for _ in range(15):
            player.wait(.1)
            assert last_time < audio_player.get_time()
            last_time = audio_player.get_time()
            if _debug:
                print('='*80)
                print('Time:', last_time)
                print('Bytes read:', source.bytes_read)
                print('='*80)

    finally:
        audio_player.delete()
