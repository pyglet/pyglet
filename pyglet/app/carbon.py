#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes

from pyglet.app import windows, BaseEventLoop
from pyglet.window.carbon import carbon, types, constants, _oscheck

EventLoopTimerProc = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
kEventDurationForever = ctypes.c_double(constants.kEventDurationForever)

class CarbonEventLoop(BaseEventLoop):
    def run(self):
        self._setup()

        e = ctypes.c_void_p()
        event_dispatcher = carbon.GetEventDispatcherTarget()
        self._event_loop = event_loop = carbon.GetMainEventLoop()
        event_queue = carbon.GetMainEventQueue()
        self._timer = timer = ctypes.c_void_p()
        idle_event_proc = EventLoopTimerProc(self._timer_proc)
        carbon.InstallEventLoopTimer(event_loop,
                                     ctypes.c_double(0.1), #?
                                     kEventDurationForever,
                                     idle_event_proc,
                                     None,
                                     ctypes.byref(timer))

        self._force_idle = False

        self.dispatch_event('on_enter')

        while not self.has_exit:
            if self._force_idle:
                duration = 0
                self._blocked = False
            else:
                duration = kEventDurationForever
                self._blocked = True
            if carbon.ReceiveNextEvent(0, None, duration,
                                       True, ctypes.byref(e)) == 0:
                carbon.SendEventToEventTarget(e, event_dispatcher)
                carbon.ReleaseEvent(e)

            # Manual idle event 
            if carbon.GetNumEventsInQueue(event_queue) == 0 or self._force_idle:
                self._force_idle = False
                self._timer_proc(timer, None, False)

        carbon.RemoveEventLoopTimer(self._timer)
        self.dispatch_event('on_exit')

    def _stop_polling(self):
        carbon.SetEventLoopTimerNextFireTime(self._timer, ctypes.c_double(0.0))

    def _timer_proc(self, timer, data, in_events=True):
        allow_polling = True

        for window in windows:
            # Check for live resizing
            if window._resizing is not None:
                allow_polling = False
                old_width, old_height = window._resizing
                rect = types.Rect()
                carbon.GetWindowBounds(window._window, 
                                       constants.kWindowContentRgn,
                                       ctypes.byref(rect))
                width = rect.right - rect.left
                height = rect.bottom - rect.top
                if width != old_width or height != old_height:
                    window._resizing = width, height
                    window.switch_to()
                    window.dispatch_event('on_resize', width, height) 
    
            # Check for live dragging
            if window._dragging:
                allow_polling = False

            # Check for deferred recreate
            if window._recreate_deferred:
                if in_events:
                    # Break out of ReceiveNextEvent so it can be processed
                    # in next iteration.
                    carbon.QuitEventLoop(self._event_loop)
                    self._force_idle = True
                else:
                    # Do it now.
                    window._recreate_immediate()

        sleep_time = self.idle()

        if sleep_time is None:
            sleep_time = constants.kEventDurationForever
        elif sleep_time == 0. and allow_polling:
            # Switch to event loop to polling.
            if self._blocked:
                carbon.QuitEventLoop(self._event_loop)
            self._force_idle = True
            sleep_time = constants.kEventDurationForever
        carbon.SetEventLoopTimerNextFireTime(timer, ctypes.c_double(sleep_time))

