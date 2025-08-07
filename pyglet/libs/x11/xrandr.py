import warnings
from ctypes import c_ulong, c_int, POINTER, Structure, c_char_p, c_uint, c_ushort

import pyglet
from pyglet.libs.x11.xlib import (
    Time,
    Window,
    Display,
    XCloseDisplay,
    XDefaultRootWindow,
    XOpenDisplay,
)

lib = None
try:
    lib = pyglet.lib.load_library("Xrandr")
except ImportError:
    if pyglet.options.debug_lib:
        warnings.warn("Xrandr could not be loaded.")
    raise ImportError

RRCrtc      = c_ulong        # typedef XID
RROutput    = c_ulong        # typedef XID
RRMode      = c_ulong        # typedef XID
Connection  = c_ushort       # Connection in Xrandr.h
SubpixelOrder = c_ushort     # SubpixelOrder in Xrandr.h
XRRModeFlags = c_ulong

class XRRModeInfo(Structure):
    _fields_ = [
        ("id",          RRMode),     # mode ID
        ("width",       c_uint),   # horizontal resolution
        ("height",      c_uint),   # vertical resolution
        ("dotClock",    c_ulong),    # pixel clock (in Hz)
        ("hSyncStart",  c_uint),
        ("hSyncEnd",    c_uint),
        ("hTotal",      c_uint),
        ("hSkew",       c_uint),
        ("vSyncStart",  c_uint),
        ("vSyncEnd",    c_uint),
        ("vTotal",      c_uint),
        ("name",        c_char_p),
        ("nameLength",  c_uint),
        ("modeFlags",   XRRModeFlags),
    ]


class XRRScreenResources(Structure):
    _fields_ = [
        ("timestamp",        Time),
        ("configTimestamp",  Time),
        ("ncrtc",            c_int),
        ("crtcs",            POINTER(RRCrtc)),
        ("noutput",          c_int),
        ("outputs",          POINTER(RROutput)),
        ("nmode",            c_int),
        ("modes",            POINTER(XRRModeInfo)),
    ]


class XRROutputInfo(Structure):
    _fields_ = [
        ("timestamp",      Time),
        ("crtc",           RRCrtc),
        ("name",           c_char_p),
        ("nameLen",        c_int),
        ("mm_width",       c_ulong),
        ("mm_height",      c_ulong),
        ("connection",     Connection),
        ("subpixel_order", SubpixelOrder),
        ("ncrtc",          c_int),
        ("crtcs",          POINTER(RRCrtc)),
        ("nclone",         c_int),
        ("clones",         POINTER(RROutput)),
        ("nmode",          c_int),
        ("npreferred",     c_int),
        ("modes",          POINTER(RRMode)),
    ]

class XRRCrtcInfo(Structure):
    _fields_ = [
        ("timestamp",  Time),
        ("x",          c_int),
        ("y",          c_int),
        ("width",      c_uint),
        ("height",     c_uint),
        ("mode",       RRMode),
        ("rotation",   c_int),
        ("noutput",    c_int),
        ("outputs",    POINTER(RROutput)),
        ("rotations",  c_ushort),
        ("npossible",  c_int),
        ("possible",   POINTER(RROutput)),
    ]


if lib:
    XRRQueryVersion = lib.XRRQueryVersion
    XRRQueryVersion.argtypes = [POINTER(Display), POINTER(c_int), POINTER(c_int)]
    XRRQueryVersion.restype    = c_int

    XRRGetScreenResources = lib.XRRGetScreenResources
    XRRGetScreenResources.argtypes = [POINTER(Display), Window]
    XRRGetScreenResources.restype = POINTER(XRRScreenResources)

    XRRGetOutputPrimary = lib.XRRGetOutputPrimary
    XRRGetOutputPrimary.argtypes = [POINTER(Display), Window]
    XRRGetOutputPrimary.restype = RROutput

    XRRGetScreenResourcesCurrent = lib.XRRGetScreenResourcesCurrent
    XRRGetScreenResourcesCurrent.argtypes = [POINTER(Display), Window]
    XRRGetScreenResourcesCurrent.restype = POINTER(XRRScreenResources)

    XRRFreeScreenResources = lib.XRRFreeScreenResources
    XRRFreeScreenResources.argtypes = [POINTER(XRRScreenResources)]
    XRRFreeScreenResources.restype = None

    XRRGetOutputInfo = lib.XRRGetOutputInfo
    XRRGetOutputInfo.argtypes = [POINTER(Display), POINTER(XRRScreenResources), RROutput]
    XRRGetOutputInfo.restype  = POINTER(XRROutputInfo)

    XRRFreeOutputInfo = lib.XRRFreeOutputInfo
    XRRFreeOutputInfo.argtypes = [POINTER(XRROutputInfo)]
    XRRFreeOutputInfo.restype = None

    XRRGetCrtcInfo = lib.XRRGetCrtcInfo
    XRRGetCrtcInfo.argtypes = [POINTER(Display), POINTER(XRRScreenResources), RRCrtc]
    XRRGetCrtcInfo.restype = POINTER(XRRCrtcInfo)

    XRRSetCrtcConfig = lib.XRRSetCrtcConfig
    XRRSetCrtcConfig.argtypes = argtypes = [POINTER(Display), POINTER(XRRScreenResources), RRCrtc, Time, c_int, c_int, RRMode, c_int,  POINTER(RROutput), c_int]
    XRRSetCrtcConfig.restype = c_int

    XRRFreeCrtcInfo = lib.XRRFreeCrtcInfo
    XRRFreeCrtcInfo.argtypes = [POINTER(XRRCrtcInfo)]
    XRRFreeCrtcInfo.restype    = None

def list_connected_outputs():
    dpy = XOpenDisplay(None)
    if not dpy:
        raise RuntimeError("Cannot open DISPLAY")

    root = XDefaultRootWindow(dpy)
    res_p = XRRGetScreenResources(dpy, root)
    if not res_p:
        XCloseDisplay(dpy)
        raise RuntimeError("Failed to get screen resources")

    res = res_p.contents
    outputs = []
    for i in range(res.noutput):
        out_id = res.outputs[i]
        info_p = XRRGetOutputInfo(dpy, res_p, out_id)
        if info_p:
            info = info_p.contents
            if info.connection == 0:  # Connected.
                outputs.append(info.name.decode())
            XRRFreeOutputInfo(info_p)

    XRRFreeScreenResources(res_p)
    XCloseDisplay(dpy)
    return outputs

if __name__ == "__main__":
    for name in list_connected_outputs():
        print(name)