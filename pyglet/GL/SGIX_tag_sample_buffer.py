
"""SGIX_tag_sample_buffer
http://oss.sgi.com/projects/ogl-sample/registry/SGIX/tag_sample_buffer.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glTagSampleBufferSGIX = _get_function('glTagSampleBufferSGIX', [], None)
