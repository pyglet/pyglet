#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes
import os
import fcntl
import mutex
import time
import select
import struct
import signal
import sys
import threading

from pyglet.window.xlib import xlib
import lib_xf86vmode as xf86vmode

class ModeList(object):
    invalid = True

    def __init__(self, x_display, x_screen):
        self.x_display = x_display
        self.x_screen = x_screen
        self.display_name = xlib.XDisplayString(self.x_display)

    @classmethod
    def from_screen(cls, screen):
        display = screen.display
        return cls(display._display, screen._x_screen_id)

    def _validate(self):
        if not self.invalid:
            return

        count = ctypes.c_int()
        modes = ctypes.POINTER(ctypes.POINTER(xf86vmode.XF86VidModeModeInfo))()
        xf86vmode.XF86VidModeGetAllModeLines(self.x_display, self.x_screen, 
                                             count, modes)

        # Copy modes out of list and free list
        self.modes = []
        for i in range(count.value):
            mode = xf86vmode.XF86VidModeModeInfo()
            ctypes.memmove(ctypes.byref(mode), ctypes.byref(modes.contents[i]), 
                           ctypes.sizeof(mode))
            self.modes.append(mode)
            if mode.privsize:
                xlib.XFree(mode.private)
        xlib.XFree(modes)

        self.invalid = False

    def _mode_packet(self, mode):
        return ModePacket(self.display_name, self.x_screen, 
                          mode.hdisplay, mode.vdisplay, mode.dotclock)

    def get_mode(self):
        '''Get current mode (ModePacket)'''
        self._validate()
        return self._mode_packet(self.modes[0])

    def set_mode(self, width, height, dotclock=None):
        '''Set mode closest to requested width, height and dotclock (if
        specified).  Actual mode is returned.  Exception is raised
        if width or height are above maximum.
        '''
        self._validate()

        best_mode = None
        for mode in self.modes:
            if width > mode.hdisplay or height > mode.vdisplay:
                continue
            
            if not best_mode:
                best_mode = mode
                continue

            if mode.hdisplay == best_mode.hdisplay:
                if mode.vdisplay < best_mode.vdisplay:
                    if (dotclock is not None and 
                        abs(dotclock - mode.dotclock) < 
                        abs(dotclock - best_mode.dotclock)):
                        best_mode = mode
                elif mode.vdisplay < best_mode.vdisplay:
                    best_mode = mode
            elif mode.hdisplay < best_mode.hdisplay:
                best_mode = mode

        if best_mode is None:
            raise Exception('No mode is in range of requested resolution.')

        xf86vmode.XF86VidModeSwitchToMode(self.x_display, self.x_screen, 
                                          best_mode)
        xlib.XFlush(self.x_display)
        self.invalid = True
        return self._mode_packet(best_mode)

# Mode packets tell the child process how to restore a given display and
# screen.  Only one packet should be sent per display/screen (more would
# indicate redundancy or incorrect restoration).  Packet format is:
#   display (max 256 chars), 
#   screen
#   width
#   height
#   dotclock
class ModePacket(object):
    format = '256siHHI'
    size = struct.calcsize(format)
    def __init__(self, display_name, screen, width, height, dotclock):
        self.display_name = display_name
        self.screen = screen
        self.width = width
        self.height = height
        self.dotclock = dotclock

    def encode(self):
        return struct.pack(self.format, self.display_name, self.screen,
                           self.width, self.height, self.dotclock)

    @classmethod
    def decode(cls, data):
        display_name, screen, width, height, dotclock = \
            struct.unpack(cls.format, data)
        return cls(display_name.strip('\0'), screen, width, height, dotclock)

    def __repr__(self):
        return '%s(%r, %r, %r, %r, %r)' % (
            self.__class__.__name__, self.display_name, self.screen,
            self.width, self.height, self.dotclock)

    def set(self):
        display = xlib.XOpenDisplay(self.display_name)
        mode_list = ModeList(display, self.screen)
        mode_list.set_mode(self.width, self.height, self.dotclock)
        xlib.XCloseDisplay(display)

_restore_mode_child_installed = False
_restorable_screens = set()
_mode_write_pipe = None

def _install_restore_mode_child():
    global _mode_write_pipe
    global _restore_mode_child_installed

    if _restore_mode_child_installed:
        return

    # Parent communicates to child by sending "mode packets" through a pipe:
    mode_read_pipe, _mode_write_pipe = os.pipe()

    if os.fork() == 0:
        # Child process (watches for parent to die then restores video mode(s).
        os.close(_mode_write_pipe)

        # Set up SIGHUP to be the signal for when the parent dies.
        PR_SET_PDEATHSIG = 1
        libc = ctypes.cdll.LoadLibrary('libc.so.6')
        libc.prctl.argtypes = (ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                               ctypes.c_ulong, ctypes.c_ulong)
        libc.prctl(PR_SET_PDEATHSIG, signal.SIGHUP, 0, 0, 0)

        # SIGHUP indicates the parent has died.  The child mutex is unlocked, it
        # stops reading from the mode packet pipe and restores video modes on
        # all displays/screens it knows about.
        def _sighup(signum, frame):
            parent_wait_mutex.unlock()
        parent_wait_mutex = mutex.mutex()
        parent_wait_mutex.lock(lambda arg: arg, None)
        signal.signal(signal.SIGHUP, _sighup)

        # Wait for parent to die and read packets from parent pipe
        packets = []
        buffer = ''
        while parent_wait_mutex.test():
            data = os.read(mode_read_pipe, ModePacket.size)
            buffer += data
            # Decode packets
            while len(buffer) >= ModePacket.size:
                packet = ModePacket.decode(buffer[:ModePacket.size])
                packets.append(packet)
                buffer = buffer[ModePacket.size:]

        for packet in packets:
            packet.set()
        sys.exit(0)
        
    else:
        # Parent process.  Clean up pipe then continue running program as
        # normal.  Send mode packets through pipe as additional
        # displays/screens are mode switched.
        os.close(mode_read_pipe)
        _restore_mode_child_installed = True

def _set_restore_mode(mode):
    _install_restore_mode_child()

    # This is not the real restore mode if one has already been set.
    if (mode.display_name, mode.screen) in _restorable_screens:
        return

    os.write(_mode_write_pipe, mode.encode())
    _restorable_screens.add((mode.display_name, mode.screen))

def _set_mode(screen, width, height):
    display_name = screen.display
    mode_list = ModeList.from_screen(screen)
    current_mode = mode_list.get_mode()
    _set_restore_mode(current_mode)
    new_mode = mode_list.set_mode(width, height)
    return new_mode.width, new_mode.height

import pyglet
window = pyglet.window.Window()
_set_mode(window.screen, 800, 600)
pyglet.app.run()

# Trigger a segfault -- mode still gets restored thanks to child :-)
print ctypes.c_char_p.from_address(0)

