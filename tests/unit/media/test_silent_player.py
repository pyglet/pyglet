"""
Tests for the silent audio driver.
"""

import mock
import unittest

from pyglet.media.drivers.silent import (EventBuffer, SilentAudioBuffer, SilentAudioPacket,
        SilentAudioPlayerPacketConsumer)
from pyglet.media.events import MediaEvent
from pyglet.media.sources import AudioData, AudioFormat

class SilentAudioPacketTest(unittest.TestCase):
    def test_partial_consume(self):
        packet = SilentAudioPacket(0., 1.)

        dt = .4
        consumed = packet.consume(dt)

        self.assertAlmostEqual(.4, consumed)
        self.assertAlmostEqual(.4, packet.timestamp)
        self.assertAlmostEqual(.6, packet.duration)
        self.assertFalse(packet.is_empty())

    def test_exact_consume(self):
        packet = SilentAudioPacket(0., 1.)

        dt = 1.
        consumed = packet.consume(dt)

        self.assertAlmostEqual(1., consumed)
        self.assertAlmostEqual(1., packet.timestamp)
        self.assertAlmostEqual(0., packet.duration)
        self.assertTrue(packet.is_empty())

    def test_over_consume(self):
        packet = SilentAudioPacket(0., 1.)

        dt = 2.
        consumed = packet.consume(dt)

        self.assertAlmostEqual(1., consumed)
        self.assertAlmostEqual(1., packet.timestamp)
        self.assertAlmostEqual(0., packet.duration)
        self.assertTrue(packet.is_empty())


class SilentAudioBufferTest(unittest.TestCase):
    def test_add_audio_data(self):
        buf = SilentAudioBuffer()
        self.assertTrue(buf.is_empty())
        self.assertAlmostEqual(0., buf.duration)

        data1 = AudioData('', 0, 0., 1., [])
        buf.add_audio_data(data1)
        self.assertFalse(buf.is_empty())
        self.assertAlmostEqual(1., buf.duration)

        data2 = AudioData('', 0, 1., 2., [])
        buf.add_audio_data(data2)
        self.assertFalse(buf.is_empty())
        self.assertAlmostEqual(3., buf.duration)

    def test_consume_audio_data(self):
        buf = SilentAudioBuffer()
        buf.add_audio_data(AudioData('', 0, 0., 1., []))
        buf.add_audio_data(AudioData('', 0, 1., 2., []))
        self.assertFalse(buf.is_empty())
        self.assertAlmostEqual(3., buf.duration)
        self.assertAlmostEqual(0., buf.get_current_timestamp())

        buf.consume_audio_data(0.8)
        self.assertFalse(buf.is_empty())
        self.assertAlmostEqual(2.2, buf.duration)
        self.assertAlmostEqual(0.8, buf.get_current_timestamp())

        buf.consume_audio_data(0.8)
        self.assertFalse(buf.is_empty())
        self.assertAlmostEqual(1.4, buf.duration)
        self.assertAlmostEqual(1.6, buf.get_current_timestamp())

        buf.consume_audio_data(1.4)
        self.assertTrue(buf.is_empty())
        self.assertAlmostEqual(0., buf.duration)
        self.assertAlmostEqual(3., buf.get_current_timestamp())

    def test_consume_too_much(self):
        buf = SilentAudioBuffer()
        buf.add_audio_data(AudioData('', 0, 0., 1., []))
        buf.add_audio_data(AudioData('', 0, 1., 2., []))

        buf.consume_audio_data(4.)
        self.assertTrue(buf.is_empty())
        self.assertAlmostEqual(0., buf.duration)
        self.assertAlmostEqual(3., buf.get_current_timestamp())

    def test_time_to_next_update(self):
        buf = SilentAudioBuffer()
        self.assertIsNone(buf.get_time_to_next_update())

        buf.add_audio_data(AudioData('', 0, 0., 1., []))
        buf.add_audio_data(AudioData('', 0, 1., 2., []))
        self.assertAlmostEqual(1., buf.get_time_to_next_update())

        buf.consume_audio_data(0.5)
        self.assertAlmostEqual(0.5, buf.get_time_to_next_update())

        buf.consume_audio_data(1.0)
        self.assertAlmostEqual(1.5, buf.get_time_to_next_update())

        buf.consume_audio_data(1.5)
        self.assertIsNone(buf.get_time_to_next_update())

    def test_current_timestamp(self):
        buf = SilentAudioBuffer()
        self.assertAlmostEqual(0., buf.get_current_timestamp())

        buf.add_audio_data(AudioData('', 0, 2., 1., []))
        buf.add_audio_data(AudioData('', 0, 1., 2., []))
        self.assertAlmostEqual(2., buf.get_current_timestamp())

        buf.consume_audio_data(0.2)
        self.assertAlmostEqual(2.2, buf.get_current_timestamp())

        buf.consume_audio_data(1.)
        self.assertAlmostEqual(1.2, buf.get_current_timestamp())

        buf.consume_audio_data(2.)
        self.assertAlmostEqual(3., buf.get_current_timestamp())


class EventBufferTest(unittest.TestCase):
    def test_add_events(self):
        buf = EventBuffer()
        self.assertIsNone(buf.get_next_event_timestamp())

        event1 = MediaEvent(.1, 'Event1')
        event2 = MediaEvent(.5, 'Event2')
        data = AudioData('', 0, 0., 1., [event1, event2])
        buf.add_events(data)

        self.assertAlmostEqual(.1, buf.get_next_event_timestamp())

    def test_get_expired_events(self):
        buf = EventBuffer()
        self.assertIsNone(buf.get_next_event_timestamp())

        event1 = MediaEvent(.1, 'Event1')
        event2 = MediaEvent(.5, 'Event2')
        data = AudioData('', 0, 0., 1., [event1, event2])
        buf.add_events(data)

        expired_events = buf.get_expired_events(0.)
        self.assertListEqual([], expired_events)

        expired_events = buf.get_expired_events(.1)
        self.assertListEqual([event1], expired_events)

        expired_events = buf.get_expired_events(.1)
        self.assertListEqual([], expired_events)

        expired_events = buf.get_expired_events(.6)
        self.assertListEqual([event2], expired_events)

        expired_events = buf.get_expired_events(.6)
        self.assertListEqual([], expired_events)

    def test_get_multiple_events(self):
        buf = EventBuffer()
        self.assertIsNone(buf.get_next_event_timestamp())

        event1 = MediaEvent(.2, 'Event1')
        event2 = MediaEvent(.2, 'Event2')
        data1 = AudioData('', 0, 0., 1., [event1, event2])
        buf.add_events(data1)

        event3 = MediaEvent(.3, 'Event3')
        event4 = MediaEvent(.4, 'Event4')
        data2 = AudioData('', 0, 1., 1., [event3, event4])
        buf.add_events(data2)

        expired_events = buf.get_expired_events(0.)
        self.assertListEqual([], expired_events)

        expired_events = buf.get_expired_events(.2)
        self.assertListEqual([event1, event2], expired_events)

        expired_events = buf.get_expired_events(1.6)
        self.assertListEqual([event3, event4], expired_events)

    def test_get_next_event_timestamp(self):
        buf = EventBuffer()
        self.assertIsNone(buf.get_next_event_timestamp())

        event1 = MediaEvent(.2, 'Event1')
        event2 = MediaEvent(.2, 'Event2')
        data1 = AudioData('', 0, 0., 1., [event1, event2])
        buf.add_events(data1)

        event3 = MediaEvent(.3, 'Event3')
        event4 = MediaEvent(.4, 'Event4')
        data2 = AudioData('', 0, 1., 1., [event3, event4])
        buf.add_events(data2)

        self.assertAlmostEqual(.2, buf.get_next_event_timestamp())

        buf.get_expired_events(.2)
        self.assertAlmostEqual(1.3, buf.get_next_event_timestamp())

        buf.get_expired_events(1.3)
        self.assertAlmostEqual(1.4, buf.get_next_event_timestamp())

        buf.get_expired_events(1.4)
        self.assertIsNone(buf.get_next_event_timestamp())

    def test_get_time_to_next_event(self):
        buf = EventBuffer()
        self.assertIsNone(buf.get_next_event_timestamp())

        event1 = MediaEvent(.2, 'Event1')
        event2 = MediaEvent(.2, 'Event2')
        data1 = AudioData('', 0, 0., 1., [event1, event2])
        buf.add_events(data1)

        event3 = MediaEvent(.3, 'Event3')
        event4 = MediaEvent(.4, 'Event4')
        data2 = AudioData('', 0, 1., 1., [event3, event4])
        buf.add_events(data2)

        self.assertAlmostEqual(.2, buf.get_time_to_next_event(0.))
        self.assertAlmostEqual(.1, buf.get_time_to_next_event(.1))

        buf.get_expired_events(.2)
        self.assertAlmostEqual(1.1, buf.get_time_to_next_event(.2))
        self.assertAlmostEqual(.1, buf.get_time_to_next_event(1.2))


class MockSourceGroup(object):
    audio_format = AudioFormat(1, 8, 44100)

    def __init__(self, duration, timestamp=0.):
        self.mock = mock.MagicMock()
        type(self.mock).audio_format = mock.PropertyMock(return_value=self.audio_format)
        self.mock.get_audio_data.side_effect = self._get_audio_data

        self.timestamp = timestamp
        self.duration = duration

        self.seconds_buffered = 0.
        self.bytes_buffered = 0

    def _get_audio_data(self, length):
        secs = float(length) / self.audio_format.bytes_per_second
        if secs > self.duration:
            secs = self.duration
            length = int(secs * self.audio_format.bytes_per_second)

        if length == 0:
            return None

        data = AudioData('a'*length, length, self.timestamp, secs, ())
        self.timestamp += secs
        self.duration -= secs
        self.seconds_buffered += secs
        self.bytes_buffered += length
        return data


class SilentAudioPlayerPacketConsumerTest(unittest.TestCase):
    def setUp(self):
        self.time_patcher = mock.patch('time.time')
        self.thread_patcher = mock.patch('pyglet.media.drivers.silent.MediaThread')
        self.mock_time = self.time_patcher.start()
        self.mock_thread = self.thread_patcher.start()

    def tearDown(self):
        self.time_patcher.stop()
        self.thread_patcher.stop()

    def set_time(self, t):
        self.mock_time.return_value = t

    def test_buffer_data_initial(self):
        mock_player = mock.MagicMock()
        mock_source_group = MockSourceGroup(1.)

        silent_player = SilentAudioPlayerPacketConsumer(mock_source_group.mock, mock_player)
        self.set_time(1000.)
        silent_player._buffer_data()
        self.assertAlmostEqual(.4, mock_source_group.seconds_buffered, delta=.01)

        self.assertAlmostEqual(0., silent_player.get_time(), delta=.01)

    def test_playing(self):
        mock_player = mock.MagicMock()
        mock_source_group = MockSourceGroup(1.)

        silent_player = SilentAudioPlayerPacketConsumer(mock_source_group.mock, mock_player)

        # Buffer initial data
        self.set_time(1000.)
        silent_player._buffer_data()
        self.assertAlmostEqual(.4, mock_source_group.seconds_buffered, delta=.01)

        # Start playing
        silent_player.play()
        self.assertAlmostEqual(0., silent_player.get_time(), delta=.01)

        # Check timestamp increases even when not consuming new data
        self.set_time(1000.2)
        self.assertAlmostEqual(.2, silent_player.get_time(), delta=.01)

        # Timestamp sill correct after consuming data
        silent_player._consume_data()
        self.assertAlmostEqual(.2, silent_player.get_time(), delta=.01)

        # Consuming data means we need to buffer more
        silent_player._buffer_data()
        self.assertAlmostEqual(.6, mock_source_group.seconds_buffered, delta=.01)
        self.assertAlmostEqual(.2, silent_player.get_time(), delta=.01)

    def test_not_started_yet(self):
        mock_player = mock.MagicMock()
        mock_source_group = MockSourceGroup(1.)
        silent_player = SilentAudioPlayerPacketConsumer(mock_source_group.mock, mock_player)

        # Do initial buffering even when not playing yet
        self.set_time(1000.)
        silent_player._buffer_data()
        self.assertAlmostEqual(.4, mock_source_group.seconds_buffered, delta=.01)
        self.assertAlmostEqual(0., silent_player.get_time(), delta=.01)

        # Increase of timestamp does not change anything
        self.set_time(1001.)
        self.assertAlmostEqual(0., silent_player.get_time(), delta=.01)

        # No data is consumed
        silent_player._consume_data()
        self.assertAlmostEqual(0., silent_player.get_time(), delta=.01)

        # No new data is buffered
        silent_player._buffer_data()
        self.assertAlmostEqual(.4, mock_source_group.seconds_buffered, delta=.01)
        self.assertAlmostEqual(0., silent_player.get_time(), delta=.01)

    def test_play_and_stop(self):
        mock_player = mock.MagicMock()
        mock_source_group = MockSourceGroup(1.)
        silent_player = SilentAudioPlayerPacketConsumer(mock_source_group.mock, mock_player)

        # Do initial buffering even when not playing yet
        self.set_time(1000.)
        silent_player._buffer_data()
        self.assertAlmostEqual(.4, mock_source_group.seconds_buffered, delta=.01)
        self.assertAlmostEqual(0., silent_player.get_time(), delta=.01)

        # Play a little bit
        silent_player.play()
        self.set_time(1000.2)
        silent_player._consume_data()
        silent_player._buffer_data()
        self.assertAlmostEqual(.6, mock_source_group.seconds_buffered, delta=.01)
        self.assertAlmostEqual(.2, silent_player.get_time(), delta=.01)

        # Now stop, this should consume data upto stopping moment
        self.set_time(1000.4)
        silent_player.stop()
        self.assertAlmostEqual(.4, silent_player.get_time(), delta=.01)

        # Buffering still happens
        silent_player._buffer_data()
        self.assertAlmostEqual(.8, mock_source_group.seconds_buffered, delta=.01)
        self.assertAlmostEqual(.4, silent_player.get_time(), delta=.01)

        # But now playback is really paused
        self.set_time(1001.)
        self.assertAlmostEqual(.4, silent_player.get_time(), delta=.01)

        # And no more buffering and consuming
        silent_player._consume_data()
        silent_player._buffer_data()
        self.assertAlmostEqual(.8, mock_source_group.seconds_buffered, delta=.01)
        self.assertAlmostEqual(.4, silent_player.get_time(), delta=.01)

