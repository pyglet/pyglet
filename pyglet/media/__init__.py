#!/usr/bin/python
# $Id$

'''Media playback interface.

'''

import sys

class MediaException(Exception):
    pass

class Medium(object):
    duration = 0
    
    has_audio = False
    has_video = False

    def get_sound(self):
        raise NotImplementedError('abstract')

    def play(self):
        sound = self.get_sound()
        sound.play()
        return sound

class Sound(object):
    '''An instance of a sound, either currently playing or ready to be played.

    By default, monaural sounds are played at nominal volume equally among
    all speakers, however they may also be positioned in 3D space.  Stereo
    sounds are not positionable.

    :Ivariables:
        `playing` : bool
            If True, the sound is currently playing.  Even after calling
            `play`, the sound may not begin playing until enough audio has
            been buffered.  This variable is read-only.
        `finished` : bool
            If True, the sound has finished playing.  This variable is
            read-only.
        `depth` : int
            The number of bits per sample per channel (usually 8 or 16).
            The value is None if the audio properties have not yet been
            determined.
        `channels` : int
            The number of audio channels provided: 1 for monoaural sound, 2
            for stereo, or more for multi-channel sound. The value is None if
            the audio properties have not yet been determined.
        `sample_rate` : float
            The audio sample rate, in Hz.  The sound may be resampled
            to match the audio device's sample rate; this value gives
            the original sample rate.  The value is None if the audio
            properties have not yet been determined.

    '''
        
    playing = False
    finished = False

    depth = None
    sample_rate = None
    channels = None

    _volume = 1.0
    _max_gain = 1.0
    _min_gain = 0.0

    _position = (0, 0, 0)
    _velocity = (0, 0, 0)
    _pitch = 1.0

    _cone_orientation = (0, 0, 0)
    _cone_inner_angle = 360.
    _cone_outer_angle = 360.
    _cone_outer_gain = 1.

    
    def play(self):
        '''Begin playing the sound.

        This has no effect if the sound is already playing.
        '''
        raise NotImplementedError('abstract')

    def pause(self):
        '''Pause playback of the sound.

        This has no effect if the sound is already paused.
        '''
        raise NotImplementedError('abstract')

    def _set_volume(self, volume):
        raise NotImplementedError('abstract')

    volume = property(lambda self: self._volume,
                      lambda self, volume: self._set_volume(volume),
                      doc='''The volume level of sound playback.

         The nominal level is 1.0, and 0.0 is silence.

         The volume level is affected by factors such as the distance from the
         listener (if positioned), and is clamped (after distance attenuation)
         to the range [min_gain, max_gain].''')

    def _set_min_gain(self, min_gain):
        raise NotImplementedError('abstract')

    min_gain = property(lambda self: self._min_gain,
                        lambda self, min_gain: self._set_min_gain(min_gain),
                        doc='''The minimum gain to apply to the sound, even

         The gain is clamped after distance attenuation.  The default value
         is 0.0.''')

    def _set_max_gain(self, max_gain):
        raise NotImplementedError('abstract')

    max_gain = property(lambda self: self._max_gain,
                        lambda self, max_gain: self._set_max_gain(max_gain),
                        doc='''The maximum gain to apply to the sound.
         
         The gain is clamped after distance attenuation.  The default value
         is 1.0.''')

    def _set_position(self, position):
        raise NotImplementedError('abstract')

    position = property(lambda self: self._position,
                        lambda self, position: self._set_position(position),
                        doc='''The position of the sound in 3D space.

        The position is given as a tuple of floats (x, y, z).  The unit
        defaults to meters, but can be modified with the listener
        properties.''')

    def _set_velocity(self, velocity):
        raise NotImplementedError('abstract')

    velocity = property(lambda self: self._velocity,
                        lambda self, velocity: self._set_velocity(velocity),
                        doc='''The velocity of the sound in 3D space.

        The velocity is given as a tuple of floats (x, y, z).  The unit
        defaults to meters per second, but can be modified with the listener
        properties.''')

    def _set_pitch(self, pitch):
        raise NotImplementedError('abstract')

    pitch = property(lambda self: self._pitch,
                     lambda self, pitch: self._set_pitch(pitch),
                     doc='''The pitch shift to apply to the sound.

        The nominal pitch is 1.0.  A pitch of 2.0 will sound one octave
        higher, and play twice as fast.  A pitch of 0.5 will sound one octave
        lower, and play twice as slow.  A pitch of 0.0 is not permitted.
        
        The pitch shift is applied to the source before doppler effects.''')

    def _set_cone_orientation(self, cone_orientation):
        raise NotImplementedError('abstract')

    cone_orientation = property(lambda self: self._cone_orientation,
                                lambda self, c: self._set_cone_orientation(c),
                                doc='''The direction of the sound in 3D space.
                                
        The direction is specified as a tuple of floats (x, y, z), and has no
        unit.  The default direction is (0, 0, -1).  Directional effects are
        only noticeable if the other cone properties are changed from their
        default values.''')

    def _set_cone_inner_angle(self, cone_inner_angle):
        raise NotImplementedError('abstract')

    cone_inner_angle = property(lambda self: self._cone_inner_angle,
                                lambda self, a: self._set_cone_inner_angle(a),
                                doc='''The interior angle of the inner cone.
                                
        The angle is given in degrees, and defaults to 360.  When the listener
        is positioned within the volume defined by the inner cone, the sound
        is played at normal gain (see `volume`).''')

    def _set_cone_outer_angle(self, cone_outer_angle):
        raise NotImplementedError('abstract')

    cone_outer_angle = property(lambda self: self._cone_outer_angle,
                                lambda self, a: self._set_cone_outer_angle(a),
                                doc='''The interior angle of the outer cone.
                                
        The angle is given in degrees, and defaults to 360.  When the listener
        is positioned within the volume defined by the outer cone, but outside
        the volume defined by the inner cone, the gain applied is a smooth
        interpolation between `volume` and `cone_outer_gain`.''')

    def _set_cone_outer_gain(self, cone_outer_gain):
        raise NotImplementedError('abstract')

    cone_outer_gain = property(lambda self: self._cone_outer_gain,
                                lambda self, g: self._set_cone_outer_gain(g),
                                doc='''The gain applied outside the cone.
                                
        When the listener is positioned outside the volume defined by the
        outer cone, this gain is applied instead of `volume`.''')

    def dispatch_events(self):
        '''Dispatch any pending events and perform regular heartbeat functions
        to maintain audio playback.

        This method is called automatically by `pyglet.media.dispatch_events`,
        there is no need to call this from an application.
        '''
        pass

class Listener(object):
    '''The listener properties for positional audio.

    You can obtain the singleton instance of this class as
    `pyglet.media.listener`.
    '''
    _volume = 1.0
    _position = (0, 0, 0)
    _velocity = (0, 0, 0)
    _forward_orientation = (0, 0, -1)
    _up_orientation = (0, 1, 0)

    _doppler_factor = 1.
    _speed_of_sound = 343.3

    def _set_volume(self, volume):
        raise NotImplementedError('abstract')

    volume = property(lambda self: self._volume,
                      lambda self, volume: self._set_volume(volume),
                      doc='''The master volume for sound playback.

        All sound volumes are multiplied by this master volume before being
        played.  A value of 0 will silence playback (but still consume
        resources).  The nominal volume is 1.0.''')

    def _set_position(self, position):
        raise NotImplementedError('abstract')

    position = property(lambda self: self._position,
                        lambda self, position: self._set_position(position),
                        doc='''The position of the listener in 3D space.

        The position is given as a tuple of floats (x, y, z).  The unit
        defaults to meters, but can be modified with the listener
        properties.''')

    def _set_velocity(self, velocity):
        raise NotImplementedError('abstract')

    velocity = property(lambda self: self._velocity,
                        lambda self, velocity: self._set_velocity(velocity),
                        doc='''The velocity of the listener in 3D space.

        The velocity is given as a tuple of floats (x, y, z).  The unit
        defaults to meters per second, but can be modified with the listener
        properties.''')

    def _set_forward_orientation(self, orientation):
        raise NotImplementedError('abstract')

    forward_orientation = property(lambda self: self._forward_orientation,
                               lambda self, o: self._set_forward_orientation(o),
                               doc='''A vector giving the direction the
        listener is facing.

        The orientation is given as a tuple of floats (x, y, z), and has
        no unit.  The forward orientation should be orthagonal to the
        up orientation.''')

    def _set_up_orientation(self, orientation):
        raise NotImplementedError('abstract')

    up_orientation = property(lambda self: self._up_orientation,
                              lambda self, o: self._set_up_orientation(o),
                              doc='''A vector giving the "up" orientation
        of the listener.

        The orientation is given as a tuple of floats (x, y, z), and has
        no unit.  The up orientation should be orthagonal to the
        forward orientation.''')

    def _set_doppler_factor(self, factor):
        raise NotImplementedError('abstract')

    doppler_factor = property(lambda self: self._doppler_factor,
                              lambda self, f: self._set_doppler_factor(f),
                              doc='''The emphasis to apply to the doppler
        effect for sounds that move relative to the listener.

        The default value is 1.0, which results in a physically-based
        calculation.  The effect can be enhanced by using a higher factor,
        or subdued using a fractional factor (negative factors are
        ignored).''')

    def _set_speed_of_sound(self, speed_of_sound):
        raise NotImplementedError('abstract')

    speed_of_sound = property(lambda self: self._speed_of_sound,
                              lambda self, s: self._set_speed_of_sound(s),
                              doc='''The speed of sound, in units per second.

        The default value is 343.3, a typical result at sea-level on a mild
        day, using meters as the distance unit.

        The speed of sound only affects the calculation of pitch shift to 
        apply due to doppler effects; in particular, no propogation delay
        or relative phase adjustment is applied (in current implementations
        of audio devices).
        ''')

if sys.platform == 'linux2':
    from pyglet.media import gst_openal
    device = gst_openal
elif sys.platform == 'darwin':
    from pyglet.media import quicktime
    device = quicktime
elif sys.platform in ('win32', 'cygwin'):
    from pyglet.media import directshow
    device = directshow
else:
    raise ImportError('pyglet.media not yet supported on %s' % sys.platform)

init = device.init
load = device.load
dispatch_events = device.dispatch_events
listener = device.listener
cleanup = device.cleanup

init()
