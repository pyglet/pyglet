from __future__ import print_function
from __future__ import division
from builtins import object
# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------
import buffered_logger as bl

import pyglet
from pyglet.media.drivers import get_audio_driver, get_silent_audio_driver
from pyglet.media.events import MediaEvent
from pyglet.media.exceptions import MediaException
from pyglet.media.sources.base import SourceGroup, StaticSource

_debug = pyglet.options['debug_media']

clock = pyglet.clock.get_default()

class Player(pyglet.event.EventDispatcher):
    """High-level sound and video player.
    """

    _last_video_timestamp = None
    _texture = None

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

    def __init__(self):
        # List of queued source groups
        self._groups = []

        self._audio_player = None

        # Desired play state (not an indication of actual state).
        self._playing = False

        self._time = 0.0
        self._systime = None

    def queue(self, source):
        if isinstance(source, SourceGroup):
            self._groups.append(source)
        else:
            if (self._groups and
                source.audio_format == self._groups[-1].audio_format and
                source.video_format == self._groups[-1].video_format):
                self._groups[-1].queue(source)
            else:
                group = SourceGroup(source.audio_format, source.video_format)
                group.queue(source)
                self._groups.append(group)

        self._set_playing(self._playing)

    def _set_playing(self, playing):
        #stopping = self._playing and not playing
        #starting = not self._playing and playing

        self._playing = playing
        source = self.source

        if playing and source:
            if not self._audio_player:
                self._create_audio_player()
                if bl.logger is not None:
                    bl.logger.init_wall_time()
                    bl.logger.log("p.P._sp", 0.0)
            self._audio_player.prefill_audio()
            self._audio_player.play()

            if source.video_format:
                if not self._texture:
                    self._create_texture()
                pyglet.clock.schedule_once(self.update_texture, 0)
            self._systime = clock.time()
            # Add a delay to de-synchronize the audio
            # Negative number means audio runs ahead.
            self._systime += -0.3
        else:
            if self._audio_player:
                self._audio_player.stop()

            pyglet.clock.unschedule(self.update_texture)
            self._time = self._get_time()
            self._systime = None

    def play(self): 
        self._set_playing(True)

    def pause(self):
        self._set_playing(False)

        # if self._audio_player:
        #     time = self._audio_player.get_time()
        #     time = self._groups[0].translate_timestamp(time)
        #     if time is not None:
        #         self._time = time

    def delete(self):
        self.pause()

        if self._audio_player:
            self._audio_player.delete()
            self._audio_player = None

        while self._groups:
            del self._groups[0]

    def next_source(self):
        if not self._groups:
            return

        group = self._groups[0]
        if group.has_next():
            group.next_source()
            return

        if self.source.video_format:
            self._texture = None
            pyglet.clock.unschedule(self.update_texture)

        if self._audio_player:
            self._audio_player.delete()
            self._audio_player = None

        del self._groups[0]
        if self._groups:
            self._set_playing(self._playing)
            return

        self._set_playing(False)
        self.dispatch_event('on_player_eos')

    #: :deprecated: Use `next_source` instead.
    next = next_source  # old API, worked badly with 2to3

    def seek(self, time):
        playing = self._playing
        self.pause()
        if not self.source:
            return

        if bl.logger is not None:
            bl.logger.log("p.P.sk", time)

        self._time = time
        self.source.seek(time)
        if self._audio_player:
            # XXX: According to docstring in AbstractAudioPlayer this cannot be called when the
            # player is not stopped
            self._audio_player.clear()
            self._audio_player.seek(time)
        if self.source.video_format:
            self._last_video_timestamp = None
            self.update_texture(time=time)
            pyglet.clock.unschedule(self.update_texture)
        self._set_playing(playing)

    def _create_audio_player(self):
        assert not self._audio_player
        assert self._groups

        group = self._groups[0]
        audio_format = group.audio_format
        if audio_format:
            audio_driver = get_audio_driver()
        else:
            audio_driver = get_silent_audio_driver()
        self._audio_player = audio_driver.create_audio_player(group, self)

        _class = self.__class__
        def _set(name):
            private_name = '_' + name
            value = getattr(self, private_name) 
            if value != getattr(_class, private_name):
                getattr(self._audio_player, 'set_' + name)(value)
        _set('volume')
        _set('min_distance')
        _set('max_distance')
        _set('position')
        _set('pitch')
        _set('cone_orientation')
        _set('cone_inner_angle')
        _set('cone_outer_angle')
        _set('cone_outer_gain')

    def _get_source(self):
        if not self._groups:
            return None
        return self._groups[0].get_current_source()

    source = property(_get_source)

    playing = property(lambda self: self._playing)

    def _get_time(self):
        if self._systime is None:
            now = self._time
        else:
            now = clock.time() - self._systime + self._time
        return now
        # time = None
        # if self._playing and self._audio_player:
        #     time = self._audio_player.get_time()
        #     time = self._groups[0].translate_timestamp(time)

        # if time is None:
        #     return self._time
        # else:
        #     return time

    time = property(_get_time)

    def _create_texture(self):
        video_format = self.source.video_format
        self._texture = pyglet.image.Texture.create(
            video_format.width, video_format.height, rectangle=True)
        self._texture = self._texture.get_transform(flip_y=True)
        self._texture.anchor_y = 0

    def get_texture(self):
        return self._texture

    def seek_next_frame(self):
        """Step forwards one video frame in the current Source.
        """
        time = self._groups[0].get_next_video_timestamp()
        if time is None:
            return
        self.seek(time)

    def update_texture(self, dt=None, time=None):
        if bl.logger is not None:
            bl.logger.log("p.P.ut.1.0", dt, time, bl.logger.rebased_wall_time())
        if time is None:
            time = self.time
            if bl.logger is not None:
                bl.logger.log("p.P.ut.1.2", time, self._audio_player.get_time())
        # if time is None:
        #     if bl.logger is not None:
        #         delay = 1. / 30
        #         bl.logger.log("p.P.ut.1.3", delay)
        #     pyglet.clock.schedule_once(self.update_texture, delay)
        #     return

        if (self._last_video_timestamp is not None and 
            time <= self._last_video_timestamp):
            delay = 1. / 30
            if bl.logger is not None:
                bl.logger.log("p.P.ut.1.4", delay)
            pyglet.clock.schedule_once(self.update_texture, delay)
            return

        ts = self._groups[0].get_next_video_timestamp()
        while ts is not None and ts+0.04 < time: # Allow 40 ms difference
            self._groups[0].get_next_video_frame() # Discard frame
            if bl.logger is not None:
                bl.logger.log("p.P.ut.1.5", ts)
            ts = self._groups[0].get_next_video_timestamp()

        if bl.logger is not None:
            bl.logger.log("p.P.ut.1.6", ts)

        if ts is None:
            self._last_video_timestamp = None
            delay = 1./ 30
            if bl.logger is not None:
                bl.logger.log("p.P.ut.1.7", delay)
            pyglet.clock.schedule_once(self.update_texture, delay)
            return

        image = self._groups[0].get_next_video_frame()
        if image is not None:
            if self._texture is None:
                self._create_texture()
            self._texture.blit_into(image, 0, 0, 0)
            self._last_video_timestamp = ts
        elif bl.logger is not None:
            bl.logger.log("p.P.ut.1.8")
        
        ts = self._groups[0].get_next_video_timestamp()
        if ts is None:
            delay = 1. / 30
        else:
            delay = ts - time

        if bl.logger is not None:
            bl.logger.log("p.P.ut.1.9", delay, ts)
        pyglet.clock.schedule_once(self.update_texture, delay)

    def _player_property(name, doc=None):
        private_name = '_' + name
        set_name = 'set_' + name
        def _player_property_set(self, value):
            setattr(self, private_name, value)
            if self._audio_player:
                getattr(self._audio_player, set_name)(value)

        def _player_property_get(self):
            return getattr(self, private_name)

        return property(_player_property_get, _player_property_set, doc=doc)

    # TODO docstrings for these...
    volume = _player_property('volume')
    min_distance = _player_property('min_distance')
    max_distance = _player_property('max_distance')
    position = _player_property('position')
    pitch = _player_property('pitch')
    cone_orientation = _player_property('cone_orientation')
    cone_inner_angle = _player_property('cone_inner_angle')
    cone_outer_angle = _player_property('cone_outer_angle')
    cone_outer_gain = _player_property('cone_outer_gain')

    # Events

    def on_player_eos(self):
        """The player ran out of sources.

        :event:
        """
        pass

    def on_source_group_eos(self):
        """The current source group ran out of data.

        The default behaviour is to advance to the next source group if
        possible.

        :event:
        """
        self.next_source()
        if _debug:
            print('Player.on_source_group_eos')

    def on_eos(self):
        """

        :event:
        """
        if bl.logger is not None:
            bl.logger.log("p.P.oe")
            bl.logger.close()

Player.register_event_type('on_eos')
Player.register_event_type('on_player_eos')
Player.register_event_type('on_source_group_eos')


class PlayerGroup(object):
    """Group of players that can be played and paused simultaneously.

    :Ivariables:
        `players` : list of `Player`
            Players in this group.

    """

    def __init__(self, players):
        """Create a player group for the given set of players.

        All players in the group must currently not belong to any other
        group.

        :Parameters:
            `players` : Sequence of `Player`
                Players to add to this group.

        """
        self.players = list(players)

    def play(self):
        """Begin playing all players in the group simultaneously.
        """
        audio_players = [p._audio_player \
                         for p in self.players if p._audio_player]
        if audio_players:
            audio_players[0]._play_group(audio_players)
        for player in self.players:
            player.play()

    def pause(self):
        """Pause all players in the group simultaneously.
        """
        audio_players = [p._audio_player \
                         for p in self.players if p._audio_player]
        if audio_players:
            audio_players[0]._stop_group(audio_players)
        for player in self.players:
            player.pause()


