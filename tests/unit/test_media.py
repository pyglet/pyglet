import ctypes
import mock
import os
import unittest

from pyglet import media
from pyglet.compat import asbytes


class AudioFormatTestCase(unittest.TestCase):
    def test_equality_true(self):
        af1 = media.AudioFormat(2, 8, 44100)
        af2 = media.AudioFormat(2, 8, 44100)
        self.assertEqual(af1, af2)

    def test_equality_false(self):
        channels = [1, 2]
        sample_sizes = [8, 16]
        sample_rates = [11025, 22050, 44100]

        formats = [media.AudioFormat(c, s, r) for c in channels for s in sample_sizes for r in sample_rates]
        while formats:
           a = formats.pop()
           for b in formats:
               self.assertNotEqual(a, b)

    def test_bytes_per(self):
        af1 = media.AudioFormat(1, 8, 22050)
        af2 = media.AudioFormat(2, 16, 44100)

        self.assertEqual(af1.bytes_per_sample, 1)
        self.assertEqual(af1.bytes_per_second, 22050)

        self.assertEqual(af2.bytes_per_sample, 4)
        self.assertEqual(af2.bytes_per_second, 176400)


class AudioDataTestCase(unittest.TestCase):
    def generate_random_string_data(self, length):
        return os.urandom(length)

    def create_string_buffer(self, data):
        return ctypes.create_string_buffer(data)

    def test_consume_part_of_data(self):
        audio_format = media.AudioFormat(1, 8, 11025)
        duration = 1.0
        length = int(duration * audio_format.bytes_per_second)
        data = self.generate_random_string_data(length)

        audio_data = media.AudioData(data, length, 0.0, duration, (media.MediaEvent(0.0, 'event'),))

        chunk_duration = 0.1
        chunk_size = int(chunk_duration * audio_format.bytes_per_second)
        self.assertLessEqual(chunk_size, length)

        audio_data.consume(chunk_size, audio_format)

        self.assertEqual(audio_data.length, length - chunk_size)
        self.assertAlmostEqual(audio_data.duration, duration - chunk_duration, places=2)
        self.assertAlmostEqual(audio_data.timestamp, chunk_duration, places=2)

        self.assertEqual(audio_data.get_string_data(), data[chunk_size:])

        self.assertTupleEqual(audio_data.events, ())

    def test_consume_too_much_data(self):
        audio_format = media.AudioFormat(1, 8, 11025)
        duration = 1.0
        length = int(duration * audio_format.bytes_per_second)
        data = self.generate_random_string_data(length)

        audio_data = media.AudioData(data, length, 0.0, duration, (media.MediaEvent(0.0, 'event'),))

        chunk_duration = 1.1
        chunk_size = int(chunk_duration * audio_format.bytes_per_second)
        self.assertGreater(chunk_size, length)

        audio_data.consume(chunk_size, audio_format)

        self.assertEqual(audio_data.length, 0)
        self.assertAlmostEqual(audio_data.duration, 0.0, places=2)
        self.assertAlmostEqual(audio_data.timestamp, duration, places=2)

        self.assertEqual(audio_data.get_string_data(), '')

        self.assertTupleEqual(audio_data.events, ())

    def test_consume_non_str_data(self):
        audio_format = media.AudioFormat(1, 8, 11025)
        duration = 1.0
        length = int(duration * audio_format.bytes_per_second)
        data = self.generate_random_string_data(length)
        non_str_data = self.create_string_buffer(data)

        audio_data = media.AudioData(non_str_data, length, 0.0, duration, (media.MediaEvent(0.0, 'event'),))

        chunk_duration = 0.1
        chunk_size = int(chunk_duration * audio_format.bytes_per_second)
        self.assertLessEqual(chunk_size, length)

        audio_data.consume(chunk_size, audio_format)

        self.assertEqual(audio_data.length, length - chunk_size)
        self.assertAlmostEqual(audio_data.duration, duration - chunk_duration, places=2)
        self.assertAlmostEqual(audio_data.timestamp, chunk_duration, places=2)

        self.assertEqual(audio_data.get_string_data(), data[chunk_size:])

        self.assertTupleEqual(audio_data.events, ())


class SourceTestCase(unittest.TestCase):
    @mock.patch('pyglet.media.ManagedSoundPlayer')
    def test_play(self, player_mock):
        source = media.Source()
        returned_player = source.play()

        self.assertIsNotNone(returned_player)
        returned_player.play.assert_called_once_with()
        returned_player.queue.assert_called_once_with(source)


class StreamingSourceTestCase(unittest.TestCase):
    def test_can_queue_only_once(self):
        source = media.StreamingSource()
        self.assertFalse(source.is_queued)

        ret = source._get_queue_source()
        self.assertIs(ret, source)
        self.assertTrue(source.is_queued)

        with self.assertRaises(media.MediaException):
            source._get_queue_source()

class StaticSourceTestCase(unittest.TestCase):
    def create_valid_mock_source(self, bitrate=8, channels=1):
        self.mock_source = mock.MagicMock()
        self.mock_queue_source = self.mock_source._get_queue_source.return_value

        byte_rate = bitrate >> 3
        self.mock_data = ['a'*22050*byte_rate*channels, 'b'*22050*byte_rate*channels, 'c'*11025*byte_rate*channels]
        self.mock_audio_data = ''.join(self.mock_data)
        def _get_audio_data(_):
            if not self.mock_data:
                return None
            data = self.mock_data.pop(0)
            return media.AudioData(data, len(data), 0.0, 1.0, ())
        self.mock_queue_source.get_audio_data.side_effect = _get_audio_data

        type(self.mock_queue_source).audio_format = mock.PropertyMock(return_value=media.AudioFormat(channels, bitrate, 11025))
        type(self.mock_queue_source).video_format = mock.PropertyMock(return_value=None)


    def test_reads_all_data_on_init(self):
        self.create_valid_mock_source()
        static_source = media.StaticSource(self.mock_source)

        self.assertEqual(len(self.mock_data), 0, 'All audio data should be read')
        self.assertEqual(self.mock_queue_source.get_audio_data.call_count, 4, 'Data should be retrieved until empty')

        # Try to read all data plus more, more should be ignored
        returned_audio_data = static_source._get_queue_source().get_audio_data(len(self.mock_audio_data)+1024)
        self.assertEqual(returned_audio_data.get_string_data(), self.mock_audio_data, 'All data from the mock should be returned')
        self.assertAlmostEqual(returned_audio_data.duration, 5.0)

    def test_video_not_supported(self):
        self.create_valid_mock_source()
        type(self.mock_queue_source).video_format = mock.PropertyMock(return_value=media.VideoFormat(800, 600))

        with self.assertRaises(NotImplementedError):
            static_source = media.StaticSource(self.mock_source)

    def test_seek(self):
        self.create_valid_mock_source()
        static_source = media.StaticSource(self.mock_source)

        queue_source = static_source._get_queue_source()
        queue_source.seek(1.0)
        returned_audio_data = queue_source.get_audio_data(len(self.mock_audio_data))
        self.assertAlmostEqual(returned_audio_data.duration, 4.0)
        self.assertEqual(returned_audio_data.length, len(self.mock_audio_data)-11025)
        self.assertEqual(returned_audio_data.get_string_data(), self.mock_audio_data[11025:], 'Should have seeked past 1 second')

    def test_multiple_queued(self):
        self.create_valid_mock_source()
        static_source = media.StaticSource(self.mock_source)

        # Check that seeking and consuming on queued instances does not affect others
        queue_source1 = static_source._get_queue_source()
        queue_source1.seek(1.0)

        queue_source2 = static_source._get_queue_source()

        returned_audio_data = queue_source2.get_audio_data(len(self.mock_audio_data))
        self.assertAlmostEqual(returned_audio_data.duration, 5.0)
        self.assertEqual(returned_audio_data.length, len(self.mock_audio_data), 'Should contain all data')


        returned_audio_data = queue_source1.get_audio_data(len(self.mock_audio_data))
        self.assertAlmostEqual(returned_audio_data.duration, 4.0)
        self.assertEqual(returned_audio_data.length, len(self.mock_audio_data)-11025)
        self.assertEqual(returned_audio_data.get_string_data(), self.mock_audio_data[11025:], 'Should have seeked past 1 second')

    def test_seek_aligned_to_sample_size(self):
        self.create_valid_mock_source(bitrate=16, channels=2)
        static_source = media.StaticSource(self.mock_source)

        queue_source = static_source._get_queue_source()
        queue_source.seek(0.01)
        returned_audio_data = queue_source.get_audio_data(len(self.mock_audio_data))
        self.assertEqual(returned_audio_data.length % 4, 0, 'Must seek and return aligned to 4 byte chunks')

    def test_consume_aligned_to_sample_size(self):
        self.create_valid_mock_source(bitrate=16, channels=2)
        static_source = media.StaticSource(self.mock_source)

        queue_source = static_source._get_queue_source()
        returned_audio_data = queue_source.get_audio_data(1000*4+3)
        self.assertEqual(returned_audio_data.length % 4, 0, 'Must return aligned to 4 byte chunks')


class SourceGroupTestCase(unittest.TestCase):
    def test_pause(self):
        pass

    def test_loop(self):
        pass

    def test_advance(self):
        pass

    def test_empty_sources_list(self):
        pass


class PlayerTestCase(unittest.TestCase):
    pass
