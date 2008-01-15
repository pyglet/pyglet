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

from pyglet import window

import xf86vmode

platform = window.get_platform()
display = platform.get_default_display()
x_display = display._display
screen = display.get_default_screen()
x_screen = screen._x_screen_id

count = ctypes.c_int()
modes_ptr = ctypes.POINTER(ctypes.POINTER(xf86vmode.XF86VidModeModeInfo))()
xf86vmode.XF86VidModeGetAllModeLines(x_display, x_screen, 
    ctypes.byref(count), ctypes.byref(modes_ptr))

modes = ctypes.cast(
    modes_ptr.contents, 
    ctypes.POINTER(xf86vmode.XF86VidModeModeInfo * count.value)).contents

restore_mode = modes[0]

for mode in modes:
    print mode.hdisplay, mode.vdisplay,
    print mode.flags
    # XXX returns -2 for current mode, and 1 for others? (0 == fine)
    print xf86vmode.XF86VidModeValidateModeLine(x_display, x_screen, mode)


new_mode = xf86vmode.XF86VidModeModeLine()
dotclock = ctypes.c_int()
xf86vmode.XF86VidModeGetModeLine(x_display, x_screen, dotclock, new_mode)

print new_mode.hdisplay, new_mode.vdisplay

#new_mode.hdisplay = 800
#new_mode.vdisplay = 600

# XXX always fails -- doesn't seem to get used, according to codesearch
#xf86vmode.XF86VidModeModModeLine(x_display, x_screen, new_mode)

# XXX mode switch doesn't happen until process exits... need to nudge X?
#xf86vmode.XF86VidModeSwitchToMode(x_display, x_screen, modes[1])

#time.sleep(5)

#xf86vmode.XF86VidModeSwitchToMode(x_display, x_screen, modes[0])

# TODO free modes_ptr
