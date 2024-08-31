import os
import ctypes
import unittest
from unittest import mock


import pyglet
from pyglet.media.drivers.base import MediaEvent
from pyglet.media.codecs.base import *



def _bytes_from_audiodata(audio_data):
    return memoryview(audio_data.data).tobytes()


class AudioFormatTestCase(unittest.TestCase):
    def test_equality_true(self):
        af1 = AudioFormat(2, 8, 44100)
        af2 = AudioFormat(2, 8, 44100)
        self.assertEqual(af1, af2)

    def test_equality_false(self):
        channels = [1, 2]
        sample_sizes = [8, 16]
        sample_rates = [11025, 22050, 44100]

        formats = [AudioFormat(c, s, r) for c in channels for s in sample_sizes for r in sample_rates]
        while formats:
            a = formats.pop()
            for b in formats:
                self.assertNotEqual(a, b)

    def test_bytes_per(self):
        af1 = AudioFormat(1, 8, 22050)
        af2 = AudioFormat(2, 16, 44100)

        self.assertEqual(af1.bytes_per_frame, 1)
        self.assertEqual(af1.bytes_per_second, 22050)

        self.assertEqual(af2.bytes_per_frame, 4)
        self.assertEqual(af2.bytes_per_second, 176400)

    def test_alignment(self):
        af = AudioFormat(2, 16, 44100)

        self.assertEqual(af.align(2049), 2048)
        self.assertEqual(af.align(2048), 2048)
        self.assertEqual(af.align(2047), 2044)
        self.assertEqual(af.align(0), 0)
        self.assertEqual(af.align(-1), -4)
        self.assertEqual(af.align_ceil(2049), 2052)
        self.assertEqual(af.align_ceil(2048), 2048)
        self.assertEqual(af.align_ceil(2047), 2048)
        self.assertEqual(af.align_ceil(0), 0)
        self.assertEqual(af.align_ceil(-1), 0)

    def test_repr(self):
        af1 = AudioFormat(1, 8, 22050)
        self.assertEqual(repr(af1), 'AudioFormat(channels=1, sample_size=8, sample_rate=22050)')

        af2 = AudioFormat(2, 16, 44100)
        self.assertEqual(repr(af2), 'AudioFormat(channels=2, sample_size=16, sample_rate=44100)')


class AudioDataTestCase(unittest.TestCase):
    def generate_random_string_data(self, length):
        return os.urandom(length)

    def create_string_buffer(self, data):
        return ctypes.create_string_buffer(data)

    def test_pointer_bytes(self):
        source_bytes = self.generate_random_string_data(2048)
        assert len(source_bytes) == 2048

        audio_data = AudioData(source_bytes, 2048)

        self.assertIsInstance(audio_data.pointer, int)
        self.assertGreater(audio_data.pointer, 0)

        retrieved_bytes = ctypes.string_at(audio_data.pointer, audio_data.length)
        self.assertEqual(retrieved_bytes, source_bytes)

    def test_buffer_protocol(self):
        d0 = AudioData(b"01234567", 8)
        d1 = AudioData((ctypes.c_char * 24)(), 24)
        d2 = AudioData(bytearray(64), 64)

        self.assertEqual(_bytes_from_audiodata(d0), b"01234567")
        self.assertEqual(_bytes_from_audiodata(d1), b"\x00" * 24)
        self.assertEqual(_bytes_from_audiodata(d2), b"\x00" * 64)


class SourceTestCase(unittest.TestCase):
    @mock.patch('pyglet.media.player.Player')
    def test_play(self, player_mock):
        source = Source()
        returned_player = source.play()

        self.assertIsNotNone(returned_player)
        returned_player.play.assert_called_once_with()
        returned_player.queue.assert_called_once_with(source)

    @mock.patch('pyglet.media.codecs.base.Source.get_next_video_timestamp')
    @mock.patch('pyglet.media.codecs.base.Source.get_next_video_frame')
    def test_get_animation(self, mock_get_next_video_frame, mock_get_next_video_timestamp):
        def _next_timestamp():
            if _next_timestamp.timestamp < 100:
                _next_timestamp.timestamp += 1
                return float(_next_timestamp.timestamp / 10)
        def _next_frame():
            return _next_timestamp.timestamp
        _next_timestamp.timestamp = 0
        mock_get_next_video_frame.side_effect = _next_frame
        mock_get_next_video_timestamp.side_effect = _next_timestamp

        source = Source()
        source.video_format = VideoFormat(800, 600)

        animation = source.get_animation()
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, pyglet.image.Animation)
        self.assertEqual(len(animation.frames), 100)
        for frame in animation.frames:
            self.assertAlmostEqual(frame.duration, 0.1)

    @unittest.skip('pyglet.image.Animation does not like getting an empty list of frames.')
    def test_get_animation_no_video(self):
        source = Source()
        animation = source.get_animation()

        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, pyglet.image.Animation)
        self.assertEqual(len(animation.frames), 0)

    def test_can_queue_only_once(self):
        source = StreamingSource()
        self.assertFalse(source.is_player_source)

        ret = source.get_queue_source()
        self.assertTrue(ret.is_player_source)
        self.assertTrue(source.is_player_source)

        with self.assertRaises(MediaException):
            source.get_queue_source()

        ret.is_player_source = False
        self.assertFalse(ret.is_player_source)
        self.assertFalse(source.is_player_source)

        ret = source.get_queue_source()
        with self.assertRaises(MediaException):
            ret.get_queue_source()

    def test_queue_source(self):
        source = StreamingSource()
        qsource = source.get_queue_source()
        self.assertIs(qsource, source)
        self.assertTrue(qsource.is_player_source)


class StaticSourceTestCase(unittest.TestCase):
    def create_valid_mock_source(self, bitrate=8, channels=1):
        self.mock_source = mock.MagicMock()
        self.mock_queue_source = self.mock_source.get_queue_source.return_value

        byte_rate = bitrate >> 3
        self.mock_data = [b'a'*22050*byte_rate*channels,
                          b'b'*22050*byte_rate*channels,
                          b'c'*11025*byte_rate*channels]
        self.mock_data_length = sum(map(len, self.mock_data))
        self.mock_audio_data = b''.join(self.mock_data)
        def _get_audio_data(_):
            if not self.mock_data:
                return None
            data = self.mock_data.pop(0)
            return AudioData(data, len(data), 0.0, 1.0, ())
        self.mock_queue_source.get_audio_data.side_effect = _get_audio_data

        self.mock_queue_source.audio_format = AudioFormat(channels, bitrate, 11025)
        self.mock_queue_source.video_format = None
        self.mock_source.audio_format = AudioFormat(channels, bitrate, 11025)
        self.mock_source.video_format = None


    def test_reads_all_data_on_init(self):
        self.create_valid_mock_source()
        static_source = StaticSource(self.mock_source)

        self.assertEqual(len(self.mock_data), 0, 'All audio data should be read')
        self.assertEqual(self.mock_queue_source.get_audio_data.call_count, 4, 'Data should be retrieved until empty')

        # Try to read all data plus more, more should be ignored
        returned_audio_data = static_source.get_queue_source().get_audio_data(len(self.mock_audio_data) + 1024)
        self.assertEqual(_bytes_from_audiodata(returned_audio_data), self.mock_audio_data, 'All data from the mock should be returned')
        self.assertAlmostEqual(returned_audio_data.duration, 5.0)

    def test_video_not_supported(self):
        self.create_valid_mock_source()
        self.mock_queue_source.video_format = VideoFormat(800, 600)

        with self.assertRaises(NotImplementedError):
            static_source = StaticSource(self.mock_source)

    def test_seek(self):
        self.create_valid_mock_source()
        static_source = StaticSource(self.mock_source)

        queue_source = static_source.get_queue_source()
        queue_source.seek(1.0)
        returned_audio_data = queue_source.get_audio_data(len(self.mock_audio_data))
        self.assertAlmostEqual(returned_audio_data.duration, 4.0)
        self.assertEqual(returned_audio_data.length, len(self.mock_audio_data)-11025)
        self.assertEqual(_bytes_from_audiodata(returned_audio_data), self.mock_audio_data[11025:], 'Should have seeked past 1 second')

    def test_multiple_queued(self):
        self.create_valid_mock_source()
        static_source = StaticSource(self.mock_source)

        # Check that seeking and consuming on queued instances does not affect others
        queue_source1 = static_source.get_queue_source()
        queue_source1.seek(1.0)

        queue_source2 = static_source.get_queue_source()

        returned_audio_data = queue_source2.get_audio_data(len(self.mock_audio_data))
        self.assertAlmostEqual(returned_audio_data.duration, 5.0)
        self.assertEqual(returned_audio_data.length, len(self.mock_audio_data), 'Should contain all data')


        returned_audio_data = queue_source1.get_audio_data(len(self.mock_audio_data))
        self.assertAlmostEqual(returned_audio_data.duration, 4.0)
        self.assertEqual(returned_audio_data.length, len(self.mock_audio_data)-11025)
        self.assertEqual(_bytes_from_audiodata(returned_audio_data), self.mock_audio_data[11025:], 'Should have seeked past 1 second')

    def test_seek_aligned_to_sample_size_2_bytes(self):
        self.create_valid_mock_source(bitrate=16, channels=1)
        static_source = StaticSource(self.mock_source)

        queue_source = static_source.get_queue_source()
        queue_source.seek(0.01)
        returned_audio_data = queue_source.get_audio_data(len(self.mock_audio_data))
        self.assertEqual(returned_audio_data.length % 2, 0, 'Must seek and return aligned to 2 byte chunks')

    def test_seek_aligned_to_sample_size_4_bytes(self):
        self.create_valid_mock_source(bitrate=16, channels=2)
        static_source = StaticSource(self.mock_source)

        queue_source = static_source.get_queue_source()
        queue_source.seek(0.01)
        returned_audio_data = queue_source.get_audio_data(len(self.mock_audio_data))
        self.assertEqual(returned_audio_data.length % 4, 0, 'Must seek and return aligned to 4 byte chunks')

    def test_empty_source(self):
        """Test that wrapping an empty source does not cause trouble."""
        self.mock_source = mock.MagicMock()
        self.mock_queue_source = self.mock_source.get_queue_source.return_value

        self.mock_queue_source.audio_format = None
        self.mock_queue_source.video_format = None
        self.mock_source.audio_format = None
        self.mock_source.video_format = None

        static_source = StaticSource(self.mock_source)

        self.assertEqual(static_source.duration, 0.)
        self.assertIsNone(static_source.get_queue_source())

    def test_not_directly_queueable(self):
        """A StaticSource cannot be played directly. Its queue source returns a playable object."""
        self.create_valid_mock_source(bitrate=16, channels=2)
        static_source = StaticSource(self.mock_source)

        with self.assertRaises(RuntimeError):
            static_source.get_audio_data(1024)

    def test_run_empty(self):
        """When running out of data, return None"""
        self.create_valid_mock_source()
        static_source = StaticSource(self.mock_source)
        queue_source = static_source.get_queue_source()
        returned_audio_data = queue_source.get_audio_data(self.mock_data_length)
        self.assertIsNotNone(returned_audio_data)

        no_more_audio_data = queue_source.get_audio_data(1024)
        self.assertIsNone(no_more_audio_data)


@unittest.skip('Too dangerous to modify 2.0.x\'s SourceGroups, this test will fail for them')
class SourceGroupTestCase(unittest.TestCase):
    def test_empty(self):
        group = SourceGroup()
        self.assertIsNone(group.get_audio_data(2048))

    def test_functionality(self):
        fake_data = ((b'a', 1000, 0.5), (b'b', 40000, 2.0), (b'c', 20000, 4.0), (b'd', 9992, 4.0))
        audio_data = [AudioData(b * l, l) for b, l, _ in fake_data]
        audio_data[0].timestamp = 1.23

        expected_data = b''.join(d * l for d, l, _ in fake_data)
        expected_duration = sum(d for _, _, d in fake_data)
        total_length = len(expected_data)

        sources = [mock.MagicMock(audio_format=AudioFormat(2, 8, 11025)) for _ in range(4)]
        exhausted = [False] * 4

        for i, mock_source in enumerate(sources):
            def _get_audio_data(_, j=i):
                if exhausted[j]:
                    return None
                exhausted[j] = True
                return audio_data[j]

            mock_source.duration = fake_data[i][2]
            mock_source.get_audio_data.side_effect = _get_audio_data
            mock_source.get_queue_source.return_value = mock_source

        group = SourceGroup()
        for mock_source in sources:
            group.add(mock_source)

        ret_data = group.get_audio_data(total_length)
        self.assertEqual(expected_data, ret_data.data)
        self.assertAlmostEqual(ret_data.timestamp, 1.23)
        self.assertAlmostEqual(ret_data.duration, expected_duration)

    def test_inequal_audio_format(self):
        source_a = mock.Mock(audio_format=AudioFormat(1, 8, 44100), duration=None)
        source_b = mock.Mock(audio_format=AudioFormat(2, 16, 44100), duration=None)
        source_a.get_queue_source.return_value = source_a
        source_b.get_queue_source.return_value = source_b

        group = SourceGroup()
        group.add(source_a)
        self.assertEqual(group.audio_format, source_a.audio_format)
        with self.assertRaises(MediaException):
            group.add(source_b)
