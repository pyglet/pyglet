from __future__ import annotations

from ctypes import POINTER, c_int, c_void_p

import pyglet

_lib = pyglet.lib.load_library('wayland-egl')

wl_egl_window_ptr = c_void_p
wl_surface_ptr = c_void_p


wl_egl_window_create = _lib.wl_egl_window_create
wl_egl_window_create.restype = wl_egl_window_ptr
wl_egl_window_create.argtypes = [wl_surface_ptr, c_int, c_int]


wl_egl_window_destroy = _lib.wl_egl_window_destroy
wl_egl_window_destroy.restype = None
wl_egl_window_destroy.argtypes = [wl_egl_window_ptr]


wl_egl_window_resize = _lib.wl_egl_window_resize
wl_egl_window_resize.restype = None
wl_egl_window_resize.argtypes = [wl_egl_window_ptr, c_int, c_int, c_int, c_int]


wl_egl_window_get_attached_size = _lib.wl_egl_window_get_attached_size
wl_egl_window_get_attached_size.restype = None
wl_egl_window_get_attached_size.argtypes = [wl_egl_window_ptr, POINTER(c_int), POINTER(c_int)]


__all__ = [
    'wl_egl_window_create',
    'wl_egl_window_destroy',
    'wl_egl_window_get_attached_size',
    'wl_egl_window_resize',
]
