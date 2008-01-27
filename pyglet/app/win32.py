#!/usr/bin/python
# $Id:$

import ctypes

from pyglet.app import windows, BaseEventLoop
from pyglet.window.win32 import _user32, types, constants

class Win32EventLoop(BaseEventLoop):
    def run(self):
        self._setup()

        self._timer_proc = types.TIMERPROC(self._timer_func)
        timer = _user32.SetTimer(0, 0, 0, self._timer_proc)
        msg = types.MSG()
        
        self.dispatch_event('on_enter')

        while not self.has_exit:
            _user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
            _user32.TranslateMessage(ctypes.byref(msg))
            _user32.DispatchMessageW(ctypes.byref(msg))
            
            # Manual idle event
            if not _user32.GetQueueStatus(constants.QS_ALLINPUT) & 0xffff0000:
                self._timer_func(0, 0, timer, 0)

        self.dispatch_event('on_exit')

    def _timer_func(self, hwnd, msg, timer, t):
        sleep_time = self.idle()

        if sleep_time is None:
            millis = constants.USER_TIMER_MAXIMUM
        else:
            millis = int(sleep_time * 1000)
        _user32.SetTimer(0, timer, millis, self._timer_proc)
