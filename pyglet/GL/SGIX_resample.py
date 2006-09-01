
"""SGIX_resample
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/resample.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_PACK_RESAMPLE_SGIX = 0x842E
GL_UNPACK_RESAMPLE_SGIX = 0x842F
GL_RESAMPLE_DECIMATE_SGIX = 0x8430
GL_RESAMPLE_REPLICATE_SGIX = 0x8433
GL_RESAMPLE_ZERO_FILL_SGIX = 0x8434
