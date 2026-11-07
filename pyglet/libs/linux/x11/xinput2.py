"""XInput2 bindings."""
from __future__ import annotations

from ctypes import POINTER, Structure, byref, c_double, c_int, c_ubyte, c_ulong, cast
from typing import TYPE_CHECKING

import pyglet.lib
from pyglet.libs.linux.x11 import xlib

if TYPE_CHECKING:
    from ctypes import Array, _Pointer


XI_ALL_DEVICES = 0
XI_ALL_MASTER_DEVICES = 1
XI_RAW_MOTION = 17
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


class XIRawEvent(Structure):
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
        ('flags', c_int),
        ('valuators', XIValuatorState),
        ('raw_values', POINTER(c_double)),
    ]


try:
    _lib = pyglet.lib.load_library('Xi')
    XIQueryVersion = _lib.XIQueryVersion
    XISelectEvents = _lib.XISelectEvents
except (ImportError, AttributeError):
    _lib = None
else:
    XIQueryVersion.restype = c_int
    XIQueryVersion.argtypes = [POINTER(xlib.Display), POINTER(c_int), POINTER(c_int)]

    XISelectEvents.restype = c_int
    XISelectEvents.argtypes = [POINTER(xlib.Display), xlib.Window, POINTER(XIEventMask), c_int]


def is_available() -> bool:
    """Return whether libXi and its required XI2 entry points could be loaded."""
    return _lib is not None


def touch_event_mask() -> tuple[Array[c_ubyte], XIEventMask]:
    """Create a mask for the three XI2 touch event types."""
    mask_length = (XI_TOUCH_END >> 3) + 1
    mask = (c_ubyte * mask_length)()
    for event_type in (XI_TOUCH_BEGIN, XI_TOUCH_UPDATE, XI_TOUCH_END):
        mask[event_type >> 3] |= 1 << (event_type & 7)
    return mask, XIEventMask(XI_ALL_DEVICES, mask_length, cast(mask, POINTER(c_ubyte)))


def raw_motion_event_mask(enabled: bool) -> tuple[Array[c_ubyte], XIEventMask]:
    """Select raw motion once per master device, or clear that selection."""
    mask_length = (XI_RAW_MOTION >> 3) + 1
    mask = (c_ubyte * mask_length)()
    if enabled:
        mask[XI_RAW_MOTION >> 3] |= 1 << (XI_RAW_MOTION & 7)
    return mask, XIEventMask(XI_ALL_MASTER_DEVICES, mask_length, cast(mask, POINTER(c_ubyte)))


def raw_motion_delta(event: XIRawEvent) -> tuple[float, float]:
    """Decode unaccelerated X/Y valuators, whose values are packed by set bit."""
    dx = dy = 0.0
    if event.valuators.mask_len and event.raw_values:
        axes = event.valuators.mask[0]
        if axes & 1:
            dx = event.raw_values[0]
        if axes & 2:
            dy = event.raw_values[bool(axes & 1)]
    return dx, dy


def get_version(display: _Pointer[xlib.Display]) -> tuple[int, int] | None:
    """Negotiate XI2 and return the supported version, or None on failure."""
    if not is_available():
        return None
    major = c_int(XI_2_MAJOR)
    minor = c_int(XI_2_MINOR)
    if XIQueryVersion(display, byref(major), byref(minor)) != 0:
        return None
    return major.value, minor.value
