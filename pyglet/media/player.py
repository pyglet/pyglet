"""High-level sound and video player."""
from __future__ import annotations

import time
from collections import deque

from typing import TYPE_CHECKING, Iterable, Generator

import pyglet

from pyglet.gl import GL_TEXTURE_2D
from pyglet.media import buffered_logger as bl
from pyglet.media.drivers import get_audio_driver
from pyglet.media.codecs.base import Source, SourceGroup

_debug = pyglet.options['debug_media']

if TYPE_CHECKING:
    from pyglet.image import Texture


class PlaybackTimer:
    """Playback Timer.

    This is a simple timer object which tracks the time elapsed. It can be
    paused and reset.
    """

    def __init__(self) -> None:
        self._elapsed = 0.0
        self._started_at = None

    def start(self) -> None:
        """Start the timer."""
        if self._started_at is None:
            self._started_at = time.perf_counter()

    def pause(self) -> None:
        """Pause the timer."""
        self._elapsed = self.get_time()
        self._started_at = None

    def reset(self) -> None:
        """Reset the timer to 0."""
        self._elapsed = 0.0
        if self._started_at is not None:
            self._started_at = time.perf_counter()

    def get_time(self) -> float:
        """Get the elapsed time."""
        if self._started_at is None:
            return self._elapsed

        return time.perf_counter() - self._started_at + self._elapsed

    def set_time(self, value: float) -> None:
        """
        Manually set the elapsed time.

        Args:
            value (float): the new elapsed time value
        """
        self.reset()
        self._elapsed = value


class _PlayerProperty:
    """Descriptor for Player attributes to forward to the AudioPlayer.

    We want the Player to have attributes like volume, pitch, etc. These are
    actually implemented by the AudioPlayer. So this descriptor will forward
    an assignement to one of the attributes to the AudioPlayer. For example
    `player.volume = 0.5` will call `player._audio_player.set_volume(0.5)`.

    The Player class has default values at the class level which are retrieved
    if not found on the instance.
    """

    def __init__(self, attribute, doc=None):
        self.private_name = '_' + attribute
        self.setter_name = 'set_' + attribute
        self.__doc__ = doc or ''

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.private_name in obj.__dict__:
            return obj.__dict__[self.private_name]
        return getattr(objtype, self.private_name)

    def __set__(self, obj, value):
        obj.__dict__[self.private_name] = value
        if obj._audio_player:
            getattr(obj._audio_player, self.setter_name)(value)


class Player(pyglet.event.EventDispatcher):
    """High-level sound and video player."""

    # Spacialisation attributes, preserved between audio players
    _volume = 1.0
    _min_distance = 1.0
    _max_distance = 100000000.

    _position = (0, 0, 0)
    _pitch = 1.0

    _cone_orientation = (0, 0, 1)
    _cone_inner_angle = 360.
    _cone_outer_angle = 360.
    _cone_outer_gain = 1.

    def __init__(self) -> None:
        """Initialize the Player with a MasterClock."""
        self._source = None
        self._playlists = deque()
        self._audio_player = None

        self._context = pyglet.gl.current_context
        self._texture = None

        # Desired play state (not an indication of actual state).
        self._playing = False

        self.last_seek_time = 0.0

        self._timer = PlaybackTimer()
        #: Loop the current source indefinitely or until
        #: :meth:`~Player.next_source` is called. Defaults to ``False``.
        #:
        #: :type: bool
        #:
        #: .. versionadded:: 1.4
        self.loop = False

    def __del__(self) -> None:
        """Release the Player resources."""
        self.delete()

    def queue(self, source: Source | Iterable[Source]) -> None:
        """Queue the source on this player.

        If the player has no source, the player will start to play immediately
        or pause depending on its :attr:`.playing` attribute.
        """
        if isinstance(source, (Source, SourceGroup)):
            source = _one_item_playlist(source)
        else:
            try:
                source = iter(source)
            except TypeError:
                raise TypeError("source must be either a Source or an iterable."
                                " Received type {0}".format(type(source)))
        self._playlists.append(source)

        if self.source is None:
            self._set_source(next(self._playlists[0]))

        self._set_playing(self._playing)

    def _set_source(self, new_source: Source | None) -> None:
        if new_source is None:
            self._source = None
        else:
            self._source = new_source.get_queue_source()

    def _set_playing(self, playing: bool) -> None:
        # stopping = self._playing and not playing
        starting = not self._playing and playing

        self._playing = playing
        source = self.source

        if playing and source:
            if source.audio_format is not None:
                if (was_created := self._audio_player is None):
                    self._create_audio_player()
                if self._audio_player is not None and (was_created or starting):
                    self._audio_player.prefill_audio()

            if bl.logger is not None:
                bl.logger.init_wall_time()
                bl.logger.log("p.P._sp", 0.0)

            if source.video_format is not None:
                if self._texture is None:
                    self._create_texture()

            if self._audio_player is not None:
                self._audio_player.play()
            if source.video_format is not None:
                pyglet.clock.schedule_once(self.update_texture, 0)
            # For audio synchronization tests, the following will
            # add a delay to de-synchronize the audio.
            # Negative number means audio runs ahead.
            # self._mclock._systime += -0.3
            self._timer.start()
            if self._audio_player is None and source.video_format is None:
                pyglet.clock.schedule_once(lambda dt: self.dispatch_event("on_eos"), source.duration)

        else:
            if self._audio_player is not None:
                self._audio_player.stop()

            pyglet.clock.unschedule(self.update_texture)
            self._timer.pause()

    @property
    def playing(self) -> bool:
        """The current playing state.

        The *playing* property is irrespective of whether or not there is
        actually a source to play. If *playing* is ``True`` and a source is
        queued, it will begin to play immediately. If *playing* is ``False``,
        it is implied that the player is paused. There is no other possible
        state.
        """
        return self._playing

    def play(self) -> None:
        """Begin playing the current source.

        This has no effect if the player is already playing.
        """
        self._set_playing(True)

    def pause(self) -> None:
        """Pause playback of the current source.

        This has no effect if the player is already paused.
        """
        self._set_playing(False)

    def delete(self) -> None:
        """Release the resources acquired by this player.

        The internal audio player and the texture will be deleted.
        """
        if self._source:
            self.source.is_player_source = False
        if self._audio_player is not None:
            self._audio_player.delete()
            self._audio_player = None
        if self._texture is not None:
            self._texture = None

    def next_source(self) -> None:
        """Move immediately to the next source in the current playlist.

        If the playlist is empty, discard it and check if another playlist
        is queued. There may be a gap in playback while the audio buffer
        is refilled.
        """
        was_playing = self._playing
        self.pause()

        self._timer.reset()
        self.last_seek_time = 0.0

        if self._source:
            self.seek(0.0)
            self.source.is_player_source = False

        playlists = self._playlists
        if not playlists:
            return

        try:
            new_source = next(playlists[0])
        except StopIteration:
            playlists.popleft()
            if not playlists:
                new_source = None
            else:
                # Could someone queue an iterator which is empty??
                new_source = next(playlists[0])

        if new_source is None:
            self._source = None
            self.delete()
            self.dispatch_event('on_player_eos')
        else:
            # Keeping a strong reference to old source directly as `_audio_player` only has
            # a weakref and still accesses it in `set_source`
            old_source = self._source
            self._set_source(new_source)

            if self._audio_player is not None:
                if self._source.audio_format == old_source.audio_format:
                    self._audio_player.set_source(self._source)
                else:
                    self._audio_player.delete()
                    self._audio_player = None
            if self._source.video_format != old_source.video_format:
                self._texture = None
                pyglet.clock.unschedule(self.update_texture)

            del old_source

            self._set_playing(was_playing)
            self.dispatch_event('on_player_next_source')

    def seek(self, timestamp: float) -> None:
        """Seek for playback to the indicated timestamp on the current source.

        Timestamp is expressed in seconds. If the timestamp is outside the
        duration of the source, it will be clamped to the end.
        """
        playing = self._playing
        if playing:
            self.pause()
        if self.source is None:
            return

        if bl.logger is not None:
            bl.logger.log("p.P.sk", timestamp)

        timestamp = max(timestamp, 0.0)
        if self._source.duration is not None:
            # TODO: If the duration is reported as None and the source clamps anyways,
            # this will have pretty bad effects.
            # Maybe have seek methods return the timestamp they actually seeked to
            timestamp = min(timestamp, self._source.duration)

        self._timer.set_time(timestamp)
        self._source.seek(timestamp)
        self.last_seek_time = timestamp

        if self._audio_player is not None:
            # XXX: According to docstring in AbstractAudioPlayer this cannot
            # be called when the player is not stopped
            self._audio_player.clear()
        if self.source.video_format is not None:
            self.update_texture()
            pyglet.clock.unschedule(self.update_texture)
        self._set_playing(playing)

    def _create_audio_player(self) -> None:
        assert not self._audio_player
        assert self.source

        source = self.source
        audio_driver = get_audio_driver()
        if audio_driver is None:
            # Failed to find a valid audio driver
            return

        self._audio_player = audio_driver.create_audio_player(source, self)

        # Set the audio player attributes
        for attr in ('volume', 'min_distance', 'max_distance', 'position',
                     'pitch', 'cone_orientation', 'cone_inner_angle',
                     'cone_outer_angle', 'cone_outer_gain'):
            value = getattr(self, attr)
            setattr(self, attr, value)

    @property
    def source(self) -> Source | None:
        """Read-only. The current :class:`Source`, or ``None``."""
        return self._source

    @property
    def time(self) -> float:
        """Read-only. Current playback time of the current source.

        The playback time is a float expressed in seconds, with 0.0 being the
        beginning of the media. The playback time returned represents the
        player master clock time which is used to synchronize both the audio
        and the video.
        """
        return self._timer.get_time()

    def _create_texture(self) -> None:
        video_format = self.source.video_format
        self._texture = pyglet.image.Texture.create(video_format.width, video_format.height, GL_TEXTURE_2D)
        self._texture = self._texture.get_transform(flip_y=True)
        # After flipping the texture along the y axis, the anchor_y is set
        # to the top of the image. We want to keep it at the bottom.
        self._texture.anchor_y = 0
        return self._texture

    @property
    def texture(self) -> Texture | None:
        """Get the texture for the current video frame, if any.

        You should query this property every time you display a frame of video,
        as multiple textures might be used. This property will be ``None`` if
        the current Source does not contain video.
        """
        return self._texture

    def seek_next_frame(self) -> None:
        """Step forwards one video frame in the current source."""
        time = self.source.get_next_video_timestamp()
        if time is None:
            return
        self.seek(time)

    def update_texture(self, dt: float | None = None) -> None:
        """Manually update the texture from the current source.

        This happens automatically, so you shouldn't need to call this method.

        Args:
            dt:
                The time elapsed since the last call to ``update_texture``.
        """
        # self.pr.disable()
        # if dt > 0.05:
        #     print("update_texture dt:", dt)
        #     import pstats
        #     ps = pstats.Stats(self.pr).sort_stats("cumulative")
        #     ps.print_stats()
        source = self.source
        time = self.time
        if bl.logger is not None:
            bl.logger.log(
                "p.P.ut.1.0", dt, time,
                self._audio_player.get_time() if self._audio_player else 0,
                bl.logger.rebased_wall_time()
            )

        frame_rate = source.video_format.frame_rate
        frame_duration = 1 / frame_rate
        ts = source.get_next_video_timestamp()
        # Allow up to frame_duration difference
        while ts is not None and ts + frame_duration < time:
            source.get_next_video_frame()  # Discard frame
            if bl.logger is not None:
                bl.logger.log("p.P.ut.1.5", ts)
            ts = source.get_next_video_timestamp()

        if bl.logger is not None:
            bl.logger.log("p.P.ut.1.6", ts)

        if ts is None:
            # No more video frames to show. End of video stream.
            if bl.logger is not None:
                bl.logger.log("p.P.ut.1.7", frame_duration)

            pyglet.clock.schedule_once(self._video_finished, 0)
            return
        elif ts > time:
            # update_texture called too early (probably manually!)
            pyglet.clock.schedule_once(self.update_texture, ts - time)
            return


        image = source.get_next_video_frame()
        if image is not None:
            with self._context:
                if self._texture is None:
                    self._create_texture()
                self._texture.blit_into(image, 0, 0, 0)
        elif bl.logger is not None:
            bl.logger.log("p.P.ut.1.8")

        ts = source.get_next_video_timestamp()
        if ts is None:
            delay = frame_duration
        else:
            delay = ts - time

        delay = max(0.0, delay)
        if bl.logger is not None:
            bl.logger.log("p.P.ut.1.9", delay, ts)
        pyglet.clock.schedule_once(self.update_texture, delay)
        # self.pr.enable()

    def _video_finished(self, _dt: float) -> None:
        if self._audio_player is None:
            self.dispatch_event("on_eos")

    volume = _PlayerProperty('volume', doc="""
    The volume level of sound playback.

    The nominal level is 1.0, and 0.0 is silence.

    The volume level is affected by the distance from the listener (if
    positioned).
    """)
    min_distance = _PlayerProperty('min_distance', doc="""
    The distance beyond which the sound volume drops by half, and within
    which no attenuation is applied.

    The minimum distance controls how quickly a sound is attenuated as it
    moves away from the listener. The gain is clamped at the nominal value
    within the min distance. By default the value is 1.0.

    The unit defaults to meters, but can be modified with the listener
    properties. """)
    max_distance = _PlayerProperty('max_distance', doc="""
    The distance at which no further attenuation is applied.

    When the distance from the listener to the player is greater than this
    value, attenuation is calculated as if the distance were value. By
    default the maximum distance is infinity.

    The unit defaults to meters, but can be modified with the listener
    properties.
    """)
    position = _PlayerProperty('position', doc="""
    The position of the sound in 3D space.

    The position is given as a tuple of floats (x, y, z). The unit
    defaults to meters, but can be modified with the listener properties.
    """)
    pitch = _PlayerProperty('pitch', doc="""
    The pitch shift to apply to the sound.

    The nominal pitch is 1.0. A pitch of 2.0 will sound one octave higher,
    and play twice as fast. A pitch of 0.5 will sound one octave lower, and
    play twice as slow. A pitch of 0.0 is not permitted.
    """)
    cone_orientation = _PlayerProperty('cone_orientation', doc="""
    The direction of the sound in 3D space.

    The direction is specified as a tuple of floats (x, y, z), and has no
    unit. The default direction is (0, 0, -1). Directional effects are only
    noticeable if the other cone properties are changed from their default
    values.
    """)
    cone_inner_angle = _PlayerProperty('cone_inner_angle', doc="""
    The interior angle of the inner cone.

    The angle is given in degrees, and defaults to 360. When the listener
    is positioned within the volume defined by the inner cone, the sound is
    played at normal gain (see :attr:`volume`).
    """)
    cone_outer_angle = _PlayerProperty('cone_outer_angle', doc="""
    The interior angle of the outer cone.

    The angle is given in degrees, and defaults to 360. When the listener
    is positioned within the volume defined by the outer cone, but outside
    the volume defined by the inner cone, the gain applied is a smooth
    interpolation between :attr:`volume` and :attr:`cone_outer_gain`.
    """)
    cone_outer_gain = _PlayerProperty('cone_outer_gain', doc="""
    The gain applied outside the cone.

    When the listener is positioned outside the volume defined by the outer
    cone, this gain is applied instead of :attr:`volume`.
    """)

    # Events

    def on_player_eos(self):
        """The player ran out of sources. The playlist is empty."""
        if _debug:
            print('Player.on_player_eos')

    def on_eos(self):
        """The current source ran out of data.

        The default behaviour is to advance to the next source in the
        playlist if the :attr:`.loop` attribute is set to ``False``.
        If :attr:`.loop` attribute is set to ``True``, the current source
        will start to play again until :meth:`next_source` is called or
        :attr:`.loop` is set to ``False``.
        """
        if _debug:
            print('Player.on_eos')
        if bl.logger is not None:
            bl.logger.log("p.P.oe")
            bl.logger.close()

        if self.loop:
            was_playing = self._playing
            self.pause()
            self._timer.reset()

            if self.source is not None:
                # Reset source to the beginning
                self.seek(0.0)
            self._set_playing(was_playing)

        else:
            self.next_source()

    def on_player_next_source(self):
        """The player starts to play the next queued source in the playlist.

        This is a useful event for adjusting the window size to the new
        source :class:`VideoFormat` for example.
        """

    def on_driver_reset(self):
        """The audio driver has been reset.

        By default this will kill the current audio player, create a new one,
        and requeue the buffers. Any buffers that may have been queued in a
        player will be resubmitted. It will continue from the last buffers
        submitted, not played, and may cause sync issues if using video.
        """
        if self._audio_player is None:
            return

        self._audio_player.on_driver_reset()

        # Voice has been changed, will need to reset all options on the voice.
        for attr in ('volume', 'min_distance', 'max_distance', 'position', 'pitch',
                     'cone_orientation', 'cone_inner_angle', 'cone_outer_angle', 'cone_outer_gain'):
            value = getattr(self, attr)
            setattr(self, attr, value)

        if self._playing:
            self._audio_player.play()


Player.register_event_type('on_eos')
Player.register_event_type('on_player_eos')
Player.register_event_type('on_player_next_source')
Player.register_event_type('on_driver_reset')


def _one_item_playlist(source: Source) -> Generator:
    yield source


class PlayerGroup:
    """Group of players that can be played and paused simultaneously.

    Create a player group for the given list of players.

    All players in the group must currently not belong to any other group.
    """

    def __init__(self, players: Iterable[Player]) -> None:
        """Initialize the PlayerGroup with the players."""
        self.players = list(players)

    def play(self) -> None:
        """Begin playing all players in the group simultaneously."""
        audio_players = [p._audio_player
                         for p in self.players if p._audio_player]
        if audio_players:
            audio_players[0]._play_group(audio_players)
        for player in self.players:
            player.play()

    def pause(self) -> None:
        """Pause all players in the group simultaneously."""
        audio_players = [p._audio_player
                         for p in self.players if p._audio_player]
        if audio_players:
            audio_players[0]._stop_group(audio_players)
        for player in self.players:
            player.pause()
