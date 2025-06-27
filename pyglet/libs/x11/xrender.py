from __future__ import annotations

import warnings
from ctypes import Structure, c_ushort, c_ulong, c_int, c_void_p, POINTER
import pyglet.lib
from pyglet.libs.x11.xlib import Visual

lib = None
try:
    lib = pyglet.lib.load_library("Xrender")
except ImportError:
    if pyglet.options.debug_lib:
        warnings.warn("XRender could not be loaded.")


class XRenderDirectFormat(Structure):
    _fields_ = [
        ('red', c_ushort),
        ('redMask', c_ushort),
        ('green', c_ushort),
        ('greenMask', c_ushort),
        ('blue', c_ushort),
        ('blueMask', c_ushort),
        ('alpha', c_ushort),
        ('alphaMask', c_ushort),
    ]

class XRenderPictFormat(Structure):
    _fields_ = [
        ('id', c_ulong),
        ('type', c_int),
        ('depth', c_int),
        ('direct', XRenderDirectFormat),
        ('colormap', c_ulong),
    ]

# XRenderFindVisualFormat(Display *dpy, Visual *visual)
try:
    XRenderFindVisualFormat = lib.XRenderFindVisualFormat
    XRenderFindVisualFormat.argtypes = [c_void_p, POINTER(Visual)]
    XRenderFindVisualFormat.restype = POINTER(XRenderPictFormat)
except ValueError:
    XRenderFindVisualFormat = None
