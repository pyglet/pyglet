#!/usr/bin/python
# $Id:$

import ctypes

from pyglet.media.drivers.directsound import lib_dsound as lib

dsound = None
def driver_init():
    global ds
    ctypes.oledll.ole32.CoInitialize(None)
    ds = IDirectSound8()
    lib.DirectSoundCreate8(None, ctypes.byref(dsound), None)
