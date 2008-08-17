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
__version__ = '$Id$'

import os
import select
import threading
import weakref

from pyglet import app
from pyglet.app.base import EventLoop

class XlibSelectDevice(object):
    def fileno(self):
        '''Get the file handle for ``select()`` for this device.

        :rtype: int
        '''
        raise NotImplementedError('abstract')

    def select(self):
        '''Perform event processing on the device.

        Called when ``select()`` returns this device in its list of active
        files.
        '''
        raise NotImplementedError('abstract')

    def poll(self):
        '''Check if the device has events ready to process.

        :rtype: bool
        :return: True if there are events to process, False otherwise.
        '''
        return False

class SynchronizedEventQueue(XlibSelectDevice):
    def __init__(self):
        self._sync_file_read, self._sync_file_write = os.pipe()
        self._events = []
        self._lock = threading.Lock()

    def fileno(self):
        return self._sync_file_read

    def post_event(self, dispatcher, event, *args):
        self._lock.acquire()
        self._events.append((dispatcher, event, args))
        os.write(self._sync_file_write, '1')
        self._lock.release()

    def select(self):
        self._lock.acquire()
        for dispatcher, event, args in self._events:
            dispatcher.dispatch_event(event, *args)
        self._events = []
        self._lock.release()

    def poll(self):
        self._lock.acquire()
        result = bool(self._events)
        self._lock.release()

        return result

class XlibEventLoop(EventLoop):
    def __init__(self):
        super(XlibEventLoop, self).__init__()
        self._synchronized_event_queue = SynchronizedEventQueue()
        self._select_devices = set()
        self._select_devices.add(self._synchronized_event_queue)

    def post_event(self, dispatcher, event, *args):
        self._synchronized_event_queue.post_event(dispatcher, event, *args)

    def run(self):
        self._setup()

        t = 0
        sleep_time = 0.

        self.dispatch_event('on_enter')

        while not self.has_exit:
            # Check for already pending events
            pending_devices = []
            for device in self._select_devices:
                if device.poll():
                    pending_devices.append(device)

            # If nothing was immediately pending, block until there's activity
            # on a device.
            if not pending_devices:
                iwtd = self._select_devices
                pending_displays, _, _ = select.select(iwtd, (), (), sleep_time)

            # Dispatch activity on matching devices
            for device in pending_devices:
                device.select()

            # Dispatch resize events
            for window in app.windows:
                if window._needs_resize:
                    window.switch_to()
                    window.dispatch_event('on_resize', 
                                          window._width, window._height)
                    window.dispatch_event('on_expose')
                    window._needs_resize = False

            sleep_time = self.idle()

        self.dispatch_event('on_exit')
