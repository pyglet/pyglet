"""Bindings for optional ARGB and themed X11 cursors."""
from __future__ import annotations

from ctypes import POINTER, Structure, c_char_p, c_int, c_uint, c_ulong
from typing import TYPE_CHECKING

import pyglet.lib

from .xlib import Display

if TYPE_CHECKING:
    from ctypes import _Pointer


_lib = pyglet.lib.load_library('Xcursor')


class XcursorImage(Structure):
    _fields_ = [
        ('version', c_uint),
        ('size', c_uint),
        ('width', c_uint),
        ('height', c_uint),
        ('xhot', c_uint),
        ('yhot', c_uint),
        ('delay', c_uint),
        ('pixels', POINTER(c_uint)),
    ]


XcursorSupportsARGB = _lib.XcursorSupportsARGB
XcursorSupportsARGB.argtypes = [POINTER(Display)]
XcursorSupportsARGB.restype = c_int

XcursorImageCreate = _lib.XcursorImageCreate
XcursorImageCreate.argtypes = [c_int, c_int]
XcursorImageCreate.restype = POINTER(XcursorImage)

XcursorImageDestroy = _lib.XcursorImageDestroy
XcursorImageDestroy.argtypes = [POINTER(XcursorImage)]
XcursorImageDestroy.restype = None

XcursorImageLoadCursor = _lib.XcursorImageLoadCursor
XcursorImageLoadCursor.argtypes = [POINTER(Display), POINTER(XcursorImage)]
XcursorImageLoadCursor.restype = c_ulong

XcursorLibraryLoadCursor = _lib.XcursorLibraryLoadCursor
XcursorLibraryLoadCursor.argtypes = [POINTER(Display), c_char_p]
XcursorLibraryLoadCursor.restype = c_ulong


def create_argb_cursor(display: _Pointer[Display], width: int, height: int,
                       rgba: bytes, hot_x: int, hot_y: int) -> int:
    """Create a cursor from top-down RGBA pixels, or return zero on allocation failure."""
    image = XcursorImageCreate(width, height)
    if not image:
        return 0

    try:
        image.contents.xhot = hot_x
        image.contents.yhot = hot_y
        # Xcursor uses native 32-bit ARGB values with premultiplied color channels.
        for index in range(width * height):
            red, green, blue, alpha = rgba[index * 4:index * 4 + 4]
            red = (red * alpha + 127) // 255
            green = (green * alpha + 127) // 255
            blue = (blue * alpha + 127) // 255
            image.contents.pixels[index] = (alpha << 24) | (red << 16) | (green << 8) | blue
        return XcursorImageLoadCursor(display, image)
    finally:
        XcursorImageDestroy(image)
