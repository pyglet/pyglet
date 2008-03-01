#!/usr/bin/python
# $Id:$

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes
import time

from pyglet.app import windows, BaseEventLoop
from pyglet.window.win32 import _user32, types, constants

class Win32EventLoop(BaseEventLoop):
    def run(self):
        self._setup()

        self._timer_proc = types.TIMERPROC(self._timer_func)
        self._timer = timer = _user32.SetTimer(0, 0, 0, self._timer_proc)
        msg = types.MSG()
        
        self.dispatch_event('on_enter')

        while not self.has_exit:
            _user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
            _user32.TranslateMessage(ctypes.byref(msg))
            _user32.DispatchMessageW(ctypes.byref(msg))
            
            # Manual idle event
            msg_types = \
                _user32.GetQueueStatus(constants.QS_ALLINPUT) & 0xffff0000
            if (msg.message != constants.WM_TIMER and
                not msg_types & ~(constants.QS_TIMER<<16)):
                self._timer_func(0, 0, timer, 0)

        self.dispatch_event('on_exit')

    def _idle_chance(self):
        if (self._next_idle_time is not None and 
            self._next_idle_time <= time.time()):
            self._timer_func(0, 0, self._timer, 0)

    def _timer_func(self, hwnd, msg, timer, t):
        sleep_time = self.idle()

        if sleep_time is None:
            millis = constants.USER_TIMER_MAXIMUM
            self._next_idle_time = None
        else:
            # XXX hack to avoid oversleep; needs to be api
            sleep_time = max(sleep_time - 0.01, 0) 
            millis = int(sleep_time * 1000)
            self._next_idle_time = time.time() + sleep_time
        _user32.SetTimer(0, timer, millis, self._timer_proc)
