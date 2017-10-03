"""Test a specific audio driver for platform. Only checks the use of the
interface. Any playback is silent."""
from __future__ import absolute_import, print_function

from tests import mock
import queue
import pytest
import time

import pyglet
_debug = False
pyglet.options['debug_media'] = _debug
pyglet.options['debug_media_buffers'] = _debug

import pyglet.app
from pyglet.media.sources import PlayList
from pyglet.media.sources.procedural import Silence


def _delete_driver():
    # if hasattr(pyglet.media.drivers._audio_driver, 'delete'):
    #     pyglet.media.drivers._audio_driver.delete()
    pyglet.media.drivers._audio_driver = None

def test_get_platform_driver():
    driver = pyglet.media.drivers.get_audio_driver()
    assert driver is not None
    assert driver is not None, 'Cannot load audio driver for your platform'
    _delete_driver()


class MockPlayer(object):
    def __init__(self, event_loop):
        self.queue = queue.Queue()
        self.event_loop = event_loop

    def dispatch_event(self, event_type, *args):
        if _debug:
            print('MockPlayer: event {} received @ {}'.format(event_type, time.time()))
        self.queue.put((event_type, args))
        self.event_loop.interrupt_event_loop()

    def wait_for_event(self, timeout, *event_types):
        end_time = time.time() + timeout
        try:
            while time.time() < end_time:
                if _debug:
                    print('MockPlayer: run for {} sec @ {}'.format(end_time-time.time(),
                                                                   time.time()))
                self.event_loop.run_event_loop(duration=end_time-time.time())
                event_type, args = self.queue.get_nowait()
                if event_type in event_types:
                    return event_type, args
        except queue.Empty:
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
                print('MockPlayer: got event {} @ {}'.format(event_type, time.time()))
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

    @property
    def time(self):
        return 0


@pytest.fixture
def player(event_loop):
    return MockPlayer(event_loop)


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


def get_drivers():
    drivers = []
    ids = []

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


def _create_play_list(*sources):
    play_list = PlayList()
    for source in sources:
        play_list.queue(source)
    return play_list


def test_create_destroy(driver):
    driver.delete()


def test_create_audio_player(driver, player):
    play_list = _create_play_list(Silence(1.))
    audio_player = driver.create_audio_player(play_list, player)
    audio_player.delete()


def test_audio_player_clear(driver, player):
    """Test clearing all buffered data."""
    source = SilentTestSource(10.)
    play_list = _create_play_list(source)

    audio_player = driver.create_audio_player(play_list, player)
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
    play_list = _create_play_list(source)

    audio_player = driver.create_audio_player(play_list, player)
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

