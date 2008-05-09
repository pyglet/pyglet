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

import pyglet
import pyglet.window

display = pyglet.window.get_platform().get_default_display()
w = pyglet.window.Window(display=display)
@w.event
def on_draw():
    w.clear()


# Parent communicates to child by sending "mode packets" through a pipe:
mode_read_pipe, mode_write_pipe = os.pipe()

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

if os.fork() == 0:
    # Child process (watches for parent to die then restores video mode(s).
    os.close(mode_write_pipe)

    # Set up SIGHUP to be the signal for when the parent dies.
    PR_SET_PDEATHSIG = 1
    libc = ctypes.cdll.LoadLibrary('libc.so.6')
    libc.prctl.argtypes = (ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                           ctypes.c_ulong, ctypes.c_ulong)
    libc.prctl(PR_SET_PDEATHSIG, signal.SIGHUP, 0, 0, 0)

    # SIGHUP indicates the parent has died.  The child mutex is unlocked, it
    # stops reading from the mode packet pipe and restores video modes on all
    # displays/screens it knows about.
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
        print packet
    
else:
    # Parent process.  Clean up pipe then continue running program as normal.
    # Send mode packets through pipe as additional displays/screens are mode
    # switched.
    os.close(mode_read_pipe)

    os.write(mode_write_pipe, ModePacket(':0', 1, 1024, 768, 75).encode())
    pyglet.app.run()
    os.write(mode_write_pipe, ModePacket(':0', 0, 1280, 1024, 60).encode())
    print 'parent finished'
