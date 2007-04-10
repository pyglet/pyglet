#!/usr/bin/python
# $Id$

'''Media playback interface.

'''

import sys

class Medium(object):
    duration = 0
    
    # Audio
    channels = 0
    sample_rate = 0

    def get_sound(self):
        raise NotImplementedError('abstract')

    def play(self):
        sound = self.get_sound()
        sound.play()
        return sound

class Sound(object):
    def play(self):
        raise NotImplementedError('abstract')

    def dispatch_events(self):
        pass

if sys.platform == 'linux2':
    from pyglet.media import gst_openal
    device = gst_openal
elif sys.platform == 'darwin':
    from pyglet.media import quicktime
    device = quicktime
else:
    raise ImportError('pyglet.media not yet supported on %s' % sys.platform)

load = device.load
dispatch_events = device.dispatch_events
