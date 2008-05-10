#!/usr/bin/python
# $Id:$

import ctypes

import pyglet
from pyglet.window.win32 import _user32
from pyglet.window.win32.constants import *
from pyglet.window.win32.types import *

WCHAR = ctypes.c_wchar
BCHAR = ctypes.c_wchar

class MONITORINFOEX(ctypes.Structure):
    _fields_ = (
        ('cbSize', DWORD),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', DWORD),
        ('szDevice', WCHAR * CCHDEVICENAME)
    )

class DEVMODE(ctypes.Structure):
    _fields_ = (
        ('dmDeviceName', BCHAR * CCHDEVICENAME),
        ('dmSpecVersion', WORD),
        ('dmDriverVersion', WORD),
        ('dmSize', WORD),
        ('dmDriverExtra', WORD),
        ('dmFields', DWORD),
        # Just using largest union member here
        ('dmOrientation', ctypes.c_short),
        ('dmPaperSize', ctypes.c_short),
        ('dmPaperLength', ctypes.c_short),
        ('dmPaperWidth', ctypes.c_short),
        ('dmScale', ctypes.c_short),
        ('dmCopies', ctypes.c_short),
        ('dmDefaultSource', ctypes.c_short),
        ('dmPrintQuality', ctypes.c_short),
        # End union
        ('dmColor', ctypes.c_short),
        ('dmDuplex', ctypes.c_short),
        ('dmYResolution', ctypes.c_short),
        ('dmTTOption', ctypes.c_short),
        ('dmCollate', ctypes.c_short),
        ('dmFormName', BCHAR * CCHFORMNAME),
        ('dmLogPixels', WORD),
        ('dmBitsPerPel', DWORD),
        ('dmPelsWidth', DWORD),
        ('dmPelsHeight', DWORD),
        ('dmDisplayFlags', DWORD), # union with dmNup
        ('dmDisplayFrequency', DWORD),
        ('dmICMMethod', DWORD),
        ('dmICMIntent', DWORD),
        ('dmDitherType', DWORD),
        ('dmReserved1', DWORD),
        ('dmReserved2', DWORD),
        ('dmPanningWidth', DWORD),
        ('dmPanningHeight', DWORD),
    )

class Win32Mode(object):
    def __init__(self, devmode):
        self._devmode = devmode
        self.width = devmode.dmPelsWidth
        self.height = devmode.dmPelsHeight
        self.rate = devmode.dmDisplayFrequency

# Find available modes for each screen
screens = pyglet.window.get_platform().get_default_display().get_screens()
for screen in screens:
    handle = screen._handle
    info = MONITORINFOEX()
    info.cbSize = ctypes.sizeof(MONITORINFOEX)
    _user32.GetMonitorInfoW(handle, ctypes.byref(info))
    
    screen.device_name = info.szDevice
    screen.modes = []

    i = 0
    while True:
        mode = DEVMODE()
        mode.dmSize = ctypes.sizeof(DEVMODE)
        r = _user32.EnumDisplaySettingsW(screen.device_name, i, 
                                         ctypes.byref(mode))
        if not r:
            break

        screen.modes.append(Win32Mode(mode))
        i += 1


def set_mode(screen, width, height, rate=None):
    # Find best matching mode.  Should factor out common with X11 mode select
    
    best_mode = None
    for mode in screen.modes:
        if width > mode.width or height > mode.height:
            continue
        
        if not best_mode:
            best_mode = mode
            continue

        if mode.width == best_mode.width:
            if mode.height < best_mode.height:
                if (rate is not None and 
                    abs(rate - mode.rate) < 
                    abs(rate - best_mode.rate)):
                    best_mode = mode
            elif mode.height < best_mode.height:
                best_mode = mode
        elif mode.width < best_mode.width:
            best_mode = mode

    if best_mode is None:
        raise Exception('No mode is in range of requested resolution.')

    _user32.ChangeDisplaySettingsExW(screen.device_name,
                                     ctypes.byref(best_mode._devmode),
                                     None,
                                     CDS_FULLSCREEN,
                                     None)

window = pyglet.window.Window()
set_mode(screens[1], 800, 600)
pyglet.app.run()

