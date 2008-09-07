# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes
import Queue

from pyglet import app
from pyglet.app.base import EventLoop

from pyglet.libs.darwin import *

EventLoopTimerProc = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)


class CarbonEventLoop(EventLoop):
    _running = False

    def __init__(self):
        self._post_event_queue = Queue.Queue()
        self._event_loop = carbon.GetMainEventLoop()
        self._timer = ctypes.c_void_p()
        super(CarbonEventLoop, self).__init__()

    def post_event(self, dispatcher, event, *args):
        # TODO consolidate to base class
        self._post_event_queue.put((dispatcher, event, args))

        if not self._running:
            return

        carbon.SetEventLoopTimerNextFireTime(self._timer, ctypes.c_double(0.0))

    # TODO consolidate to base class
    def process_posted_events(self):
        while True:
            try:
                dispatcher, event, args = self._post_event_queue.get(False)
            except Queue.Empty:
                break

            dispatcher.dispatch_event(event, *args)

    def run(self):
        self._setup()

        e = ctypes.c_void_p()
        event_dispatcher = carbon.GetEventDispatcherTarget()
        event_loop = self._event_loop
        self._event_queue = carbon.GetMainEventQueue()

        # Create timer
        timer = self._timer
        idle_event_proc = EventLoopTimerProc(self._timer_proc)
        carbon.InstallEventLoopTimer(event_loop,
                                     ctypes.c_double(0.1), #?
                                     ctypes.c_double(kEventDurationForever),
                                     idle_event_proc,
                                     None,
                                     ctypes.byref(timer))

        self._force_idle = False
        self._allow_polling = True

        self.dispatch_event('on_enter')

        # Dispatch events posted before entered run looop
        self._running = True #XXX consolidate
        self.process_posted_events()

        try:
            while not self.has_exit:
                if self._force_idle:
                    duration = 0
                else:
                    duration = kEventDurationForever
                if carbon.ReceiveNextEvent(0, None, ctypes.c_double(duration),
                                           True, ctypes.byref(e)) == 0:
                    carbon.SendEventToEventTarget(e, event_dispatcher)
                    carbon.ReleaseEvent(e)

                # Manual idle event 
                if (carbon.GetNumEventsInQueue(self._event_queue) == 0 or 
                    self._force_idle):
                    self._force_idle = False
                    self._timer_proc(timer, None, False)
        except KeyboardInterrupt:
            self.exit()

        carbon.RemoveEventLoopTimer(self._timer)
        self.dispatch_event('on_exit')

    def _stop_polling(self):
        carbon.SetEventLoopTimerNextFireTime(self._timer, ctypes.c_double(0.0))

    def _enter_blocking(self):
        carbon.SetEventLoopTimerNextFireTime(self._timer, ctypes.c_double(0.0))
        self._allow_polling = False

    def _exit_blocking(self):
        self._allow_polling = True

    def _timer_proc(self, timer, data, in_events=True):
        self.process_posted_events()

        allow_polling = True

        for window in app.windows:
            # Check for live resizing
            if window._resizing is not None:
                allow_polling = False
                old_width, old_height = window._resizing
                rect = Rect()
                carbon.GetWindowBounds(window._window, 
                                       kWindowContentRgn,
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
            sleep_time = kEventDurationForever
        elif sleep_time < 0.01 and allow_polling and self._allow_polling:
            # Switch event loop to polling.
            if in_events:
                carbon.QuitEventLoop(self._event_loop)
            self._force_idle = True
            sleep_time = kEventDurationForever
        carbon.SetEventLoopTimerNextFireTime(timer, ctypes.c_double(sleep_time))
