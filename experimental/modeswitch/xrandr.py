#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes

import pyglet
from pyglet.window.xlib import xlib

import lib_xrandr as xrandr

def _check_extension(display):
    major_opcode = ctypes.c_int()
    first_event = ctypes.c_int()
    first_error = ctypes.c_int()
    xlib.XQueryExtension(display._display, 'RANDR', 
        ctypes.byref(major_opcode), 
        ctypes.byref(first_event),
        ctypes.byref(first_error))
    if not major_opcode.value:
        raise Exception('RANDR extension not available')

def _check_version(display):
    major = ctypes.c_int()
    minor = ctypes.c_int()
    xrandr.XRRQueryVersion(display._display, 
                           ctypes.byref(major), ctypes.byref(minor))
    if major.value < 1 or minor.value < 2:
        raise Exception('Server does not support RandR 1.2')
    return '%d.%d' % (major.value, minor.value)

display = pyglet.window.get_platform().get_default_display()
_check_extension(display)
_check_version(display)

_display = display._display
root_windows = set()
for screen in display.get_screens():
    x_screen = xlib.XScreenOfDisplay(_display, screen._x_screen_id)
    root_window = xlib.XRootWindowOfScreen(x_screen)
    root_windows.add(root_window)

for root_window in root_windows:
    resources_p = xrandr.XRRGetScreenResources(_display, root_window)
    resources = resources_p.contents
    print 'CRTCs:'
    for i in range(resources.ncrtc):
        info = xrandr.XRRGetCrtcInfo(_display, resources_p, resources.crtcs[i])
        info = info.contents
        print '  %dx%d @ %d,%d' % (info.width, info.height, info.x, info.y)

    print 'Modes:'
    for i in range(resources.nmode):
        info = resources.modes[i]
        print '  (%d) %dx%d "%s"' % (info.id, 
            info.width, info.height, info.name)

# Set CRTC 0 to mode 1 without changing outputs
info = xrandr.XRRGetCrtcInfo(_display, resources_p, resources.crtcs[0])
info = info.contents

xrandr.XRRSetCrtcConfig(_display, resources_p, resources.crtcs[0], 
    info.timestamp, info.x, info.y, resources.modes[0].id,
    info.rotation, info.outputs, info.noutput)
