"""
Test the internal RIFF reader.
"""

import os
import unittest

from pyglet.media.codecs.wave import WaveSource

test_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'media'))


class RiffTest(unittest.TestCase):
    def test_pcm_16_11025_1ch(self):
        file_name = os.path.join(test_data_dir, 'alert_pcm_16_11025_1ch.wav')
        source = WaveSource(file_name)

        self._check_audio_format(source, 1, 16, 11025)
        self._check_data(source, 11584, 0.525)

    def test_pcm_16_22050_1ch(self):
        file_name = os.path.join(test_data_dir, 'alert_pcm_16_22050_1ch.wav')
        source = WaveSource(file_name)

        self._check_audio_format(source, 1, 16, 22050)
        self._check_data(source, 23166, 0.525)

    def test_pcm_8_22050_1ch(self):
        file_name = os.path.join(test_data_dir, 'alert_pcm_8_22050_1ch.wav')
        source = WaveSource(file_name)

        self._check_audio_format(source, 1, 8, 22050)
        self._check_data(source, 11583, 0.525)

    def test_seek(self):
        file_name = os.path.join(test_data_dir, 'alert_pcm_16_22050_1ch.wav')
        source = WaveSource(file_name)

        seek_time = 0.3
        seek_bytes = seek_time * source.audio_format.bytes_per_second
        source.seek(seek_time)
        self._check_data(source, 23166-seek_bytes, 0.225)

    def _check_audio_format(self, source, channels, sample_size, sample_rate):
        self.assertEqual(channels, source.audio_format.channels)
        self.assertEqual(sample_size, source.audio_format.sample_size)
        self.assertEqual(sample_rate, source.audio_format.sample_rate)

    def _check_data(self, source, expected_bytes, expected_duration):
        received_bytes = 0
        received_seconds = 0.
        bytes_to_read = 1024

        while True:
            data = source.get_audio_data(bytes_to_read)
            if data is None:
                break

            received_bytes += data.length
            received_seconds += data.duration

            self.assertEqual(data.length, len(data.data))

        self.assertAlmostEqual(expected_duration, received_seconds, places=1)
        self.assertAlmostEqual(expected_bytes, received_bytes, delta=5)

