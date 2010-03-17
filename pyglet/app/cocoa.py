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
from __future__ import with_statement

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet.app.base import PlatformEventLoop
from pyglet.libs.darwin import *

# Prepare the default application.
NSApplication.sharedApplication()
NSApp().finishLaunching()

# Memory management.


class CocoaEventLoop(PlatformEventLoop):

    def start(self):
        self._pool = NSAutoreleasePool.alloc().init()

    def step(self, timeout=None):

        # Recycle the autorelease pool.
        self._pool.release()
        self._pool = NSAutoreleasePool.alloc().init()

        # Determine the timeout date.
        if timeout is None:
            timeout_date = NSDate.distantFuture()
        else:
            timeout_date = NSDate.date().addTimeInterval_(timeout)

        # Retrieve the next event (if any).
        event = NSApp().nextEventMatchingMask_untilDate_inMode_dequeue_(
                NSAnyEventMask, timeout_date, NSDefaultRunLoopMode, True)

        # Dispatch the event (if any).
        if event.type() != NSApplicationDefined:
            NSApp().sendEvent_(event)
        NSApp().updateWindows()
    
    def stop(self):
        self._pool.release()

    def notify(self):
        with autorelease:
            event = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                    NSApplicationDefined, # type
                    NSPoint(0.0, 0.0),    # location
                    0,                    # modifierFlags
                    0,                    # timestamp
                    0,                    # windowNumber
                    None,                 # graphicsContext
                    0,                    # subtype
                    0,                    # data1
                    0,                    # data2
                    )
            NSApp().postEvent_atStart_(event, False)
