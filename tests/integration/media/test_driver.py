import mock
import unittest

import pyglet
from pyglet.media.drivers import silent
from pyglet.media.drivers.silent import SilentAudioDriver
from pyglet.media.sources import SourceGroup
from pyglet.media.sources.procedural import Silence

pyglet.options['debug_media'] = True
pyglet.options['debug_media_buffers'] = True


class GetMediaDriverTestCase(unittest.TestCase):
    def test_get_platform_driver(self):
        driver = pyglet.media.drivers.get_audio_driver()
        self.assertIsNotNone(driver)
        self.assertFalse(isinstance(driver, SilentAudioDriver), msg='Cannot load audio driver for your platform')

    def test_get_silent_driver(self):
        driver = pyglet.media.drivers.get_silent_audio_driver()
        self.assertIsNotNone(driver)
        self.assertIsInstance(driver, SilentAudioDriver)


class _AudioDriverTestCase(unittest.TestCase):
    """Test a specific audio driver (either for platform or silent). Only checks the use of the
    interface. Any playback is silent."""

    driver = None

    @classmethod
    def setUpClass(cls):
        if cls.driver is None:
            raise unittest.SkipTest

    def test_create_destroy(self):
        driver = self.driver.create_audio_driver()
        self.assertIsNotNone(driver)
        del driver

    def test_create_audio_player(self):
        driver = self.driver.create_audio_driver()
        self.assertIsNotNone(driver)

        silence = Silence(1.)
        source_group = SourceGroup(silence.audio_format, None)
        source_group.queue(silence)
        player = mock.MagicMock()

        audio_player = driver.create_audio_player(source_group, player)
        audio_player.delete()



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
