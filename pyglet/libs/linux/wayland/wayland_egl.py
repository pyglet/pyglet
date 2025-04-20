from ctypes import Structure, POINTER, c_int

import pyglet

_lib = pyglet.lib.load_library('wayland-egl')


class struct_wl_egl_window(Structure):
    _fields_ = [('value', c_int)]


class struct_wl_surface(Structure):
    _fields_ = [('value', c_int)]


wl_egl_window_create = _lib.wl_egl_window_create
wl_egl_window_create.restype = POINTER(struct_wl_egl_window)
wl_egl_window_create.argtypes = [POINTER(struct_wl_surface), c_int, c_int]


wl_egl_window_destroy = _lib.wl_egl_window_destroy
wl_egl_window_destroy.restype = None
wl_egl_window_destroy.argtypes = [POINTER(struct_wl_egl_window)]


wl_egl_window_resize = _lib.wl_egl_window_resize
wl_egl_window_resize.restype = None
wl_egl_window_resize.argtypes = [POINTER(struct_wl_egl_window), c_int, c_int, c_int, c_int]


wl_egl_window_get_attached_size = _lib.wl_egl_window_get_attached_size
wl_egl_window_get_attached_size.restype = None
wl_egl_window_get_attached_size.argtypes = [POINTER(struct_wl_egl_window), POINTER(c_int), POINTER(c_int)]


__all__ = ['wl_egl_window_create', 'wl_egl_window_destroy', 'wl_egl_window_resize', 'wl_egl_window_get_attached_size',
           'struct_wl_surface', 'struct_wl_egl_window']
