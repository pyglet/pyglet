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
# $Id:$

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes
import time
import Queue

from pyglet import app
from base import EventLoop

from pyglet.libs.win32 import _kernel32, _user32, types, constants
from pyglet.libs.win32.constants import *
from pyglet.libs.win32.types import *

class Win32EventLoop(EventLoop):
    def __init__(self):
        super(Win32EventLoop, self).__init__()

        self._next_idle_time = None

        # Force immediate creation of an event queue on this thread -- note
        # that since event loop is created on pyglet.app import, whatever
        # imports pyglet.app _must_ own the main run loop.
        msg = types.MSG()
        _user32.PeekMessageW(ctypes.byref(msg), 0,
                             constants.WM_USER, constants.WM_USER, 
                             constants.PM_NOREMOVE)

        self._event_thread = _kernel32.GetCurrentThreadId()
        self._post_event_queue = Queue.Queue()

    def post_event(self, dispatcher, event, *args):
        self._post_event_queue.put((dispatcher, event, args))

        # Nudge the event loop with a message it will discard.  Note that only
        # user events are actually posted.  The posted event will not
        # interrupt the window move/size drag loop -- it seems there's no way
        # to do this.
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
        if _kernel32.GetCurrentThreadId() != self._event_thread:
            raise RuntimeError('EventLoop.run() must be called from the same ' +
                               'thread that imports pyglet.app')

        self._setup()

        self._timer_proc = types.TIMERPROC(self._timer_func)
        self._timer = timer = _user32.SetTimer(0, 0, 0, self._timer_proc)
        self._polling = False
        self._allow_polling = True
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

    def _idle_chance(self):
        if (self._next_idle_time is not None and 
            self._next_idle_time <= time.time()):
            self._timer_func(0, 0, self._timer, 0)

    def _timer_func(self, hwnd, msg, timer, t):
        sleep_time = self.idle()

        if sleep_time is None:
            # Block indefinitely
            millis = constants.USER_TIMER_MAXIMUM
            self._next_idle_time = None
            self._polling = False
            _user32.SetTimer(0, timer, millis, self._timer_proc)
        elif sleep_time < 0.01 and self._allow_polling:
            # Degenerate to polling
            millis = constants.USER_TIMER_MAXIMUM
            self._next_idle_time = 0.
            if not self._polling:
                self._polling = True
                _user32.SetTimer(0, timer, millis, self._timer_proc)
        else:
            # Block until timer
            # XXX hack to avoid oversleep; needs to be api
            sleep_time = max(sleep_time - 0.01, 0) 
            millis = int(sleep_time * 1000)
            self._next_idle_time = time.time() + sleep_time
            self._polling = False
            _user32.SetTimer(0, timer, millis, self._timer_proc)
