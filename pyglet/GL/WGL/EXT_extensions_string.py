'''XXX hand-coded from

http://oss.sgi.com/projects/ogl-sample/registry/EXT/wgl_extensions_string.txt
'''

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
wglGetExtensionsStringEXT = _get_function('wglGetExtensionsStringEXT', [], _ctypes.c_char_p)
