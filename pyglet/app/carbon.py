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
from pyglet.app.base import EventLoop, Display

from pyglet.libs.darwin import *

EventLoopTimerProc = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)


class CarbonDisplay(Display):
    # TODO: CarbonDisplay could be per display device, which would make
    # reporting of screens and available configs more accurate.  The number of
    # Macs with more than one video card is probably small, though.
    def __init__(self):
        super(CarbonDisplay, self).__init__()

        import MacOS
        if not MacOS.WMAvailable():
            raise app.AppException('Window manager is not available.  ' \
                                   'Ensure you run "pythonw", not "python"')

        self._install_application_event_handlers()
        
    def get_screens(self):
        from pyglet.window.carbon import CarbonScreen
        count = CGDisplayCount()
        carbon.CGGetActiveDisplayList(0, None, byref(count))
        displays = (CGDirectDisplayID * count.value)()
        carbon.CGGetActiveDisplayList(count.value, displays, byref(count))
        return [CarbonScreen(self, id) for id in displays]

    def _install_application_event_handlers(self):
        self._carbon_event_handlers = []
        self._carbon_event_handler_refs = []

        target = carbon.GetApplicationEventTarget()

        # TODO something with a metaclass or hacky like CarbonWindow
        # to make this list extensible
        handlers = [
            (self._on_mouse_down, kEventClassMouse, kEventMouseDown),
            (self._on_apple_event, kEventClassAppleEvent, kEventAppleEvent),
            (self._on_command, kEventClassCommand, kEventProcessCommand),
        ]

        ae_handlers = [
            (self._on_ae_quit, kCoreEventClass, kAEQuitApplication),
        ]

        # Install the application-wide handlers
        for method, cls, event in handlers:
            proc = EventHandlerProcPtr(method)
            self._carbon_event_handlers.append(proc)
            upp = carbon.NewEventHandlerUPP(proc)
            types = EventTypeSpec()
            types.eventClass = cls
            types.eventKind = event
            handler_ref = EventHandlerRef()
            carbon.InstallEventHandler(
                target,
                upp,
                1,
                byref(types),
                c_void_p(),
                byref(handler_ref))
            self._carbon_event_handler_refs.append(handler_ref)

        # Install Apple event handlers
        for method, cls, event in ae_handlers:
            proc = EventHandlerProcPtr(method)
            self._carbon_event_handlers.append(proc)
            upp = carbon.NewAEEventHandlerUPP(proc)
            carbon.AEInstallEventHandler(
                cls,
                event,
                upp,
                0,
                False)

    def _on_command(self, next_handler, ev, data):
        command = HICommand()
        carbon.GetEventParameter(ev, kEventParamDirectObject,
            typeHICommand, c_void_p(), sizeof(command), c_void_p(),
            byref(command))

        if command.commandID == kHICommandQuit:
            self._on_quit()

        return noErr

    def _on_mouse_down(self, next_handler, ev, data):
        # Check for menubar hit
        position = Point()
        carbon.GetEventParameter(ev, kEventParamMouseLocation,
            typeQDPoint, c_void_p(), sizeof(position), c_void_p(),
            byref(position))
        if carbon.FindWindow(position, None) == inMenuBar:
            # Mouse down in menu bar.  MenuSelect() takes care of all
            # menu tracking and blocks until the menu is dismissed.
            # Use command events to handle actual menu item invokations.

            # This function blocks, so tell the event loop it needs to install
            # a timer.
            app.event_loop._enter_blocking()
            carbon.MenuSelect(position)
            app.event_loop._exit_blocking()

            # Menu selection has now returned.  Remove highlight from the
            # menubar.
            carbon.HiliteMenu(0)

        carbon.CallNextEventHandler(next_handler, ev)
        return noErr

    def _on_apple_event(self, next_handler, ev, data):
        # Somewhat involved way of redispatching Apple event contained
        # within a Carbon event, described in
        # http://developer.apple.com/documentation/AppleScript/
        #  Conceptual/AppleEvents/dispatch_aes_aepg/chapter_4_section_3.html

        release = False
        if carbon.IsEventInQueue(carbon.GetMainEventQueue(), ev):
            carbon.RetainEvent(ev)
            release = True
            carbon.RemoveEventFromQueue(carbon.GetMainEventQueue(), ev)

        ev_record = EventRecord()
        carbon.ConvertEventRefToEventRecord(ev, byref(ev_record))
        carbon.AEProcessAppleEvent(byref(ev_record))

        if release:
            carbon.ReleaseEvent(ev)
        
        return noErr

    def _on_ae_quit(self, ae, reply, refcon):
        self._on_quit()
        return noErr

    def _on_quit(self):
        '''Called when the user tries to quit the application.

        This is not an actual event handler, it is called in response
        to Command+Q, the Quit menu item, and the Dock context menu's Quit
        item.

        The default implementation calls `EventLoop.exit` on
        `pyglet.app.event_loop`.
        '''
        app.event_loop.exit()

class CarbonEventLoop(EventLoop):
    _running = False

    def __init__(self):
        self._post_event_queue = Queue.Queue()
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
        self._event_loop = event_loop = carbon.GetMainEventLoop()
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
