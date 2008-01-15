'''Wrapper for Xxf86vm

Generated with:
tools/genwrappers.py

Do not modify this file.
'''

__docformat__ =  'restructuredtext'
__version__ = '$Id$'

import ctypes
from ctypes import *

import pyglet.lib

_lib = pyglet.lib.load_library('Xxf86vm')

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


import pyglet.gl.glx
import pyglet.window.xlib.xlib

Bool = pyglet.window.xlib.xlib.Bool
X_XF86VidModeQueryVersion = 0 	# xf86vmode.h:43
X_XF86VidModeGetModeLine = 1 	# xf86vmode.h:44
X_XF86VidModeModModeLine = 2 	# xf86vmode.h:45
X_XF86VidModeSwitchMode = 3 	# xf86vmode.h:46
X_XF86VidModeGetMonitor = 4 	# xf86vmode.h:47
X_XF86VidModeLockModeSwitch = 5 	# xf86vmode.h:48
X_XF86VidModeGetAllModeLines = 6 	# xf86vmode.h:49
X_XF86VidModeAddModeLine = 7 	# xf86vmode.h:50
X_XF86VidModeDeleteModeLine = 8 	# xf86vmode.h:51
X_XF86VidModeValidateModeLine = 9 	# xf86vmode.h:52
X_XF86VidModeSwitchToMode = 10 	# xf86vmode.h:53
X_XF86VidModeGetViewPort = 11 	# xf86vmode.h:54
X_XF86VidModeSetViewPort = 12 	# xf86vmode.h:55
X_XF86VidModeGetDotClocks = 13 	# xf86vmode.h:57
X_XF86VidModeSetClientVersion = 14 	# xf86vmode.h:58
X_XF86VidModeSetGamma = 15 	# xf86vmode.h:59
X_XF86VidModeGetGamma = 16 	# xf86vmode.h:60
X_XF86VidModeGetGammaRamp = 17 	# xf86vmode.h:61
X_XF86VidModeSetGammaRamp = 18 	# xf86vmode.h:62
X_XF86VidModeGetGammaRampSize = 19 	# xf86vmode.h:63
X_XF86VidModeGetPermissions = 20 	# xf86vmode.h:64
CLKFLAG_PROGRAMABLE = 1 	# xf86vmode.h:66
XF86VidModeNumberEvents = 0 	# xf86vmode.h:77
XF86VidModeBadClock = 0 	# xf86vmode.h:80
XF86VidModeBadHTimings = 1 	# xf86vmode.h:81
XF86VidModeBadVTimings = 2 	# xf86vmode.h:82
XF86VidModeModeUnsuitable = 3 	# xf86vmode.h:83
XF86VidModeExtensionDisabled = 4 	# xf86vmode.h:84
XF86VidModeClientNotLocal = 5 	# xf86vmode.h:85
XF86VidModeZoomLocked = 6 	# xf86vmode.h:86
XF86VidModeNumberErrors = 7 	# xf86vmode.h:87
XF86VM_READ_PERMISSION = 1 	# xf86vmode.h:89
XF86VM_WRITE_PERMISSION = 2 	# xf86vmode.h:90
class struct_anon_1(Structure):
    __slots__ = [
        'hdisplay',
        'hsyncstart',
        'hsyncend',
        'htotal',
        'hskew',
        'vdisplay',
        'vsyncstart',
        'vsyncend',
        'vtotal',
        'flags',
        'privsize',
        'private',
    ]
INT32 = c_int 	# /usr/include/X11/Xmd.h:135
struct_anon_1._fields_ = [
    ('hdisplay', c_ushort),
    ('hsyncstart', c_ushort),
    ('hsyncend', c_ushort),
    ('htotal', c_ushort),
    ('hskew', c_ushort),
    ('vdisplay', c_ushort),
    ('vsyncstart', c_ushort),
    ('vsyncend', c_ushort),
    ('vtotal', c_ushort),
    ('flags', c_uint),
    ('privsize', c_int),
    ('private', POINTER(INT32)),
]

XF86VidModeModeLine = struct_anon_1 	# xf86vmode.h:112
class struct_anon_2(Structure):
    __slots__ = [
        'dotclock',
        'hdisplay',
        'hsyncstart',
        'hsyncend',
        'htotal',
        'hskew',
        'vdisplay',
        'vsyncstart',
        'vsyncend',
        'vtotal',
        'flags',
        'privsize',
        'private',
    ]
struct_anon_2._fields_ = [
    ('dotclock', c_uint),
    ('hdisplay', c_ushort),
    ('hsyncstart', c_ushort),
    ('hsyncend', c_ushort),
    ('htotal', c_ushort),
    ('hskew', c_ushort),
    ('vdisplay', c_ushort),
    ('vsyncstart', c_ushort),
    ('vsyncend', c_ushort),
    ('vtotal', c_ushort),
    ('flags', c_uint),
    ('privsize', c_int),
    ('private', POINTER(INT32)),
]

XF86VidModeModeInfo = struct_anon_2 	# xf86vmode.h:133
class struct_anon_3(Structure):
    __slots__ = [
        'hi',
        'lo',
    ]
struct_anon_3._fields_ = [
    ('hi', c_float),
    ('lo', c_float),
]

XF86VidModeSyncRange = struct_anon_3 	# xf86vmode.h:138
class struct_anon_4(Structure):
    __slots__ = [
        'vendor',
        'model',
        'EMPTY',
        'nhsync',
        'hsync',
        'nvsync',
        'vsync',
    ]
struct_anon_4._fields_ = [
    ('vendor', c_char_p),
    ('model', c_char_p),
    ('EMPTY', c_float),
    ('nhsync', c_ubyte),
    ('hsync', POINTER(XF86VidModeSyncRange)),
    ('nvsync', c_ubyte),
    ('vsync', POINTER(XF86VidModeSyncRange)),
]

XF86VidModeMonitor = struct_anon_4 	# xf86vmode.h:148
Display = pyglet.gl.glx.Display
Window = pyglet.gl.glx.Window
Time = pyglet.window.xlib.xlib.Time
Status = pyglet.window.xlib.xlib.Status
class struct_anon_5(Structure):
    __slots__ = [
        'type',
        'serial',
        'send_event',
        'display',
        'root',
        'state',
        'kind',
        'forced',
        'time',
    ]
struct_anon_5._fields_ = [
    ('type', c_int),
    ('serial', c_ulong),
    ('send_event', Bool),
    ('display', POINTER(Display)),
    ('root', Window),
    ('state', c_int),
    ('kind', c_int),
    ('forced', Bool),
    ('time', Time),
]

XF86VidModeNotifyEvent = struct_anon_5 	# xf86vmode.h:165
class struct_anon_6(Structure):
    __slots__ = [
        'red',
        'green',
        'blue',
    ]
struct_anon_6._fields_ = [
    ('red', c_float),
    ('green', c_float),
    ('blue', c_float),
]

XF86VidModeGamma = struct_anon_6 	# xf86vmode.h:171
# xf86vmode.h:181
XF86VidModeQueryVersion = _lib.XF86VidModeQueryVersion
XF86VidModeQueryVersion.restype = Bool
XF86VidModeQueryVersion.argtypes = [POINTER(Display), POINTER(c_int), POINTER(c_int)]

# xf86vmode.h:187
XF86VidModeQueryExtension = _lib.XF86VidModeQueryExtension
XF86VidModeQueryExtension.restype = Bool
XF86VidModeQueryExtension.argtypes = [POINTER(Display), POINTER(c_int), POINTER(c_int)]

# xf86vmode.h:193
XF86VidModeSetClientVersion = _lib.XF86VidModeSetClientVersion
XF86VidModeSetClientVersion.restype = Bool
XF86VidModeSetClientVersion.argtypes = [POINTER(Display)]

# xf86vmode.h:197
XF86VidModeGetModeLine = _lib.XF86VidModeGetModeLine
XF86VidModeGetModeLine.restype = Bool
XF86VidModeGetModeLine.argtypes = [POINTER(Display), c_int, POINTER(c_int), POINTER(XF86VidModeModeLine)]

# xf86vmode.h:204
XF86VidModeGetAllModeLines = _lib.XF86VidModeGetAllModeLines
XF86VidModeGetAllModeLines.restype = Bool
XF86VidModeGetAllModeLines.argtypes = [POINTER(Display), c_int, POINTER(c_int), POINTER(POINTER(POINTER(XF86VidModeModeInfo)))]

# xf86vmode.h:211
XF86VidModeAddModeLine = _lib.XF86VidModeAddModeLine
XF86VidModeAddModeLine.restype = Bool
XF86VidModeAddModeLine.argtypes = [POINTER(Display), c_int, POINTER(XF86VidModeModeInfo), POINTER(XF86VidModeModeInfo)]

# xf86vmode.h:218
XF86VidModeDeleteModeLine = _lib.XF86VidModeDeleteModeLine
XF86VidModeDeleteModeLine.restype = Bool
XF86VidModeDeleteModeLine.argtypes = [POINTER(Display), c_int, POINTER(XF86VidModeModeInfo)]

# xf86vmode.h:224
XF86VidModeModModeLine = _lib.XF86VidModeModModeLine
XF86VidModeModModeLine.restype = Bool
XF86VidModeModModeLine.argtypes = [POINTER(Display), c_int, POINTER(XF86VidModeModeLine)]

# xf86vmode.h:230
XF86VidModeValidateModeLine = _lib.XF86VidModeValidateModeLine
XF86VidModeValidateModeLine.restype = Status
XF86VidModeValidateModeLine.argtypes = [POINTER(Display), c_int, POINTER(XF86VidModeModeInfo)]

# xf86vmode.h:236
XF86VidModeSwitchMode = _lib.XF86VidModeSwitchMode
XF86VidModeSwitchMode.restype = Bool
XF86VidModeSwitchMode.argtypes = [POINTER(Display), c_int, c_int]

# xf86vmode.h:242
XF86VidModeSwitchToMode = _lib.XF86VidModeSwitchToMode
XF86VidModeSwitchToMode.restype = Bool
XF86VidModeSwitchToMode.argtypes = [POINTER(Display), c_int, POINTER(XF86VidModeModeInfo)]

# xf86vmode.h:248
XF86VidModeLockModeSwitch = _lib.XF86VidModeLockModeSwitch
XF86VidModeLockModeSwitch.restype = Bool
XF86VidModeLockModeSwitch.argtypes = [POINTER(Display), c_int, c_int]

# xf86vmode.h:254
XF86VidModeGetMonitor = _lib.XF86VidModeGetMonitor
XF86VidModeGetMonitor.restype = Bool
XF86VidModeGetMonitor.argtypes = [POINTER(Display), c_int, POINTER(XF86VidModeMonitor)]

# xf86vmode.h:260
XF86VidModeGetViewPort = _lib.XF86VidModeGetViewPort
XF86VidModeGetViewPort.restype = Bool
XF86VidModeGetViewPort.argtypes = [POINTER(Display), c_int, POINTER(c_int), POINTER(c_int)]

# xf86vmode.h:267
XF86VidModeSetViewPort = _lib.XF86VidModeSetViewPort
XF86VidModeSetViewPort.restype = Bool
XF86VidModeSetViewPort.argtypes = [POINTER(Display), c_int, c_int, c_int]

# xf86vmode.h:274
XF86VidModeGetDotClocks = _lib.XF86VidModeGetDotClocks
XF86VidModeGetDotClocks.restype = Bool
XF86VidModeGetDotClocks.argtypes = [POINTER(Display), c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(POINTER(c_int))]

# xf86vmode.h:283
XF86VidModeGetGamma = _lib.XF86VidModeGetGamma
XF86VidModeGetGamma.restype = Bool
XF86VidModeGetGamma.argtypes = [POINTER(Display), c_int, POINTER(XF86VidModeGamma)]

# xf86vmode.h:289
XF86VidModeSetGamma = _lib.XF86VidModeSetGamma
XF86VidModeSetGamma.restype = Bool
XF86VidModeSetGamma.argtypes = [POINTER(Display), c_int, POINTER(XF86VidModeGamma)]

# xf86vmode.h:295
XF86VidModeSetGammaRamp = _lib.XF86VidModeSetGammaRamp
XF86VidModeSetGammaRamp.restype = Bool
XF86VidModeSetGammaRamp.argtypes = [POINTER(Display), c_int, c_int, POINTER(c_ushort), POINTER(c_ushort), POINTER(c_ushort)]

# xf86vmode.h:304
XF86VidModeGetGammaRamp = _lib.XF86VidModeGetGammaRamp
XF86VidModeGetGammaRamp.restype = Bool
XF86VidModeGetGammaRamp.argtypes = [POINTER(Display), c_int, c_int, POINTER(c_ushort), POINTER(c_ushort), POINTER(c_ushort)]

# xf86vmode.h:313
XF86VidModeGetGammaRampSize = _lib.XF86VidModeGetGammaRampSize
XF86VidModeGetGammaRampSize.restype = Bool
XF86VidModeGetGammaRampSize.argtypes = [POINTER(Display), c_int, POINTER(c_int)]

# xf86vmode.h:319
XF86VidModeGetPermissions = _lib.XF86VidModeGetPermissions
XF86VidModeGetPermissions.restype = Bool
XF86VidModeGetPermissions.argtypes = [POINTER(Display), c_int, POINTER(c_int)]


__all__ = ['Bool', 'X_XF86VidModeQueryVersion', 'X_XF86VidModeGetModeLine',
'X_XF86VidModeModModeLine', 'X_XF86VidModeSwitchMode',
'X_XF86VidModeGetMonitor', 'X_XF86VidModeLockModeSwitch',
'X_XF86VidModeGetAllModeLines', 'X_XF86VidModeAddModeLine',
'X_XF86VidModeDeleteModeLine', 'X_XF86VidModeValidateModeLine',
'X_XF86VidModeSwitchToMode', 'X_XF86VidModeGetViewPort',
'X_XF86VidModeSetViewPort', 'X_XF86VidModeGetDotClocks',
'X_XF86VidModeSetClientVersion', 'X_XF86VidModeSetGamma',
'X_XF86VidModeGetGamma', 'X_XF86VidModeGetGammaRamp',
'X_XF86VidModeSetGammaRamp', 'X_XF86VidModeGetGammaRampSize',
'X_XF86VidModeGetPermissions', 'CLKFLAG_PROGRAMABLE',
'XF86VidModeNumberEvents', 'XF86VidModeBadClock', 'XF86VidModeBadHTimings',
'XF86VidModeBadVTimings', 'XF86VidModeModeUnsuitable',
'XF86VidModeExtensionDisabled', 'XF86VidModeClientNotLocal',
'XF86VidModeZoomLocked', 'XF86VidModeNumberErrors', 'XF86VM_READ_PERMISSION',
'XF86VM_WRITE_PERMISSION', 'XF86VidModeModeLine', 'XF86VidModeModeInfo',
'XF86VidModeSyncRange', 'XF86VidModeMonitor', 'Display', 'Window', 'Time',
'Status', 'XF86VidModeNotifyEvent', 'XF86VidModeGamma',
'XF86VidModeQueryVersion', 'XF86VidModeQueryExtension',
'XF86VidModeSetClientVersion', 'XF86VidModeGetModeLine',
'XF86VidModeGetAllModeLines', 'XF86VidModeAddModeLine',
'XF86VidModeDeleteModeLine', 'XF86VidModeModModeLine',
'XF86VidModeValidateModeLine', 'XF86VidModeSwitchMode',
'XF86VidModeSwitchToMode', 'XF86VidModeLockModeSwitch',
'XF86VidModeGetMonitor', 'XF86VidModeGetViewPort', 'XF86VidModeSetViewPort',
'XF86VidModeGetDotClocks', 'XF86VidModeGetGamma', 'XF86VidModeSetGamma',
'XF86VidModeSetGammaRamp', 'XF86VidModeGetGammaRamp',
'XF86VidModeGetGammaRampSize', 'XF86VidModeGetPermissions']
