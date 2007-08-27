#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.media import BasePlayer, ManagedSoundPlayerMixIn, Listener
from pyglet.media import MediaException

from pyglet.media.drivers.alsa import asound as lib

class ALSAPlayer(BasePlayer):
    pass

class ALSAManagedSoundPlayer(ALSAPlayer, ManagedSoundPlayerMixIn):
    pass

class ALSAListener(Listener):
    pass

def driver_init():
    print lib.snd_asoundlib_version()

driver_listener = ALSAListener()
DriverPlayer = ALSAPlayer
DriverManagedSoundPlayer = ALSAManagedSoundPlayer
