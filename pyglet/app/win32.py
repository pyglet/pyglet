#!/usr/bin/python
# $Id:$

import ctypes

from pyglet.app import windows, BaseEventLoop
from pyglet import clock
from pyglet.window.win32 import _user32, types, constants

class Win32EventLoop(BaseEventLoop):
    def run(self):
        self.setup()

        self._timer_proc = types.TIMERPROC(self._timer_func)
        timer = _user32.SetTimer(0, 0, 0, self._timer_proc)

        msg = types.MSG()
        while not self.has_exit:
            _user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
            _user32.TranslateMessage(ctypes.byref(msg))
            _user32.DispatchMessageW(ctypes.byref(msg))
            
            # Manual idle event
            if not _user32.GetQueueStatus(constants.QS_ALLINPUT) & 0xffff0000:
                self._timer_func(0, 0, timer, 0)

    def _timer_func(self, hwnd, msg, timer, t):
        dt = clock.tick(True)

        for window in windows:
            # Dispatch update event
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
            millis = constants.USER_TIMER_MAXIMUM
        else:
            millis = int(sleep_time * 1000)
        _user32.SetTimer(0, timer, millis, self._timer_proc)
