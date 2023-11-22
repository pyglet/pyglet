from collections import deque
import ctypes
import weakref
from abc import ABCMeta, abstractmethod

import pyglet
from pyglet.media.codecs import AudioData
from pyglet.util import debug_print


_debug = debug_print('debug_media')


class AbstractAudioPlayer(metaclass=ABCMeta):
    """Base class for driver audio players to be used by the high-level
    player. Relies on a thread to regularly call a `work` method in order
    for it to operate.
    """

    audio_sync_required_measurements = 8
    audio_desync_time_critical = 0.280
    audio_desync_time_minor = 0.030
    audio_minor_desync_correction_time = 0.012

    audio_buffer_length = 0.9

    def __init__(self, source, player):
        """Create a new audio player.

        :Parameters:
            `source` : `Source`
                Source to play from.
            `player` : `Player`
                Player to receive EOS and video frame sync events.

        """
        # We only keep weakref to the player and its source to avoid
        # circular references. It's the player who owns the source and
        # the audio_player
        self.source = weakref.proxy(source)
        self.player = weakref.proxy(player)

        afmt = source.audio_format
        # How much data should ideally be in memory ready to be played.
        self._buffered_data_ideal_size = max(
            32768,
            afmt.timestamp_to_bytes_aligned(self.audio_buffer_length),
        )

        # At which point a driver should try and refill data from the source
        self._buffered_data_comfortable_limit = int(self._buffered_data_ideal_size * (2/3))

        # A deque of (play_cursor, MediaEvent)
        self._events = deque()

        # Audio synchronization
        self.desync_bytes_critical = afmt.timestamp_to_bytes_aligned(
            self.audio_desync_time_critical)
        self.desync_bytes_minor = afmt.timestamp_to_bytes_aligned(
            self.audio_desync_time_minor)
        self.desync_correction_bytes_minor = afmt.timestamp_to_bytes_aligned(
            self.audio_minor_desync_correction_time)

        self.audio_sync_measurements = deque(maxlen=self.audio_sync_required_measurements)
        self.audio_sync_cumul_measurements = 0

        # Bytes that have been skipped or artificially added to compensate for audio
        # desync since initialization or the last call to `clear`.
        # Negative when data was skipped, positive if it was padded in.
        self._compensated_bytes = 0

    def on_driver_destroy(self):
        """Called before the audio driver is going to be destroyed (a planned destroy)."""
        pass

    def on_driver_reset(self):
        """Called after the audio driver has been re-initialized."""
        pass

    def set_source(self, source):
        """Change the player's source for a new one.
        It must be of the same audio format.
        Will clear the player, make sure you paused it beforehand.
        """
        assert self.source.audio_format == source.audio_format

        self.clear()
        self.source = weakref.proxy(source)

    @abstractmethod
    def prefill_audio(self):
        """Prefill the audio buffer with audio data.

        This method is called before the audio player starts in order to
        have it play as soon as possible.
        """
        # It is illegal to call this method while the player is playing.

    @abstractmethod
    def work(self):
        """Ran regularly by the worker thread. This method should fill up
        the player's buffers if required, and dispatch any necessary events.
        """
        # The general flow for a work method should be something like:
        # update_play_cursor()
        # dispatch_media_events()
        # if not source_exhausted:
        #   if play_cursor_too_close_to_write_cursor():
        #     get_and_submit_new_audio_data()
        #     if not source_exhausted:
        #       return
        #     else:
        #       update_play_cursor()
        #   else:
        #     return
        # if play_cursor > write_cursor and not _has_underrun:
        #   _has_underrun = True
        #   dispatch_on_eos()
        #
        # Player backends might report an underflow or buffer ends via a callback.
        # In that case, it should look something like this, but beware to protect
        # appropiate sections (any time variables and buffers are used which get accessed by both
        # callbacks and the work method) with a lock, otherwise you are probably opening yourself
        # up to really unlucky issues where the callback is unscheduled in favor of the work
        # method or vice versa, which may leave some variables in inconclusive states.
        # work:
        #  update_play_cursor()
        #  dispatch_media_events()
        #  if not source_exhausted:
        #    if play_cursor_too_close_to_write_cursor():
        #      get_and_submit_new_audio_data()
        #      if _has_underrun:
        #        if source_exhausted:
        #          dispatch_eon_eos()
        #        else:
        #          restart_player()
        #          _has_underrun = False
        #
        # on_underrun:
        #   if source_exhausted:
        #     dispatch_on_eos()
        #   else:
        #     _has_underrun = True
        #
        # Implementing this method in tandem with the others safely is prone to pitfalls,
        # so here's some hints:
        # It may get called from the worker thread. While that happens, the worker thread
        # will hold its operation lock.
        # These things could theoretically happen to the player while `work` is being
        # called:
        #
        # It may get paused/unpaused.
        # - Receiving data after getting paused/unpaused is typically not a problem.
        #   Realistically, this won't happen as all implementations include a
        #   `self.driver.worker.remove/add(self)` snippet in their `play`/`pause`
        #   implementations.
        #
        # It may get deleted.
        # - In this case, attempting to continue with the data will cause some sort of error
        #   To combat this, all `delete` implementations contain a form of
        #   `self.driver.worker.remove(self)`.
        #
        # It may *not* get cleared.
        # - It is illegal to call `clear`` on an unpaused player, and only playing players
        #   are in the worker thread.
        #
        # A native callback may run which changes the internal state of the player
        # - See above; protecting some sections with a lock local to the player
        #   Be sure to never hold the lock around get_audio_data; that ruins the entire
        #   point of running work outside of native callbacks.
        #
        # NOTE: In order for these calls to be more reliable, `remove` should be the first
        # statement in such implementations and `add` the last one, to ensure that `work`
        # will not be run after/not start before player attributes have been changed.
        #
        # Don't assume `work` stops being called just because it dispatched `on_eos`!
        #
        # This method may also be called from the main thread through `prefill_audio`.
        # This will only happen before the player is started: `work` will never interfere
        # with itself.
        # Audioplayers are not threadsafe and should only be interacted with through the main
        # thread.
        # TODO: That last line is more directed to pyglet users, maybe throw it into the docs
        # somewhere.
        pass

    @abstractmethod
    def play(self):
        """Begin playback."""

    @abstractmethod
    def stop(self):
        """Stop (pause) playback."""

    @abstractmethod
    def clear(self):
        """Clear all buffered data and prepare for replacement data.

        The player must be stopped before calling this method.
        """
        self._events.clear()
        self._compensated_bytes = 0
        self.audio_sync_measurements.clear()
        self.audio_sync_cumul_measurements = 0

    @abstractmethod
    def delete(self):
        """Stop playing and clean up all resources used by player."""
        # This may be called from high level Players on shutdown after the player's driver
        # has been deleted. AudioPlayer implementations must handle this.

    @abstractmethod
    def get_play_cursor(self):
        """Get this player's most recent play cursor/read index/byte offset,
        starting from the last clear operation or initialization.

        ``0`` is an acceptable return value when unavailable or unknown.
        """
        # This method should not/does not need to ask the audio backend for the
        # most recent play cursor position.
        # It is not supposed to be accurate; accurate play cursor info is always
        # passed into the corresponding methods from the implementation subclass.

    def get_time(self):
        """Retrieve the time in the current source the player is at, in seconds.
        By default, calculated using :meth:`get_play_cursor`, divided by the
        bytes per second played.
        """
        # See notes on `get_play_cursor` as well.
        return self._raw_play_cursor_to_time(self.get_play_cursor()) + self.player.last_seek_time

    def _raw_play_cursor_to_time(self, cursor):
        if cursor is None:
            return None
        return self._to_perceived_play_cursor(cursor) / self.source.audio_format.bytes_per_second

    def _to_perceived_play_cursor(self, play_cursor):
        return play_cursor - self._compensated_bytes

    def _play_group(self, audio_players):
        """Begin simultaneous playback on a list of audio players."""
        # This should be overridden by subclasses for better synchrony.
        for player in audio_players:
            player.play()

    def _stop_group(self, audio_players):
        """Stop simultaneous playback on a list of audio players."""
        # This should be overridden by subclasses for better synchrony.
        for player in audio_players:
            player.stop()

    def append_events(self, start_index, events):
        """Append the given :class:`MediaEvent`s to the events deque using
        the current source's audio format and the supplied ``start_index``
        to convert their timestamps to dispatch indices.

        The high level player's ``last_seek_time`` will be subtracted from
        each event's timestamp.
        """
        bps = self.source.audio_format.bytes_per_second
        lst = self.player.last_seek_time
        for event in events:
            event_cursor = start_index + (max(0.0, event.timestamp - lst) * bps)
            assert _debug(f'AbstractAudioPlayer: Adding event {event} at {event_cursor}')
            self._events.append((event_cursor, event))

    def dispatch_media_events(self, until_cursor):
        """Dispatch all :class:`MediaEvent`s whose index is less than or equal
        to the specified ``until_cursor`` (which should be a very recent play
        cursor position).
        Please note that :attr:`_compensated_bytes` will be subtracted from
        the passed ``until_cursor``.
        """
        until_cursor = self._to_perceived_play_cursor(until_cursor)

        while self._events and self._events[0][0] <= until_cursor:
            self._events.popleft()[1].sync_dispatch_to_player(self.player)

    def get_audio_time_diff(self, audio_time):
        """Query the difference between the provided time and the high
        level `Player`'s master clock.

        The time difference returned is calculated as an average on previous
        audio time differences.

        Return a tuple of the bytes the player is off by, aligned to correspond
        to an integer number of audio frames, as well as bool designating
        whether the difference is extreme. If it is, it should be rectified
        immediately and all previous measurements will have been cleared.

        This method will return ``0, False`` if the difference is not
        significant or ``audio_time`` is ``None``.

        :rtype: int, bool
        """
        if audio_time is not None:
            p_time = self.player.time
            audio_time += self.player.last_seek_time

            diff_bytes = self.source.audio_format.timestamp_to_bytes_aligned(audio_time - p_time)

            if abs(diff_bytes) >= self.desync_bytes_critical:
                self.audio_sync_measurements.clear()
                self.audio_sync_cumul_measurements = 0
                return diff_bytes, True

            required_measurement_count = self.audio_sync_measurements.maxlen
            if len(self.audio_sync_measurements) == required_measurement_count:
                self.audio_sync_cumul_measurements -= self.audio_sync_measurements[0]
            self.audio_sync_measurements.append(diff_bytes)
            self.audio_sync_cumul_measurements += diff_bytes

        if len(self.audio_sync_measurements) == required_measurement_count:
            avg_diff = self.source.audio_format.align(
                self.audio_sync_cumul_measurements // required_measurement_count)

            # print(
            #     f"{diff_bytes:>6}, {avg_diff:>6} | "
            #     f"{(diff_bytes / self.source.audio_format.bytes_per_second):>9.6f}, "
            #     f"{(avg_diff / self.source.audio_format.bytes_per_second):>9.6f}"
            # )
            if abs(avg_diff) > self.desync_bytes_minor:
                return avg_diff, False
        # else:
        #     if audio_time is not None:
        #         print(
        #             f"{diff_bytes:>6}, | "
        #             f"{(diff_bytes / self.source.audio_format.bytes_per_second):>9.6f}, "
        #         )

        return 0, False

    def _get_and_compensate_audio_data(self, requested_size, audio_position=None):
        """
        Retrieve a packet of `AudioData` of the given size.
        """
        audio_time = self._raw_play_cursor_to_time(audio_position)
        desync_bytes, extreme_desync = self.get_audio_time_diff(audio_time)

        if desync_bytes == 0:
            return self.source.get_audio_data(requested_size)

        compensated_bytes = 0
        afmt = self.source.audio_format

        assert _debug(f"Audio desync, {desync_bytes=}, {extreme_desync=}")
        assert desync_bytes % afmt.bytes_per_frame == 0

        if desync_bytes > 0:
            # Player running ahead
            # Request at most 12ms less or only enough to not undercut the request size by 1024
            # We can't do anything if this is a major desync (other than seeking backwards later),
            # but trying to avoid seeking behind the high level player's back)
            compensated_bytes = min(
                requested_size - afmt.align_ceil(1024),
                desync_bytes,
                self.desync_correction_bytes_minor,
            )

            audio_data = self.source.get_audio_data(requested_size - compensated_bytes)
            if audio_data is not None:
                if audio_data.length < afmt.bytes_per_frame:
                    raise RuntimeError("Partial audio frame returned?")

                first_frame = ctypes.string_at(audio_data.pointer, afmt.bytes_per_frame)
                ad = bytearray(audio_data.length + compensated_bytes)
                ad[0:compensated_bytes] = first_frame * (compensated_bytes // afmt.bytes_per_frame)
                ad[compensated_bytes:] = audio_data.data

                audio_data = AudioData(ad, len(ad), audio_data.events)

        elif desync_bytes < 0:
            # Player falling behind
            # Skip at most 12ms if this is a minor desync, otherwise skip the entire
            # difference. this will be noticeable, but the desync is
            # likely already noticable in context of whatever the application does.
            compensated_bytes = (-desync_bytes
                                 if extreme_desync
                                 else min(-desync_bytes, self.desync_correction_bytes_minor))

            audio_data = self.source.get_audio_data(requested_size + compensated_bytes)
            if audio_data is not None:
                if audio_data.length <= compensated_bytes:
                    compensated_bytes = -audio_data.length
                    audio_data = None
                else:
                    audio_data = AudioData(
                        ctypes.string_at(
                            audio_data.pointer + compensated_bytes,
                            audio_data.length - compensated_bytes,
                        ),
                        audio_data.length - compensated_bytes,
                        audio_data.events,
                    )
                    compensated_bytes *= -1

        assert _debug(f"Compensated {compensated_bytes} after audio desync")
        self._compensated_bytes += compensated_bytes

        return audio_data

    def set_volume(self, volume):
        """See `Player.volume`."""
        pass

    def set_position(self, position):
        """See :py:attr:`~pyglet.media.Player.position`."""
        pass

    def set_min_distance(self, min_distance):
        """See `Player.min_distance`."""
        pass

    def set_max_distance(self, max_distance):
        """See `Player.max_distance`."""
        pass

    def set_pitch(self, pitch):
        """See :py:attr:`~pyglet.media.Player.pitch`."""
        pass

    def set_cone_orientation(self, cone_orientation):
        """See `Player.cone_orientation`."""
        pass

    def set_cone_inner_angle(self, cone_inner_angle):
        """See `Player.cone_inner_angle`."""
        pass

    def set_cone_outer_angle(self, cone_outer_angle):
        """See `Player.cone_outer_angle`."""
        pass

    def set_cone_outer_gain(self, cone_outer_gain):
        """See `Player.cone_outer_gain`."""
        pass


class AbstractAudioDriver(metaclass=ABCMeta):
    @abstractmethod
    def create_audio_player(self, source, player):
        pass

    @abstractmethod
    def get_listener(self):
        pass

    @abstractmethod
    def delete(self):
        pass


class MediaEvent:
    """Representation of a media event.

    These events are used internally by some audio driver implementation to
    communicate events to the :class:`~pyglet.media.player.Player`.
    One example is the ``on_eos`` event.

    Args:
        event (str): Event description.
        timestamp (float): The time when this event happens.
        *args: Any required positional argument to go along with this event.
    """

    __slots__ = 'event', 'timestamp', 'args'

    def __init__(self, event, timestamp=0.0, *args):
        # Meaning of timestamp is dependent on context; and not seen by application.
        self.event = event
        self.timestamp = timestamp
        self.args = args

    def sync_dispatch_to_player(self, player):
        pyglet.app.platform_event_loop.post_event(player, self.event, *self.args)

    def __repr__(self):
        return f"MediaEvent({self.event}, {self.timestamp}, {self.args})"

    def __lt__(self, other):
        if not isinstance(other, MediaEvent):
            return NotImplemented
        return self.timestamp < other.timestamp
