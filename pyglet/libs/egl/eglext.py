from ctypes import *
from pyglet.libs.egl import egl
from pyglet.libs.egl.lib import link_EGL as _link_function
from pyglet.graphics.api.gl.lib import MissingFunctionException, missing_function


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


EGL_KHR_image = 1
EGL_NATIVE_PIXMAP_KHR = 12464
EGL_IMAGE_PRESERVED_KHR = 12498
EGLImageKHR = POINTER(None)

eglCreateImageKHR = _link_function(
    'eglCreateImageKHR',
    EGLImageKHR,
    [egl.EGLDisplay, egl.EGLContext, egl.EGLenum, egl.EGLClientBuffer, POINTER(egl.EGLint)],
    requires='EGL_KHR_image')

eglDestroyImageKHR = _link_function(
    'eglDestroyImageKHR',
    egl.EGLBoolean,
    [egl.EGLDisplay, EGLImageKHR],
    requires='EGL_KHR_image')

__all__ = ['EGL_PLATFORM_DEVICE_EXT', 'EGL_PLATFORM_GBM_MESA', 'EGL_PLATFORM_WAYLAND',
           'EGLDeviceEXT', 'eglGetPlatformDisplayEXT', 'eglCreatePlatformWindowSurfaceEXT',
           'eglQueryDevicesEXT',
           'EGL_KHR_image', 'EGL_NATIVE_PIXMAP_KHR', 'EGL_IMAGE_PRESERVED_KHR',
           'EGLImageKHR', 'eglCreateImageKHR', 'eglDestroyImageKHR',
           'MissingFunctionException', 'missing_function']
