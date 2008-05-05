'''Wrapper for Xrandr

Generated with:
tools/genwrappers.py xrandr

Do not modify this file.
'''

__docformat__ =  'restructuredtext'
__version__ = '$Id$'

import ctypes
from ctypes import *

import pyglet.lib

_lib = pyglet.lib.load_library('Xrandr')

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


import pyglet.window.xlib.xlib

Rotation = c_ushort 	# /usr/include/X11/extensions/randr.h:31
SizeID = c_ushort 	# /usr/include/X11/extensions/randr.h:32
SubpixelOrder = c_ushort 	# /usr/include/X11/extensions/randr.h:33
Connection = c_ushort 	# /usr/include/X11/extensions/randr.h:34
XRandrRotation = c_ushort 	# /usr/include/X11/extensions/randr.h:35
XRandrSizeID = c_ushort 	# /usr/include/X11/extensions/randr.h:36
XRandrSubpixelOrder = c_ushort 	# /usr/include/X11/extensions/randr.h:37
XRandrModeFlags = c_ulong 	# /usr/include/X11/extensions/randr.h:38
RANDR_MAJOR = 1 	# /usr/include/X11/extensions/randr.h:41
RANDR_MINOR = 2 	# /usr/include/X11/extensions/randr.h:42
RRNumberErrors = 3 	# /usr/include/X11/extensions/randr.h:44
RRNumberEvents = 2 	# /usr/include/X11/extensions/randr.h:45
RRNumberRequests = 25 	# /usr/include/X11/extensions/randr.h:46
X_RRQueryVersion = 0 	# /usr/include/X11/extensions/randr.h:48
X_RROldGetScreenInfo = 1 	# /usr/include/X11/extensions/randr.h:50
X_RR1_0SetScreenConfig = 2 	# /usr/include/X11/extensions/randr.h:51
X_RRSetScreenConfig = 2 	# /usr/include/X11/extensions/randr.h:53
X_RROldScreenChangeSelectInput = 3 	# /usr/include/X11/extensions/randr.h:54
X_RRSelectInput = 4 	# /usr/include/X11/extensions/randr.h:56
X_RRGetScreenInfo = 5 	# /usr/include/X11/extensions/randr.h:57
X_RRGetScreenSizeRange = 6 	# /usr/include/X11/extensions/randr.h:60
X_RRSetScreenSize = 7 	# /usr/include/X11/extensions/randr.h:61
X_RRGetScreenResources = 8 	# /usr/include/X11/extensions/randr.h:62
X_RRGetOutputInfo = 9 	# /usr/include/X11/extensions/randr.h:63
X_RRListOutputProperties = 10 	# /usr/include/X11/extensions/randr.h:64
X_RRQueryOutputProperty = 11 	# /usr/include/X11/extensions/randr.h:65
X_RRConfigureOutputProperty = 12 	# /usr/include/X11/extensions/randr.h:66
X_RRChangeOutputProperty = 13 	# /usr/include/X11/extensions/randr.h:67
X_RRDeleteOutputProperty = 14 	# /usr/include/X11/extensions/randr.h:68
X_RRGetOutputProperty = 15 	# /usr/include/X11/extensions/randr.h:69
X_RRCreateMode = 16 	# /usr/include/X11/extensions/randr.h:70
X_RRDestroyMode = 17 	# /usr/include/X11/extensions/randr.h:71
X_RRAddOutputMode = 18 	# /usr/include/X11/extensions/randr.h:72
X_RRDeleteOutputMode = 19 	# /usr/include/X11/extensions/randr.h:73
X_RRGetCrtcInfo = 20 	# /usr/include/X11/extensions/randr.h:74
X_RRSetCrtcConfig = 21 	# /usr/include/X11/extensions/randr.h:75
X_RRGetCrtcGammaSize = 22 	# /usr/include/X11/extensions/randr.h:76
X_RRGetCrtcGamma = 23 	# /usr/include/X11/extensions/randr.h:77
X_RRSetCrtcGamma = 24 	# /usr/include/X11/extensions/randr.h:78
RRScreenChangeNotifyMask = 1 	# /usr/include/X11/extensions/randr.h:81
RRCrtcChangeNotifyMask = 2 	# /usr/include/X11/extensions/randr.h:83
RROutputChangeNotifyMask = 4 	# /usr/include/X11/extensions/randr.h:84
RROutputPropertyNotifyMask = 8 	# /usr/include/X11/extensions/randr.h:85
RRScreenChangeNotify = 0 	# /usr/include/X11/extensions/randr.h:88
RRNotify = 1 	# /usr/include/X11/extensions/randr.h:90
RRNotify_CrtcChange = 0 	# /usr/include/X11/extensions/randr.h:92
RRNotify_OutputChange = 1 	# /usr/include/X11/extensions/randr.h:93
RRNotify_OutputProperty = 2 	# /usr/include/X11/extensions/randr.h:94
RR_Rotate_0 = 1 	# /usr/include/X11/extensions/randr.h:97
RR_Rotate_90 = 2 	# /usr/include/X11/extensions/randr.h:98
RR_Rotate_180 = 4 	# /usr/include/X11/extensions/randr.h:99
RR_Rotate_270 = 8 	# /usr/include/X11/extensions/randr.h:100
RR_Reflect_X = 16 	# /usr/include/X11/extensions/randr.h:104
RR_Reflect_Y = 32 	# /usr/include/X11/extensions/randr.h:105
RRSetConfigSuccess = 0 	# /usr/include/X11/extensions/randr.h:107
RRSetConfigInvalidConfigTime = 1 	# /usr/include/X11/extensions/randr.h:108
RRSetConfigInvalidTime = 2 	# /usr/include/X11/extensions/randr.h:109
RRSetConfigFailed = 3 	# /usr/include/X11/extensions/randr.h:110
RR_HSyncPositive = 1 	# /usr/include/X11/extensions/randr.h:114
RR_HSyncNegative = 2 	# /usr/include/X11/extensions/randr.h:115
RR_VSyncPositive = 4 	# /usr/include/X11/extensions/randr.h:116
RR_VSyncNegative = 8 	# /usr/include/X11/extensions/randr.h:117
RR_Interlace = 16 	# /usr/include/X11/extensions/randr.h:118
RR_DoubleScan = 32 	# /usr/include/X11/extensions/randr.h:119
RR_CSync = 64 	# /usr/include/X11/extensions/randr.h:120
RR_CSyncPositive = 128 	# /usr/include/X11/extensions/randr.h:121
RR_CSyncNegative = 256 	# /usr/include/X11/extensions/randr.h:122
RR_HSkewPresent = 512 	# /usr/include/X11/extensions/randr.h:123
RR_BCast = 1024 	# /usr/include/X11/extensions/randr.h:124
RR_PixelMultiplex = 2048 	# /usr/include/X11/extensions/randr.h:125
RR_DoubleClock = 4096 	# /usr/include/X11/extensions/randr.h:126
RR_ClockDivideBy2 = 8192 	# /usr/include/X11/extensions/randr.h:127
RR_Connected = 0 	# /usr/include/X11/extensions/randr.h:129
RR_Disconnected = 1 	# /usr/include/X11/extensions/randr.h:130
RR_UnknownConnection = 2 	# /usr/include/X11/extensions/randr.h:131
BadRROutput = 0 	# /usr/include/X11/extensions/randr.h:133
BadRRCrtc = 1 	# /usr/include/X11/extensions/randr.h:134
BadRRMode = 2 	# /usr/include/X11/extensions/randr.h:135
XID = pyglet.window.xlib.xlib.XID
RROutput = XID 	# /usr/include/X11/extensions/Xrandr.h:4876
RRCrtc = XID 	# /usr/include/X11/extensions/Xrandr.h:4877
RRMode = XID 	# /usr/include/X11/extensions/Xrandr.h:4878
class struct_anon_93(Structure):
    __slots__ = [
        'width',
        'height',
        'mwidth',
        'mheight',
    ]
struct_anon_93._fields_ = [
    ('width', c_int),
    ('height', c_int),
    ('mwidth', c_int),
    ('mheight', c_int),
]

XRRScreenSize = struct_anon_93 	# /usr/include/X11/extensions/Xrandr.h:4883
class struct_anon_94(Structure):
    __slots__ = [
        'type',
        'serial',
        'send_event',
        'display',
        'window',
        'root',
        'timestamp',
        'config_timestamp',
        'size_index',
        'subpixel_order',
        'rotation',
        'width',
        'height',
        'mwidth',
        'mheight',
    ]
Display = pyglet.window.xlib.xlib.Display
Window = pyglet.window.xlib.xlib.Window
Time = pyglet.window.xlib.xlib.Time
struct_anon_94._fields_ = [
    ('type', c_int),
    ('serial', c_ulong),
    ('send_event', c_int),
    ('display', POINTER(Display)),
    ('window', Window),
    ('root', Window),
    ('timestamp', Time),
    ('config_timestamp', Time),
    ('size_index', SizeID),
    ('subpixel_order', SubpixelOrder),
    ('rotation', Rotation),
    ('width', c_int),
    ('height', c_int),
    ('mwidth', c_int),
    ('mheight', c_int),
]

XRRScreenChangeNotifyEvent = struct_anon_94 	# /usr/include/X11/extensions/Xrandr.h:4905
class struct_anon_95(Structure):
    __slots__ = [
        'type',
        'serial',
        'send_event',
        'display',
        'window',
        'subtype',
    ]
struct_anon_95._fields_ = [
    ('type', c_int),
    ('serial', c_ulong),
    ('send_event', c_int),
    ('display', POINTER(Display)),
    ('window', Window),
    ('subtype', c_int),
]

XRRNotifyEvent = struct_anon_95 	# /usr/include/X11/extensions/Xrandr.h:4914
class struct_anon_96(Structure):
    __slots__ = [
        'type',
        'serial',
        'send_event',
        'display',
        'window',
        'subtype',
        'output',
        'crtc',
        'mode',
        'rotation',
        'connection',
        'subpixel_order',
    ]
struct_anon_96._fields_ = [
    ('type', c_int),
    ('serial', c_ulong),
    ('send_event', c_int),
    ('display', POINTER(Display)),
    ('window', Window),
    ('subtype', c_int),
    ('output', RROutput),
    ('crtc', RRCrtc),
    ('mode', RRMode),
    ('rotation', Rotation),
    ('connection', Connection),
    ('subpixel_order', SubpixelOrder),
]

XRROutputChangeNotifyEvent = struct_anon_96 	# /usr/include/X11/extensions/Xrandr.h:4929
class struct_anon_97(Structure):
    __slots__ = [
        'type',
        'serial',
        'send_event',
        'display',
        'window',
        'subtype',
        'crtc',
        'mode',
        'rotation',
        'x',
        'y',
        'width',
        'height',
    ]
struct_anon_97._fields_ = [
    ('type', c_int),
    ('serial', c_ulong),
    ('send_event', c_int),
    ('display', POINTER(Display)),
    ('window', Window),
    ('subtype', c_int),
    ('crtc', RRCrtc),
    ('mode', RRMode),
    ('rotation', Rotation),
    ('x', c_int),
    ('y', c_int),
    ('width', c_uint),
    ('height', c_uint),
]

XRRCrtcChangeNotifyEvent = struct_anon_97 	# /usr/include/X11/extensions/Xrandr.h:4943
class struct_anon_98(Structure):
    __slots__ = [
        'type',
        'serial',
        'send_event',
        'display',
        'window',
        'subtype',
        'output',
        'property',
        'timestamp',
        'state',
    ]
Atom = pyglet.window.xlib.xlib.Atom
struct_anon_98._fields_ = [
    ('type', c_int),
    ('serial', c_ulong),
    ('send_event', c_int),
    ('display', POINTER(Display)),
    ('window', Window),
    ('subtype', c_int),
    ('output', RROutput),
    ('property', Atom),
    ('timestamp', Time),
    ('state', c_int),
]

XRROutputPropertyNotifyEvent = struct_anon_98 	# /usr/include/X11/extensions/Xrandr.h:4956
class struct__XRRScreenConfiguration(Structure):
    __slots__ = [
    ]
struct__XRRScreenConfiguration._fields_ = [
    ('_opaque_struct', c_int)
]

class struct__XRRScreenConfiguration(Structure):
    __slots__ = [
    ]
struct__XRRScreenConfiguration._fields_ = [
    ('_opaque_struct', c_int)
]

XRRScreenConfiguration = struct__XRRScreenConfiguration 	# /usr/include/X11/extensions/Xrandr.h:4959
# /usr/include/X11/extensions/Xrandr.h:4961
XRRQueryExtension = _lib.XRRQueryExtension
XRRQueryExtension.restype = c_int
XRRQueryExtension.argtypes = [POINTER(Display), POINTER(c_int), POINTER(c_int)]

# /usr/include/X11/extensions/Xrandr.h:4962
XRRQueryVersion = _lib.XRRQueryVersion
XRRQueryVersion.restype = c_int
XRRQueryVersion.argtypes = [POINTER(Display), POINTER(c_int), POINTER(c_int)]

# /usr/include/X11/extensions/Xrandr.h:4966
XRRGetScreenInfo = _lib.XRRGetScreenInfo
XRRGetScreenInfo.restype = POINTER(XRRScreenConfiguration)
XRRGetScreenInfo.argtypes = [POINTER(Display), Window]

# /usr/include/X11/extensions/Xrandr.h:4969
XRRFreeScreenConfigInfo = _lib.XRRFreeScreenConfigInfo
XRRFreeScreenConfigInfo.restype = None
XRRFreeScreenConfigInfo.argtypes = [POINTER(XRRScreenConfiguration)]

Drawable = pyglet.window.xlib.xlib.Drawable
# /usr/include/X11/extensions/Xrandr.h:4978
XRRSetScreenConfig = _lib.XRRSetScreenConfig
XRRSetScreenConfig.restype = c_int
XRRSetScreenConfig.argtypes = [POINTER(Display), POINTER(XRRScreenConfiguration), Drawable, c_int, Rotation, Time]

# /usr/include/X11/extensions/Xrandr.h:4986
XRRSetScreenConfigAndRate = _lib.XRRSetScreenConfigAndRate
XRRSetScreenConfigAndRate.restype = c_int
XRRSetScreenConfigAndRate.argtypes = [POINTER(Display), POINTER(XRRScreenConfiguration), Drawable, c_int, Rotation, c_short, Time]

# /usr/include/X11/extensions/Xrandr.h:4995
XRRConfigRotations = _lib.XRRConfigRotations
XRRConfigRotations.restype = Rotation
XRRConfigRotations.argtypes = [POINTER(XRRScreenConfiguration), POINTER(Rotation)]

# /usr/include/X11/extensions/Xrandr.h:4997
XRRConfigTimes = _lib.XRRConfigTimes
XRRConfigTimes.restype = Time
XRRConfigTimes.argtypes = [POINTER(XRRScreenConfiguration), POINTER(Time)]

# /usr/include/X11/extensions/Xrandr.h:4999
XRRConfigSizes = _lib.XRRConfigSizes
XRRConfigSizes.restype = POINTER(XRRScreenSize)
XRRConfigSizes.argtypes = [POINTER(XRRScreenConfiguration), POINTER(c_int)]

# /usr/include/X11/extensions/Xrandr.h:5001
XRRConfigRates = _lib.XRRConfigRates
XRRConfigRates.restype = POINTER(c_short)
XRRConfigRates.argtypes = [POINTER(XRRScreenConfiguration), c_int, POINTER(c_int)]

# /usr/include/X11/extensions/Xrandr.h:5003
XRRConfigCurrentConfiguration = _lib.XRRConfigCurrentConfiguration
XRRConfigCurrentConfiguration.restype = SizeID
XRRConfigCurrentConfiguration.argtypes = [POINTER(XRRScreenConfiguration), POINTER(Rotation)]

# /usr/include/X11/extensions/Xrandr.h:5006
XRRConfigCurrentRate = _lib.XRRConfigCurrentRate
XRRConfigCurrentRate.restype = c_short
XRRConfigCurrentRate.argtypes = [POINTER(XRRScreenConfiguration)]

# /usr/include/X11/extensions/Xrandr.h:5008
XRRRootToScreen = _lib.XRRRootToScreen
XRRRootToScreen.restype = c_int
XRRRootToScreen.argtypes = [POINTER(Display), Window]

'''
# XXX HACK these functions don't exist in my libXrandr.so, are marked
# RandR version 0.1
#
# /usr/include/X11/extensions/Xrandr.h:5019
XRRScreenConfig = _lib.XRRScreenConfig
XRRScreenConfig.restype = POINTER(XRRScreenConfiguration)
XRRScreenConfig.argtypes = [POINTER(Display), c_int]

Screen = pyglet.window.xlib.xlib.Screen
# /usr/include/X11/extensions/Xrandr.h:5020
XRRConfig = _lib.XRRConfig
XRRConfig.restype = POINTER(XRRScreenConfiguration)
XRRConfig.argtypes = [POINTER(Screen)]
'''

# /usr/include/X11/extensions/Xrandr.h:5021
XRRSelectInput = _lib.XRRSelectInput
XRRSelectInput.restype = None
XRRSelectInput.argtypes = [POINTER(Display), Window, c_int]

# /usr/include/X11/extensions/Xrandr.h:5029
XRRRotations = _lib.XRRRotations
XRRRotations.restype = Rotation
XRRRotations.argtypes = [POINTER(Display), c_int, POINTER(Rotation)]

# /usr/include/X11/extensions/Xrandr.h:5030
XRRSizes = _lib.XRRSizes
XRRSizes.restype = POINTER(XRRScreenSize)
XRRSizes.argtypes = [POINTER(Display), c_int, POINTER(c_int)]

# /usr/include/X11/extensions/Xrandr.h:5031
XRRRates = _lib.XRRRates
XRRRates.restype = POINTER(c_short)
XRRRates.argtypes = [POINTER(Display), c_int, c_int, POINTER(c_int)]

# /usr/include/X11/extensions/Xrandr.h:5032
XRRTimes = _lib.XRRTimes
XRRTimes.restype = Time
XRRTimes.argtypes = [POINTER(Display), c_int, POINTER(Time)]

# /usr/include/X11/extensions/Xrandr.h:5038
XRRGetScreenSizeRange = _lib.XRRGetScreenSizeRange
XRRGetScreenSizeRange.restype = c_int
XRRGetScreenSizeRange.argtypes = [POINTER(Display), Window, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# /usr/include/X11/extensions/Xrandr.h:5043
XRRSetScreenSize = _lib.XRRSetScreenSize
XRRSetScreenSize.restype = None
XRRSetScreenSize.argtypes = [POINTER(Display), Window, c_int, c_int, c_int, c_int]

XRRModeFlags = c_ulong 	# /usr/include/X11/extensions/Xrandr.h:5047
class struct__XRRModeInfo(Structure):
    __slots__ = [
        'id',
        'width',
        'height',
        'dotClock',
        'hSyncStart',
        'hSyncEnd',
        'hTotal',
        'hSkew',
        'vSyncStart',
        'vSyncEnd',
        'vTotal',
        'name',
        'nameLength',
        'modeFlags',
    ]
struct__XRRModeInfo._fields_ = [
    ('id', RRMode),
    ('width', c_uint),
    ('height', c_uint),
    ('dotClock', c_ulong),
    ('hSyncStart', c_uint),
    ('hSyncEnd', c_uint),
    ('hTotal', c_uint),
    ('hSkew', c_uint),
    ('vSyncStart', c_uint),
    ('vSyncEnd', c_uint),
    ('vTotal', c_uint),
    ('name', c_char_p),
    ('nameLength', c_uint),
    ('modeFlags', XRRModeFlags),
]

XRRModeInfo = struct__XRRModeInfo 	# /usr/include/X11/extensions/Xrandr.h:5064
class struct__XRRScreenResources(Structure):
    __slots__ = [
        'timestamp',
        'configTimestamp',
        'ncrtc',
        'crtcs',
        'noutput',
        'outputs',
        'nmode',
        'modes',
    ]
struct__XRRScreenResources._fields_ = [
    ('timestamp', Time),
    ('configTimestamp', Time),
    ('ncrtc', c_int),
    ('crtcs', POINTER(RRCrtc)),
    ('noutput', c_int),
    ('outputs', POINTER(RROutput)),
    ('nmode', c_int),
    ('modes', POINTER(XRRModeInfo)),
]

XRRScreenResources = struct__XRRScreenResources 	# /usr/include/X11/extensions/Xrandr.h:5075
# /usr/include/X11/extensions/Xrandr.h:5077
XRRGetScreenResources = _lib.XRRGetScreenResources
XRRGetScreenResources.restype = POINTER(XRRScreenResources)
XRRGetScreenResources.argtypes = [POINTER(Display), Window]

# /usr/include/X11/extensions/Xrandr.h:5081
XRRFreeScreenResources = _lib.XRRFreeScreenResources
XRRFreeScreenResources.restype = None
XRRFreeScreenResources.argtypes = [POINTER(XRRScreenResources)]

class struct__XRROutputInfo(Structure):
    __slots__ = [
        'timestamp',
        'crtc',
        'name',
        'nameLen',
        'mm_width',
        'mm_height',
        'connection',
        'subpixel_order',
        'ncrtc',
        'crtcs',
        'nclone',
        'clones',
        'nmode',
        'npreferred',
        'modes',
    ]
struct__XRROutputInfo._fields_ = [
    ('timestamp', Time),
    ('crtc', RRCrtc),
    ('name', c_char_p),
    ('nameLen', c_int),
    ('mm_width', c_ulong),
    ('mm_height', c_ulong),
    ('connection', Connection),
    ('subpixel_order', SubpixelOrder),
    ('ncrtc', c_int),
    ('crtcs', POINTER(RRCrtc)),
    ('nclone', c_int),
    ('clones', POINTER(RROutput)),
    ('nmode', c_int),
    ('npreferred', c_int),
    ('modes', POINTER(RRMode)),
]

XRROutputInfo = struct__XRROutputInfo 	# /usr/include/X11/extensions/Xrandr.h:5099
# /usr/include/X11/extensions/Xrandr.h:5101
XRRGetOutputInfo = _lib.XRRGetOutputInfo
XRRGetOutputInfo.restype = POINTER(XRROutputInfo)
XRRGetOutputInfo.argtypes = [POINTER(Display), POINTER(XRRScreenResources), RROutput]

# /usr/include/X11/extensions/Xrandr.h:5105
XRRFreeOutputInfo = _lib.XRRFreeOutputInfo
XRRFreeOutputInfo.restype = None
XRRFreeOutputInfo.argtypes = [POINTER(XRROutputInfo)]

# /usr/include/X11/extensions/Xrandr.h:5107
XRRListOutputProperties = _lib.XRRListOutputProperties
XRRListOutputProperties.restype = POINTER(Atom)
XRRListOutputProperties.argtypes = [POINTER(Display), RROutput, POINTER(c_int)]

class struct_anon_99(Structure):
    __slots__ = [
        'pending',
        'range',
        'immutable',
        'num_values',
        'values',
    ]
struct_anon_99._fields_ = [
    ('pending', c_int),
    ('range', c_int),
    ('immutable', c_int),
    ('num_values', c_int),
    ('values', POINTER(c_long)),
]

XRRPropertyInfo = struct_anon_99 	# /usr/include/X11/extensions/Xrandr.h:5116
# /usr/include/X11/extensions/Xrandr.h:5118
XRRQueryOutputProperty = _lib.XRRQueryOutputProperty
XRRQueryOutputProperty.restype = POINTER(XRRPropertyInfo)
XRRQueryOutputProperty.argtypes = [POINTER(Display), RROutput, Atom]

# /usr/include/X11/extensions/Xrandr.h:5122
XRRConfigureOutputProperty = _lib.XRRConfigureOutputProperty
XRRConfigureOutputProperty.restype = None
XRRConfigureOutputProperty.argtypes = [POINTER(Display), RROutput, Atom, c_int, c_int, c_int, POINTER(c_long)]

# /usr/include/X11/extensions/Xrandr.h:5127
XRRChangeOutputProperty = _lib.XRRChangeOutputProperty
XRRChangeOutputProperty.restype = None
XRRChangeOutputProperty.argtypes = [POINTER(Display), RROutput, Atom, Atom, c_int, c_int, POINTER(c_ubyte), c_int]

# /usr/include/X11/extensions/Xrandr.h:5133
XRRDeleteOutputProperty = _lib.XRRDeleteOutputProperty
XRRDeleteOutputProperty.restype = None
XRRDeleteOutputProperty.argtypes = [POINTER(Display), RROutput, Atom]

# /usr/include/X11/extensions/Xrandr.h:5136
XRRGetOutputProperty = _lib.XRRGetOutputProperty
XRRGetOutputProperty.restype = c_int
XRRGetOutputProperty.argtypes = [POINTER(Display), RROutput, Atom, c_long, c_long, c_int, c_int, Atom, POINTER(Atom), POINTER(c_int), POINTER(c_ulong), POINTER(c_ulong), POINTER(POINTER(c_ubyte))]

# /usr/include/X11/extensions/Xrandr.h:5143
XRRAllocModeInfo = _lib.XRRAllocModeInfo
XRRAllocModeInfo.restype = POINTER(XRRModeInfo)
XRRAllocModeInfo.argtypes = [c_char_p, c_int]

# /usr/include/X11/extensions/Xrandr.h:5147
XRRCreateMode = _lib.XRRCreateMode
XRRCreateMode.restype = RRMode
XRRCreateMode.argtypes = [POINTER(Display), Window, POINTER(XRRModeInfo)]

# /usr/include/X11/extensions/Xrandr.h:5150
XRRDestroyMode = _lib.XRRDestroyMode
XRRDestroyMode.restype = None
XRRDestroyMode.argtypes = [POINTER(Display), RRMode]

# /usr/include/X11/extensions/Xrandr.h:5153
XRRAddOutputMode = _lib.XRRAddOutputMode
XRRAddOutputMode.restype = None
XRRAddOutputMode.argtypes = [POINTER(Display), RROutput, RRMode]

# /usr/include/X11/extensions/Xrandr.h:5156
XRRDeleteOutputMode = _lib.XRRDeleteOutputMode
XRRDeleteOutputMode.restype = None
XRRDeleteOutputMode.argtypes = [POINTER(Display), RROutput, RRMode]

# /usr/include/X11/extensions/Xrandr.h:5159
XRRFreeModeInfo = _lib.XRRFreeModeInfo
XRRFreeModeInfo.restype = None
XRRFreeModeInfo.argtypes = [POINTER(XRRModeInfo)]

class struct__XRRCrtcInfo(Structure):
    __slots__ = [
        'timestamp',
        'x',
        'y',
        'width',
        'height',
        'mode',
        'rotation',
        'noutput',
        'outputs',
        'rotations',
        'npossible',
        'possible',
    ]
struct__XRRCrtcInfo._fields_ = [
    ('timestamp', Time),
    ('x', c_int),
    ('y', c_int),
    ('width', c_uint),
    ('height', c_uint),
    ('mode', RRMode),
    ('rotation', Rotation),
    ('noutput', c_int),
    ('outputs', POINTER(RROutput)),
    ('rotations', Rotation),
    ('npossible', c_int),
    ('possible', POINTER(RROutput)),
]

XRRCrtcInfo = struct__XRRCrtcInfo 	# /usr/include/X11/extensions/Xrandr.h:5172
# /usr/include/X11/extensions/Xrandr.h:5174
XRRGetCrtcInfo = _lib.XRRGetCrtcInfo
XRRGetCrtcInfo.restype = POINTER(XRRCrtcInfo)
XRRGetCrtcInfo.argtypes = [POINTER(Display), POINTER(XRRScreenResources), RRCrtc]

# /usr/include/X11/extensions/Xrandr.h:5178
XRRFreeCrtcInfo = _lib.XRRFreeCrtcInfo
XRRFreeCrtcInfo.restype = None
XRRFreeCrtcInfo.argtypes = [POINTER(XRRCrtcInfo)]

# /usr/include/X11/extensions/Xrandr.h:5181
XRRSetCrtcConfig = _lib.XRRSetCrtcConfig
XRRSetCrtcConfig.restype = c_int
XRRSetCrtcConfig.argtypes = [POINTER(Display), POINTER(XRRScreenResources), RRCrtc, Time, c_int, c_int, RRMode, Rotation, POINTER(RROutput), c_int]

# /usr/include/X11/extensions/Xrandr.h:5192
XRRGetCrtcGammaSize = _lib.XRRGetCrtcGammaSize
XRRGetCrtcGammaSize.restype = c_int
XRRGetCrtcGammaSize.argtypes = [POINTER(Display), RRCrtc]

class struct__XRRCrtcGamma(Structure):
    __slots__ = [
        'size',
        'red',
        'green',
        'blue',
    ]
struct__XRRCrtcGamma._fields_ = [
    ('size', c_int),
    ('red', POINTER(c_ushort)),
    ('green', POINTER(c_ushort)),
    ('blue', POINTER(c_ushort)),
]

XRRCrtcGamma = struct__XRRCrtcGamma 	# /usr/include/X11/extensions/Xrandr.h:5199
# /usr/include/X11/extensions/Xrandr.h:5201
XRRGetCrtcGamma = _lib.XRRGetCrtcGamma
XRRGetCrtcGamma.restype = POINTER(XRRCrtcGamma)
XRRGetCrtcGamma.argtypes = [POINTER(Display), RRCrtc]

# /usr/include/X11/extensions/Xrandr.h:5204
XRRAllocGamma = _lib.XRRAllocGamma
XRRAllocGamma.restype = POINTER(XRRCrtcGamma)
XRRAllocGamma.argtypes = [c_int]

# /usr/include/X11/extensions/Xrandr.h:5208
XRRSetCrtcGamma = _lib.XRRSetCrtcGamma
XRRSetCrtcGamma.restype = None
XRRSetCrtcGamma.argtypes = [POINTER(Display), RRCrtc, POINTER(XRRCrtcGamma)]

# /usr/include/X11/extensions/Xrandr.h:5211
XRRFreeGamma = _lib.XRRFreeGamma
XRRFreeGamma.restype = None
XRRFreeGamma.argtypes = [POINTER(XRRCrtcGamma)]

XEvent = pyglet.window.xlib.xlib.XEvent
# /usr/include/X11/extensions/Xrandr.h:5218
XRRUpdateConfiguration = _lib.XRRUpdateConfiguration
XRRUpdateConfiguration.restype = c_int
XRRUpdateConfiguration.argtypes = [POINTER(XEvent)]


__all__ = ['Rotation', 'SizeID', 'SubpixelOrder', 'Connection',
'XRandrRotation', 'XRandrSizeID', 'XRandrSubpixelOrder', 'XRandrModeFlags',
'RANDR_MAJOR', 'RANDR_MINOR', 'RRNumberErrors', 'RRNumberEvents',
'RRNumberRequests', 'X_RRQueryVersion', 'X_RROldGetScreenInfo',
'X_RR1_0SetScreenConfig', 'X_RRSetScreenConfig',
'X_RROldScreenChangeSelectInput', 'X_RRSelectInput', 'X_RRGetScreenInfo',
'X_RRGetScreenSizeRange', 'X_RRSetScreenSize', 'X_RRGetScreenResources',
'X_RRGetOutputInfo', 'X_RRListOutputProperties', 'X_RRQueryOutputProperty',
'X_RRConfigureOutputProperty', 'X_RRChangeOutputProperty',
'X_RRDeleteOutputProperty', 'X_RRGetOutputProperty', 'X_RRCreateMode',
'X_RRDestroyMode', 'X_RRAddOutputMode', 'X_RRDeleteOutputMode',
'X_RRGetCrtcInfo', 'X_RRSetCrtcConfig', 'X_RRGetCrtcGammaSize',
'X_RRGetCrtcGamma', 'X_RRSetCrtcGamma', 'RRScreenChangeNotifyMask',
'RRCrtcChangeNotifyMask', 'RROutputChangeNotifyMask',
'RROutputPropertyNotifyMask', 'RRScreenChangeNotify', 'RRNotify',
'RRNotify_CrtcChange', 'RRNotify_OutputChange', 'RRNotify_OutputProperty',
'RR_Rotate_0', 'RR_Rotate_90', 'RR_Rotate_180', 'RR_Rotate_270',
'RR_Reflect_X', 'RR_Reflect_Y', 'RRSetConfigSuccess',
'RRSetConfigInvalidConfigTime', 'RRSetConfigInvalidTime', 'RRSetConfigFailed',
'RR_HSyncPositive', 'RR_HSyncNegative', 'RR_VSyncPositive',
'RR_VSyncNegative', 'RR_Interlace', 'RR_DoubleScan', 'RR_CSync',
'RR_CSyncPositive', 'RR_CSyncNegative', 'RR_HSkewPresent', 'RR_BCast',
'RR_PixelMultiplex', 'RR_DoubleClock', 'RR_ClockDivideBy2', 'RR_Connected',
'RR_Disconnected', 'RR_UnknownConnection', 'BadRROutput', 'BadRRCrtc',
'BadRRMode', 'RROutput', 'RRCrtc', 'RRMode', 'XRRScreenSize',
'XRRScreenChangeNotifyEvent', 'XRRNotifyEvent', 'XRROutputChangeNotifyEvent',
'XRRCrtcChangeNotifyEvent', 'XRROutputPropertyNotifyEvent',
'XRRScreenConfiguration', 'XRRQueryExtension', 'XRRQueryVersion',
'XRRGetScreenInfo', 'XRRFreeScreenConfigInfo', 'XRRSetScreenConfig',
'XRRSetScreenConfigAndRate', 'XRRConfigRotations', 'XRRConfigTimes',
'XRRConfigSizes', 'XRRConfigRates', 'XRRConfigCurrentConfiguration',
'XRRConfigCurrentRate', 'XRRRootToScreen', 'XRRScreenConfig', 'XRRConfig',
'XRRSelectInput', 'XRRRotations', 'XRRSizes', 'XRRRates', 'XRRTimes',
'XRRGetScreenSizeRange', 'XRRSetScreenSize', 'XRRModeFlags', 'XRRModeInfo',
'XRRScreenResources', 'XRRGetScreenResources', 'XRRFreeScreenResources',
'XRROutputInfo', 'XRRGetOutputInfo', 'XRRFreeOutputInfo',
'XRRListOutputProperties', 'XRRPropertyInfo', 'XRRQueryOutputProperty',
'XRRConfigureOutputProperty', 'XRRChangeOutputProperty',
'XRRDeleteOutputProperty', 'XRRGetOutputProperty', 'XRRAllocModeInfo',
'XRRCreateMode', 'XRRDestroyMode', 'XRRAddOutputMode', 'XRRDeleteOutputMode',
'XRRFreeModeInfo', 'XRRCrtcInfo', 'XRRGetCrtcInfo', 'XRRFreeCrtcInfo',
'XRRSetCrtcConfig', 'XRRGetCrtcGammaSize', 'XRRCrtcGamma', 'XRRGetCrtcGamma',
'XRRAllocGamma', 'XRRSetCrtcGamma', 'XRRFreeGamma', 'XRRUpdateConfiguration']
