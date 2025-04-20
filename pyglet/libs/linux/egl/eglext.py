from ctypes import *
from pyglet.libs.linux.egl import egl
from pyglet.libs.linux.egl.lib import link_EGL as _link_function


EGL_PLATFORM_DEVICE_EXT = 0X313F
EGL_PLATFORM_GBM_MESA = 0X31D7
EGL_PLATFORM_WAYLAND = 0x31D8

EGLDeviceEXT = POINTER(None)

eglGetPlatformDisplayEXT = _link_function('eglGetPlatformDisplayEXT', egl.EGLDisplay, [egl.EGLenum, POINTER(None), POINTER(
    egl.EGLint)], None)
eglCreatePlatformWindowSurfaceEXT = _link_function('eglCreatePlatformWindowSurfaceEXT', egl.EGLSurface, [egl.EGLDisplay, egl.EGLConfig, POINTER(None), POINTER(
    egl.EGLAttrib)], None)
eglQueryDevicesEXT = _link_function('eglQueryDevicesEXT', egl.EGLBoolean, [egl.EGLint, POINTER(EGLDeviceEXT), POINTER(
    egl.EGLint)], None)


__all__ = ['EGL_PLATFORM_DEVICE_EXT', 'EGL_PLATFORM_GBM_MESA', 'EGL_PLATFORM_WAYLAND',
           'EGLDeviceEXT', 'eglGetPlatformDisplayEXT', 'eglCreatePlatformWindowSurfaceEXT',
           'eglQueryDevicesEXT']
