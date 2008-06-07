#!/usr/bin/env python

'''
Hack synchronisation into pyglet event loop.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import select
import threading

import pyglet

class XlibEventDispatcher(object):
    def fileno(self):
        raise NotImplementedError('abstract')

    def dispatch_events(self):
        pass

from pyglet.window.xlib import xlib

class XlibDisplayDevice(pyglet.window.xlib.XlibDisplayDevice):
    def dispatch_events(self):
        e = xlib.XEvent()
        while xlib.XPending(self._display):
            xlib.XNextEvent(self._display, e)

            # Key events are filtered by the xlib window event
            # handler so they get a shot at the prefiltered event.
            if e.xany.type not in (xlib.KeyPress, xlib.KeyRelease):
                if xlib.XFilterEvent(e, e.xany.window):
                    continue
            try:
                window = self._window_map[e.xany.window]
            except KeyError:
                continue

            window.dispatch_platform_event(e)
    
class XlibPlatform(pyglet.window.xlib.XlibPlatform):
    def get_display(self, name):
        if name not in self._displays:
            self._displays[name] = XlibDisplayDevice(name)
        return self._displays[name]

platform = XlibPlatform()
pyglet.window.get_platform = lambda: platform

import os
class SynchronizedEventDispatcher(XlibEventDispatcher):
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

    def dispatch_events(self):
        self._lock.acquire()
        for dispatcher, event, args in self._events:
            dispatcher.dispatch_event(event, *args)
        self._events = []
        self._lock.release()

class MTXlibEventLoop(pyglet.app.xlib.XlibEventLoop):
    def __init__(self, *args, **kwargs):
        super(MTXlibEventLoop, self).__init__(*args, **kwargs)
        self._synchronized_event_dispatcher = SynchronizedEventDispatcher()

    def post_event(self, dispatcher, event, *args):
        self._synchronized_event_dispatcher.post_event(dispatcher, event, *args)

    def get_select_files(self):
        return list(pyglet.app.displays) + [self._synchronized_event_dispatcher]

    def run(self):
        self._setup()

        e = xlib.XEvent()
        t = 0
        sleep_time = 0.

        self.dispatch_event('on_enter')

        while not self.has_exit:
            # Check for already pending events
            for display in pyglet.app.displays:
                if xlib.XPending(display._display):
                    pending_dispatchers = (display,)
                    break
            else:
                # None found; select on all file descriptors or timeout
                iwtd = self.get_select_files()
                pending_dispatchers, _, _ = \
                    select.select(iwtd, (), (), sleep_time)

            # Dispatch platform events
            for dispatcher in pending_dispatchers:
                dispatcher.dispatch_events()

            # Dispatch resize events 
            # XXX integrate into dispatchers?
            for window in pyglet.app.windows:
                if window._needs_resize:
                    window.switch_to()
                    window.dispatch_event('on_resize', 
                                          window._width, window._height)
                    window.dispatch_event('on_expose')
                    window._needs_resize = False

            sleep_time = self.idle()

        self.dispatch_event('on_exit')

pyglet.app.EventLoop = MTXlibEventLoop
