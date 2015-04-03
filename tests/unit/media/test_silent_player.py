"""
Tests for the silent audio driver.
"""

import unittest

from pyglet.media.drivers.silent import EventBuffer, SilentAudioBuffer, SilentAudioPacket
from pyglet.media.events import MediaEvent
from pyglet.media.sources import AudioData

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


