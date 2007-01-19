
"""OML_swap_method
http://oss.sgi.com/projects/ogl-sample/registry/OML/glx_swap_method.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GLX_SWAP_METHOD_OML = 0x8060
GLX_SWAP_EXCHANGE_OML = 0x8061
GLX_SWAP_COPY_OML = 0x8062
GLX_SWAP_UNDEFINED_OML = 0x8063
