"""XInput2 bindings."""
from __future__ import annotations

from ctypes import POINTER, Structure, byref, c_double, c_int, c_ubyte, c_ulong, cast, _Pointer

import pyglet.lib
from pyglet.libs.linux.x11 import xlib


_lib = pyglet.lib.load_library('Xi')

XI_ALL_DEVICES = 0
XI_TOUCH_BEGIN = 18
XI_TOUCH_UPDATE = 19
XI_TOUCH_END = 20
XI_2_MAJOR = 2
XI_2_MINOR = 2


class XIEventMask(Structure):
    _fields_ = [
        ('deviceid', c_int),
        ('mask_len', c_int),
        ('mask', POINTER(c_ubyte)),
    ]


class XIButtonState(Structure):
    _fields_ = [
        ('mask_len', c_int),
        ('mask', POINTER(c_ubyte)),
    ]


class XIValuatorState(Structure):
    _fields_ = [
        ('mask_len', c_int),
        ('mask', POINTER(c_ubyte)),
        ('values', POINTER(c_double)),
    ]


class XIModifierState(Structure):
    _fields_ = [
        ('base', c_int),
        ('latched', c_int),
        ('locked', c_int),
        ('effective', c_int),
    ]


class XIGroupState(Structure):
    _fields_ = [
        ('base', c_int),
        ('latched', c_int),
        ('locked', c_int),
        ('effective', c_int),
    ]


class XIDeviceEvent(Structure):
    _fields_ = [
        ('type', c_int),
        ('serial', c_ulong),
        ('send_event', c_int),
        ('display', POINTER(xlib.Display)),
        ('extension', c_int),
        ('evtype', c_int),
        ('time', xlib.Time),
        ('deviceid', c_int),
        ('sourceid', c_int),
        ('detail', c_int),
        ('root', xlib.Window),
        ('event', xlib.Window),
        ('child', xlib.Window),
        ('root_x', c_double),
        ('root_y', c_double),
        ('event_x', c_double),
        ('event_y', c_double),
        ('flags', c_int),
        ('buttons', XIButtonState),
        ('valuators', XIValuatorState),
        ('mods', XIModifierState),
        ('group', XIGroupState),
    ]


XIQueryVersion = _lib.XIQueryVersion
XIQueryVersion.restype = c_int
XIQueryVersion.argtypes = [POINTER(xlib.Display), POINTER(c_int), POINTER(c_int)]

XISelectEvents = _lib.XISelectEvents
XISelectEvents.restype = c_int
XISelectEvents.argtypes = [POINTER(xlib.Display), xlib.Window, POINTER(XIEventMask), c_int]


def touch_event_mask() -> tuple[object, XIEventMask]:
    """Create a mask for the three XI2 touch event types."""
    mask_length = (XI_TOUCH_END >> 3) + 1
    mask = (c_ubyte * mask_length)()
    for event_type in (XI_TOUCH_BEGIN, XI_TOUCH_UPDATE, XI_TOUCH_END):
        mask[event_type >> 3] |= 1 << (event_type & 7)
    return mask, XIEventMask(XI_ALL_DEVICES, mask_length, cast(mask, POINTER(c_ubyte)))


def query_version(display: _Pointer[xlib.Display]) -> bool:
    """Return whether the X server supports XInput 2.2 touch events."""
    major = c_int(XI_2_MAJOR)
    minor = c_int(XI_2_MINOR)
    return XIQueryVersion(display, byref(major), byref(minor)) == 0 and (major.value, minor.value) >= (2, 2)
