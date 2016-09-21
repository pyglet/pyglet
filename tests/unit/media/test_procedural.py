from __future__ import absolute_import
from builtins import bytes, object
from ctypes import sizeof
from io import BytesIO
import unittest

from pyglet.media.sources.procedural import *


local_dir = os.path.dirname(__file__)
test_data_path = os.path.abspath(os.path.join(local_dir, '..', '..', 'data'))
del local_dir


def get_test_data_file(*file_parts):
    """Get a file from the test data directory in an OS independent way.

    Supply relative file name as you would in os.path.join().
    """
    return os.path.join(test_data_path, *file_parts)


class ProceduralSourceTest(object):
    """Simple test to check procedural sources provide data."""
    source_class = None

    def test_default(self):
        source = self.source_class(1.)
        self._test_total_duration(source)
        if self.source_class is not WhiteNoise:
            self._test_generated_bytes(source)

    def test_sample_size_8(self):
        source = self.source_class(1., sample_size=8)
        self._test_total_duration(source)
        if self.source_class is not WhiteNoise:
            self._test_generated_bytes(source, sample_size=8)

    def test_sample_rate_11025(self):
        source = self.source_class(1., sample_rate=11025)
        self._test_total_duration(source)
        if self.source_class is not WhiteNoise:
            self._test_generated_bytes(source, sample_rate=11025)

    def _test_total_duration(self, source):
        total_bytes = source.audio_format.bytes_per_second
        self._check_audio_data(source, total_bytes, 1.)

    def _check_audio_data(self, source, expected_bytes, expected_duration):
        data = source.get_audio_data(expected_bytes + 100)
        self.assertIsNotNone(data)
        self.assertAlmostEqual(expected_bytes, data.length, delta=20)
        self.assertAlmostEqual(expected_duration, data.duration)

        self.assertIsNotNone(data.data)
        if isinstance(data.data, (bytes, str)):
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
        bytes_left = source.audio_format.bytes_per_second * .5
        source.seek(seek_time)
        self._check_audio_data(source, bytes_left, .5)

    def _test_generated_bytes(self, source, sample_rate=44800, sample_size=16):
        source_name = self.source_class.__name__.lower()
        filename = "procedural_{0}_{1}_{2}_1ch.wav".format(
            source_name, sample_size, sample_rate)

        with open(get_test_data_file('media', filename), 'rb') as f:
            loaded_bytes = f.read()
            source.seek(0)
            generated_data = source.get_audio_data(source._max_offset)
            bytes_buffer = BytesIO(generated_data.data)
            # Compare raw bytes, ignoring the loaded file's wave header:
            assert bytes_buffer.getvalue() == loaded_bytes[44:]


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


class FMTest(ProceduralSourceTest, unittest.TestCase):
    source_class = FM

