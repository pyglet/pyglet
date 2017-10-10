from __future__ import division
from builtins import range
import ctypes
from tests import mock
import os
import random
from collections import deque
from tests.base.future_test import FutureTestCase

import pyglet
from pyglet.media.player import Player, PlayerGroup
from pyglet.media.sources.base import *

#pyglet.options['debug_media'] = True


class PlayerTestCase(FutureTestCase):
    # Default values to use
    audio_format_1 = AudioFormat(1, 8, 11025)
    audio_format_2 = AudioFormat(2, 8, 11025)
    audio_format_3 = AudioFormat(2, 16, 44100)
    video_format_1 = VideoFormat(800, 600)
    video_format_2 = VideoFormat(1920, 1280)
    video_format_2.frame_rate = 25

    def setUp(self):
        self.player = Player()

        self._get_audio_driver_patcher = mock.patch('pyglet.media.player.get_audio_driver')
        self.mock_get_audio_driver = self._get_audio_driver_patcher.start()
        self.mock_audio_driver = self.mock_get_audio_driver.return_value
        self.mock_audio_driver_player = self.mock_audio_driver.create_audio_player.return_value

        self._clock_patcher = mock.patch('pyglet.clock')
        self.mock_clock = self._clock_patcher.start()

        self._texture_patcher = mock.patch('pyglet.image.Texture.create')
        self.mock_texture_create = self._texture_patcher.start()
        self.mock_texture = self.mock_texture_create.return_value
        # Need to do this as side_effect instead of return_value, or reset_mock will recurse
        self.mock_texture.get_transform.side_effect = lambda flip_y: self.mock_texture

        self.current_play_list = None

    def tearDown(self):
        self._get_audio_driver_patcher.stop()
        self._clock_patcher.stop()
        self._texture_patcher.stop()

    def reset_mocks(self):
        # These mocks will recursively reset their children
        self.mock_get_audio_driver.reset_mock()
        self.mock_clock.reset_mock()
        self.mock_texture_create.reset_mock()

    def create_mock_source(self, audio_format, video_format):
        mock_source = mock.MagicMock()
        type(mock_source).audio_format = mock.PropertyMock(return_value=audio_format)
        type(mock_source).video_format = mock.PropertyMock(return_value=video_format)
        type(mock_source._get_queue_source.return_value).audio_format = mock.PropertyMock(return_value=audio_format)
        type(mock_source._get_queue_source.return_value).video_format = mock.PropertyMock(return_value=video_format)
        if video_format:
            mock_source.video_format.frame_rate = 30
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

    def _assert_player_created_for(self, mock_get_audio_driver, mock_audio_driver, *sources):
        mock_get_audio_driver.assert_called_once_with()
        self.assertEqual(mock_audio_driver.create_audio_player.call_count, 1)
        call_args = mock_audio_driver.create_audio_player.call_args
        self.assertIsInstance(call_args[0][0], PlayList)
        self.assertIs(call_args[0][1], self.player)

        self.current_play_list = call_args[0][0]
        self.assert_in_current_play_list(*sources)

    def assert_no_new_driver_player_created(self):
        """Assert that no new driver specific audio player is created."""
        self.assertFalse(self.mock_get_audio_driver.called, msg='No new audio driver should be created')

    def assert_in_current_play_list(self, *sources):
        self.assertIsNotNone(self.current_play_list, msg='No previous call to create driver player')

        queue_sources = deque(source._get_queue_source.return_value for source in sources)
        self.assertSequenceEqual(self.current_play_list._sources, queue_sources)

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

    def assert_update_texture_scheduled(self):
        self.mock_clock.schedule_once.assert_called_once_with(self.player.update_texture, 0)

    def assert_update_texture_unscheduled(self):
        self.mock_clock.unschedule.assert_called_with(self.player.update_texture)

    def pretend_player_at_time(self, t):
        self.player._mclock.set_time(t)

    def pretend_silent_driver_player_at_time(self, t):
        self.mock_silent_audio_driver_player.get_time.return_value = t

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
        self.assert_driver_player_created_for(mock_source1, 
            mock_source2, mock_source3)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source1)

        self.reset_mocks()
        self.player.next_source()
        self.assert_driver_player_destroyed()
        self.assert_driver_player_created_for(mock_source2, mock_source3)
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
        self.assert_in_current_play_list(mock_source2, mock_source3)
        self.assert_driver_player_not_destroyed()
        self.assert_no_new_driver_player_created()
        self.assert_now_playing(mock_source2)

        self.reset_mocks()
        self.player.next_source()
        self.assert_in_current_play_list(mock_source3)
        self.assert_driver_player_not_destroyed()
        self.assert_no_new_driver_player_created()
        self.assert_now_playing(mock_source3)

    def test_on_eos(self):
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
        self.assert_in_current_play_list(mock_source2, mock_source3)

    def test_player_stops_after_last_eos(self):
        """If the last playlist source is eos, the player stops."""
        mock_source = self.create_mock_source(self.audio_format_1, None)
        self.player.queue(mock_source)
        self.assert_not_playing_yet(mock_source)

        self.player.play()
        self.assert_driver_player_created_for(mock_source)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source)

        self.reset_mocks()
        self.player.dispatch_event('on_eos')
        self.assert_driver_player_destroyed()
        self.assert_not_playing(None)

    def test_eos_events(self):
        """Test receiving various eos events: on source eos, 
        on playlist exhausted and on player eos and on player next source.
        """
        on_eos_mock = mock.MagicMock(return_value=None)
        self.player.event('on_eos')(on_eos_mock)
        on_player_eos_mock = mock.MagicMock(return_value=None)
        self.player.event('on_player_eos')(on_player_eos_mock)
        on_player_next_source_mock = mock.MagicMock(return_value=None)
        self.player.event('on_player_next_source')(on_player_next_source_mock)

        def reset_eos_mocks():
            on_eos_mock.reset_mock()
            on_player_eos_mock.reset_mock()
            on_player_next_source_mock.reset_mock()

        def assert_eos_events_received(on_eos=False, on_player_eos=False, 
                                       on_player_next_source=False):
            self.assertEqual(on_eos_mock.called, on_eos)
            self.assertEqual(on_player_eos_mock.called, on_player_eos)
            self.assertEqual(on_player_next_source_mock.called, on_player_next_source)

        mock_source1 = self.create_mock_source(self.audio_format_1, None)
        mock_source2 = self.create_mock_source(self.audio_format_1, None)
        mock_source3 = self.create_mock_source(self.audio_format_2, None)

        self.player.queue(mock_source1)
        self.player.queue(mock_source2)
        self.player.queue(mock_source3)
        self.assert_not_playing_yet(mock_source1)

        self.player.play()
        self.assert_driver_player_created_for(mock_source1, mock_source2, mock_source3)

        self.reset_mocks()
        reset_eos_mocks()
        # Pretend the current source in the group was eos and next source started
        self.player.dispatch_event('on_eos')
        self.assert_driver_player_not_destroyed()
        assert_eos_events_received(on_eos=True, on_player_next_source=True)
        self.assertEqual(len(self.current_play_list._sources), 2)

        # Pretend playlist is exhausted. Should be no more sources to play.
        self.player.dispatch_event('on_eos')
        self.reset_mocks()
        reset_eos_mocks()
        self.player.dispatch_event('on_eos')
        self.assert_not_playing(None)
        assert_eos_events_received(on_eos=True, on_player_eos=True)

    def test_pause_resume(self):
        """A stream can be paused. After that play will resume where paused."""
        mock_source = self.create_mock_source(self.audio_format_1, None)
        self.player.queue(mock_source)
        self.player.play()
        self.assert_driver_player_created_for(mock_source)
        self.assert_driver_player_started()
        self.assert_now_playing(mock_source)

        self.reset_mocks()
        self.pretend_player_at_time(0.5)
        self.player.pause()
        self.assert_driver_player_stopped()
        self.assert_driver_player_not_destroyed()

        self.reset_mocks()
        self.player.play()
        self.assertAlmostEqual(self.player.time, 0.5, places=2,
            msg='While playing, player should return time from driver player')
        self.assert_driver_player_started()
        self.assert_no_new_driver_player_created()
        self.assert_now_playing(mock_source)

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
        self.assert_driver_player_created_for(mock_source1, mock_source2, mock_source3)
        self.assert_driver_player_started()

        self.reset_mocks()
        self.pretend_player_at_time(1.)
        self.player.delete()
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
        """When setting player properties before a driver specific player is 
        created, these settings should be propagated after creating the 
        player.
        """
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
        self.assert_driver_player_created_for(mock_source1, mock_source2)
        self.assert_now_playing(mock_source1)
        assert_properties_set()

        self.reset_mocks()
        self.player.next_source()
        self.assert_driver_player_destroyed()
        self.assert_driver_player_created_for(mock_source2)
        assert_properties_set()

    def test_set_player_properties_while_playing(self):
        """When setting player properties while playing, the properties should 
        be propagated to the driver specific player right away."""
        mock_source1 = self.create_mock_source(self.audio_format_1, None)
        mock_source2 = self.create_mock_source(self.audio_format_2, None)
        self.player.queue(mock_source1)
        self.player.queue(mock_source2)
        self.assert_not_playing_yet(mock_source1)

        self.reset_mocks()
        self.player.play()
        self.assert_driver_player_created_for(mock_source1, mock_source2)
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

    def test_video_queue_and_play(self):
        """Sources can also include video. Instead of using a player to 
        continuously play the video, a texture is updated based on the
        video packet timestamp."""
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
        self.assert_update_texture_scheduled()

        self.reset_mocks()
        self.pretend_player_at_time(0.2)
        self.player.update_texture()
        self.assert_texture_updated('a')
        self.assertIs(self.player.get_texture(), self.mock_texture)

    def test_video_seek(self):
        """Sources with video can also be seeked. It's the Source 
        responsibility to present the Player with audio and video at the
        correct time."""
        mock_source = self.create_mock_source(self.audio_format_1, self.video_format_1)
        self.set_video_data_for_mock_source(mock_source, [(0.0, 'a'), (0.1, 'b'), (0.2, 'c'),
                                                          (0.3, 'd'), (0.4, 'e'), (0.5, 'f')])
        self.player.queue(mock_source)
        self.player.play()
        self.assert_new_texture_created(self.video_format_1)
        self.assert_update_texture_scheduled()

        self.reset_mocks()
        self.pretend_player_at_time(0.0)
        self.player.update_texture()
        self.assert_texture_updated('a')

        self.reset_mocks()
        self.player.seek(0.3)
        self.assert_source_seek(mock_source, 0.3)
        self.assert_no_new_texture_created()
        self.assert_texture_updated('d')

        self.reset_mocks()
        self.pretend_player_at_time(0.4)
        self.player.update_texture()
        self.assert_texture_updated('e')

    def test_video_frame_rate(self):
        """Videos texture are scheduled according to the video packet 
        timestamp."""
        mock_source1 = self.create_mock_source(self.audio_format_1, self.video_format_1)
        mock_source2 = self.create_mock_source(self.audio_format_1, self.video_format_2)
        self.player.queue(mock_source1)
        self.player.queue(mock_source2)

        self.player.play()
        self.assert_new_texture_created(self.video_format_1)
        self.assert_update_texture_scheduled()

        self.reset_mocks()
        self.player.next_source()
        self.assert_new_texture_created(self.video_format_2)
        self.assert_update_texture_unscheduled()
        self.assert_update_texture_scheduled()

    def test_video_seek_next_frame(self):
        """It is possible to jump directly to the next frame of video and adjust the audio player
        accordingly."""
        mock_source = self.create_mock_source(self.audio_format_1, self.video_format_1)
        self.set_video_data_for_mock_source(mock_source, [(0.0, 'a'), (0.2, 'b')])
        self.player.queue(mock_source)
        self.player.play()
        self.assert_new_texture_created(self.video_format_1)
        self.assert_update_texture_scheduled()

        self.reset_mocks()
        self.pretend_player_at_time(0.0)
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
        self.assert_update_texture_scheduled()

        self.reset_mocks()
        self.pretend_player_at_time(0.0)
        self.player.update_texture()
        self.assert_texture_updated('a')

        self.reset_mocks()
        self.pretend_player_at_time(0.1)
        self.player.update_texture()
        self.assert_texture_updated('b')

        self.reset_mocks()
        self.pretend_player_at_time(0.2)
        self.player.update_texture()
        self.assert_texture_not_updated()

        self.reset_mocks()
        self.player.seek_next_frame()
        self.assert_texture_not_updated()

    def test_video_without_audio(self):
        """It is possible to have videos without audio streams."""
        mock_source = self.create_mock_source(None, self.video_format_1)
        self.player.queue(mock_source)
        self.player.play()
        self.assert_new_texture_created(self.video_format_1)
        self.assert_update_texture_scheduled()
        self.assert_no_new_driver_player_created()


class PlayerGroupTestCase(FutureTestCase):
    def create_mock_player(self, has_audio=True):
        player = mock.MagicMock()
        if has_audio:
            audio_player = mock.PropertyMock(return_value=mock.MagicMock())
        else:
            audio_player = mock.PropertyMock(return_value=None)
        type(player)._audio_player = audio_player
        return player

    def assert_players_started(self, *players):
        for player in players:
            player.play.assert_called_once_with()

    def assert_audio_players_started(self, *players):
        # Find the one player that was used to start the group, the rest should not be used
        call_args = None
        audio_players = []
        for player in players:
            audio_player = player._audio_player
            audio_players.append(audio_player)
            if call_args is not None:
                self.assertFalse(audio_player._play_group.called, msg='Only one player should be used to start the group')
            elif audio_player._play_group.called:
                call_args = audio_player._play_group.call_args

        self.assertIsNotNone(call_args, msg='No player was used to start all audio players.')
        started_players = call_args[0][0]
        self.assertCountEqual(started_players, audio_players, msg='Not all players with audio players were started')

    def assert_players_stopped(self, *players):
        for player in players:
            player.pause.assert_called_once_with()

    def assert_audio_players_stopped(self, *players):
        # Find the one player that was used to start the group, the rest should not be used
        call_args = None
        audio_players = []
        for player in players:
            audio_player = player._audio_player
            audio_players.append(audio_player)
            if call_args is not None:
                self.assertFalse(audio_player._stop_group.called, msg='Only one player should be used to stop the group')
            elif audio_player._stop_group.called:
                call_args = audio_player._stop_group.call_args

        self.assertIsNotNone(call_args, msg='No player was used to stop all audio players.')
        stopped_players = call_args[0][0]
        self.assertCountEqual(stopped_players, audio_players, msg='Not all players with audio players were stopped')

    def reset_mocks(self, *mocks):
        for m in mocks:
            m.reset_mock()

    def test_empty_group(self):
        """Just check nothing explodes on an empty group."""
        group = PlayerGroup([])
        group.play()
        group.pause()

    def test_only_with_audio(self):
        """Test a group containing only players with audio."""
        players = [self.create_mock_player(has_audio=True) for _ in range(10)]
        group = PlayerGroup(players)

        group.play()
        self.assert_audio_players_started(*players)
        self.assert_players_started(*players)
        self.reset_mocks(*players)

        group.pause()
        self.assert_audio_players_stopped(*players)
        self.assert_players_stopped(*players)

    def test_only_without_audio(self):
        """Test a group containing only players without audio."""
        players = [self.create_mock_player(has_audio=False) for _ in range(10)]
        group = PlayerGroup(players)

        group.play()
        self.assert_players_started(*players)
        self.reset_mocks(*players)

        group.pause()
        self.assert_players_stopped(*players)

    def test_mixed_players(self):
        """Test a group containing both players with audio and players without audio."""
        players_with_audio = [self.create_mock_player(has_audio=True) for _ in range(10)]
        players_without_audio = [self.create_mock_player(has_audio=False) for _ in range(10)]
        players = players_with_audio + players_without_audio
        random.shuffle(players)
        group = PlayerGroup(players)

        group.play()
        self.assert_audio_players_started(*players_with_audio)
        self.assert_players_started(*players)
        self.reset_mocks(*players)

        group.pause()
        self.assert_audio_players_stopped(*players_with_audio)
        self.assert_players_stopped(*players)

