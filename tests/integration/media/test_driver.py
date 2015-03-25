from __future__ import print_function

import mock
import Queue
import time
import unittest

import pyglet
import pyglet.app  # Make sure it is loaded before patching it
from pyglet.media.drivers import silent
from pyglet.media.drivers.silent import SilentAudioDriver
from pyglet.media.sources import SourceGroup
from pyglet.media.sources.procedural import Silence

from tests.annotations import Platform

pyglet.options['debug_media'] = True
pyglet.options['debug_media_buffers'] = True


class GetMediaDriverTestCase(unittest.TestCase):
    def test_get_platform_driver(self):
        driver = pyglet.media.drivers.get_audio_driver()
        self.assertIsNotNone(driver)
        self.assertFalse(isinstance(driver, SilentAudioDriver), msg='Cannot load audio driver for your platform')

        # Make sure driver is deleted before other tests
        if hasattr(pyglet.media.drivers._audio_driver, 'delete'):
            pyglet.media.drivers._audio_driver.delete()
        pyglet.media.drivers._audio_driver = None

    def test_get_silent_driver(self):
        driver = pyglet.media.drivers.get_silent_audio_driver()
        self.assertIsNotNone(driver)
        self.assertIsInstance(driver, SilentAudioDriver)

        # Make sure driver is deleted before other tests
        if hasattr(pyglet.media.drivers._silent_audio_driver, 'delete'):
            pyglet.media.drivers._silent_audio_driver.delete()
        pyglet.media.drivers._silent_audio_driver = None


class MockPlayer(object):
    def __init__(self):
        self.queue = Queue.Queue()

    def dispatch_event(self, event_type, *args):
        self.queue.put((event_type, args))

    def wait_for_event(self, timeout, *event_types):
        end_time = time.time() + timeout
        try:
            while time.time() < end_time:
                event_type, args = self.queue.get(timeout=end_time-time.time())
                if event_type in event_types:
                    return event_type, args
        except Queue.Empty:
            return None, None


class EventForwarder(object):
    def post_event(self, destination, event_type, *args):
        destination.dispatch_event(event_type, *args)


class _AudioDriverTestCase(unittest.TestCase):
    """Test a specific audio driver (either for platform or silent). Only checks the use of the
    interface. Any playback is silent."""

    driver = None

    @classmethod
    def setUpClass(cls):
        if cls.driver is None:
            raise unittest.SkipTest

    def wait_for_all_events(self, player, timeout, *expected_events):
        expected_events = list(expected_events)
        received_events = []
        while expected_events:
            event_type, args = player.wait_for_event(timeout, *expected_events)
            if not event_type:
                self.fail('Timeout before all events have been received. Still waiting for: '
                        + ','.join(expected_events))
            else:
                expected_events.remove(event_type)
                received_events.append((event_type, args))
        return received_events

    def create_source_group(self, *sources):
        source_group = SourceGroup(sources[0].audio_format, None)
        for source in sources:
            source_group.queue(source)
        return source_group

    def test_create_destroy(self):
        driver = self.driver.create_audio_driver()
        self.assertIsNotNone(driver)
        driver.delete()

    def test_create_audio_player(self):
        driver = self.driver.create_audio_driver()
        self.assertIsNotNone(driver)

        try:
            source_group = self.create_source_group(Silence(1.))
            player = mock.MagicMock()

            audio_player = driver.create_audio_player(source_group, player)
            audio_player.delete()
        finally:
            driver.delete()

    @mock.patch('pyglet.app.platform_event_loop', EventForwarder())
    def test_audio_player_play(self):
        driver = self.driver.create_audio_driver()
        self.assertIsNotNone(driver)

        try:
            source_group = self.create_source_group(Silence(.1))
            player = MockPlayer()

            audio_player = driver.create_audio_player(source_group, player)
            try:
                audio_player.play()
                self.wait_for_all_events(player, 0.2, 'on_eos', 'on_source_group_eos')

            finally:
                audio_player.delete()
        finally:
            driver.delete()

    @mock.patch('pyglet.app.platform_event_loop', EventForwarder())
    def test_audio_player_play_multiple(self):
        driver = self.driver.create_audio_driver()
        self.assertIsNotNone(driver)

        try:
            source_group = self.create_source_group(Silence(.1), Silence(.1))
            player = MockPlayer()

            audio_player = driver.create_audio_player(source_group, player)
            try:
                audio_player.play()
                self.wait_for_all_events(player, 0.3, 'on_eos', 'on_eos', 'on_source_group_eos')

            finally:
                audio_player.delete()
        finally:
            driver.delete()


class SilentAudioDriverTestCase(_AudioDriverTestCase):
    driver = silent


# Try to get all available drivers
try:
    from pyglet.media.drivers import pulse
    class PulseAudioDriverTestCase(_AudioDriverTestCase):
        driver = pulse
except:
    pass

try:
    if pyglet.compat_platform not in Platform.LINUX:
        # Segmentation fault in OpenAL on Ubuntu 14.10, so for now disabling this test for Linux

        from pyglet.media.drivers import openal
        class OpenALAudioDriverTestCase(_AudioDriverTestCase):
            driver = openal
except:
    pass

try:
    from pyglet.media.drivers import directsound
    class DirectSoundAudioDriverTestCase(_AudioDriverTestCase):
        driver = directsound
except:
    pass
