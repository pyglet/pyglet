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
    audio_format = media.AudioFormat(1, 8, 11025)

    def create_mock_source(self, duration, audio_data=None):
        mock_source = mock.MagicMock()
        m = mock_source._get_queue_source.return_value
        type(m).audio_format = mock.PropertyMock(return_value=self.audio_format)
        type(m).video_format = mock.PropertyMock(return_value=None)
        type(m).duration = mock.PropertyMock(return_value=duration)
        m.get_audio_data.return_value = self.create_audio_data(duration, audio_data)
        return mock_source

    def create_audio_data(self, duration=1., data=None):
        if data is None:
            return None

        audio_data = media.AudioData(data, len(data), 0., duration, [])
        return audio_data

    def test_queueing(self):
        source_group = media.SourceGroup(self.audio_format, None)
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
        source_group = media.SourceGroup(self.audio_format, None)
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
        source_group = media.SourceGroup(self.audio_format, None)
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
        source_group = media.SourceGroup(self.audio_format, None)
        source_group.loop = True
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

    def test_loop_advance_on_eos(self):
        """Test advancing to the next source on eos when looping is enabled."""
        source_group = media.SourceGroup(self.audio_format, None)
        source_group.loop = True
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

    def test_loop_advance_immediate(self):
        """Test advancing immediately to the next source when looping is enabled."""
        source_group = media.SourceGroup(self.audio_format, None)
        source_group.loop = True
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

    def test_empty_source_group(self):
        """Test an empty source group"""
        source_group = media.SourceGroup(self.audio_format, None)
        self.assertFalse(source_group.has_next())
        self.assertAlmostEqual(source_group.duration, 0.)
        self.assertIsNone(source_group.get_current_source())
        source_group.seek(1.)
        source_group.next_source()
        self.assertIsNone(source_group.get_audio_data(1024))
        self.assertAlmostEqual(source_group.translate_timestamp(1.), 1.)
        self.assertIsNone(source_group.get_next_video_timestamp())
        self.assertIsNone(source_group.get_next_video_frame())

    def test_translate_timestamp(self):
        """Test that translate_timestamp works correctly with advancing and looping."""
        source_group = media.SourceGroup(self.audio_format, None)
        source_group.loop = True
        source1 = self.create_mock_source(1., '1')
        source2 = self.create_mock_source(2., '2')
        source_group.queue(source1)
        source_group.queue(source2)
        self.assertAlmostEqual(source_group.translate_timestamp(1.), 1.)

        # Loop source 1
        def seek(_):
            source1._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='1')
        source1._get_queue_source.return_value.seek.side_effect = seek
        source1._get_queue_source.return_value.get_audio_data.return_value = None
        source_group.get_audio_data(1024)
        self.assertAlmostEqual(source_group.translate_timestamp(2.), 1.)

        # Loop source 1 again
        def seek(_):
            source1._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='1')
        source1._get_queue_source.return_value.seek.side_effect = seek
        source1._get_queue_source.return_value.get_audio_data.return_value = None
        source_group.get_audio_data(1024)
        self.assertAlmostEqual(source_group.translate_timestamp(3.), 1.)

        # Advance to source 2
        source_group.next_source()
        self.assertAlmostEqual(source_group.translate_timestamp(4.), 1.)

        # Loop source 2
        def seek(_):
            source2._get_queue_source.return_value.get_audio_data.return_value = self.create_audio_data(duration=1., data='2')
        source2._get_queue_source.return_value.seek.side_effect = seek
        source2._get_queue_source.return_value.get_audio_data.return_value = None
        source_group.get_audio_data(1024)
        self.assertAlmostEqual(source_group.translate_timestamp(6.), 1.)


class PlayerTestCase(unittest.TestCase):
    def create_mock_source(self, audio_format, video_format):
        mock_source = mock.MagicMock()
        type(mock_source).audio_format = mock.PropertyMock(return_value=audio_format)
        type(mock_source).video_format = mock.PropertyMock(return_value=video_format)
        type(mock_source._get_queue_source.return_value).audio_format = mock.PropertyMock(return_value=audio_format)
        type(mock_source._get_queue_source.return_value).video_format = mock.PropertyMock(return_value=video_format)
        return mock_source

    @mock.patch('pyglet.media.get_audio_driver')
    def test_queue_single_audio_source(self, mock_get_audio_driver):
        """Queue a single audio source and start playing it."""
        mock_audio_driver = mock_get_audio_driver.return_value
        player = media.Player()

        mock_source = self.create_mock_source(media.AudioFormat(1, 8, 11025), None)
        player.queue(mock_source)

        self.assertFalse(mock_get_audio_driver.called, msg='No audio driver required yet')
        self.assertFalse(player.playing)
        self.assertIs(player.source, mock_source._get_queue_source.return_value)
        self.assertAlmostEqual(player.time, 0.)

        player.play()

        # Check a audio driver specific player is created for the single source
        mock_get_audio_driver.assert_called_once_with()
        self.assertEqual(mock_audio_driver.create_audio_player.call_count, 1)
        call_args = mock_audio_driver.create_audio_player.call_args
        self.assertIsInstance(call_args[0][0], media.SourceGroup)
        self.assertIs(call_args[0][0].get_current_source(), mock_source._get_queue_source.return_value)
        self.assertIs(call_args[0][1], player)














