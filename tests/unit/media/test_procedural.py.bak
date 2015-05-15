from ctypes import sizeof
import unittest

from pyglet.compat import bytes_type
from pyglet.media.sources.procedural import *


class ProceduralSourceTest(object):
    """Simple test to check procedural sources provide data."""
    source_class = None

    def test_default(self):
        source = self.source_class(1.)
        self._test_total_duration(source)

    def test_sample_size_8(self):
        source = self.source_class(1., sample_size=8)
        self._test_total_duration(source)

    def test_sample_rate_11025(self):
        source = self.source_class(1., sample_rate=11025)
        self._test_total_duration(source)

    def _test_total_duration(self, source):
        total_bytes = source.audio_format.bytes_per_second
        self._check_audio_data(source, total_bytes, 1.)

    def _check_audio_data(self, source, expected_bytes, expected_duration):
        data = source.get_audio_data(expected_bytes + 100)
        self.assertIsNotNone(data)
        self.assertAlmostEqual(expected_bytes, data.length, delta=20)
        self.assertAlmostEqual(expected_duration, data.duration)

        self.assertIsNotNone(data.data)
        if isinstance(data.data, bytes_type):
            self.assertAlmostEqual(expected_bytes, len(data.data), delta=20)
        else:
            self.assertAlmostEqual(expected_bytes, sizeof(data.data), delta=20)

        # Should now be out of data
        last_data = source.get_audio_data(100)
        self.assertIsNone(last_data)

    def test_seek_default(self):
        source = self.source_class(1.)
        self._test_seek(source)

    def test_seek_sample_size_8(self):
        source = self.source_class(1., sample_size=8)
        self._test_seek(source)

    def _test_seek(self, source):
        seek_time = .5
        bytes_left = source.audio_format.bytes_per_second *.5
        source.seek(seek_time)
        self._check_audio_data(source, bytes_left, .5)


class SilenceTest(ProceduralSourceTest, unittest.TestCase):
    source_class = Silence


class WhiteNoiseTest(ProceduralSourceTest, unittest.TestCase):
    source_class = WhiteNoise


class SineTest(ProceduralSourceTest, unittest.TestCase):
    source_class = Sine


class SawTest(ProceduralSourceTest, unittest.TestCase):
    source_class = Saw


class SquareTest(ProceduralSourceTest, unittest.TestCase):
    source_class = Square

