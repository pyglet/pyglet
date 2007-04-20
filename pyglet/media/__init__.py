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
    _position = (0, 0, 0)
    
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

                      The value is in the range 0.0 (silent) to 1.0 (nominal).
                      Negative values are not permitted, while values higher
                      than 1.0 may result in clipping.''')

    def _set_position(self, position):
        raise NotImplementedError('abstract')

    position = property(lambda self: self._position,
                        lambda self, position: self._set_position(position),
                        doc='''The position of the sound in 3D space.

                        The position is given as a tuple of floats (x, y, z).
                        The unit defaults to meters, but can be modified
                        with the listener properties.''')

    def dispatch_events(self):
        '''Dispatch any pending events and perform regular heartbeat functions
        to maintain audio playback.

        This method is called automatically by `pyglet.media.dispatch_events`,
        there is no need to call this from an application.
        '''
        pass

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
cleanup = device.cleanup

init()
