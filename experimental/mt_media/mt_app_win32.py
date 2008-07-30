#!/usr/bin/python
# $Id:$

import ctypes
import Queue

import pyglet
from pyglet.window.win32 import _kernel32, _user32, constants, types

class MTWin32EventLoop(pyglet.app.win32.Win32EventLoop):
    def __init__(self, *args, **kwargs):
        super(MTWin32EventLoop, self).__init__(*args, **kwargs)

        # Force immediate creation of an event queue on this thread
        msg = types.MSG()
        _user32.PeekMessageW(ctypes.byref(msg), 0,
                             constants.WM_USER, constants.WM_USER, 
                             constants.PM_NOREMOVE)

        self._event_thread = _kernel32.GetCurrentThreadId()
        self._post_event_queue = Queue.Queue()

    def post_event(self, dispatcher, event, *args):
        self._post_event_queue.put((dispatcher, event, args))

        # Nudge the event loop with a message it will discard
        _user32.PostThreadMessageW(self._event_thread, constants.WM_USER, 0, 0)

    def _dispatch_posted_events(self):
        # Dispatch (synchronised) queued events
        while True:
            try:
                dispatcher, event, args = self._post_event_queue.get(False)
            except Queue.Empty:
                break

            dispatcher.dispatch_event(event, *args)

    def run(self):
        self._setup()

        self._timer_proc = types.TIMERPROC(self._timer_func)
        self._timer = timer = _user32.SetTimer(0, 0, 0, self._timer_proc)
        self._polling = False
        self._allow_polling = False
        msg = types.MSG()
        
        self.dispatch_event('on_enter')

        self._dispatch_posted_events()

        while not self.has_exit:
            if self._polling:
                while _user32.PeekMessageW(ctypes.byref(msg), 
                                           0, 0, 0, constants.PM_REMOVE):
                    _user32.TranslateMessage(ctypes.byref(msg))
                    _user32.DispatchMessageW(ctypes.byref(msg))
                self._timer_func(0, 0, timer, 0)
            else:
                _user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
                _user32.TranslateMessage(ctypes.byref(msg))
                _user32.DispatchMessageW(ctypes.byref(msg))
            
                # Manual idle event
                msg_types = \
                    _user32.GetQueueStatus(constants.QS_ALLINPUT) & 0xffff0000
                if (msg.message != constants.WM_TIMER and
                    not msg_types & ~(constants.QS_TIMER<<16)):
                    self._timer_func(0, 0, timer, 0)

            self._dispatch_posted_events()

        self.dispatch_event('on_exit')

pyglet.app.EventLoop = MTWin32EventLoop
