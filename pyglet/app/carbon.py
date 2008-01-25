#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes

from pyglet.app import windows, BaseEventLoop
from pyglet import clock
from pyglet.window.carbon import carbon

class CarbonEventLoop(BaseEventLoop):
    def run(self):
        self.setup()

        #event_queue = carbon.GetMainEventQueue()
        e = ctypes.c_void_p()
        event_dispatcher = carbon.GetEventDispatcherTarget()

        while not self.has_exit:
            # Deal with pending events
            while carbon.ReceiveNextEvent(0, None, 0, True, 
                                          ctypes.byref(e)) == 0:
                carbon.SendEventToEventTarget(e, event_dispatcher)
                carbon.ReleaseEvent(e)

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

            sleep_time = clock.get_sleep_time(True)

            # Wait for timeout or interruption by another event
            if carbon.ReceiveNextEvent(0, None, sleep_time, True,
                                       ctypes.byref(e)) == 0:
                carbon.SendEventToEventTarget(e, event_dispatcher)
                carbon.ReleaseEvent(e)

            
