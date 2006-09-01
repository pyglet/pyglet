
"""HP_image_transform
http://oss.sgi.com/projects/ogl-sample/registry/HP/image_transform.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
glGetImageTransformParameterfvHP = _get_function('glGetImageTransformParameterfvHP', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glGetImageTransformParameterivHP = _get_function('glGetImageTransformParameterivHP', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glImageTransformParameterfHP = _get_function('glImageTransformParameterfHP', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_float], None)
glImageTransformParameterfvHP = _get_function('glImageTransformParameterfvHP', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
glImageTransformParameteriHP = _get_function('glImageTransformParameteriHP', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int], None)
glImageTransformParameterivHP = _get_function('glImageTransformParameterivHP', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
