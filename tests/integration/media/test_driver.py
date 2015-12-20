"""Test a specific audio driver (either for platform or silent). Only checks the use of the
interface. Any playback is silent."""
from __future__ import absolute_import, print_function
from future import standard_library
standard_library.install_aliases()
from builtins import object

from tests import mock
import queue
import pytest
import time

import pyglet
#pyglet.options['debug_media'] = True
#pyglet.options['debug_media_buffers'] = True

import pyglet.app
from pyglet.media.drivers import silent
from pyglet.media.drivers.silent import SilentAudioDriver
from pyglet.media.sources import SourceGroup
from pyglet.media.sources.procedural import Silence

from tests.annotations import Platform
from ..event_loop_test_base import event_loop


def _delete_driver():
    if hasattr(pyglet.media.drivers._audio_driver, 'delete'):
        pyglet.media.drivers._audio_driver.delete()
    pyglet.media.drivers._audio_driver = None

def test_get_platform_driver():
    driver = pyglet.media.drivers.get_audio_driver()
    assert driver is not None
    assert not isinstance(driver, SilentAudioDriver), 'Cannot load audio driver for your platform'
    _delete_driver()


def test_get_silent_driver():
    driver = pyglet.media.drivers.get_silent_audio_driver()
    assert driver is not None
    assert isinstance(driver, SilentAudioDriver)
    _delete_driver()


class MockPlayer(object):
    def __init__(self, event_loop):
        self.queue = queue.Queue()
        self.event_loop = event_loop

    def dispatch_event(self, event_type, *args):
        self.queue.put((event_type, args))
        self.event_loop.interrupt_event_loop()

    def wait_for_event(self, timeout, *event_types):
        end_time = time.time() + timeout
        try:
            while time.time() < end_time:
                self.event_loop.run_event_loop(duration=end_time-time.time())
                event_type, args = self.queue.get_nowait()
                if event_type in event_types:
                    return event_type, args
        except queue.Empty:
            return None, None

    def wait_for_all_events(self, timeout, *expected_events):
        expected_events = list(expected_events)
        received_events = []
        while expected_events:
            event_type, args = self.wait_for_event(timeout, *expected_events)
            if not event_type:
                pytest.fail('Timeout before all events have been received. Still waiting for: '
                        + ','.join(expected_events))
            else:
                expected_events.remove(event_type)
                received_events.append((event_type, args))
        return received_events


@pytest.fixture
def player(event_loop):
    return MockPlayer(event_loop)


class SilentTestSource(Silence):
    def __init__(self, duration, sample_rate=44800, sample_size=16):
        super(Silence, self).__init__(duration, sample_rate, sample_size)
        self._bytes_read = 0

    def get_audio_data(self, bytes):
        data = super(Silence, self).get_audio_data(bytes)
        if data:
            self._bytes_read += data.length
        return data

    def has_fully_played(self):
        return self._bytes_read == self._max_offset


def get_drivers():
    drivers = [silent]
    ids = ['Silent']

    try:
        from pyglet.media.drivers import pulse
        drivers.append(pulse)
        ids.append('PulseAudio')
    except:
        pass

    try:
        if pyglet.compat_platform not in Platform.LINUX:
            # Segmentation fault in OpenAL on Ubuntu 14.10, so for now disabling this test for Linux

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
    driver = request.param.create_audio_driver()
    assert driver is not None
    def fin():
        driver.delete()
    request.addfinalizer(fin)
    return driver


def _create_source_group(*sources):
    source_group = SourceGroup(sources[0].audio_format, None)
    for source in sources:
        source_group.queue(source)
    return source_group


def test_create_destroy(driver):
    driver.delete()


def test_create_audio_player(driver, player):
    source_group = _create_source_group(Silence(1.))
    audio_player = driver.create_audio_player(source_group, player)
    audio_player.delete()


def test_audio_player_play(driver, player):
    source = SilentTestSource(.1)
    source_group = _create_source_group(source)

    audio_player = driver.create_audio_player(source_group, player)
    try:
        audio_player.play()
        player.wait_for_all_events(1., 'on_eos', 'on_source_group_eos')
        assert source.has_fully_played(), 'Source not fully played'

    finally:
        audio_player.delete()


def test_audio_player_play_multiple(driver, player):
    sources = (SilentTestSource(.1), SilentTestSource(.1))
    source_group = _create_source_group(*sources)

    audio_player = driver.create_audio_player(source_group, player)
    try:
        audio_player.play()
        player.wait_for_all_events(1., 'on_eos', 'on_eos', 'on_source_group_eos')
        for source in sources:
            assert source.has_fully_played(), 'Source not fully played'

    finally:
        audio_player.delete()


def test_audio_player_add_to_paused_group(driver, player):
    """This is current behaviour when adding a sound of the same format as the previous to a
    player paused due to end of stream for previous sound."""
    source = SilentTestSource(.1)
    source_group = _create_source_group(source)

    audio_player = driver.create_audio_player(source_group, player)
    try:
        audio_player.play()
        player.wait_for_all_events(1., 'on_eos', 'on_source_group_eos')

        source2 = SilentTestSource(.1)
        source_group.queue(source2)
        audio_player.play()
        player.wait_for_all_events(1., 'on_eos', 'on_source_group_eos')
        assert source2.has_fully_played(), 'Source not fully played'

    finally:
        audio_player.delete()


def test_audio_player_delete_driver_with_players(driver, player):
    """Delete a driver with active players. Should not cause problems."""
    source = SilentTestSource(10.)
    source_group = _create_source_group(source)

    audio_player = driver.create_audio_player(source_group, player)
    audio_player.play()

