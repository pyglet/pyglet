import unittest

import pyglet
from pyglet.media.drivers.silent import SilentAudioDriver


class GetMediaDriverTestCase(unittest.TestCase):
    def test_get_platform_driver(self):
        driver = pyglet.media.drivers.get_audio_driver()
        self.assertIsNotNone(driver)
        self.assertFalse(isinstance(driver, SilentAudioDriver), msg='Cannot load audio driver for your platform')

    def test_get_silent_driver(self):
        driver = pyglet.media.drivers.get_silent_audio_driver()
        self.assertIsNotNone(driver)
        self.assertIsInstance(driver, SilentAudioDriver)
