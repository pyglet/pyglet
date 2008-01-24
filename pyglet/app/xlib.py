#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import select
import weakref

from pyglet.app import displays, windows, BaseEventLoop
from pyglet import clock
from pyglet.window.xlib import xlib

class XlibEventLoop(BaseEventLoop):
    def run(self):
        self.setup()

        e = xlib.XEvent()
        t = 0
        while not self.has_exit:
            # Check for already pending events
            for display in displays:
                if xlib.XPending(display._display):
                    pending_displays = (display,)
                    break
            else:
                # None found; select on all file descriptors or timeout
                iwtd = self.get_select_files()
                timeout = clock.get_sleep_time(True)
                pending_displays, _, _ = select.select(iwtd, (), (), timeout)

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

            # Call scheduled functions
            dt = clock.tick(True)

            # Dispatch update event
            for window in windows:
                window.dispatch_event('on_update', dt)
                window.dispatch_pending_events()
                if window.has_exit:
                    window.close() # XXX hack

            # Redraw all windows
            for window in windows:
                window.switch_to()
                window.dispatch_event('on_draw')
                window.flip()

            # XXX temporary hack
            if not windows:
                self.has_exit = True

    def get_select_files(self):
        return list(displays)
