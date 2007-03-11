#!/usr/bin/env python

# Play an audio file with QuickTime.  Tested ok with MP3, WAV.
# Notes
#   - Easy enough to read from a stream instead of filename, use DataRef
#     interface
#   - Not sure about playing same sound multiple times without reloading.
#   - No direct support for OpenAL, could be tricky/impossible extracting
#     samples from QT.. we'll see.

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes
import sys
import time

from pyglet.window.carbon import _create_cfstring, _oscheck
from pyglet.window.carbon import carbon
from pyglet.window.carbon import quicktime

quicktime.EnterMovies()

filename = sys.argv[1]
filename = _create_cfstring(filename)
data_ref = ctypes.c_void_p()
data_ref_type = ctypes.c_ulong()
result = quicktime.QTNewDataReferenceFromFullPathCFString(filename,
    -1, 0, ctypes.byref(data_ref), ctypes.byref(data_ref_type))
_oscheck(result)

sound = ctypes.c_void_p()
fileid = ctypes.c_short(0)
quicktime.NewMovieFromDataRef.argtypes = (
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.c_short,
    ctypes.POINTER(ctypes.c_short),
    ctypes.c_void_p,
    ctypes.c_ulong)
    
newMovieActive = 1

result = quicktime.NewMovieFromDataRef(ctypes.byref(sound), 
    newMovieActive, ctypes.byref(fileid), data_ref, data_ref_type)
_oscheck(result)

carbon.CFRelease(filename)


quicktime.StartMovie(sound)

try:
    while not quicktime.IsMovieDone(sound):
        quicktime.MoviesTask(0)
        time.sleep(0.1)
except KeyboardInterrupt:
    pass

quicktime.StopMovie(sound)

quicktime.ExitMovies()
