from __future__ import annotations
from ctypes import *
from typing import Sequence, Callable, NoReturn

import pyglet

__all__ = ['link_EGL']

from pyglet.libs.egl.egl_lib import EGLenum, EGLDisplay, EGLConfig, EGLSurface, EGLBoolean, EGLint, EGLAttrib

egl_lib = pyglet.lib.load_library('EGL')

# Look for eglGetProcAddress
eglGetProcAddress = getattr(egl_lib, 'eglGetProcAddress')
eglGetProcAddress.restype = POINTER(CFUNCTYPE(None))
eglGetProcAddress.argtypes = [POINTER(c_ubyte)]

class MissingFunctionException(Exception):  # noqa: N818
    def __init__(self, name: str, requires: str | None = None, suggestions: Sequence[str] | None=None) -> None:
        msg = f'{name} is not exported by the available OpenGL driver.'
        if requires:
            msg += f'  {requires} is required for this functionality.'
        if suggestions:
            msg += '  Consider alternative(s) {}.'.format(', '.join(suggestions))
        Exception.__init__(self, msg)

def missing_function(name: str, requires: str | None =None, suggestions: Sequence[str] | None=None) -> Callable:
    def MissingFunction(*_args, **_kwargs) -> NoReturn:  # noqa: ANN002, ANN003, N802
        raise MissingFunctionException(name, requires, suggestions)

    return MissingFunction

def link_EGL(name, restype, argtypes, requires=None, suggestions=None):
    try:
        func = getattr(egl_lib, name)
        func.restype = restype
        func.argtypes = argtypes
        return func
    except AttributeError:
        bname = cast(pointer(create_string_buffer(pyglet.util.asbytes(name))), POINTER(c_ubyte))
        addr = eglGetProcAddress(bname)
        if addr:
            ftype = CFUNCTYPE(*((restype,) + tuple(argtypes)))
            func = cast(addr, ftype)
            return func

    return missing_function(name, requires, suggestions)

EGL_PLATFORM_GBM_MESA = 12759
EGL_PLATFORM_DEVICE_EXT = 12607
EGLDeviceEXT = POINTER(None)

eglGetPlatformDisplayEXT = link_EGL('eglGetPlatformDisplayEXT', EGLDisplay, [EGLenum, POINTER(None), POINTER(
    EGLint)], None)
eglCreatePlatformWindowSurfaceEXT = link_EGL('eglCreatePlatformWindowSurfaceEXT', EGLSurface, [EGLDisplay, EGLConfig, POINTER(None), POINTER(
    EGLAttrib)], None)
eglQueryDevicesEXT = link_EGL('eglQueryDevicesEXT', EGLBoolean, [EGLint, POINTER(EGLDeviceEXT), POINTER(
    EGLint)], None)


__all__ = ['EGL_PLATFORM_DEVICE_EXT', 'EGL_PLATFORM_GBM_MESA',
           'EGLDeviceEXT', 'eglGetPlatformDisplayEXT', 'eglCreatePlatformWindowSurfaceEXT',
           'eglQueryDevicesEXT']
