'''Wrapper for /usr/include/EGL/egl

Generated with:
tools/wraptypes/wrap.py -o egl.py /usr/include/EGL/egl.h

Do not modify this file.
'''

__docformat__ =  'restructuredtext'
__version__ = '$Id$'

import ctypes
from ctypes import *

import pyglet.lib

_lib = pyglet.lib.load_library('EGL')

_int_types = (c_int16, c_int32)
if hasattr(ctypes, 'c_int64'):
    # Some builds of ctypes apparently do not have c_int64
    # defined; it's a pretty good bet that these builds do not
    # have 64-bit pointers.
    _int_types += (ctypes.c_int64,)
for t in _int_types:
    if sizeof(t) == sizeof(c_size_t):
        c_ptrdiff_t = t

class c_void(Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', c_int)]



__egl_h_ = 1 	# /usr/include/EGL/egl.h:2
EGL_VERSION_1_0 = 1 	# /usr/include/EGL/egl.h:53
EGLBoolean = c_uint 	# /usr/include/EGL/egl.h:54
EGLDisplay = POINTER(None) 	# /usr/include/EGL/egl.h:55
EGLConfig = POINTER(None) 	# /usr/include/EGL/egl.h:58
EGLSurface = POINTER(None) 	# /usr/include/EGL/egl.h:59
EGLContext = POINTER(None) 	# /usr/include/EGL/egl.h:60
__eglMustCastToProperFunctionPointerType = CFUNCTYPE(None) 	# /usr/include/EGL/egl.h:61
EGL_ALPHA_SIZE = 12321 	# /usr/include/EGL/egl.h:62
EGL_BAD_ACCESS = 12290 	# /usr/include/EGL/egl.h:63
EGL_BAD_ALLOC = 12291 	# /usr/include/EGL/egl.h:64
EGL_BAD_ATTRIBUTE = 12292 	# /usr/include/EGL/egl.h:65
EGL_BAD_CONFIG = 12293 	# /usr/include/EGL/egl.h:66
EGL_BAD_CONTEXT = 12294 	# /usr/include/EGL/egl.h:67
EGL_BAD_CURRENT_SURFACE = 12295 	# /usr/include/EGL/egl.h:68
EGL_BAD_DISPLAY = 12296 	# /usr/include/EGL/egl.h:69
EGL_BAD_MATCH = 12297 	# /usr/include/EGL/egl.h:70
EGL_BAD_NATIVE_PIXMAP = 12298 	# /usr/include/EGL/egl.h:71
EGL_BAD_NATIVE_WINDOW = 12299 	# /usr/include/EGL/egl.h:72
EGL_BAD_PARAMETER = 12300 	# /usr/include/EGL/egl.h:73
EGL_BAD_SURFACE = 12301 	# /usr/include/EGL/egl.h:74
EGL_BLUE_SIZE = 12322 	# /usr/include/EGL/egl.h:75
EGL_BUFFER_SIZE = 12320 	# /usr/include/EGL/egl.h:76
EGL_CONFIG_CAVEAT = 12327 	# /usr/include/EGL/egl.h:77
EGL_CONFIG_ID = 12328 	# /usr/include/EGL/egl.h:78
EGL_CORE_NATIVE_ENGINE = 12379 	# /usr/include/EGL/egl.h:79
EGL_DEPTH_SIZE = 12325 	# /usr/include/EGL/egl.h:80
EGL_DRAW = 12377 	# /usr/include/EGL/egl.h:82
EGL_EXTENSIONS = 12373 	# /usr/include/EGL/egl.h:83
EGL_FALSE = 0 	# /usr/include/EGL/egl.h:84
EGL_GREEN_SIZE = 12323 	# /usr/include/EGL/egl.h:85
EGL_HEIGHT = 12374 	# /usr/include/EGL/egl.h:86
EGL_LARGEST_PBUFFER = 12376 	# /usr/include/EGL/egl.h:87
EGL_LEVEL = 12329 	# /usr/include/EGL/egl.h:88
EGL_MAX_PBUFFER_HEIGHT = 12330 	# /usr/include/EGL/egl.h:89
EGL_MAX_PBUFFER_PIXELS = 12331 	# /usr/include/EGL/egl.h:90
EGL_MAX_PBUFFER_WIDTH = 12332 	# /usr/include/EGL/egl.h:91
EGL_NATIVE_RENDERABLE = 12333 	# /usr/include/EGL/egl.h:92
EGL_NATIVE_VISUAL_ID = 12334 	# /usr/include/EGL/egl.h:93
EGL_NATIVE_VISUAL_TYPE = 12335 	# /usr/include/EGL/egl.h:94
EGL_NONE = 12344 	# /usr/include/EGL/egl.h:95
EGL_NON_CONFORMANT_CONFIG = 12369 	# /usr/include/EGL/egl.h:96
EGL_NOT_INITIALIZED = 12289 	# /usr/include/EGL/egl.h:97
EGL_PBUFFER_BIT = 1 	# /usr/include/EGL/egl.h:101
EGL_PIXMAP_BIT = 2 	# /usr/include/EGL/egl.h:102
EGL_READ = 12378 	# /usr/include/EGL/egl.h:103
EGL_RED_SIZE = 12324 	# /usr/include/EGL/egl.h:104
EGL_SAMPLES = 12337 	# /usr/include/EGL/egl.h:105
EGL_SAMPLE_BUFFERS = 12338 	# /usr/include/EGL/egl.h:106
EGL_SLOW_CONFIG = 12368 	# /usr/include/EGL/egl.h:107
EGL_STENCIL_SIZE = 12326 	# /usr/include/EGL/egl.h:108
EGL_SUCCESS = 12288 	# /usr/include/EGL/egl.h:109
EGL_SURFACE_TYPE = 12339 	# /usr/include/EGL/egl.h:110
EGL_TRANSPARENT_BLUE_VALUE = 12341 	# /usr/include/EGL/egl.h:111
EGL_TRANSPARENT_GREEN_VALUE = 12342 	# /usr/include/EGL/egl.h:112
EGL_TRANSPARENT_RED_VALUE = 12343 	# /usr/include/EGL/egl.h:113
EGL_TRANSPARENT_RGB = 12370 	# /usr/include/EGL/egl.h:114
EGL_TRANSPARENT_TYPE = 12340 	# /usr/include/EGL/egl.h:115
EGL_TRUE = 1 	# /usr/include/EGL/egl.h:116
EGL_VENDOR = 12371 	# /usr/include/EGL/egl.h:117
EGL_VERSION = 12372 	# /usr/include/EGL/egl.h:118
EGL_WIDTH = 12375 	# /usr/include/EGL/egl.h:119
EGL_WINDOW_BIT = 4 	# /usr/include/EGL/egl.h:120
khronos_int32_t = c_int32 	# /usr/include/KHR/khrplatform.h:146
EGLint = khronos_int32_t 	# /usr/include/EGL/eglplatform.h:158
# /usr/include/EGL/egl.h:121
eglChooseConfig = _lib.eglChooseConfig
eglChooseConfig.restype = EGLBoolean
eglChooseConfig.argtypes = [EGLDisplay, POINTER(EGLint), POINTER(EGLConfig), EGLint, POINTER(EGLint)]

XID = c_ulong 	# /usr/include/X11/X.h:66
Pixmap = XID 	# /usr/include/X11/X.h:102
EGLNativePixmapType = Pixmap 	# /usr/include/EGL/eglplatform.h:128
# /usr/include/EGL/egl.h:122
eglCopyBuffers = _lib.eglCopyBuffers
eglCopyBuffers.restype = EGLBoolean
eglCopyBuffers.argtypes = [EGLDisplay, EGLSurface, EGLNativePixmapType]

# /usr/include/EGL/egl.h:123
eglCreateContext = _lib.eglCreateContext
eglCreateContext.restype = EGLContext
eglCreateContext.argtypes = [EGLDisplay, EGLConfig, EGLContext, POINTER(EGLint)]

# /usr/include/EGL/egl.h:124
eglCreatePbufferSurface = _lib.eglCreatePbufferSurface
eglCreatePbufferSurface.restype = EGLSurface
eglCreatePbufferSurface.argtypes = [EGLDisplay, EGLConfig, POINTER(EGLint)]

# /usr/include/EGL/egl.h:125
eglCreatePixmapSurface = _lib.eglCreatePixmapSurface
eglCreatePixmapSurface.restype = EGLSurface
eglCreatePixmapSurface.argtypes = [EGLDisplay, EGLConfig, EGLNativePixmapType, POINTER(EGLint)]

Window = XID 	# /usr/include/X11/X.h:96
EGLNativeWindowType = Window 	# /usr/include/EGL/eglplatform.h:129
# /usr/include/EGL/egl.h:126
eglCreateWindowSurface = _lib.eglCreateWindowSurface
eglCreateWindowSurface.restype = EGLSurface
eglCreateWindowSurface.argtypes = [EGLDisplay, EGLConfig, EGLNativeWindowType, POINTER(EGLint)]

# /usr/include/EGL/egl.h:127
eglDestroyContext = _lib.eglDestroyContext
eglDestroyContext.restype = EGLBoolean
eglDestroyContext.argtypes = [EGLDisplay, EGLContext]

# /usr/include/EGL/egl.h:128
eglDestroySurface = _lib.eglDestroySurface
eglDestroySurface.restype = EGLBoolean
eglDestroySurface.argtypes = [EGLDisplay, EGLSurface]

# /usr/include/EGL/egl.h:129
eglGetConfigAttrib = _lib.eglGetConfigAttrib
eglGetConfigAttrib.restype = EGLBoolean
eglGetConfigAttrib.argtypes = [EGLDisplay, EGLConfig, EGLint, POINTER(EGLint)]

# /usr/include/EGL/egl.h:130
eglGetConfigs = _lib.eglGetConfigs
eglGetConfigs.restype = EGLBoolean
eglGetConfigs.argtypes = [EGLDisplay, POINTER(EGLConfig), EGLint, POINTER(EGLint)]

# /usr/include/EGL/egl.h:131
eglGetCurrentDisplay = _lib.eglGetCurrentDisplay
eglGetCurrentDisplay.restype = EGLDisplay
eglGetCurrentDisplay.argtypes = []

# /usr/include/EGL/egl.h:132
eglGetCurrentSurface = _lib.eglGetCurrentSurface
eglGetCurrentSurface.restype = EGLSurface
eglGetCurrentSurface.argtypes = [EGLint]

class struct__XDisplay(Structure):
    __slots__ = [
    ]
struct__XDisplay._fields_ = [
    ('_opaque_struct', c_int)
]

class struct__XDisplay(Structure):
    __slots__ = [
    ]
struct__XDisplay._fields_ = [
    ('_opaque_struct', c_int)
]

Display = struct__XDisplay 	# /usr/include/X11/Xlib.h:487
EGLNativeDisplayType = POINTER(Display) 	# /usr/include/EGL/eglplatform.h:127
# /usr/include/EGL/egl.h:133
eglGetDisplay = _lib.eglGetDisplay
eglGetDisplay.restype = EGLDisplay
eglGetDisplay.argtypes = [EGLNativeDisplayType]

# /usr/include/EGL/egl.h:134
eglGetError = _lib.eglGetError
eglGetError.restype = EGLint
eglGetError.argtypes = []

# /usr/include/EGL/egl.h:135
eglGetProcAddress = _lib.eglGetProcAddress
eglGetProcAddress.restype = __eglMustCastToProperFunctionPointerType
eglGetProcAddress.argtypes = [c_char_p]

# /usr/include/EGL/egl.h:136
eglInitialize = _lib.eglInitialize
eglInitialize.restype = EGLBoolean
eglInitialize.argtypes = [EGLDisplay, POINTER(EGLint), POINTER(EGLint)]

# /usr/include/EGL/egl.h:137
eglMakeCurrent = _lib.eglMakeCurrent
eglMakeCurrent.restype = EGLBoolean
eglMakeCurrent.argtypes = [EGLDisplay, EGLSurface, EGLSurface, EGLContext]

# /usr/include/EGL/egl.h:138
eglQueryContext = _lib.eglQueryContext
eglQueryContext.restype = EGLBoolean
eglQueryContext.argtypes = [EGLDisplay, EGLContext, EGLint, POINTER(EGLint)]

# /usr/include/EGL/egl.h:139
eglQueryString = _lib.eglQueryString
eglQueryString.restype = c_char_p
eglQueryString.argtypes = [EGLDisplay, EGLint]

# /usr/include/EGL/egl.h:140
eglQuerySurface = _lib.eglQuerySurface
eglQuerySurface.restype = EGLBoolean
eglQuerySurface.argtypes = [EGLDisplay, EGLSurface, EGLint, POINTER(EGLint)]

# /usr/include/EGL/egl.h:141
eglSwapBuffers = _lib.eglSwapBuffers
eglSwapBuffers.restype = EGLBoolean
eglSwapBuffers.argtypes = [EGLDisplay, EGLSurface]

# /usr/include/EGL/egl.h:142
eglTerminate = _lib.eglTerminate
eglTerminate.restype = EGLBoolean
eglTerminate.argtypes = [EGLDisplay]

# /usr/include/EGL/egl.h:143
eglWaitGL = _lib.eglWaitGL
eglWaitGL.restype = EGLBoolean
eglWaitGL.argtypes = []

# /usr/include/EGL/egl.h:144
eglWaitNative = _lib.eglWaitNative
eglWaitNative.restype = EGLBoolean
eglWaitNative.argtypes = [EGLint]

EGL_VERSION_1_1 = 1 	# /usr/include/EGL/egl.h:148
EGL_BACK_BUFFER = 12420 	# /usr/include/EGL/egl.h:149
EGL_BIND_TO_TEXTURE_RGB = 12345 	# /usr/include/EGL/egl.h:150
EGL_BIND_TO_TEXTURE_RGBA = 12346 	# /usr/include/EGL/egl.h:151
EGL_CONTEXT_LOST = 12302 	# /usr/include/EGL/egl.h:152
EGL_MIN_SWAP_INTERVAL = 12347 	# /usr/include/EGL/egl.h:153
EGL_MAX_SWAP_INTERVAL = 12348 	# /usr/include/EGL/egl.h:154
EGL_MIPMAP_TEXTURE = 12418 	# /usr/include/EGL/egl.h:155
EGL_MIPMAP_LEVEL = 12419 	# /usr/include/EGL/egl.h:156
EGL_NO_TEXTURE = 12380 	# /usr/include/EGL/egl.h:157
EGL_TEXTURE_2D = 12383 	# /usr/include/EGL/egl.h:158
EGL_TEXTURE_FORMAT = 12416 	# /usr/include/EGL/egl.h:159
EGL_TEXTURE_RGB = 12381 	# /usr/include/EGL/egl.h:160
EGL_TEXTURE_RGBA = 12382 	# /usr/include/EGL/egl.h:161
EGL_TEXTURE_TARGET = 12417 	# /usr/include/EGL/egl.h:162
# /usr/include/EGL/egl.h:163
eglBindTexImage = _lib.eglBindTexImage
eglBindTexImage.restype = EGLBoolean
eglBindTexImage.argtypes = [EGLDisplay, EGLSurface, EGLint]

# /usr/include/EGL/egl.h:164
eglReleaseTexImage = _lib.eglReleaseTexImage
eglReleaseTexImage.restype = EGLBoolean
eglReleaseTexImage.argtypes = [EGLDisplay, EGLSurface, EGLint]

# /usr/include/EGL/egl.h:165
eglSurfaceAttrib = _lib.eglSurfaceAttrib
eglSurfaceAttrib.restype = EGLBoolean
eglSurfaceAttrib.argtypes = [EGLDisplay, EGLSurface, EGLint, EGLint]

# /usr/include/EGL/egl.h:166
eglSwapInterval = _lib.eglSwapInterval
eglSwapInterval.restype = EGLBoolean
eglSwapInterval.argtypes = [EGLDisplay, EGLint]

EGL_VERSION_1_2 = 1 	# /usr/include/EGL/egl.h:170
EGLenum = c_uint 	# /usr/include/EGL/egl.h:171
EGLClientBuffer = POINTER(None) 	# /usr/include/EGL/egl.h:172
EGL_ALPHA_FORMAT = 12424 	# /usr/include/EGL/egl.h:173
EGL_ALPHA_FORMAT_NONPRE = 12427 	# /usr/include/EGL/egl.h:174
EGL_ALPHA_FORMAT_PRE = 12428 	# /usr/include/EGL/egl.h:175
EGL_ALPHA_MASK_SIZE = 12350 	# /usr/include/EGL/egl.h:176
EGL_BUFFER_PRESERVED = 12436 	# /usr/include/EGL/egl.h:177
EGL_BUFFER_DESTROYED = 12437 	# /usr/include/EGL/egl.h:178
EGL_CLIENT_APIS = 12429 	# /usr/include/EGL/egl.h:179
EGL_COLORSPACE = 12423 	# /usr/include/EGL/egl.h:180
EGL_COLORSPACE_sRGB = 12425 	# /usr/include/EGL/egl.h:181
EGL_COLORSPACE_LINEAR = 12426 	# /usr/include/EGL/egl.h:182
EGL_COLOR_BUFFER_TYPE = 12351 	# /usr/include/EGL/egl.h:183
EGL_CONTEXT_CLIENT_TYPE = 12439 	# /usr/include/EGL/egl.h:184
EGL_DISPLAY_SCALING = 10000 	# /usr/include/EGL/egl.h:185
EGL_HORIZONTAL_RESOLUTION = 12432 	# /usr/include/EGL/egl.h:186
EGL_LUMINANCE_BUFFER = 12431 	# /usr/include/EGL/egl.h:187
EGL_LUMINANCE_SIZE = 12349 	# /usr/include/EGL/egl.h:188
EGL_OPENGL_ES_BIT = 1 	# /usr/include/EGL/egl.h:189
EGL_OPENVG_BIT = 2 	# /usr/include/EGL/egl.h:190
EGL_OPENGL_ES_API = 12448 	# /usr/include/EGL/egl.h:191
EGL_OPENVG_API = 12449 	# /usr/include/EGL/egl.h:192
EGL_OPENVG_IMAGE = 12438 	# /usr/include/EGL/egl.h:193
EGL_PIXEL_ASPECT_RATIO = 12434 	# /usr/include/EGL/egl.h:194
EGL_RENDERABLE_TYPE = 12352 	# /usr/include/EGL/egl.h:195
EGL_RENDER_BUFFER = 12422 	# /usr/include/EGL/egl.h:196
EGL_RGB_BUFFER = 12430 	# /usr/include/EGL/egl.h:197
EGL_SINGLE_BUFFER = 12421 	# /usr/include/EGL/egl.h:198
EGL_SWAP_BEHAVIOR = 12435 	# /usr/include/EGL/egl.h:199
EGL_VERTICAL_RESOLUTION = 12433 	# /usr/include/EGL/egl.h:201
# /usr/include/EGL/egl.h:202
eglBindAPI = _lib.eglBindAPI
eglBindAPI.restype = EGLBoolean
eglBindAPI.argtypes = [EGLenum]

# /usr/include/EGL/egl.h:203
eglQueryAPI = _lib.eglQueryAPI
eglQueryAPI.restype = EGLenum
eglQueryAPI.argtypes = []

# /usr/include/EGL/egl.h:204
eglCreatePbufferFromClientBuffer = _lib.eglCreatePbufferFromClientBuffer
eglCreatePbufferFromClientBuffer.restype = EGLSurface
eglCreatePbufferFromClientBuffer.argtypes = [EGLDisplay, EGLenum, EGLClientBuffer, EGLConfig, POINTER(EGLint)]

# /usr/include/EGL/egl.h:205
eglReleaseThread = _lib.eglReleaseThread
eglReleaseThread.restype = EGLBoolean
eglReleaseThread.argtypes = []

# /usr/include/EGL/egl.h:206
eglWaitClient = _lib.eglWaitClient
eglWaitClient.restype = EGLBoolean
eglWaitClient.argtypes = []

EGL_VERSION_1_3 = 1 	# /usr/include/EGL/egl.h:210
EGL_CONFORMANT = 12354 	# /usr/include/EGL/egl.h:211
EGL_CONTEXT_CLIENT_VERSION = 12440 	# /usr/include/EGL/egl.h:212
EGL_MATCH_NATIVE_PIXMAP = 12353 	# /usr/include/EGL/egl.h:213
EGL_OPENGL_ES2_BIT = 4 	# /usr/include/EGL/egl.h:214
EGL_VG_ALPHA_FORMAT = 12424 	# /usr/include/EGL/egl.h:215
EGL_VG_ALPHA_FORMAT_NONPRE = 12427 	# /usr/include/EGL/egl.h:216
EGL_VG_ALPHA_FORMAT_PRE = 12428 	# /usr/include/EGL/egl.h:217
EGL_VG_ALPHA_FORMAT_PRE_BIT = 64 	# /usr/include/EGL/egl.h:218
EGL_VG_COLORSPACE = 12423 	# /usr/include/EGL/egl.h:219
EGL_VG_COLORSPACE_sRGB = 12425 	# /usr/include/EGL/egl.h:220
EGL_VG_COLORSPACE_LINEAR = 12426 	# /usr/include/EGL/egl.h:221
EGL_VG_COLORSPACE_LINEAR_BIT = 32 	# /usr/include/EGL/egl.h:222
EGL_VERSION_1_4 = 1 	# /usr/include/EGL/egl.h:226
EGL_MULTISAMPLE_RESOLVE_BOX_BIT = 512 	# /usr/include/EGL/egl.h:228
EGL_MULTISAMPLE_RESOLVE = 12441 	# /usr/include/EGL/egl.h:229
EGL_MULTISAMPLE_RESOLVE_DEFAULT = 12442 	# /usr/include/EGL/egl.h:230
EGL_MULTISAMPLE_RESOLVE_BOX = 12443 	# /usr/include/EGL/egl.h:231
EGL_OPENGL_API = 12450 	# /usr/include/EGL/egl.h:232
EGL_OPENGL_BIT = 8 	# /usr/include/EGL/egl.h:233
EGL_SWAP_BEHAVIOR_PRESERVED_BIT = 1024 	# /usr/include/EGL/egl.h:234
# /usr/include/EGL/egl.h:235
eglGetCurrentContext = _lib.eglGetCurrentContext
eglGetCurrentContext.restype = EGLContext
eglGetCurrentContext.argtypes = []

EGL_VERSION_1_5 = 1 	# /usr/include/EGL/egl.h:239
EGLSync = POINTER(None) 	# /usr/include/EGL/egl.h:240
intptr_t = c_long 	# /usr/include/stdint.h:87
EGLAttrib = intptr_t 	# /usr/include/EGL/egl.h:241
khronos_uint64_t = c_uint64 	# /usr/include/KHR/khrplatform.h:149
khronos_utime_nanoseconds_t = khronos_uint64_t 	# /usr/include/KHR/khrplatform.h:263
EGLTime = khronos_utime_nanoseconds_t 	# /usr/include/EGL/egl.h:242
EGLImage = POINTER(None) 	# /usr/include/EGL/egl.h:243
EGL_CONTEXT_MAJOR_VERSION = 12440 	# /usr/include/EGL/egl.h:244
EGL_CONTEXT_MINOR_VERSION = 12539 	# /usr/include/EGL/egl.h:245
EGL_CONTEXT_OPENGL_PROFILE_MASK = 12541 	# /usr/include/EGL/egl.h:246
EGL_CONTEXT_OPENGL_RESET_NOTIFICATION_STRATEGY = 12733 	# /usr/include/EGL/egl.h:247
EGL_NO_RESET_NOTIFICATION = 12734 	# /usr/include/EGL/egl.h:248
EGL_LOSE_CONTEXT_ON_RESET = 12735 	# /usr/include/EGL/egl.h:249
EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT = 1 	# /usr/include/EGL/egl.h:250
EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT = 2 	# /usr/include/EGL/egl.h:251
EGL_CONTEXT_OPENGL_DEBUG = 12720 	# /usr/include/EGL/egl.h:252
EGL_CONTEXT_OPENGL_FORWARD_COMPATIBLE = 12721 	# /usr/include/EGL/egl.h:253
EGL_CONTEXT_OPENGL_ROBUST_ACCESS = 12722 	# /usr/include/EGL/egl.h:254
EGL_OPENGL_ES3_BIT = 64 	# /usr/include/EGL/egl.h:255
EGL_CL_EVENT_HANDLE = 12444 	# /usr/include/EGL/egl.h:256
EGL_SYNC_CL_EVENT = 12542 	# /usr/include/EGL/egl.h:257
EGL_SYNC_CL_EVENT_COMPLETE = 12543 	# /usr/include/EGL/egl.h:258
EGL_SYNC_PRIOR_COMMANDS_COMPLETE = 12528 	# /usr/include/EGL/egl.h:259
EGL_SYNC_TYPE = 12535 	# /usr/include/EGL/egl.h:260
EGL_SYNC_STATUS = 12529 	# /usr/include/EGL/egl.h:261
EGL_SYNC_CONDITION = 12536 	# /usr/include/EGL/egl.h:262
EGL_SIGNALED = 12530 	# /usr/include/EGL/egl.h:263
EGL_UNSIGNALED = 12531 	# /usr/include/EGL/egl.h:264
EGL_SYNC_FLUSH_COMMANDS_BIT = 1 	# /usr/include/EGL/egl.h:265
EGL_FOREVER = 18446744073709551615 	# /usr/include/EGL/egl.h:266
EGL_TIMEOUT_EXPIRED = 12533 	# /usr/include/EGL/egl.h:267
EGL_CONDITION_SATISFIED = 12534 	# /usr/include/EGL/egl.h:268
EGL_SYNC_FENCE = 12537 	# /usr/include/EGL/egl.h:270
EGL_GL_COLORSPACE = 12445 	# /usr/include/EGL/egl.h:271
EGL_GL_COLORSPACE_SRGB = 12425 	# /usr/include/EGL/egl.h:272
EGL_GL_COLORSPACE_LINEAR = 12426 	# /usr/include/EGL/egl.h:273
EGL_GL_RENDERBUFFER = 12473 	# /usr/include/EGL/egl.h:274
EGL_GL_TEXTURE_2D = 12465 	# /usr/include/EGL/egl.h:275
EGL_GL_TEXTURE_LEVEL = 12476 	# /usr/include/EGL/egl.h:276
EGL_GL_TEXTURE_3D = 12466 	# /usr/include/EGL/egl.h:277
EGL_GL_TEXTURE_ZOFFSET = 12477 	# /usr/include/EGL/egl.h:278
EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_X = 12467 	# /usr/include/EGL/egl.h:279
EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_X = 12468 	# /usr/include/EGL/egl.h:280
EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_Y = 12469 	# /usr/include/EGL/egl.h:281
EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_Y = 12470 	# /usr/include/EGL/egl.h:282
EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_Z = 12471 	# /usr/include/EGL/egl.h:283
EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_Z = 12472 	# /usr/include/EGL/egl.h:284
EGL_IMAGE_PRESERVED = 12498 	# /usr/include/EGL/egl.h:285
# /usr/include/EGL/egl.h:287
eglCreateSync = _lib.eglCreateSync
eglCreateSync.restype = EGLSync
eglCreateSync.argtypes = [EGLDisplay, EGLenum, POINTER(EGLAttrib)]

# /usr/include/EGL/egl.h:288
eglDestroySync = _lib.eglDestroySync
eglDestroySync.restype = EGLBoolean
eglDestroySync.argtypes = [EGLDisplay, EGLSync]

# /usr/include/EGL/egl.h:289
eglClientWaitSync = _lib.eglClientWaitSync
eglClientWaitSync.restype = EGLint
eglClientWaitSync.argtypes = [EGLDisplay, EGLSync, EGLint, EGLTime]

# /usr/include/EGL/egl.h:290
eglGetSyncAttrib = _lib.eglGetSyncAttrib
eglGetSyncAttrib.restype = EGLBoolean
eglGetSyncAttrib.argtypes = [EGLDisplay, EGLSync, EGLint, POINTER(EGLAttrib)]

# /usr/include/EGL/egl.h:291
eglCreateImage = _lib.eglCreateImage
eglCreateImage.restype = EGLImage
eglCreateImage.argtypes = [EGLDisplay, EGLContext, EGLenum, EGLClientBuffer, POINTER(EGLAttrib)]

# /usr/include/EGL/egl.h:292
eglDestroyImage = _lib.eglDestroyImage
eglDestroyImage.restype = EGLBoolean
eglDestroyImage.argtypes = [EGLDisplay, EGLImage]

# /usr/include/EGL/egl.h:293
eglGetPlatformDisplay = _lib.eglGetPlatformDisplay
eglGetPlatformDisplay.restype = EGLDisplay
eglGetPlatformDisplay.argtypes = [EGLenum, POINTER(None), POINTER(EGLAttrib)]

# /usr/include/EGL/egl.h:294
eglCreatePlatformWindowSurface = _lib.eglCreatePlatformWindowSurface
eglCreatePlatformWindowSurface.restype = EGLSurface
eglCreatePlatformWindowSurface.argtypes = [EGLDisplay, EGLConfig, POINTER(None), POINTER(EGLAttrib)]

# /usr/include/EGL/egl.h:295
eglCreatePlatformPixmapSurface = _lib.eglCreatePlatformPixmapSurface
eglCreatePlatformPixmapSurface.restype = EGLSurface
eglCreatePlatformPixmapSurface.argtypes = [EGLDisplay, EGLConfig, POINTER(None), POINTER(EGLAttrib)]

# /usr/include/EGL/egl.h:296
eglWaitSync = _lib.eglWaitSync
eglWaitSync.restype = EGLBoolean
eglWaitSync.argtypes = [EGLDisplay, EGLSync, EGLint]


__all__ = ['__egl_h_', 'EGL_VERSION_1_0', 'EGLBoolean', 'EGLDisplay',
'EGLConfig', 'EGLSurface', 'EGLContext',
'__eglMustCastToProperFunctionPointerType', 'EGL_ALPHA_SIZE',
'EGL_BAD_ACCESS', 'EGL_BAD_ALLOC', 'EGL_BAD_ATTRIBUTE', 'EGL_BAD_CONFIG',
'EGL_BAD_CONTEXT', 'EGL_BAD_CURRENT_SURFACE', 'EGL_BAD_DISPLAY',
'EGL_BAD_MATCH', 'EGL_BAD_NATIVE_PIXMAP', 'EGL_BAD_NATIVE_WINDOW',
'EGL_BAD_PARAMETER', 'EGL_BAD_SURFACE', 'EGL_BLUE_SIZE', 'EGL_BUFFER_SIZE',
'EGL_CONFIG_CAVEAT', 'EGL_CONFIG_ID', 'EGL_CORE_NATIVE_ENGINE',
'EGL_DEPTH_SIZE', 'EGL_DRAW', 'EGL_EXTENSIONS', 'EGL_FALSE', 'EGL_GREEN_SIZE',
'EGL_HEIGHT', 'EGL_LARGEST_PBUFFER', 'EGL_LEVEL', 'EGL_MAX_PBUFFER_HEIGHT',
'EGL_MAX_PBUFFER_PIXELS', 'EGL_MAX_PBUFFER_WIDTH', 'EGL_NATIVE_RENDERABLE',
'EGL_NATIVE_VISUAL_ID', 'EGL_NATIVE_VISUAL_TYPE', 'EGL_NONE',
'EGL_NON_CONFORMANT_CONFIG', 'EGL_NOT_INITIALIZED', 'EGL_PBUFFER_BIT',
'EGL_PIXMAP_BIT', 'EGL_READ', 'EGL_RED_SIZE', 'EGL_SAMPLES',
'EGL_SAMPLE_BUFFERS', 'EGL_SLOW_CONFIG', 'EGL_STENCIL_SIZE', 'EGL_SUCCESS',
'EGL_SURFACE_TYPE', 'EGL_TRANSPARENT_BLUE_VALUE',
'EGL_TRANSPARENT_GREEN_VALUE', 'EGL_TRANSPARENT_RED_VALUE',
'EGL_TRANSPARENT_RGB', 'EGL_TRANSPARENT_TYPE', 'EGL_TRUE', 'EGL_VENDOR',
'EGL_VERSION', 'EGL_WIDTH', 'EGL_WINDOW_BIT', 'eglChooseConfig',
'eglCopyBuffers', 'eglCreateContext', 'eglCreatePbufferSurface',
'eglCreatePixmapSurface', 'eglCreateWindowSurface', 'eglDestroyContext',
'eglDestroySurface', 'eglGetConfigAttrib', 'eglGetConfigs',
'eglGetCurrentDisplay', 'eglGetCurrentSurface', 'eglGetDisplay',
'eglGetError', 'eglGetProcAddress', 'eglInitialize', 'eglMakeCurrent',
'eglQueryContext', 'eglQueryString', 'eglQuerySurface', 'eglSwapBuffers',
'eglTerminate', 'eglWaitGL', 'eglWaitNative', 'EGL_VERSION_1_1',
'EGL_BACK_BUFFER', 'EGL_BIND_TO_TEXTURE_RGB', 'EGL_BIND_TO_TEXTURE_RGBA',
'EGL_CONTEXT_LOST', 'EGL_MIN_SWAP_INTERVAL', 'EGL_MAX_SWAP_INTERVAL',
'EGL_MIPMAP_TEXTURE', 'EGL_MIPMAP_LEVEL', 'EGL_NO_TEXTURE', 'EGL_TEXTURE_2D',
'EGL_TEXTURE_FORMAT', 'EGL_TEXTURE_RGB', 'EGL_TEXTURE_RGBA',
'EGL_TEXTURE_TARGET', 'eglBindTexImage', 'eglReleaseTexImage',
'eglSurfaceAttrib', 'eglSwapInterval', 'EGL_VERSION_1_2', 'EGLenum',
'EGLClientBuffer', 'EGL_ALPHA_FORMAT', 'EGL_ALPHA_FORMAT_NONPRE',
'EGL_ALPHA_FORMAT_PRE', 'EGL_ALPHA_MASK_SIZE', 'EGL_BUFFER_PRESERVED',
'EGL_BUFFER_DESTROYED', 'EGL_CLIENT_APIS', 'EGL_COLORSPACE',
'EGL_COLORSPACE_sRGB', 'EGL_COLORSPACE_LINEAR', 'EGL_COLOR_BUFFER_TYPE',
'EGL_CONTEXT_CLIENT_TYPE', 'EGL_DISPLAY_SCALING', 'EGL_HORIZONTAL_RESOLUTION',
'EGL_LUMINANCE_BUFFER', 'EGL_LUMINANCE_SIZE', 'EGL_OPENGL_ES_BIT',
'EGL_OPENVG_BIT', 'EGL_OPENGL_ES_API', 'EGL_OPENVG_API', 'EGL_OPENVG_IMAGE',
'EGL_PIXEL_ASPECT_RATIO', 'EGL_RENDERABLE_TYPE', 'EGL_RENDER_BUFFER',
'EGL_RGB_BUFFER', 'EGL_SINGLE_BUFFER', 'EGL_SWAP_BEHAVIOR',
'EGL_VERTICAL_RESOLUTION', 'eglBindAPI', 'eglQueryAPI',
'eglCreatePbufferFromClientBuffer', 'eglReleaseThread', 'eglWaitClient',
'EGL_VERSION_1_3', 'EGL_CONFORMANT', 'EGL_CONTEXT_CLIENT_VERSION',
'EGL_MATCH_NATIVE_PIXMAP', 'EGL_OPENGL_ES2_BIT', 'EGL_VG_ALPHA_FORMAT',
'EGL_VG_ALPHA_FORMAT_NONPRE', 'EGL_VG_ALPHA_FORMAT_PRE',
'EGL_VG_ALPHA_FORMAT_PRE_BIT', 'EGL_VG_COLORSPACE', 'EGL_VG_COLORSPACE_sRGB',
'EGL_VG_COLORSPACE_LINEAR', 'EGL_VG_COLORSPACE_LINEAR_BIT', 'EGL_VERSION_1_4',
'EGL_MULTISAMPLE_RESOLVE_BOX_BIT', 'EGL_MULTISAMPLE_RESOLVE',
'EGL_MULTISAMPLE_RESOLVE_DEFAULT', 'EGL_MULTISAMPLE_RESOLVE_BOX',
'EGL_OPENGL_API', 'EGL_OPENGL_BIT', 'EGL_SWAP_BEHAVIOR_PRESERVED_BIT',
'eglGetCurrentContext', 'EGL_VERSION_1_5', 'EGLSync', 'EGLAttrib', 'EGLTime',
'EGLImage', 'EGL_CONTEXT_MAJOR_VERSION', 'EGL_CONTEXT_MINOR_VERSION',
'EGL_CONTEXT_OPENGL_PROFILE_MASK',
'EGL_CONTEXT_OPENGL_RESET_NOTIFICATION_STRATEGY', 'EGL_NO_RESET_NOTIFICATION',
'EGL_LOSE_CONTEXT_ON_RESET', 'EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT',
'EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT', 'EGL_CONTEXT_OPENGL_DEBUG',
'EGL_CONTEXT_OPENGL_FORWARD_COMPATIBLE', 'EGL_CONTEXT_OPENGL_ROBUST_ACCESS',
'EGL_OPENGL_ES3_BIT', 'EGL_CL_EVENT_HANDLE', 'EGL_SYNC_CL_EVENT',
'EGL_SYNC_CL_EVENT_COMPLETE', 'EGL_SYNC_PRIOR_COMMANDS_COMPLETE',
'EGL_SYNC_TYPE', 'EGL_SYNC_STATUS', 'EGL_SYNC_CONDITION', 'EGL_SIGNALED',
'EGL_UNSIGNALED', 'EGL_SYNC_FLUSH_COMMANDS_BIT', 'EGL_FOREVER',
'EGL_TIMEOUT_EXPIRED', 'EGL_CONDITION_SATISFIED', 'EGL_SYNC_FENCE',
'EGL_GL_COLORSPACE', 'EGL_GL_COLORSPACE_SRGB', 'EGL_GL_COLORSPACE_LINEAR',
'EGL_GL_RENDERBUFFER', 'EGL_GL_TEXTURE_2D', 'EGL_GL_TEXTURE_LEVEL',
'EGL_GL_TEXTURE_3D', 'EGL_GL_TEXTURE_ZOFFSET',
'EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_X', 'EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_X',
'EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_Y', 'EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_Y',
'EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_Z', 'EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_Z',
'EGL_IMAGE_PRESERVED', 'eglCreateSync', 'eglDestroySync', 'eglClientWaitSync',
'eglGetSyncAttrib', 'eglCreateImage', 'eglDestroyImage',
'eglGetPlatformDisplay', 'eglCreatePlatformWindowSurface',
'eglCreatePlatformPixmapSurface', 'eglWaitSync']
