
"""OML_resample
http://oss.sgi.com/projects/ogl-sample/registry/OML/resample.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_PACK_RESAMPLE_OML = 0x8984
GL_UNPACK_RESAMPLE_OML = 0x8985
GL_RESAMPLE_REPLICATE_OML = 0x8986
GL_RESAMPLE_ZERO_FILL_OML = 0x8987
GL_RESAMPLE_AVERAGE_OML = 0x8988
GL_RESAMPLE_DECIMATE_OML = 0x8989
