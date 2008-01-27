#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import select
import weakref

from pyglet.app import displays, windows, BaseEventLoop
from pyglet.window.xlib import xlib

class XlibEventLoop(BaseEventLoop):
    def run(self):
        self._setup()

        e = xlib.XEvent()
        t = 0
        sleep_time = 0.

        self.dispatch_event('on_enter')

        while not self.has_exit:
            # Check for already pending events
            for display in displays:
                if xlib.XPending(display._display):
                    pending_displays = (display,)
                    break
            else:
                # None found; select on all file descriptors or timeout
                iwtd = self.get_select_files()
                pending_displays, _, _ = select.select(iwtd, (), (), sleep_time)

            # Dispatch platform events
            for display in pending_displays:
                while xlib.XPending(display._display):
                    xlib.XNextEvent(display._display, e)
                    if e.xany.type not in (xlib.KeyPress, xlib.KeyRelease):
                        if xlib.XFilterEvent(e, 0):
                            continue
                    try:
                        window = display._window_map[e.xany.window]
                    except KeyError:
                        continue

                    window.dispatch_platform_event(e)

            sleep_time = self.idle()

        self.dispatch_event('on_exit')

    def get_select_files(self):
        return list(displays)
