from ctypes import sizeof
import unittest

from pyglet.compat import bytes_type
from pyglet.media.sources.procedural import *


class ProceduralSourceTest(object):
    """Simple test to check procedural sources provide data."""
    source_class = None

    def test_total_duration(self):
        source = self.source_class(1.)
        total_bytes = source.audio_format.bytes_per_second
        data = source.get_audio_data(total_bytes + 100)

        self.assertIsNotNone(data)
        self.assertAlmostEqual(total_bytes, data.length, delta=20)
        self.assertAlmostEqual(1., data.duration)

        self.assertIsNotNone(data.data)
        if isinstance(data.data, bytes_type):
            self.assertAlmostEqual(total_bytes, len(data.data), delta=20)
        else:
            self.assertAlmostEqual(total_bytes, sizeof(data.data), delta=20)


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

