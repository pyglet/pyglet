# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2023 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------
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
