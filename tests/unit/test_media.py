import ctypes
import mock
import os
import unittest

import pyglet
from pyglet import media
from pyglet.compat import asbytes
from pyglet.media import Player
from pyglet.media.events import MediaEvent
from pyglet.media.exceptions import MediaException
from pyglet.media.sources.base import *

#pyglet.options['debug_media'] = True


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

        self.assertEqual(af1.bytes_per_sample, 1)
        self.assertEqual(af1.bytes_per_second, 22050)

        self.assertEqual(af2.bytes_per_sample, 4)
        self.assertEqual(af2.bytes_per_second, 176400)

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

    def test_consume_part_of_data(self):
        audio_format = AudioFormat(1, 8, 11025)
        duration = 1.0
        length = int(duration * audio_format.bytes_per_second)
        data = self.generate_random_string_data(length)

        audio_data = AudioData(data, length, 0.0, duration, (MediaEvent(0.0, 'event'),))

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
        audio_format = AudioFormat(1, 8, 11025)
        duration = 1.0
        length = int(duration * audio_format.bytes_per_second)
        data = self.generate_random_string_data(length)

        audio_data = AudioData(data, length, 0.0, duration, (MediaEvent(0.0, 'event'),))

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
        audio_format = AudioFormat(1, 8, 11025)
        duration = 1.0
        length = int(duration * audio_format.bytes_per_second)
        data = self.generate_random_string_data(length)
        non_str_data = self.create_string_buffer(data)

        audio_data = AudioData(non_str_data, length, 0.0, duration, (MediaEvent(0.0, 'event'),))

        chunk_duration = 0.1
        chunk_size = int(chunk_duration * audio_format.bytes_per_second)
        self.assertLessEqual(chunk_size, length)

        audio_data.consume(chunk_size, audio_format)

        self.assertEqual(audio_data.length, length - chunk_size)
        self.assertAlmostEqual(audio_data.duration, duration - chunk_duration, places=2)
        self.assertAlmostEqual(audio_data.timestamp, chunk_duration, places=2)

        self.assertEqual(audio_data.get_string_data(), data[chunk_size:])

        self.assertTupleEqual(audio_data.events, ())

    def test_consume_only_events(self):
        audio_format = AudioFormat(1, 8, 11025)
        duration = 1.0
        length = int(duration * audio_format.bytes_per_second)
        data = self.generate_random_string_data(length)

        audio_data = AudioData(data, length, 0.0, duration, (MediaEvent(0.0, 'event'),))

        chunk_size = 0

        audio_data.consume(chunk_size, audio_format)

        self.assertEqual(audio_data.length, length)
        self.assertAlmostEqual(audio_data.duration, duration, places=2)
        self.assertAlmostEqual(audio_data.timestamp, 0., places=2)

        self.assertEqual(audio_data.get_string_data(), data)

        self.assertTupleEqual(audio_data.events, ())


class SourceTestCase(unittest.TestCase):
    @mock.patch('pyglet.media.Player')
    def test_play(self, player_mock):
        source = Source()
        returned_player = source.play()

        self.assertIsNotNone(returned_player)
        returned_player.play.assert_called_once_with()
        returned_player.queue.assert_called_once_with(source)

    @mock.patch('pyglet.media.sources.base.Source.get_next_video_timestamp')
    @mock.patch('pyglet.media.sources.base.Source.get_next_video_frame')
    def test_get_animation(self, mock_get_next_video_frame, mock_get_next_video_timestamp):
        def _next_timestamp():
            if _next_timestamp.timestamp < 100:
                _next_timestamp.timestamp += 1
                return float(_next_timestamp.timestamp/10.)
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


class StreamingSourceTestCase(unittest.TestCase):
    def test_can_queue_only_once(self):
        source = StreamingSource()
        self.assertFalse(source.is_queued)

        ret = source._get_queue_source()
        self.assertIs(ret, source)
        self.assertTrue(source.is_queued)

        with self.assertRaises(MediaException):
            source._get_queue_source()

class StaticSourceTestCase(unittest.TestCase):
    def create_valid_mock_source(self, bitrate=8, channels=1):
        self.mock_source = mock.MagicMock()
        self.mock_queue_source = self.mock_source._get_queue_source.return_value

        byte_rate = bitrate >> 3
        self.mock_data = ['a'*22050*byte_rate*channels, 'b'*22050*byte_rate*channels, 'c'*11025*byte_rate*channels]
        self.mock_data_length = sum(map(len, self.mock_data))
        self.mock_audio_data = ''.join(self.mock_data)
        def _get_audio_data(_):
            if not self.mock_data:
                return None
            data = self.mock_data.pop(0)
            return AudioData(data, len(data), 0.0, 1.0, ())
        self.mock_queue_source.get_audio_data.side_effect = _get_audio_data

        type(self.mock_queue_source).audio_format = mock.PropertyMock(return_value=AudioFormat(channels, bitrate, 11025))
        type(self.mock_queue_source).video_format = mock.PropertyMock(return_value=None)


    def test_reads_all_data_on_init(self):
        self.create_valid_mock_source()
        static_source = StaticSource(self.mock_source)

        self.assertEqual(len(self.mock_data), 0, 'All audio data should be read')
        self.assertEqual(self.mock_queue_source.get_audio_data.call_count, 4, 'Data should be retrieved until empty')

        # Try to read all data plus more, more should be ignored
        returned_audio_data = static_source._get_queue_source().get_audio_data(len(self.mock_audio_data)+1024)
        self.assertEqual(returned_audio_data.get_string_data(), self.mock_audio_data, 'All data from the mock should be returned')
        self.assertAlmostEqual(returned_audio_data.duration, 5.0)

    def test_video_not_supported(self):
        self.create_valid_mock_source()
        type(self.mock_queue_source).video_format = mock.PropertyMock(return_value=VideoFormat(800, 600))

        with self.assertRaises(NotImplementedError):
            static_source = StaticSource(self.mock_source)

    def test_seek(self):
        self.create_valid_mock_source()
        static_source = StaticSource(self.mock_source)

        queue_source = static_source._get_queue_source()
        queue_source.seek(1.0)
        returned_audio_data = queue_source.get_audio_data(len(self.mock_audio_data))
        self.assertAlmostEqual(returned_audio_data.duration, 4.0)
        self.assertEqual(returned_audio_data.length, len(self.mock_audio_data)-11025)
        self.assertEqual(returned_audio_data.get_string_data(), self.mock_audio_data[11025:], 'Should have seeked past 1 second')

    def test_multiple_queued(self):
        self.create_valid_mock_source()
        static_source = StaticSource(self.mock_source)

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

    def test_seek_aligned_to_sample_size_2_bytes(self):
        self.create_valid_mock_source(bitrate=16, channels=1)
        static_source = StaticSource(self.mock_source)

        queue_source = static_source._get_queue_source()
        queue_source.seek(0.01)
        returned_audio_data = queue_source.get_audio_data(len(self.mock_audio_data))
        self.assertEqual(returned_audio_data.length % 2, 0, 'Must seek and return aligned to 2 byte chunks')

    def test_consume_aligned_to_sample_size_2_bytes(self):
        self.create_valid_mock_source(bitrate=16, channels=1)
        static_source = StaticSource(self.mock_source)

        queue_source = static_source._get_queue_source()
        returned_audio_data = queue_source.get_audio_data(1000*2+1)
        self.assertEqual(returned_audio_data.length % 2, 0, 'Must return aligned to 2 byte chunks')

    def test_seek_aligned_to_sample_size_4_bytes(self):
        self.create_valid_mock_source(bitrate=16, channels=2)
        static_source = StaticSource(self.mock_source)

        queue_source = static_source._get_queue_source()
        queue_source.seek(0.01)
        returned_audio_data = queue_source.get_audio_data(len(self.mock_audio_data))
        self.assertEqual(returned_audio_data.length % 4, 0, 'Must seek and return aligned to 4 byte chunks')

    def test_consume_aligned_to_sample_size_4_bytes(self):
        self.create_valid_mock_source(bitrate=16, channels=2)
        static_source = StaticSource(self.mock_source)

        queue_source = static_source._get_queue_source()
        returned_audio_data = queue_source.get_audio_data(1000*4+3)
        self.assertEqual(returned_audio_data.length % 4, 0, 'Must return aligned to 4 byte chunks')

    def test_empty_source(self):
        """Test that wrapping an empty source does not cause trouble."""
        self.mock_source = mock.MagicMock()
        self.mock_queue_source = self.mock_source._get_queue_source.return_value

        type(self.mock_queue_source).audio_format = mock.PropertyMock(return_value=None)
        type(self.mock_queue_source).video_format = mock.PropertyMock(return_value=None)

        static_source = StaticSource(self.mock_source)

        self.assertEqual(static_source.duration, 0.)
        self.assertIsNone(static_source._get_queue_source())

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
        queue_source = static_source._get_queue_source()
        returned_audio_data = queue_source.get_audio_data(self.mock_data_length)
        self.assertIsNotNone(returned_audio_data)

        no_more_audio_data = queue_source.get_audio_data(1024)
        self.assertIsNone(no_more_audio_data)


class SourceGroupTestCase(unittest.TestCase):
    audio_format = AudioFormat(1, 8, 11025)
    video_format = VideoFormat(800, 600)

    def create_mock_source(self, duration, audio_data=None, video_frame=None):
        mock_source = mock.MagicMock()
        m = mock_source._get_queue_source.return_value
        type(m).audio_format = mock.PropertyMock(return_value=self.audio_format)
        type(m).video_format = mock.PropertyMock(return_value=self.video_format)
        type(m).duration = mock.PropertyMock(return_value=duration)
        m.get_audio_data.return_value = self.create_audio_data(duration, audio_data)
        m.get_next_video_timestamp.return_value=0.1
        m.get_next_video_frame.return_value=video_frame
        return mock_source

    def create_audio_data(self, duration=1., data=None):
        if data is None:
            return None

        audio_data = AudioData(data, len(data), 0., duration, [])
        return audio_data

    def test_queueing(self):
        source_group = SourceGroup(self.audio_format, None)
        self.assertFalse(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 0.)

        source1 = self.create_mock_source(1.)
        source_group.queue(source1)
        self.assertFalse(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 1.)

        source2 = self.create_mock_source(2.0)
        source_group.queue(source2)
        self.assertTrue(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 3.)

    def test_seek(self):
        source_group = SourceGroup(self.audio_format, None)
        source1 = self.create_mock_source(1.)
        source_group.queue(source1)
        source2 = self.create_mock_source(2.)
        source_group.queue(source2)

        source_group.seek(0.5)

        source1._get_queue_source.return_value.seek.assert_called_once_with(0.5)
        self.assertFalse(source2._get_queue_source.return_value.seek.called)

    def test_advance_eos_no_loop(self):
        """Test that the source group advances to the next source if eos is encountered and looping
        is not enabled"""
        source_group = SourceGroup(self.audio_format, None)
        source1 = self.create_mock_source(1., '1')
        source2 = self.create_mock_source(2., '2')
        source_group.queue(source1)
        source_group.queue(source2)

        self.assertTrue(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 3.)

        audio_data = source_group.get_audio_data(1024)
        self.assertEqual(audio_data.data, '1')
        self.assertAlmostEqual(audio_data.timestamp, 0.)
        self.assertTrue(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 3.)

        # Source 1 is eos, source 2 returns 1.0 seconds (of 2.0)
        source1._get_queue_source.return_value.get_audio_data.return_value = None
        source2._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='2')
        audio_data = source_group.get_audio_data(1024)
        self.assertEqual(audio_data.data, '2')
        self.assertAlmostEqual(audio_data.timestamp, 1.)
        self.assertFalse(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 2.)
        self.assertEqual(len(audio_data.events), 1)
        self.assertEqual(audio_data.events[0].event, 'on_eos')

        # Source 2 not eos yet
        source2._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='2')
        audio_data = source_group.get_audio_data(1024)
        self.assertEqual(audio_data.data, '2')
        self.assertAlmostEqual(audio_data.timestamp, 1.)
        self.assertFalse(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 2.)
        self.assertEqual(len(audio_data.events), 0)

        # Now source 2 is eos
        source2._get_queue_source.return_value.get_audio_data.return_value = None
        audio_data = source_group.get_audio_data(1024)
        self.assertIsNone(audio_data)
        self.assertFalse(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 2., msg='Last source is not removed')

    def test_loop(self):
        """Test that the source group seeks to the start of the current source if eos is reached
        and looping is enabled."""
        source_group = SourceGroup(self.audio_format, None)
        source_group.loop = True
        source1 = self.create_mock_source(1., '1')
        source2 = self.create_mock_source(2., '2')
        source_group.queue(source1)
        source_group.queue(source2)

        self.assertTrue(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 3.)
        self.assertTrue(source_group.loop)

        audio_data = source_group.get_audio_data(1024)
        self.assertEqual(audio_data.data, '1')
        self.assertAlmostEqual(audio_data.timestamp, 0.)
        self.assertTrue(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 3.)
        self.assertTrue(source_group.loop)

        # Source 1 is eos, seek resets it to start
        def seek(_):
            source1._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='1')
        source1._get_queue_source.return_value.seek.side_effect = seek
        source1._get_queue_source.return_value.get_audio_data.return_value = None
        audio_data = source_group.get_audio_data(1024)
        self.assertEqual(audio_data.data, '1')
        self.assertAlmostEqual(audio_data.timestamp, 1.)
        self.assertTrue(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 3.)
        self.assertEqual(len(audio_data.events), 1)
        self.assertEqual(audio_data.events[0].event, 'on_eos')
        self.assertTrue(source_group.loop)

    def test_loop_advance_on_eos(self):
        """Test advancing to the next source on eos when looping is enabled."""
        source_group = SourceGroup(self.audio_format, None)
        source_group.loop = True
        source1 = self.create_mock_source(1., '1')
        source2 = self.create_mock_source(2., '2')
        source_group.queue(source1)
        source_group.queue(source2)

        self.assertTrue(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 3.)
        self.assertTrue(source_group.loop)

        audio_data = source_group.get_audio_data(1024)
        self.assertEqual(audio_data.data, '1')
        self.assertAlmostEqual(audio_data.timestamp, 0.)
        self.assertTrue(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 3.)
        self.assertTrue(source_group.loop)

        # Request advance on eos
        source_group.next_source(immediate=False)
        source1._get_queue_source.return_value.get_audio_data.return_value = None
        source2._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='2')
        audio_data = source_group.get_audio_data(1024)
        self.assertEqual(audio_data.data, '2')
        self.assertAlmostEqual(audio_data.timestamp, 1.)
        self.assertFalse(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 2.)
        self.assertEqual(len(audio_data.events), 1)
        self.assertEqual(audio_data.events[0].event, 'on_eos')
        self.assertTrue(source_group.loop)

        # Source 2 still loops
        def seek(_):
            source2._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='2')
        source2._get_queue_source.return_value.seek.side_effect = seek
        source2._get_queue_source.return_value.get_audio_data.return_value = None
        audio_data = source_group.get_audio_data(1024)
        self.assertEqual(audio_data.data, '2')
        self.assertAlmostEqual(audio_data.timestamp, 3.)
        self.assertFalse(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 2.)
        self.assertEqual(len(audio_data.events), 1)
        self.assertEqual(audio_data.events[0].event, 'on_eos')
        self.assertTrue(source_group.loop)

    def test_loop_advance_immediate(self):
        """Test advancing immediately to the next source when looping is enabled."""
        source_group = SourceGroup(self.audio_format, None)
        source_group.loop = True
        source1 = self.create_mock_source(1., '1')
        source2 = self.create_mock_source(2., '2')
        source_group.queue(source1)
        source_group.queue(source2)

        self.assertTrue(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 3.)
        self.assertTrue(source_group.loop)

        audio_data = source_group.get_audio_data(1024)
        self.assertEqual(audio_data.data, '1')
        self.assertAlmostEqual(audio_data.timestamp, 0.)
        self.assertTrue(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 3.)
        self.assertTrue(source_group.loop)

        # Request advance immediately
        source_group.next_source(immediate=True)
        source1._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='1')
        source2._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='2')
        audio_data = source_group.get_audio_data(1024)
        self.assertEqual(audio_data.data, '2')
        self.assertAlmostEqual(audio_data.timestamp, 1.)
        self.assertFalse(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 2.)
        self.assertEqual(len(audio_data.events), 0)
        self.assertTrue(source_group.loop)

        # Source 2 still loops
        def seek(_):
            source2._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='2')
        source2._get_queue_source.return_value.seek.side_effect = seek
        source2._get_queue_source.return_value.get_audio_data.return_value = None
        audio_data = source_group.get_audio_data(1024)
        self.assertEqual(audio_data.data, '2')
        self.assertAlmostEqual(audio_data.timestamp, 3.)
        self.assertFalse(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 2.)
        self.assertEqual(len(audio_data.events), 1)
        self.assertEqual(audio_data.events[0].event, 'on_eos')
        self.assertTrue(source_group.loop)

    def test_empty_source_group(self):
        """Test an empty source group"""
        source_group = SourceGroup(self.audio_format, None)
        self.assertFalse(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 0.)
        self.assertIsNone(source_group.get_current_source())
        source_group.seek(1.)
        source_group.next_source()
        self.assertIsNone(source_group.get_audio_data(1024))
        self.assertAlmostEqual(source_group.translate_timestamp(1.), 1.)
        self.assertIsNone(source_group.get_next_video_timestamp())
        self.assertIsNone(source_group.get_next_video_frame())
        self.assertFalse(source_group.loop)

    def test_translate_timestamp(self):
        """Test that translate_timestamp works correctly with advancing and looping."""
        source_group = SourceGroup(self.audio_format, None)
        source_group.loop = True
        source1 = self.create_mock_source(1., '1')
        source2 = self.create_mock_source(2., '2')
        source_group.queue(source1)
        source_group.queue(source2)
        self.assertAlmostEqual(source_group.translate_timestamp(.5), .5)
        self.assertAlmostEqual(source_group.translate_timestamp(1.), 1.)

        # Loop source 1
        def seek(_):
            source1._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='1')
        source1._get_queue_source.return_value.seek.side_effect = seek
        source1._get_queue_source.return_value.get_audio_data.return_value = None
        source_group.get_audio_data(1024)
        self.assertAlmostEqual(source_group.translate_timestamp(1.5), .5)
        self.assertAlmostEqual(source_group.translate_timestamp(2.), 1.)

        # Loop source 1 again
        def seek(_):
            source1._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='1')
        source1._get_queue_source.return_value.seek.side_effect = seek
        source1._get_queue_source.return_value.get_audio_data.return_value = None
        source_group.get_audio_data(1024)
        self.assertAlmostEqual(source_group.translate_timestamp(2.5), .5)
        self.assertAlmostEqual(source_group.translate_timestamp(3.), 1.)

        # Advance to source 2
        source_group.next_source()
        self.assertAlmostEqual(source_group.translate_timestamp(3.5), .5)
        self.assertAlmostEqual(source_group.translate_timestamp(4.), 1.)

        # Loop source 2
        def seek(_):
            source2._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='2')
        source2._get_queue_source.return_value.seek.side_effect = seek
        source2._get_queue_source.return_value.get_audio_data.return_value = None
        source_group.get_audio_data(1024)
        self.assertAlmostEqual(source_group.translate_timestamp(5.5), .5)
        self.assertAlmostEqual(source_group.translate_timestamp(6.), 1.)

        # Also try going back to previous source
        self.assertAlmostEqual(source_group.translate_timestamp(.5), .5)
        self.assertAlmostEqual(source_group.translate_timestamp(1.5), .5)

        # And finally do not fail on None
        self.assertIsNone(source_group.translate_timestamp(None))

    def test_get_next_video_timestamp(self):
        source1 = self.create_mock_source(1., audio_data=None, video_frame='a')
        source2 = self.create_mock_source(2., audio_data=None, video_frame='b')
        source_group = SourceGroup(self.audio_format, self.video_format)
        source_group.queue(source1)
        source_group.queue(source2)

        timestamp = source_group.get_next_video_timestamp()
        self.assertAlmostEqual(timestamp, 0.1)

        source_group.next_source()
        timestamp = source_group.get_next_video_timestamp()
        self.assertAlmostEqual(timestamp, 1.1)

    def test_get_next_video_frame(self):
        source1 = self.create_mock_source(1., audio_data=None, video_frame='a')
        source2 = self.create_mock_source(2., audio_data=None, video_frame='b')
        source_group = SourceGroup(self.audio_format, self.video_format)
        source_group.queue(source1)
        source_group.queue(source2)

        self.assertEqual(source_group.get_next_video_frame(), 'a')

        source_group.next_source()
        self.assertEqual(source_group.get_next_video_frame(), 'b')


class PlayerTestCase(unittest.TestCase):
    # Default values to use
    audio_format_1 = AudioFormat(1, 8, 11025)
    audio_format_2 = AudioFormat(2, 8, 11025)
    audio_format_3 = AudioFormat(2, 16, 44100)
    video_format_1 = VideoFormat(800, 600)
    video_format_2 = VideoFormat(1920, 1280)
    video_format_2.frame_rate = 25

    def setUp(self):
        self.player = Player()

        self._get_audio_driver_patcher = mock.patch('pyglet.media.get_audio_driver')
        self.mock_get_audio_driver = self._get_audio_driver_patcher.start()
        self.mock_audio_driver = self.mock_get_audio_driver.return_value
        self.mock_audio_driver_player = self.mock_audio_driver.create_audio_player.return_value

        self._get_silent_audio_driver_patcher = mock.patch('pyglet.media.get_silent_audio_driver')
        self.mock_get_silent_audio_driver = self._get_silent_audio_driver_patcher.start()
        self.mock_silent_audio_driver = self.mock_get_silent_audio_driver.return_value
        self.mock_silent_audio_driver_player = self.mock_silent_audio_driver.create_audio_player.return_value

        self._clock_patcher = mock.patch('pyglet.clock')
        self.mock_clock = self._clock_patcher.start()

        self._texture_patcher = mock.patch('pyglet.image.Texture.create')
        self.mock_texture_create = self._texture_patcher.start()
        self.mock_texture = self.mock_texture_create.return_value
        # Need to do this as side_effect instead of return_value, or reset_mock will recurse
        self.mock_texture.get_transform.side_effect = lambda flip_y: self.mock_texture

        self.current_playing_source_group = None

    def tearDown(self):
        self._get_audio_driver_patcher.stop()
        self._get_silent_audio_driver_patcher.stop()
        self._clock_patcher.stop()
        self._texture_patcher.stop()

    def reset_mocks(self):
        # These mocks will recursively reset their children
        self.mock_get_audio_driver.reset_mock()
        self.mock_get_silent_audio_driver.reset_mock()
        self.mock_clock.reset_mock()
        self.mock_texture_create.reset_mock()

    def create_mock_source(self, audio_format, video_format):
        mock_source = mock.MagicMock()
        type(mock_source).audio_format = mock.PropertyMock(return_value=audio_format)
        type(mock_source).video_format = mock.PropertyMock(return_value=video_format)
        type(mock_source._get_queue_source.return_value).audio_format = mock.PropertyMock(return_value=audio_format)
        type(mock_source._get_queue_source.return_value).video_format = mock.PropertyMock(return_value=video_format)
        return mock_source

    def set_video_data_for_mock_source(self, mock_source, timestamp_data_pairs):
        """Make the given mock source return video data. Video data is given in pairs of timestamp
        and data to return."""
        def _get_frame():
            if timestamp_data_pairs:
                current_frame = timestamp_data_pairs.pop(0)
                return current_frame[1]
        def _get_timestamp():
            if timestamp_data_pairs:
                return timestamp_data_pairs[0][0]
        queue_source = mock_source._get_queue_source.return_value
        queue_source.get_next_video_timestamp.side_effect = _get_timestamp
        queue_source.get_next_video_frame.side_effect = _get_frame

    def assert_not_playing_yet(self, current_source=None):
        """Assert the the player did not start playing yet."""
        self.assertFalse(self.mock_get_audio_driver.called, msg='No audio driver required yet')
        self.assertAlmostEqual(self.player.time, 0.)
        self.assert_not_playing(current_source)

    def assert_not_playing(self, current_source=None):
        self._assert_playing(False, current_source)

    def assert_now_playing(self, current_source):
        self._assert_playing(True, current_source)

    def _assert_playing(self, playing, current_source=None):
        self.assertEqual(self.player.playing, playing)
        queued_source = (current_source._get_queue_source.return_value
                         if current_source is not None
                         else None)
        self.assertIs(self.player.source, queued_source)

    def assert_driver_player_created_for(self, *sources):
        """Assert that a driver specific audio player is created to play back given sources"""
        self._assert_player_created_for(self.mock_get_audio_driver, self.mock_audio_driver, *sources)

    def assert_silent_driver_player_created_for(self, *sources):
        """Assert that a silent audio player is created for given sources."""
        self._assert_player_created_for(self.mock_get_silent_audio_driver, self.mock_silent_audio_driver, *sources)

    def _assert_player_created_for(self, mock_get_audio_driver, mock_audio_driver, *sources):
        mock_get_audio_driver.assert_called_once_with()
        self.assertEqual(mock_audio_driver.create_audio_player.call_count, 1)
        call_args = mock_audio_driver.create_audio_player.call_args
        self.assertIsInstance(call_args[0][0], SourceGroup)
        self.assertIs(call_args[0][1], self.player)

        self.current_playing_source_group = call_args[0][0]
        self.assert_in_current_playing_source_group(*sources)

    def assert_no_new_driver_player_created(self):
        """Assert that no new driver specific audio player is created."""
        self.assertFalse(self.mock_get_audio_driver.called, msg='No new audio driver should be created')

    def assert_in_current_playing_source_group(self, *sources):
        self.assertIsNotNone(self.current_playing_source_group, msg='No previous call to create driver player')

        queue_sources = [source._get_queue_source.return_value for source in sources]
        self.assertListEqual(self.current_playing_source_group._sources, queue_sources)

    def assert_driver_player_destroyed(self):
        self.mock_audio_driver_player.delete.assert_called_once_with()

    def assert_driver_player_not_destroyed(self):
        self.assertFalse(self.mock_audio_driver_player.delete.called)

    def assert_silent_driver_player_destroyed(self):
        self.mock_silent_audio_driver_player.delete.assert_called_once_with()

    def assert_driver_player_started(self):
        self.mock_audio_driver_player.play.assert_called_once_with()

    def assert_driver_player_stopped(self):
        self.mock_audio_driver_player.stop.assert_called_once_with()

    def assert_driver_player_cleared(self):
        self.mock_audio_driver_player.clear.assert_called_once_with()

    def assert_source_seek(self, source, time):
        source._get_queue_source.return_value.seek.assert_called_once_with(time)

    def assert_new_texture_created(self, video_format):
        self.mock_texture_create.assert_called_once_with(video_format.width, video_format.height, rectangle=True)

    def assert_no_new_texture_created(self):
        self.assertFalse(self.mock_texture_create.called)

    def assert_texture_updated(self, frame_data):
        self.mock_texture.blit_into.assert_called_once_with(frame_data, 0, 0, 0)

    def assert_texture_not_updated(self):
        self.assertFalse(self.mock_texture.blit_into.called)

    def assert_update_texture_scheduled(self, period):
        self.mock_clock.schedule_interval.assert_called_once_with(self.player.update_texture, period)

    def assert_update_texture_unscheduled(self):
        self.mock_clock.unschedule.assert_called_once_with(self.player.update_texture)

    def pretend_driver_player_at_time(self, t):
        self.mock_audio_driver_player.get_time.return_value = t

    def test_queue_single_audio_source_and_play(self):
        """Queue a single audio source and start playing it."""

        mock_source = self.create_mock_source(self.audio_format_1, None)
        self.player.queue(mock_source)
        self.assert_not_playing_yet(mock_source)

        self.player.play()
        self.assert_driver_player_created_for(mock_source)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source)

    def test_queue_multiple_audio_sources_same_format_and_play(self):
        """Queue multiple audio sources using the same audio format and start playing."""
        mock_source1 = self.create_mock_source(self.audio_format_1, None)
        mock_source2 = self.create_mock_source(self.audio_format_1, None)
        mock_source3 = self.create_mock_source(self.audio_format_1, None)

        self.player.queue(mock_source1)
        self.assert_not_playing_yet(mock_source1)

        self.player.queue(mock_source2)
        self.assert_not_playing_yet(mock_source1)

        self.player.queue(mock_source3)
        self.assert_not_playing_yet(mock_source1)

        self.player.play()
        self.assert_driver_player_created_for(mock_source1, mock_source2, mock_source3)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source1)

    def test_queue_multiple_audio_sources_different_format_and_play_and_skip(self):
        """Queue multiple audio sources having different formats and start playing. Different
        formats should be played by seperate driver players."""
        mock_source1 = self.create_mock_source(self.audio_format_1, None)
        mock_source2 = self.create_mock_source(self.audio_format_2, None)
        mock_source3 = self.create_mock_source(self.audio_format_3, None)

        self.player.queue(mock_source1)
        self.assert_not_playing_yet(mock_source1)

        self.player.queue(mock_source2)
        self.assert_not_playing_yet(mock_source1)

        self.player.queue(mock_source3)
        self.assert_not_playing_yet(mock_source1)

        self.player.play()
        self.assert_driver_player_created_for(mock_source1)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source1)

        self.reset_mocks()
        self.player.next_source()
        self.assert_driver_player_destroyed()
        self.assert_driver_player_created_for(mock_source2)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source2)

        self.reset_mocks()
        self.player.next_source()
        self.assert_driver_player_destroyed()
        self.assert_driver_player_created_for(mock_source3)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source3)

    def test_queue_multiple_audio_sources_same_format_and_play_and_skip(self):
        """When multiple audio sources with the same format are queued, they are played using the
        same driver player. Skipping to the next source is just advancing the source group.
        """
        mock_source1 = self.create_mock_source(self.audio_format_1, None)
        mock_source2 = self.create_mock_source(self.audio_format_1, None)
        mock_source3 = self.create_mock_source(self.audio_format_1, None)

        self.player.queue(mock_source1)
        self.player.queue(mock_source2)
        self.player.queue(mock_source3)

        self.player.play()
        self.assert_driver_player_created_for(mock_source1, mock_source2, mock_source3)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source1)

        self.reset_mocks()
        self.player.next_source()
        self.assert_in_current_playing_source_group(mock_source2, mock_source3)
        self.assert_driver_player_not_destroyed()
        self.assert_no_new_driver_player_created()
        self.assert_now_playing(mock_source2)

        self.reset_mocks()
        self.player.next_source()
        self.assert_in_current_playing_source_group(mock_source3)
        self.assert_driver_player_not_destroyed()
        self.assert_no_new_driver_player_created()
        self.assert_now_playing(mock_source3)

    def test_on_eos_ignored(self):
        """The player receives on_eos for every source, but does not need to do anything."""
        mock_source1 = self.create_mock_source(self.audio_format_1, None)
        mock_source2 = self.create_mock_source(self.audio_format_1, None)
        mock_source3 = self.create_mock_source(self.audio_format_1, None)

        self.player.queue(mock_source1)
        self.player.queue(mock_source2)
        self.player.queue(mock_source3)

        self.player.play()
        self.assert_driver_player_created_for(mock_source1, mock_source2, mock_source3)
        self.assert_driver_player_started()

        self.reset_mocks()
        self.player.dispatch_event('on_eos')
        self.assert_driver_player_not_destroyed()
        # The following is not completely realistic, in normal cases the source group would have
        # advanced to the next source, but in this case we want to see it is also not manually
        # advanced by the player
        self.assert_in_current_playing_source_group(mock_source1, mock_source2, mock_source3)

    def test_on_source_group_eos_advance_to_next_group(self):
        """If a source group is depleted and a next group is available, start a new player for
        the next group."""
        mock_source1 = self.create_mock_source(self.audio_format_1, None)
        mock_source2 = self.create_mock_source(self.audio_format_2, None)
        mock_source3 = self.create_mock_source(self.audio_format_3, None)

        self.player.queue(mock_source1)
        self.player.queue(mock_source2)
        self.player.queue(mock_source3)
        self.assert_not_playing_yet(mock_source1)

        self.player.play()
        self.assert_driver_player_created_for(mock_source1)
        self.assert_driver_player_started()

        self.reset_mocks()
        self.player.dispatch_event('on_source_group_eos')
        self.assert_driver_player_destroyed()
        self.assert_driver_player_created_for(mock_source2)
        self.assert_now_playing(mock_source2)

    def test_player_stops_after_last_group_eos(self):
        """If the last or only source group is eos, the player stops."""
        mock_source = self.create_mock_source(self.audio_format_1, None)
        self.player.queue(mock_source)
        self.assert_not_playing_yet(mock_source)

        self.player.play()
        self.assert_driver_player_created_for(mock_source)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source)

        self.reset_mocks()
        self.player.dispatch_event('on_source_group_eos')
        self.assert_driver_player_destroyed()
        self.assert_not_playing(None)

    def test_eos_events(self):
        """Test receiving various eos events: on source eos, on source group eos and on player eos.
        """
        on_eos_mock = mock.MagicMock(return_value=None)
        self.player.event('on_eos')(on_eos_mock)
        on_source_group_eos_mock = mock.MagicMock(return_value=None)
        self.player.event('on_source_group_eos')(on_source_group_eos_mock)
        on_player_eos_mock = mock.MagicMock(return_value=None)
        self.player.event('on_player_eos')(on_player_eos_mock)

        def reset_eos_mocks():
            on_eos_mock.reset_mock()
            on_source_group_eos_mock.reset_mock()
            on_player_eos_mock.reset_mock()

        def assert_eos_events_received(on_eos=False, on_source_group_eos=False, on_player_eos=False):
            self.assertEqual(on_eos_mock.called, on_eos)
            self.assertEqual(on_source_group_eos_mock.called, on_source_group_eos)
            self.assertEqual(on_player_eos_mock.called, on_player_eos)

        mock_source1 = self.create_mock_source(self.audio_format_1, None)
        mock_source2 = self.create_mock_source(self.audio_format_1, None)
        mock_source3 = self.create_mock_source(self.audio_format_2, None)

        self.player.queue(mock_source1)
        self.player.queue(mock_source2)
        self.player.queue(mock_source3)
        self.assert_not_playing_yet(mock_source1)

        self.player.play()
        self.assert_driver_player_created_for(mock_source1, mock_source2)

        self.reset_mocks()
        reset_eos_mocks()
        # Pretend the current source in the group was eos and next source started
        self.current_playing_source_group.next_source()
        self.player.dispatch_event('on_eos')
        self.assert_driver_player_not_destroyed()
        assert_eos_events_received(on_eos=True)

        self.reset_mocks()
        reset_eos_mocks()
        # Pretend current source group is eos, triggers player to play next source group on a new
        # player
        self.player.dispatch_event('on_source_group_eos')
        self.assert_driver_player_destroyed()
        self.assert_driver_player_created_for(mock_source3)
        assert_eos_events_received(on_source_group_eos=True)

        self.reset_mocks()
        reset_eos_mocks()
        # Pretend current source group is eos. Should be no more source groups to play.
        self.player.dispatch_event('on_source_group_eos')
        self.assert_driver_player_destroyed()
        self.assert_not_playing(None)
        assert_eos_events_received(on_source_group_eos=True, on_player_eos=True)

    def test_pause_resume(self):
        """A stream can be paused. After that play will resume where paused."""
        mock_source = self.create_mock_source(self.audio_format_1, None)
        self.player.queue(mock_source)
        self.player.play()
        self.assert_driver_player_created_for(mock_source)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source)

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.5)
        self.player.pause()
        self.assert_driver_player_stopped()
        self.assert_driver_player_not_destroyed()

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.6)
        self.assertEqual(self.player.time, 0.5, msg='While paused, player should returned paused time')

        self.reset_mocks()
        self.player.play()
        self.assert_driver_player_started()
        self.assert_no_new_driver_player_created()
        self.assert_now_playing(mock_source)
        self.assertEqual(self.player.time, 0.6, msg='While playing, player should return time from driver player')

    def test_delete(self):
        """Test clean up of the player when delete() is called."""
        mock_source1 = self.create_mock_source(self.audio_format_1, None)
        mock_source2 = self.create_mock_source(self.audio_format_2, None)
        mock_source3 = self.create_mock_source(self.audio_format_3, None)

        self.player.queue(mock_source1)
        self.player.queue(mock_source2)
        self.player.queue(mock_source3)
        self.assert_not_playing_yet(mock_source1)

        self.player.play()
        self.assert_driver_player_created_for(mock_source1)
        self.assert_driver_player_started()

        self.reset_mocks()
        self.player.delete()
        self.assert_driver_player_stopped()
        self.assert_driver_player_destroyed()

    def test_empty_player(self):
        """A player without queued sources should not start a driver player and should not raise
        exceptions"""
        self.assert_not_playing_yet(None)

        self.reset_mocks()
        self.player.play()
        self.assert_no_new_driver_player_created()

        self.reset_mocks()
        self.player.pause()
        self.assert_no_new_driver_player_created()
        self.assert_driver_player_not_destroyed()

        self.reset_mocks()
        self.player.next_source()
        self.assert_no_new_driver_player_created()
        self.assert_driver_player_not_destroyed()

        self.reset_mocks()
        self.player.seek(0.8)
        self.assert_no_new_driver_player_created()
        self.assert_driver_player_not_destroyed()

        self.player.delete()

    def test_set_player_properties_before_playing(self):
        """When setting player properties before a driver specific player is created, these settings
        should be propagated after creating the player."""
        mock_source1 = self.create_mock_source(self.audio_format_1, None)
        mock_source2 = self.create_mock_source(self.audio_format_2, None)
        self.player.queue(mock_source1)
        self.player.queue(mock_source2)
        self.assert_not_playing_yet(mock_source1)

        self.reset_mocks()
        self.player.volume = 10.
        self.player.min_distance = 2.
        self.player.max_distance = 3.
        self.player.position = (4, 4, 4)
        self.player.pitch = 5.0
        self.player.cone_orientation = (6, 6, 6)
        self.player.cone_inner_angle = 7.
        self.player.cone_outer_angle = 8.
        self.player.cone_outer_gain = 9.

        def assert_properties_set():
            self.mock_audio_driver_player.set_volume.assert_called_once_with(10.)
            self.mock_audio_driver_player.set_min_distance.assert_called_once_with(2.)
            self.mock_audio_driver_player.set_max_distance.assert_called_once_with(3.)
            self.mock_audio_driver_player.set_position.assert_called_once_with((4, 4, 4))
            self.mock_audio_driver_player.set_pitch.assert_called_once_with(5.)
            self.mock_audio_driver_player.set_cone_orientation.assert_called_once_with((6, 6, 6))
            self.mock_audio_driver_player.set_cone_inner_angle.assert_called_once_with(7.)
            self.mock_audio_driver_player.set_cone_outer_angle.assert_called_once_with(8.)
            self.mock_audio_driver_player.set_cone_outer_gain.assert_called_once_with(9.)

        self.reset_mocks()
        self.player.play()
        self.assert_driver_player_created_for(mock_source1)
        self.assert_now_playing(mock_source1)
        assert_properties_set()

        self.reset_mocks()
        self.player.next_source()
        self.assert_driver_player_destroyed()
        self.assert_driver_player_created_for(mock_source2)
        assert_properties_set()

    def test_set_player_properties_while_playing(self):
        """When setting player properties while playing, the properties should be propagated to the
        driver specific player right away."""
        mock_source1 = self.create_mock_source(self.audio_format_1, None)
        mock_source2 = self.create_mock_source(self.audio_format_2, None)
        self.player.queue(mock_source1)
        self.player.queue(mock_source2)
        self.assert_not_playing_yet(mock_source1)

        self.reset_mocks()
        self.player.play()
        self.assert_driver_player_created_for(mock_source1)
        self.assert_now_playing(mock_source1)

        self.reset_mocks()
        self.player.volume = 10.
        self.mock_audio_driver_player.set_volume.assert_called_once_with(10.)

        self.reset_mocks()
        self.player.min_distance = 2.
        self.mock_audio_driver_player.set_min_distance.assert_called_once_with(2.)

        self.reset_mocks()
        self.player.max_distance = 3.
        self.mock_audio_driver_player.set_max_distance.assert_called_once_with(3.)

        self.reset_mocks()
        self.player.position = (4, 4, 4)
        self.mock_audio_driver_player.set_position.assert_called_once_with((4, 4, 4))

        self.reset_mocks()
        self.player.pitch = 5.0
        self.mock_audio_driver_player.set_pitch.assert_called_once_with(5.)

        self.reset_mocks()
        self.player.cone_orientation = (6, 6, 6)
        self.mock_audio_driver_player.set_cone_orientation.assert_called_once_with((6, 6, 6))

        self.reset_mocks()
        self.player.cone_inner_angle = 7.
        self.mock_audio_driver_player.set_cone_inner_angle.assert_called_once_with(7.)

        self.reset_mocks()
        self.player.cone_outer_angle = 8.
        self.mock_audio_driver_player.set_cone_outer_angle.assert_called_once_with(8.)

        self.reset_mocks()
        self.player.cone_outer_gain = 9.
        self.mock_audio_driver_player.set_cone_outer_gain.assert_called_once_with(9.)

        self.reset_mocks()
        self.player.next_source()
        self.assert_driver_player_destroyed()
        self.assert_driver_player_created_for(mock_source2)
        self.mock_audio_driver_player.set_volume.assert_called_once_with(10.)
        self.mock_audio_driver_player.set_min_distance.assert_called_once_with(2.)
        self.mock_audio_driver_player.set_max_distance.assert_called_once_with(3.)
        self.mock_audio_driver_player.set_position.assert_called_once_with((4, 4, 4))
        self.mock_audio_driver_player.set_pitch.assert_called_once_with(5.)
        self.mock_audio_driver_player.set_cone_orientation.assert_called_once_with((6, 6, 6))
        self.mock_audio_driver_player.set_cone_inner_angle.assert_called_once_with(7.)
        self.mock_audio_driver_player.set_cone_outer_angle.assert_called_once_with(8.)
        self.mock_audio_driver_player.set_cone_outer_gain.assert_called_once_with(9.)

    def test_seek(self):
        """Test seeking to a specific time in the current source."""
        mock_source = self.create_mock_source(self.audio_format_1, None)
        self.player.queue(mock_source)
        self.assert_not_playing_yet(mock_source)

        self.reset_mocks()
        mock_source.reset_mock()
        self.player.seek(0.7)
        self.assert_source_seek(mock_source, 0.7)

        self.reset_mocks()
        mock_source.reset_mock()
        self.player.play()
        self.assert_driver_player_created_for(mock_source)
        self.assert_now_playing(mock_source)

        self.reset_mocks()
        mock_source.reset_mock()
        self.player.seek(0.2)
        self.assert_source_seek(mock_source, 0.2)
        # Clear buffers for immediate result
        self.assert_driver_player_cleared()

    def test_queue_source_group(self):
        """Source groups can also be queued. They are added as is without checking compatibility
        with the current source group."""
        mock_source1 = self.create_mock_source(self.audio_format_1, None)
        mock_source2 = self.create_mock_source(self.audio_format_1, None)
        mock_source3 = self.create_mock_source(self.audio_format_1, None)
        group = SourceGroup(self.audio_format_1, None)
        group.queue(mock_source2)
        group.queue(mock_source3)

        self.player.queue(mock_source1)
        self.player.queue(group)
        self.assert_not_playing_yet(mock_source1)

        self.reset_mocks()
        self.player.play()
        self.assert_driver_player_created_for(mock_source1)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source1)

        self.reset_mocks()
        self.player.next_source()
        self.assert_driver_player_destroyed()
        self.assert_driver_player_created_for(mock_source2, mock_source3)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source2)

    def test_video_queue_and_play(self):
        """Sources can also include video. Instead of using a player to continuously play the video
        a texture is updated on a fixed interval."""
        mock_source = self.create_mock_source(self.audio_format_1, self.video_format_1)
        self.set_video_data_for_mock_source(mock_source, [(0.2, 'a')])
        self.player.queue(mock_source)
        self.assert_not_playing_yet(mock_source)

        self.reset_mocks()
        self.player.play()
        self.assert_driver_player_created_for(mock_source)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source)
        self.assert_new_texture_created(self.video_format_1)
        self.assert_update_texture_scheduled(1. / 30)

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.2)
        self.player.update_texture()
        self.assert_texture_updated('a')
        self.assertIs(self.player.get_texture(), self.mock_texture)

    def test_video_peek_before_play(self):
        """Before starting to play a video source, we can peek and see a frame. It will then
        wait for the next frame when play has started."""
        mock_source = self.create_mock_source(self.audio_format_1, self.video_format_1)
        self.set_video_data_for_mock_source(mock_source, [(0.1, 'a'), (0.2, 'b')])
        self.player.queue(mock_source)
        self.assert_not_playing_yet(mock_source)

        self.reset_mocks()
        self.player.update_texture(time=0.1)
        self.assert_new_texture_created(self.video_format_1)
        self.assert_not_playing_yet(mock_source)
        self.assert_texture_updated('a')

        self.reset_mocks()
        self.player.play()
        self.assert_now_playing(mock_source)
        self.assert_update_texture_scheduled(1. / 30)
        self.assert_no_new_texture_created()
        self.assert_texture_not_updated()

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.0)
        self.player.update_texture()
        self.assert_no_new_texture_created()
        self.assert_texture_not_updated()

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.1)
        self.player.update_texture()
        self.assert_no_new_texture_created()
        self.assert_texture_not_updated()

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.2)
        self.player.update_texture()
        self.assert_no_new_texture_created()
        self.assert_texture_updated('b')

    def test_video_seek(self):
        """Sources with video can also be seeked. This will cause the audio source to seek and
        video will follow the timestamps."""
        mock_source = self.create_mock_source(self.audio_format_1, self.video_format_1)
        self.set_video_data_for_mock_source(mock_source, [(0.0, 'a'), (0.1, 'b'), (0.2, 'c'),
                                                          (0.3, 'd'), (0.4, 'e'), (0.5, 'f')])
        self.player.queue(mock_source)
        self.player.play()
        self.assert_new_texture_created(self.video_format_1)
        self.assert_update_texture_scheduled(1. / 30)

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.0)
        self.player.update_texture()
        self.assert_texture_updated('a')

        self.reset_mocks()
        self.player.seek(0.3)
        self.assert_source_seek(mock_source, 0.3)
        self.assert_no_new_texture_created()
        self.assert_texture_updated('d')

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.3)
        self.player.update_texture()
        self.assert_texture_not_updated()

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.4)
        self.player.update_texture()
        self.assert_texture_updated('e')

    def test_video_frame_rate(self):
        """Videos with different framerates need to be rescheduled at the clock."""
        mock_source1 = self.create_mock_source(self.audio_format_1, self.video_format_1)
        mock_source2 = self.create_mock_source(self.audio_format_1, self.video_format_2)
        self.player.queue(mock_source1)
        self.player.queue(mock_source2)

        self.player.play()
        self.assert_new_texture_created(self.video_format_1)
        self.assert_update_texture_scheduled(1. / 30)

        self.reset_mocks()
        self.player.next_source()
        self.assert_new_texture_created(self.video_format_2)
        self.assert_update_texture_unscheduled()
        self.assert_update_texture_scheduled(1. / 25)

    def test_video_seek_next_frame(self):
        """It is possible to jump directly to the next frame of video and adjust the audio player
        accordingly."""
        mock_source = self.create_mock_source(self.audio_format_1, self.video_format_1)
        self.set_video_data_for_mock_source(mock_source, [(0.0, 'a'), (0.2, 'b')])
        self.player.queue(mock_source)
        self.player.play()
        self.assert_new_texture_created(self.video_format_1)
        self.assert_update_texture_scheduled(1./30)

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.0)
        self.player.update_texture()
        self.assert_texture_updated('a')

        self.reset_mocks()
        self.player.seek_next_frame()
        self.assert_source_seek(mock_source, 0.2)
        self.assert_texture_updated('b')

    def test_video_runs_out_of_frames(self):
        """When the video runs out of frames, it stops updating the texture. The audio player is
        responsible for triggering eos."""
        mock_source = self.create_mock_source(self.audio_format_1, self.video_format_1)
        self.set_video_data_for_mock_source(mock_source, [(0.0, 'a'), (0.1, 'b')])
        self.player.queue(mock_source)
        self.player.play()
        self.assert_new_texture_created(self.video_format_1)
        self.assert_update_texture_scheduled(1./30)

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.0)
        self.player.update_texture()
        self.assert_texture_updated('a')

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.1)
        self.player.update_texture()
        self.assert_texture_updated('b')

        self.reset_mocks()
        self.pretend_driver_player_at_time(0.2)
        self.player.update_texture()
        self.assert_texture_not_updated()

        self.reset_mocks()
        self.player.seek_next_frame()
        self.assert_texture_not_updated()

    def test_video_without_audio(self):
        """It is possible to have videos without audio streams. A special audio driver will take
        care of providing the timing."""
        mock_source = self.create_mock_source(None, self.video_format_1)
        self.player.queue(mock_source)
        self.player.play()
        self.assert_new_texture_created(self.video_format_1)
        self.assert_update_texture_scheduled(1./30)
        self.assert_no_new_driver_player_created()
        self.assert_silent_driver_player_created_for(mock_source)

        self.reset_mocks()
        self.player.delete()
        self.assert_silent_driver_player_destroyed()


