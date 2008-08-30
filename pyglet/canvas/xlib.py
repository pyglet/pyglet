#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *

from pyglet import app
from pyglet.app.xlib import XlibSelectDevice
from base import Display, Screen, Canvas

# XXX
#from pyglet.window import NoSuchDisplayException
class NoSuchDisplayException(Exception):
    pass

from pyglet.libs.x11 import xlib
try:
    from pyglet.libs.x11 import xinerama
    _have_xinerama = True
except:
    _have_xinerama = False

try:
    from pyglet.libs.x11 import xsync
    _have_xsync = True
except:
    _have_xsync = False

# Set up error handler
def _error_handler(display, event):
    # By default, all errors are silently ignored: this has a better chance
    # of working than the default behaviour of quitting ;-)
    #
    # We've actually never seen an error that was our fault; they're always
    # driver bugs (and so the reports are useless).  Nevertheless, set
    # environment variable PYGLET_DEBUG_X11 to 1 to get dumps of the error
    # and a traceback (execution will continue).
    import pyglet
    if pyglet.options['debug_x11']:
        event = event.contents
        buf = c_buffer(1024)
        xlib.XGetErrorText(display, event.error_code, buf, len(buf))
        print 'X11 error:', buf.value
        print '   serial:', event.serial
        print '  request:', event.request_code
        print '    minor:', event.minor_code
        print ' resource:', event.resourceid

        import traceback
        print 'Python stack trace (innermost last):'
        traceback.print_stack()
    return 0
_error_handler_ptr = xlib.XErrorHandler(_error_handler)
xlib.XSetErrorHandler(_error_handler_ptr)

class XlibDisplay(XlibSelectDevice, Display):
    _display = None     # POINTER(xlib.Display)

    _x_im = None        # X input method
                        # TODO close _x_im when display connection closed.
    _enable_xsync = False

    def __init__(self, name=None, x_screen=None):
        if x_screen is None:
            x_screen = 0

        self._display = xlib.XOpenDisplay(name)
        if not self._display:
            raise NoSuchDisplayException('Cannot connect to "%s"' % name)

        screen_count = xlib.XScreenCount(self._display)
        if x_screen >= screen_count:
            raise NoSuchDisplayException(
                'Display "%s" has no screen %d' % (name, x_screen))

        super(XlibDisplay, self).__init__()
        self.name = name
        self.x_screen = x_screen

        # XXX
        from pyglet.gl import glx_info
        self.info = glx_info.GLXInfo(self._display)

        # Also set the default GLX display for future info queries
        # XXX
        glx_info.set_display(self._display.contents)

        self._fileno = xlib.XConnectionNumber(self._display)
        self._window_map = {}

        # Initialise XSync
        if _have_xsync:
            event_base = c_int()
            error_base = c_int()
            if xsync.XSyncQueryExtension(self._display, 
                                         byref(event_base),
                                         byref(error_base)):
                major_version = c_int()
                minor_version = c_int()
                if xsync.XSyncInitialize(self._display,
                                         byref(major_version),
                                         byref(minor_version)):
                    self._enable_xsync = True

        # Add to event loop select list.  Assume we never go away.
        app.event_loop._select_devices.add(self)

    def get_screens(self):
        if _have_xinerama and xinerama.XineramaIsActive(self._display):
            number = c_int()
            infos = xinerama.XineramaQueryScreens(self._display, 
                                                  byref(number))
            infos = cast(infos, 
                 POINTER(xinerama.XineramaScreenInfo * number.value)).contents
            result = []
            for info in infos:
                result.append(XlibScreen(self,
                                         info.x_org,
                                         info.y_org,
                                         info.width,
                                         info.height,
                                         True))
            xlib.XFree(infos)
            return result
        else:
            # No xinerama
            screen_info = xlib.XScreenOfDisplay(self._display, self.x_screen)
            screen = XlibScreen(self,
                                0, 0,
                                screen_info.contents.width,
                                screen_info.contents.height,
                                False)
            return [screen]

    # XlibSelectDevice interface

    def fileno(self):
        return self._fileno

    def select(self):
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

    def poll(self):
        return xlib.XPending(self._display)

class XlibScreen(Screen):
    def __init__(self, display, x, y, width, height, xinerama):
        super(XlibScreen, self).__init__(display, x, y, width, height)
        self._xinerama = xinerama
 
    def get_matching_configs(self, template):
        canvas = XlibCanvas(self.display, None)
        configs = template.match(canvas)
        # XXX deprecate
        for config in configs:
            config.screen = self
        return configs

    def __repr__(self):
        return 'XlibScreen(display=%r, x=%d, y=%d, ' \
               'width=%d, height=%d, xinerama=%d)' % \
            (self.display, self.x, self.y, self.width, self.height,
             self._xinerama)

class XlibCanvas(Canvas):
    def __init__(self, display, x_window):
        super(XlibCanvas, self).__init__(display)
        self.x_window = x_window
