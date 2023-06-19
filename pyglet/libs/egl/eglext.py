from ctypes import *
from pyglet.libs.egl import egl
from pyglet.libs.egl.lib import link_EGL as _link_function


EGL_PLATFORM_GBM_MESA = 12759
EGL_PLATFORM_DEVICE_EXT = 12607
EGLDeviceEXT = POINTER(None)

eglGetPlatformDisplayEXT = _link_function('eglGetPlatformDisplayEXT', egl.EGLDisplay, [egl.EGLenum, POINTER(None), POINTER(egl.EGLint)], None)
eglCreatePlatformWindowSurfaceEXT = _link_function('eglCreatePlatformWindowSurfaceEXT', egl.EGLSurface, [egl.EGLDisplay, egl.EGLConfig, POINTER(None), POINTER(egl.EGLAttrib)], None)
eglQueryDevicesEXT = _link_function('eglQueryDevicesEXT', egl.EGLBoolean, [egl.EGLint, POINTER(EGLDeviceEXT), POINTER(egl.EGLint)], None)


__all__ = ['EGL_PLATFORM_DEVICE_EXT', 'EGL_PLATFORM_GBM_MESA',
           'EGLDeviceEXT', 'eglGetPlatformDisplayEXT', 'eglCreatePlatformWindowSurfaceEXT',
           'eglQueryDevicesEXT']
