"""Wrapper for include/libswscale/swscale.h
"""
from ctypes import POINTER, Structure
from ctypes import c_int
from ctypes import c_uint8, c_double

import pyglet.lib
from pyglet.util import debug_print
from . import compat

_debug = debug_print('debug_media')


swscale = pyglet.lib.load_library(
    'swscale',
    win32=('swscale-9', 'swscale-8', 'swscale-7', 'swscale-6', 'swscale-5'),
    darwin=('swscale.9', 'swscale.8', 'swscale.7', 'swscale.6', 'swscale.5')
)

swscale.swscale_version.restype = c_int

compat.set_version('swscale', swscale.swscale_version() >> 16)


SWS_FAST_BILINEAR = 1


class SwsContext(Structure):
    pass


class SwsFilter(Structure):
    pass


swscale.sws_getCachedContext.restype = POINTER(SwsContext)
swscale.sws_getCachedContext.argtypes = [POINTER(SwsContext),
                                         c_int, c_int, c_int, c_int,
                                         c_int, c_int, c_int,
                                         POINTER(SwsFilter), POINTER(SwsFilter),
                                         POINTER(c_double)]
swscale.sws_freeContext.argtypes = [POINTER(SwsContext)]
swscale.sws_scale.restype = c_int
swscale.sws_scale.argtypes = [POINTER(SwsContext),
                              POINTER(POINTER(c_uint8)),
                              POINTER(c_int),
                              c_int, c_int,
                              POINTER(POINTER(c_uint8)),
                              POINTER(c_int)]

__all__ = [
    'swscale',
    'SWS_FAST_BILINEAR',
    'SwsContext',
    'SwsFilter'
]
