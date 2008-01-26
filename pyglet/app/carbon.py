#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes

from pyglet.app import windows, BaseEventLoop
from pyglet import clock
from pyglet.window.carbon import carbon

kEventDurationForever = ctypes.c_double(-1.0)

EventLoopTimerProc = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)

class CarbonEventLoop(BaseEventLoop):
    def run(self):
        self.setup()

        e = ctypes.c_void_p()
        event_dispatcher = carbon.GetEventDispatcherTarget()
        event_loop = carbon.GetMainEventLoop()
        event_queue = carbon.GetMainEventQueue()
        timer = ctypes.c_void_p()
        idle_event_proc = EventLoopTimerProc(self._timer_proc)
        carbon.InstallEventLoopTimer(event_loop,
                                     ctypes.c_double(0.1), #?
                                     kEventDurationForever,
                                     idle_event_proc,
                                     None,
                                     ctypes.byref(timer))


        while not self.has_exit:
            if carbon.ReceiveNextEvent(0, None, kEventDurationForever, 
                                       True, ctypes.byref(e)) == 0:
                carbon.SendEventToEventTarget(e, event_dispatcher)
                carbon.ReleaseEvent(e)

            # Manual idle event 
            if carbon.GetNumEventsInQueue(event_queue) == 0:
                self._timer_proc(timer, None)

    def _timer_proc(self, timer, data):
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

        # Update timout
        sleep_time = clock.get_sleep_time(True)
        if sleep_time is None:
            sleep_time = kEventDurationForever
        carbon.SetEventLoopTimerNextFireTime(timer, ctypes.c_double(sleep_time))
