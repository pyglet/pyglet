#!/usr/bin/env python

'''

Some ideas and test code.

Windows and OS X easily support per-screen mode switching.  Interface should
be::

class Screen
    def can_set_size(self, width, height):
        return True

    def set_size(self, width, height):
        raise UnsupportedScreenModeException()

    width = ..
    height = ..     # as currently, but updated when size changes.

Linux supports per-screen mode switching for real X screens only (not Xinerama
screens).  The above interface works for that case.  XFree86-VidModeExtension
is used.

RANDR extension can also be used to switch modes.  It can be used in
conjunction with nvidia extensions to set individual screen modes in TwinView
(the nvidia Xinerama implementation).

For non-nvidia Xinerama there is no way to distinguish which modes apply to
which screens, and in what way.  For example, VidMode reports the following
modes on my machine (dual-head TwinView):

    0: 2560x1024
    1: 1280x1024
    2: 1280x1024

My meta-modes line is:

    1280x1024,1280x1024; 1280x1024,NULL; NULL,1280x1024

So, modeline 0 is for the extended desktop, modeline 1 is for the primary
monitor, modeline 2 is for the secondary monitor.  There's no way to
distinguish them; and so it doesn't fit into pyglet's Screen class at all.  I
don't think setting modelines by number as an X11-only option is very useful
either (since the application cannot know what it's going to get on a
multi-monitor setup -- the user may as well hit Ctrl++ a couple of times to
set it manually).

Proposed Linux behaviour:

    if len(screens) == 1:
        Use VidMode extension       # Most people get this: only 1 screen
    elif screen is not xinerama:
        Use VidMode extension       # Rare -- Xinerama is used by everyone
    elif screen is nvidia TwinView
        Use nvidia/RANDR extension  # nvidia users get Win/OSX functionality
    else:
        Fail.                       # ATI/Intel Xinerama users are shafted



'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import setup_path

import ctypes
import time

import pyglet
from pyglet.gl import *
from pyglet.window.xlib import xlib
from pyglet import window

import xf86vmode

platform = window.get_platform()
display = platform.get_default_display()
x_display = display._display
screen = display.get_default_screen()
x_screen = screen._x_screen_id

count = ctypes.c_int()
modes = ctypes.POINTER(ctypes.POINTER(xf86vmode.XF86VidModeModeInfo))()
xf86vmode.XF86VidModeGetAllModeLines(x_display, x_screen, 
    ctypes.byref(count), ctypes.byref(modes))

restore_mode = modes[0]

def mode_info_to_line(info):
    line = xf86vmode.XF86VidModeModeLine()
    line.hdisplay = info.hdisplay
    line.hsyncstart = info.hsyncstart
    line.hsyncend = info.hsyncend
    line.htotal = info.htotal
    line.vdisplay = info.vdisplay
    line.vsyncstart = info.vsyncstart
    line.vtotal = info.vtotal
    line.flags = info.flags
    line.privsize = info.privsize
    line.private = info.private
    return line

def print_modes():
    for i in range(count.value):
        mode = modes.contents[i]
        print (mode.hdisplay, mode.vdisplay, mode.hsyncstart, mode.hsyncend,
            mode.htotal, mode.vsyncstart, mode.vsyncend, mode.vtotal)
        # XXX returns -2 for current mode, and 1 for others? (0 == fine)
        #print xf86vmode.XF86VidModeValidateModeLine(x_display, x_screen, mode)

# TODO free modes_ptr

def test_mod_modeline():
    '''Doesn't work at all.'''
    new_mode = xf86vmode.XF86VidModeModeLine()
    dotclock = ctypes.c_int()
    xf86vmode.XF86VidModeGetModeLine(x_display, x_screen, dotclock, new_mode)

    print new_mode.hdisplay, new_mode.vdisplay, dotclock

    new_mode.hdisplay = 800
    new_mode.vdisplay = 800

    # XXX always fails -- doesn't seem to get used, according to codesearch
    print xf86vmode.XF86VidModeModModeLine(x_display, x_screen, new_mode)
    xlib.XFlush(x_display)
    #xlib.XSync(x_display, False)

    xf86vmode.XF86VidModeGetModeLine(x_display, x_screen, dotclock, new_mode)
    print new_mode.hdisplay, new_mode.vdisplay

def test_change_modes():
    '''Select an existing mode.'''
    x = ctypes.c_int()
    y = ctypes.c_int()
    xf86vmode.XF86VidModeGetViewPort(x_display, x_screen, x, y)
    print 'old viewport %d, %d' % (x.value, y.value)

    xf86vmode.XF86VidModeSwitchToMode(x_display, x_screen, modes[1])
    xf86vmode.XF86VidModeSetViewPort(x_display, x_screen, 0, 0)
    xlib.XFlush(x_display)

    screen.width = 1024
    screen.height = 768
    window = pyglet.window.Window(fullscreen=True, screen=screen)
    window.set_location(0, 0)

    xlib.XGrabPointer(x_display, window._window,
                       True,
                        0,
                        xlib.GrabModeAsync,
                        xlib.GrabModeAsync,
                        window._window,
                        0,
                        xlib.CurrentTime)

    @window.event
    def on_key_press(symbol, modifiers):
        xf86vmode.XF86VidModeSwitchToMode(x_display, x_screen, modes[0])
        xf86vmode.XF86VidModeSetViewPort(x_display, x_screen, x, y)
        xlib.XFlush(x_display)
        pyglet.app.exit()

    @window.event
    def on_draw():
        glClearColor(.5, .5, .5, 1)
        window.clear()
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glColor3f(0.6, 0, 0)
        glRectf(0, 0, 320, 200)
        glColor3f(0.6, 0.6, 0)
        glRectf(0, 0, 640, 480)
        glColor3f(0.6, 0.6, 0.6)
        glRectf(0, 0, 800, 600)
        glColor3f(0, 0.6, 0)
        glRectf(0, 0, 1024, 768)
        glColor3f(0, 0, 0.6)
        glRectf(0, 0, 1280, 1024)

    pyglet.app.run()

def test_add_mode():
    # Copy an existing mode and modify its hdisplay
    src_mode = modes.contents[0]
    new_mode = xf86vmode.XF86VidModeModeInfo()
    ctypes.memmove(ctypes.byref(new_mode), ctypes.byref(src_mode), ctypes.sizeof(new_mode))
    #new_mode.hdisplay = 800
    #new_mode.vdisplay = 800
    print 'adding',
    print xf86vmode.XF86VidModeValidateModeLine(x_display, x_screen, new_mode)
    xf86vmode.XF86VidModeAddModeLine(x_display, x_screen, new_mode, src_mode)
    xlib.XFlush(x_display)

    print_modes()     

print_modes()     
test_change_modes()
