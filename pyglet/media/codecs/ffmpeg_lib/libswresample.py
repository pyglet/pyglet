"""Wrapper for include/libswresample/swresample.h
"""
from ctypes import c_int, c_int64, c_char_p, c_double
from ctypes import c_uint8
from ctypes import c_void_p, POINTER, Structure

import pyglet.lib
from pyglet.util import debug_print
from . import compat
from .libavutil import AVChannelLayout, AVSampleFormat

_debug = debug_print('debug_media')

swresample = pyglet.lib.load_library(
    'swresample',
    win32=('swresample-5', 'swresample-4', 'swresample-3'),
    darwin=('swresample.5', 'swresample.4', 'swresample.3')
)

swresample.swresample_version.restype = c_int

swresample_version = swresample.swresample_version() >> 16

compat.set_version('swresample', swresample_version)

SWR_CH_MAX = 32

class SwrContext(Structure):
    pass


if swresample_version < 5:
    swresample.swr_alloc_set_opts.restype = POINTER(SwrContext)
    swresample.swr_alloc_set_opts.argtypes = [POINTER(SwrContext),
                                              c_int64, c_int, c_int, c_int64,
                                              c_int, c_int, c_int, c_void_p]
else:
    swresample.swr_alloc.restype = POINTER(SwrContext)
    swresample.swr_alloc.argtypes = []

    swresample.swr_alloc_set_opts2.restype = c_int
    swresample.swr_alloc_set_opts2.argtypes = [POINTER(POINTER(SwrContext)),
                                              POINTER(AVChannelLayout), AVSampleFormat, c_int,
                                              POINTER(AVChannelLayout), AVSampleFormat, c_int,
                                              c_int, c_void_p]


swresample.swr_init.restype = c_int
swresample.swr_init.argtypes = [POINTER(SwrContext)]
swresample.swr_free.argtypes = [POINTER(POINTER(SwrContext))]
swresample.swr_convert.restype = c_int
swresample.swr_convert.argtypes = [POINTER(SwrContext),
                                   POINTER(c_uint8) * SWR_CH_MAX,
                                   c_int,
                                   POINTER(POINTER(c_uint8)),
                                   c_int]
swresample.swr_set_compensation.restype = c_int
swresample.swr_set_compensation.argtypes = [POINTER(SwrContext),
                                            c_int, c_int]
swresample.swr_get_out_samples.restype = c_int
swresample.swr_get_out_samples.argtypes = [POINTER(SwrContext), c_int]

__all__ = [
    'swresample',
    'SWR_CH_MAX',
    'SwrContext',
    'swresample_version',
]
