"""This file is currently hand-coded; I don't have a MESA header file to build
off.
"""

from ctypes import c_int
from pyglet.gl.lib import link_GLX as _link_function

glXSwapIntervalMESA = _link_function('glXSwapIntervalMESA', c_int, [c_int], 'MESA_swap_control')
