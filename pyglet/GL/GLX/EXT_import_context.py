
"""EXT_import_context
http://oss.sgi.com/projects/ogl-sample/registry/EXT/import_context.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GLX_SHARE_CONTEXT_EXT = 0x800A
GLX_VISUAL_ID_EXT = 0x800B
GLX_SCREEN_EXT = 0x800C
GLXContextID = _ctypes.c_ulong
glXFreeContextEXT = _get_function('glXFreeContextEXT', [_ctypes.POINTER(Display), GLXContext], None)
glXGetContextIDEXT = _get_function('glXGetContextIDEXT', [GLXContext], GLXContextID)
glXImportContextEXT = _get_function('glXImportContextEXT', [_ctypes.POINTER(Display), GLXContextID], GLXContext)
glXQueryContextInfoEXT = _get_function('glXQueryContextInfoEXT', [_ctypes.POINTER(Display), GLXContext, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_int)], _ctypes.c_int)
