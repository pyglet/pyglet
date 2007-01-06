#!/usr/bin/env python

'''
Documentation sources for Xlib programming:

http://tronche.com/gui/x/ (specifically xlib/ and icccm/)

http://users.actcom.co.il/~choo/lupg/tutorials/xlib-programming/xlib-programming.html

Resize and move are handled by a bunch of different events:

- ResizeRequest (reports another client's attempts to change the size of a
  window)
- ConfigureNotify (reports actual changes to a window's state, such as
  size, position, border, and stacking order)
- ConfigureRequest (reports when another client initiates a configure window
  request on any child of a specified window)

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sets
from ctypes import *
from ctypes import util
import unicodedata
import warnings

from pyglet.GL.VERSION_1_1 import *
import pyglet.GL.info
import pyglet.GLU.info
from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *
from pyglet.window.xlib.glx.VERSION_1_4 import *
from pyglet.window.xlib.constants import *
from pyglet.window.xlib.types import *

try:
    from pyglet.window.xlib.glx.SGI_video_sync import *
    _have_SGI_video_sync = True
except ImportError:
    _have_SGI_video_sync = False

# Load X11 library, specify argtypes and restype only when necessary.
Atom = c_ulong

path = util.find_library('X11')
if not path:
    raise ImportError('Cannot locate X11 library')
xlib = cdll.LoadLibrary(path)

path = util.find_library('Xinerama')
if path:
    _have_xinerama = True
    xinerama = cdll.LoadLibrary(path)
    xinerama.XineramaQueryScreens.restype = POINTER(XineramaScreenInfo)
else:
    _have_xinerama = False

xlib.XOpenDisplay.argtypes = [c_char_p]
xlib.XScreenOfDisplay.restype = POINTER(Screen)
xlib.XInternAtom.restype = Atom
xlib.XNextEvent.argtypes = [POINTER(Display), POINTER(XEvent)]
xlib.XCheckTypedWindowEvent.argtypes = [POINTER(Display),
    c_ulong, c_int, POINTER(XEvent)]
xlib.XPutBackEvent.argtypes = [POINTER(Display), POINTER(XEvent)]
xlib.XCreateWindow.argtypes = [POINTER(Display), WindowRef,
    c_int, c_int, c_uint, c_uint, c_uint, c_int, c_uint,
    POINTER(Visual), c_ulong, POINTER(XSetWindowAttributes)]

# Do we have the November 2000 UTF8 extension?
_have_utf8 = hasattr(xlib, 'Xutf8TextListToTextProperty')

class XlibException(WindowException):
    pass

class XlibPlatform(BasePlatform):
    def get_screens(self, factory):
        display = self._get_display(factory)
        x_screen = xlib.XDefaultScreen(display)
        if _have_xinerama and xinerama.XineramaIsActive(display):
            number = c_int()
            infos = xinerama.XineramaQueryScreens(display, 
                                                  byref(number))
            infos = cast(infos, 
                         POINTER(XineramaScreenInfo * number.value)).contents
            result = []
            for info in infos:
                result.append(XlibScreen(display,
                                         x_screen,
                                         info.x_org,
                                         info.y_org,
                                         info.width,
                                         info.height,
                                         True))
            xlib.XFree(infos)
            return result
        else:
            # No xinerama
            screen_count = xlib.XScreenCount(display)
            result = []
            for i in range(screen_count):
                screen = xlib.XScreenOfDisplay(display, i)
                result.append(XlibScreen(display,
                                         i, 
                                         0, 0,
                                         screen.contents.width,
                                         screen.contents.height,
                                         False))
            # Move default screen to be first in list.
            s = result.pop(x_screen)
            result.insert(0, s)
            return result
    
    def create_configs(self, factory):
        display = self._get_display(factory)
        screen = factory.get_screen()

        have_13 = display.contents.have_glx_version(1, 3)
        if have_13:
            config_class = XlibGLConfig13
            factory.set_gl_attribute('x_renderable', True)
        else:
            if 'ATI' in display.contents.get_glx_client_vendor():
                config_class = XlibGLConfig10ATI
            else:
                config_class = XlibGLConfig10
        
        # Construct array of attributes
        attrs = []
        for name, value in factory.get_gl_attributes().items():
            attr = config_class.attribute_ids.get(name, None)
            if not attr:
                warnings.warn('Unknown GLX attribute "%s"' % name)
            else:
                attrs.extend([attr, int(value)])

        if not have_13:
            attrs.extend([GLX_RGBA, True])

        if len(attrs):
            attrs.extend([0, 0])
            attrib_list = (c_int * len(attrs))(*attrs)
        else:
            attrib_list = None

        if have_13:
            elements = c_int()
            configs = glXChooseFBConfig(display, screen._x_screen_id,
                attrib_list, byref(elements))
            if not configs:
                return []
            result = []
            for i in range(elements.value):
                result.append(XlibGLConfig13(display, screen, configs[i]))
            xlib.XFree(configs)
            return result
        else:
            return [XlibGLConfig10(display, screen, attrib_list)]

    def create_context(self, factory):
        config = factory.get_config()
        context_share = factory.get_context_share()

        context = config.create_context(context_share)

        if context == GLXBadContext:
            raise XlibException('Invalid context share')
        elif context == GLXBadFBConfig:
            raise XlibException('Invalid GL configuration')
        elif context < 0:
            raise XlibException('Could not create GL context') 

        return XlibGLContext(config._display, context, context_share)

    def get_window_class(self):
        return XlibWindow

    def _get_display(self, factory):
        # Get the X display, and resolve name if necessary
        display = factory.get_x_display()
        if not display:
            display = ''
        if type(display) in (str, unicode):
            display = xlib.XOpenDisplay(display)
            if not display:
                raise XlibException('Cannot connect to X server') 
            factory.set_x_display(display)
        return display

class XlibDisplay(Display):
    def __repr__(self):
        return 'XlibDisplay(%d)' % self

    def have_glx_version(self, major, minor):
        if not glXQueryExtension(self, None, None):
            raise XlibException('pyglet requires an X server with GLX')

        server = [int(i) for i in self.get_glx_server_version().split('.')]
        client = [int(i) for i in self.get_glx_client_version().split('.')]
        return (tuple(server) >= (major, minor) and 
                tuple(client) >= (major, minor))

    def get_glx_server_vendor(self):
        return glXQueryServerString(self, 0, GLX_VENDOR)

    def get_glx_server_version(self):
        # glXQueryServerString was introduced in GLX 1.1, so we need to use the
        # 1.0 function here which queries the server implementation for its
        # version.
        major = c_int()
        minor = c_int()
        if not glXQueryVersion(self, byref(major), byref(minor)):
            raise XlibException('Could not determine GLX server version')
        return '%s.%s'%(major.value, minor.value)

    def get_glx_server_extensions(self):
        return glXQueryServerString(self, 0, GLX_EXTENSIONS).split()

    def get_glx_client_vendor(self):
        return glXGetClientString(self, GLX_VENDOR)

    def get_glx_client_version(self):
        return glXGetClientString(self, GLX_VERSION)

    def get_glx_client_extensions(self):
        return glXGetClientString(self, GLX_EXTENSIONS).split()

    def get_glx_extensions(self):
        return glXQueryExtensionsString(self, 0).split()

class XlibScreen(BaseScreen):
    def __init__(self, display, x_screen_id, x, y, width, height, xinerama):
        super(XlibScreen, self).__init__(x, y, width, height)
        self._display = display
        self._x_screen_id = x_screen_id
        self._xinerama = xinerama

    def __repr__(self):
        return 'XlibScreen(screen=%d, x=%d, y=%d, ' \
               'width=%d, height=%d, xinerama=%d)' % \
            (self._x_screen_id, self.x, self.y, self.width, self.height,
             self._xinerama)

class XlibGLConfig(BaseGLConfig):
    attribute_ids = {
        'buffer_size': GLX_BUFFER_SIZE,
        'level': GLX_LEVEL,
        'doublebuffer': GLX_DOUBLEBUFFER,
        'stereo': GLX_STEREO,
        'aux_buffers': GLX_AUX_BUFFERS,
        'red_size': GLX_RED_SIZE,
        'green_size': GLX_GREEN_SIZE,
        'blue_size': GLX_BLUE_SIZE,
        'alpha_size': GLX_ALPHA_SIZE,
        'depth_size': GLX_DEPTH_SIZE,
        'stencil_size': GLX_STENCIL_SIZE,
        'accum_red_size': GLX_ACCUM_RED_SIZE,
        'accum_green_size': GLX_ACCUM_GREEN_SIZE,
        'accum_blue_size': GLX_ACCUM_BLUE_SIZE,
        'accum_alpha_size': GLX_ACCUM_ALPHA_SIZE,
    }

    def get_gl_attributes(self):
        return self._attributes

    def get_visual_info(self):
        raise NotImplementedError('abstract')

    def create_context(self, context_share):
        raise NotImplementedError('abstract')

class XlibGLConfig10(XlibGLConfig):
    def __init__(self, display, screen, attrib_list):
        super(XlibGLConfig10, self).__init__()
        self._display = display
        self._screen = screen
        self._attrib_list = attrib_list
        self._visual_info = glXChooseVisual(self._display,
            screen._x_screen_id, self._attrib_list)
        if not self._visual_info:
            raise XlibException('No conforming visual exists')

        self._attributes = {}
        for name, attr in self.attribute_ids.items():
            value = c_int()
            result = glXGetConfig(self._display,
                self._visual_info, attr, byref(value))
            if result >= 0:
                self._attributes[name] = value.value

    def get_visual_info(self):
        return self._visual_info.contents

    def create_context(self, context_share):
        if context_share:
            return glXCreateContext(self._display, self._visual_info,
                context_share._context, True)
        else:
            return glXCreateContext(self._display, self._visual_info,
                None, True)

class XlibGLConfig10ATI(XlibGLConfig10):
    attribute_ids = XlibGLConfig.attribute_ids.copy()
    del attribute_ids['stereo']

class XlibGLConfig13(XlibGLConfig):
    attribute_ids = XlibGLConfig.attribute_ids.copy()
    attribute_ids.update({
        'sample_buffers': GLX_SAMPLE_BUFFERS,
        'samples': GLX_SAMPLES,
        'render_type': GLX_RENDER_TYPE,
        'config_caveat': GLX_CONFIG_CAVEAT,
        'transparent_type': GLX_TRANSPARENT_TYPE,
        'transparent_index_value': GLX_TRANSPARENT_INDEX_VALUE,
        'transparent_red_value': GLX_TRANSPARENT_RED_VALUE,
        'transparent_green_value': GLX_TRANSPARENT_GREEN_VALUE,
        'transparent_blue_value': GLX_TRANSPARENT_BLUE_VALUE,
        'transparent_alpha_value': GLX_TRANSPARENT_ALPHA_VALUE,
        'x_renderable': GLX_X_RENDERABLE,
    })

    def __init__(self, display, screen, fbconfig):
        super(XlibGLConfig13, self).__init__()
        self._display = display
        self._screen = screen
        self._fbconfig = fbconfig
        self._attributes = {}
        for name, attr in self.attribute_ids.items():
            value = c_int()
            result = glXGetFBConfigAttrib(self._display, 
                self._fbconfig, attr, byref(value))
            if result >= 0:
                self._attributes[name] = value.value

    def get_visual_info(self):
        return glXGetVisualFromFBConfig(self._display, self._fbconfig).contents

    def create_context(self, context_share):
        if context_share:
            return glXCreateNewContext(self._display, self._fbconfig,
                GLX_RGBA_TYPE, context_share._context, True)
        else:
            return glXCreateNewContext(self._display, self._fbconfig,
                GLX_RGBA_TYPE, None, True)

class XlibGLContext(BaseGLContext):
    def __init__(self, display, context, share):
        super(XlibGLContext, self).__init__(share)
        self._display = display
        self._context = context

    def destroy(self):
        super(XlibGLContext, self).destroy()
        glXDestroyContext(self._display, self._context)

    def is_direct(self):
        return glXIsDirect(self._display, self._context)


_xlib_event_handler_names = []

def XlibEventHandler(event):
    def handler_wrapper(f):
        _xlib_event_handler_names.append(f.__name__)
        if not hasattr(f, '_xlib_handler'):
            f._xlib_handler = []
        f._xlib_handler.append(event)
        return f
    return handler_wrapper

class XlibMouse(object):
    def __init__(self):
        self.x, self.y = 0, 0
        self.buttons = [False] * 6      # mouse buttons index from 1 + 

class XlibWindow(BaseWindow):
    _display = None         # X display connection
    _screen_id = None       # X screen index
    _glx_context = None     # GLX context handle
    _glx_window = None      # GLX window handle
    _window = None          # Xlib window handle
    _minimum_size = None
    _maximum_size = None
    _vsync = None

    _x = 0
    _y = 0                  # Last known window position
    _width = 0
    _height = 0             # Last known window size
    _mouse = None           # Last known mouse position and button state
    _ignore_motion = False  # Set to true to skip the next mousemotion event
    _exclusive_mouse = False
    _exclusive_mouse_client = None
    _exclusive_keyboard = False
    _mapped = False
    _lost_context = False
    _lost_context_state = False

    _default_event_mask = (0x1ffffff 
        & ~PointerMotionHintMask
        & ~ResizeRedirectMask)

    def __init__(self):
        super(XlibWindow, self).__init__()
        self._mouse = XlibMouse()

        # Bind event handlers
        self._event_handlers = {}
        for func_name in _xlib_event_handler_names:
            if not hasattr(self, func_name):
                continue
            func = getattr(self, func_name)
            for message in func._xlib_handler:
                self._event_handlers[message] = func

    def create(self, factory):
        # Unmap existing window if necessary while we fiddle with it.
        if self._window:
            self._unmap()

        # If flipping to/from fullscreen and using override_redirect,
        # need to recreate the window.
        # A possible improvement could be to just hide the top window,
        # destroy the GLX window, and reshow it again when leaving fullscreen.
        # This would prevent the floating window from being moved by the
        # WM.
        if self._window and factory.get_fullscreen() != self._fullscreen:
            # clear out the GLX context
            glFlush()
            glXMakeCurrent(self._display, 0, 0)
            if self._glx_window:
                glXDestroyWindow(self._display, self._glx_window)
            xlib.XDestroyWindow(self._display, self._window)
            self._glx_window = None
            self._window = None

        super(XlibWindow, self).create(factory)
        config = factory.get_config()
        screen = config._screen
        context = factory.get_context()
        fullscreen = factory.get_fullscreen()

        # TODO: detect state loss only by examining context share.
        if self._glx_context and self._glx_context != context._context:
            self._lost_context = True
            self._lost_context_state = True

        self._display = config._display
        self._screen_id = config._screen._x_screen_id
        self._glx_context = context._context
        self._width, self._height = factory.get_size()

        self._glx_1_3 = self._display.contents.have_glx_version(1, 3)

        # Create X window if not already existing.
        if not self._window:
            root = xlib.XRootWindow(self._display, self._screen_id)

            visual_info = config.get_visual_info()

            visual = visual_info.visual
            visual_id = xlib.XVisualIDFromVisual(visual)
            default_visual = xlib.XDefaultVisual(self._display, self._screen_id)
            default_visual_id = xlib.XVisualIDFromVisual(default_visual)
            window_attributes = XSetWindowAttributes()
            if visual_id != default_visual_id:
                window_attributes.colormap = xlib.XCreateColormap(
                    self._display, root, visual, AllocNone)
            else:
                window_attributes.colormap = xlib.XDefaultColormap(
                    self._display, self._screen_id)
            self._window = xlib.XCreateWindow(self._display, root,
                0, 0, self._width, self._height, 0, visual_info.depth,
                InputOutput, visual, CWColormap, byref(window_attributes))

            # Setting null background pixmap disables drawing the background,
            # preventing flicker while resizing.
            xlib.XSetWindowBackgroundPixmap(self._display, self._window,
                c_void_p())

            # Enable WM_DELETE_WINDOW message
            wm_delete_window = xlib.XInternAtom(self._display,
                'WM_DELETE_WINDOW', False)
            wm_delete_window = c_ulong(wm_delete_window)
            xlib.XSetWMProtocols(self._display, self._window,
                byref(wm_delete_window), 1)

        # Set window attributes
        attributes = XSetWindowAttributes()
        attributes_mask = 0

        # Bypass the window manager in fullscreen.  This is the only reliable
        # technique (over _NET_WM_STATE_FULLSCREEN, Motif, KDE and Gnome
        # hints) that is pretty much guaranteed to work.  Unfortunately
        # we run into window activation and focus problems that require
        # attention.  Search for "override_redirect" for all occurences.
        attributes.override_redirect = fullscreen
        attributes_mask |= CWOverrideRedirect

        if fullscreen:
            xlib.XMoveResizeWindow(self._display, self._window, 
                screen.x, screen.y, screen.width, screen.height)
        else:
            xlib.XResizeWindow(self._display, self._window, 
                self._width, self._height)

        xlib.XChangeWindowAttributes(self._display, self._window, 
            attributes_mask, byref(attributes))

        # Set vsync if requested
        vsync = factory.get_vsync()
        if vsync is not None:
            self.set_vsync(vsync)

    def _map(self):
        if self._mapped:
            return

        # Map the window, wait for map event before continuing.
        xlib.XSelectInput(self._display, self._window, StructureNotifyMask)
        xlib.XMapRaised(self._display, self._window)
        e = XEvent()
        while True:
            xlib.XNextEvent(self._display, e)
            if e.type == MapNotify:
                break

        xlib.XSelectInput(self._display, self._window, self._default_event_mask)
        self._mapped = True

        if self._fullscreen:
            self.activate()

        self.dispatch_event(EVENT_RESIZE, *self.get_size())
        self.dispatch_event(EVENT_EXPOSE)

    def _unmap(self):
        if not self._mapped:
            return

        xlib.XSelectInput(self._display, self._window, StructureNotifyMask)
        xlib.XUnmapWindow(self._display, self._window)
        e = XEvent()
        while True:
            xlib.XNextEvent(self._display, e)
            if e.type == UnmapNotify:
                break

        xlib.XSelectInput(self._display, self._window, self._default_event_mask)
        self._mapped = False

    def _get_root(self):
        attributes = XWindowAttributes()
        xlib.XGetWindowAttributes(self._display, self._window,
                                  byref(attributes))
        return attributes.root

    def close(self):
        # clear out the GLX context
        glFlush()
        glXMakeCurrent(self._display, 0, 0)

        self._unmap()
        if self._glx_window:
            glXDestroyWindow(self._display, self._glx_window)
        if self._window:
            xlib.XDestroyWindow(self._display, self._window)
        super(XlibWindow, self).close()

        self._window = None
        self._glx_window = None

    def switch_to(self):
        if self._glx_1_3:
            if not self._glx_window:
                self._glx_window = glXCreateWindow(self._display,
                    self._config._fbconfig, self._window, None)
            glXMakeContextCurrent(self._display,
                self._glx_window, self._glx_window, self._glx_context)
        else:
            glXMakeCurrent(self._display, self._window, self._glx_context)

        self._context.set_current()
        pyglet.GL.info.set_context()
        pyglet.GLU.info.set_context()

        if self._lost_context:
            self._lost_context = False
            self.dispatch_event(EVENT_CONTEXT_LOST)
        if self._lost_context_state:
            self._lost_context_state = False
            self.dispatch_event(EVENT_CONTEXT_STATE_LOST)

    def flip(self):
        if self._vsync and _have_SGI_video_sync:
            count = c_uint()
            glXGetVideoSyncSGI(byref(count))
            glXWaitVideoSyncSGI(2, (count.value + 1) % 2, byref(count))

        if self._glx_1_3:
            if not self._glx_window:
                self._glx_window = glXCreateWindow(self._display,
                    self._config._fbconfig, self._window, None)
            glXSwapBuffers(self._display, self._glx_window)
        else:
            glXSwapBuffers(self._display, self._window)

    def get_vsync(self):
        return self._vsync

    def set_vsync(self, vsync):
        self._vsync = vsync

    def set_caption(self, caption):
        self._caption = caption
        self._set_property('WM_NAME', caption, allow_utf8=False)
        self._set_property('WM_ICON_NAME', caption, allow_utf8=False)
        self._set_property('_NET_WM_NAME', caption)
        self._set_property('_NET_WM_ICON_NAME', caption)

    def get_caption(self):
        return self._caption

    def set_size(self, width, height):
        xlib.XResizeWindow(self._display, self._window, width, height)

    def get_size(self):
        # XGetGeometry and XWindowAttributes seem to always return the
        # original size of the window, which is wrong after the user
        # has resized it.
        # XXX this is probably fixed now, with fix of resize.
        return self._width, self._height

    def set_location(self, x, y):
        # Assume the window manager has reparented our top-level window
        # only once, in which case attributes.x/y give the offset from
        # the frame to the content window.  Better solution would be
        # to use _NET_FRAME_EXTENTS, where supported.
        attributes = XWindowAttributes()
        xlib.XGetWindowAttributes(self._display, self._window,
                                  byref(attributes))
        # XXX at least under KDE's WM these attrs are both 0
        x -= attributes.x
        y -= attributes.y
        xlib.XMoveWindow(self._display, self._window, x, y)

    def get_location(self):
        child = WindowRef()
        x = c_int()
        y = c_int()
        xlib.XTranslateCoordinates(self._display,
                                   self._window,
                                   self._get_root(),
                                   0, 0,
                                   byref(x),
                                   byref(y),
                                   byref(child))
        return x.value, y.value

    def activate(self):
        xlib.XSetInputFocus(self._display, self._window,
            RevertToParent, CurrentTime)

    def set_visible(self, visible=True):
        if visible:
            self._map()
        else:
            self._unmap()

    def set_minimum_size(self, width, height):
        self._minimum_size = width, height
        self._set_wm_normal_hints()

    def set_maximum_size(self, width, height):
        self._maximum_size = width, height
        self._set_wm_normal_hints()

    def minimize(self):
        xlib.XIconifyWindow(self._display, self._window, self._screen_id)

    def maximize(self):
        self._set_wm_state('_NET_WM_STATE_MAXIMIZED_HORZ',
                           '_NET_WM_STATE_MAXIMIZED_VERT')

    def set_exclusive_mouse(self, exclusive=True):
        if exclusive == self._exclusive_mouse:
            return

        if exclusive:
            # Hide pointer by creating an empty cursor
            black = xlib.XBlackPixel(self._display, self._screen_id)
            black = c_int(black)
            bmp = xlib.XCreateBitmapFromData(self._display, self._window,
                (c_byte * 8)(), 8, 8)
            cursor = xlib.XCreatePixmapCursor(self._display, bmp, bmp,
                byref(black), byref(black), 0, 0)
            xlib.XDefineCursor(self._display, self._window, cursor)
            xlib.XFreeCursor(self._display, cursor)
            xlib.XFreePixmap(self._display, bmp)

            # Restrict to client area
            xlib.XGrabPointer(self._display, self._window,
                True,
                0,
                GrabModeAsync,
                GrabModeAsync,
                self._window,
                0,
                CurrentTime)

            # Move pointer to center of window
            x = self._width / 2
            y = self._height / 2
            self._exclusive_mouse_client = x, y
            xlib.XWarpPointer(self._display,
                0,              # src window
                self._window,   # dst window
                0, 0,           # src x, y
                0, 0,           # src w, h
                x, y)
            self._ignore_motion = True
        else:
            # Restore cursor
            xlib.XUndefineCursor(self._display, self._window)

            # Unclip
            xlib.XUngrabPointer(self._display, CurrentTime)

        self._exclusive_mouse = exclusive

    def set_exclusive_keyboard(self, exclusive=True):
        if exclusive == self._exclusive_keyboard:
            return
        
        self._exclusive_keyboard = exclusive
        if exclusive:
            xlib.XGrabKeyboard(self._display,
                self._window,
                False,
                GrabModeAsync,
                GrabModeAsync,
                CurrentTime)
        else:
             xlib.XUngrabKeyboard(self._display, CurrentTime)

    # Private utility

    def _set_wm_normal_hints(self):
        hints = XSizeHints.from_address(xlib.XAllocSizeHints())
        if self._minimum_size:
            hints.flags |= PMinSize
            hints.min_width, hints.min_height = self._minimum_size
        if self._maximum_size:
            hints.flags |= PMaxSize
            hints.max_width, hints.max_height = self._maximum_size
        xlib.XSetWMNormalHints(self._display, self._window, byref(hints))

    def _set_property(self, name, value, allow_utf8=True):
        atom = xlib.XInternAtom(self._display, name, True)
        if not atom:
            raise XlibException('Undefined atom "%s"' % name)
        if type(value) in (str, unicode):
            property = XTextProperty()
            if _have_utf8 and allow_utf8:
                buf = create_string_buffer(value.encode('utf8'))
                result = xlib.Xutf8TextListToTextProperty(self._display,
                    byref(pointer(buf)), 1, XUTF8StringStyle, byref(property))
                if result < 0:
                    raise XlibException('Could not create UTF8 text property')
            else:
                buf = create_string_buffer(value.encode('ascii', 'ignore'))
                result = xlib.XStringListToTextProperty(byref(pointer(buf)),
                    1, byref(property))
                if result < 0:
                    raise XlibException('Could not create text property')
            xlib.XSetTextProperty(self._display,
                self._window, byref(property), atom)
            # XXX <rj> Xlib doesn't like us freeing this
            #xlib.XFree(property.value)

    def _set_wm_state(self, *states):
        # Set property
        net_wm_state = xlib.XInternAtom(self._display, '_NET_WM_STATE', False)
        atoms = []
        for state in states:
            atoms.append(xlib.XInternAtom(self._display, state, False))
        atom_type = xlib.XInternAtom(self._display, 'ATOM', False)
        if len(atoms):
            atoms_ar = (Atom * len(atoms))(*atoms)
            xlib.XChangeProperty(self._display, self._window,
                net_wm_state, atom_type, 32, PropModePrepend,
                atoms_ar, len(atoms))
        else:
            xlib.XDeleteProperty(self._display, self._window, net_wm_state)

        # Nudge the WM
        e = XEvent()
        e.xclient.type = ClientMessage
        e.xclient.message_type = net_wm_state
        e.xclient.display = self._display
        e.xclient.window = self._window
        e.xclient.format = 32
        e.xclient.data.l[0] = PropModePrepend
        for i, atom in enumerate(atoms):
            e.xclient.data.l[i + 1] = atom
        xlib.XSendEvent(self._display, self._get_root(),
            False, SubstructureRedirectMask, byref(e))

    # Event handling

    def dispatch_events(self):
        e = XEvent()

        # Check for the events specific to this window
        while xlib.XCheckWindowEvent(self._display, self._window,
                0x1ffffff, byref(e)):
            event_handler = self._event_handlers.get(e.type)
            if event_handler:
                event_handler(e)

        # Now check generic events for this display and manually filter
        # them to see whether they're for this window. sigh.
        # Store off the events we need to push back so we don't confuse
        # XCheckTypedEvent
        push_back = []
        while xlib.XCheckTypedEvent(self._display, ClientMessage, byref(e)):
            if e.xclient.window != self._window:
                push_back.append(e)
                e = XEvent()
            else:
                event_handler = self._event_handlers.get(e.type)
                if event_handler:
                    event_handler(e)
        for e in push_back:
            xlib.XPutBackEvent(self._display, byref(e))

    @staticmethod
    def _translate_modifiers(state):
        modifiers = 0
        if state & ShiftMask:
            modifiers |= MOD_SHIFT
        if state & ControlMask:
            modifiers |= MOD_CTRL
        if state & LockMask:
            modifiers |= MOD_CAPSLOCK
        if state & Mod1Mask:
            modifiers |= MOD_ALT
        if state & Mod2Mask:
            modifiers |= MOD_NUMLOCK
        if state & Mod4Mask:
            modifiers |= MOD_WINDOWS
        return modifiers

    # Event handlers

    @XlibEventHandler(KeyPress)
    @XlibEventHandler(KeyRelease)
    def _event_key(self, event):
        if event.type == KeyRelease:
            # Look in the queue for a matching KeyPress with same timestamp,
            # indicating an auto-repeat rather than actual key event.
            auto_event = XEvent()
            result = xlib.XCheckTypedWindowEvent(self._display,
                self._window, KeyPress, byref(auto_event))
            if result and abs(event.xkey.time - auto_event.xkey.time) < 4:
                buffer = create_string_buffer(16)
                count = xlib.XLookupString(byref(auto_event),
                                           byref(buffer),
                                           len(buffer),
                                           c_void_p(),
                                           c_void_p())
                if count:
                    text = buffer.value[:count]
                    self.dispatch_event(EVENT_TEXT, text)
                return
            elif result:
                # Whoops, put the event back, it's for real.
                xlib.XPutBackEvent(self._display, byref(event))

        # pyglet.self.key keysymbols are identical to X11 keysymbols, no
        # need to map the keysymbol.
        text = None 
        if event.type == KeyPress:
            buffer = create_string_buffer(16)
            # TODO lookup UTF8
            count = xlib.XLookupString(byref(event),
                                       byref(buffer),
                                       len(buffer),
                                       c_void_p(),
                                       c_void_p())
            if count:
                text = unicode(buffer.value[:count])
        symbol = xlib.XKeycodeToKeysym(self._display, event.xkey.keycode, 0)

        modifiers = self._translate_modifiers(event.xkey.state)

        if event.type == KeyPress:
            self.dispatch_event(EVENT_KEY_PRESS, symbol, modifiers)
            if (text and 
                (unicodedata.category(text) != 'Cc' or text == '\r')):
                self.dispatch_event(EVENT_TEXT, text)
        elif event.type == KeyRelease:
            self.dispatch_event(EVENT_KEY_RELEASE, symbol, modifiers)

    @XlibEventHandler(MotionNotify)
    def _event_motionnotify(self, event):
        x = event.xmotion.x
        y = self.height - event.xmotion.y

        if self._ignore_motion:
            # Ignore events caused by XWarpPointer
            self._ignore_motion = False
            self._mouse.x = x
            self._mouse.y = y
            return

        if self._exclusive_mouse:
            # Reset pointer position
            xlib.XWarpPointer(self._display,
                0,
                self._window,
                0, 0,
                0, 0,
                self._exclusive_mouse_client[0],
                self._exclusive_mouse_client[1])
            self._ignore_motion = True

        dx = x - self._mouse.x
        dy = y - self._mouse.y

        self._mouse.x = x
        self._mouse.y = y

        buttons = 0
        if event.xmotion.state & Button1MotionMask:
            buttons |= MOUSE_LEFT_BUTTON
        if event.xmotion.state & Button2MotionMask:
            buttons |= MOUSE_MIDDLE_BUTTON
        if event.xmotion.state & Button3MotionMask:
            buttons |= MOUSE_RIGHT_BUTTON

        if buttons:
            # Drag event
            modifiers = self._translate_modifiers(event.xmotion.state)
            self.dispatch_event(EVENT_MOUSE_DRAG,
                x, y, dx, dy, buttons, modifiers)
        else:
            # Motion event
            self.dispatch_event(EVENT_MOUSE_MOTION, x, y, dx, dy)

    @XlibEventHandler(ClientMessage)
    def _event_clientmessage(self, event):
        wm_delete_window = xlib.XInternAtom(event.xclient.display,
            'WM_DELETE_WINDOW', False)
        if event.xclient.data.l[0] == wm_delete_window:
            self.dispatch_event(EVENT_CLOSE)
        else:
            raise NotImplementedError

    @XlibEventHandler(ButtonPress)
    @XlibEventHandler(ButtonRelease)
    def _event_button(self, event):
        x = event.xbutton.x
        y = self.height - event.xbutton.y
        modifiers = self._translate_modifiers(event.xbutton.state)
        if event.type == ButtonPress:
            if event.xbutton.button == 4:
                self.dispatch_event(EVENT_MOUSE_SCROLL, 0, 1)
            elif event.xbutton.button == 5:
                self.dispatch_event(EVENT_MOUSE_SCROLL, 0, -1)
            else:
                self._mouse.buttons[event.xbutton.button] = True
                self.dispatch_event(EVENT_MOUSE_PRESS, event.xbutton.button,
                    x, y, modifiers)
        else:
            if event.xbutton.button < 4:
                self._mouse.buttons[event.xbutton.button] = False
                self.dispatch_event(EVENT_MOUSE_RELEASE, event.xbutton.button,
                    x, y, modifiers)

    @XlibEventHandler(Expose)
    def _event_expose(self, event):
        # Ignore all expose events except the last one. We could be told
        # about exposure rects - but I don't see the point since we're
        # working with OpenGL and we'll just redraw the whole scene.
        if event.xexpose.count > 0: return
        self.dispatch_event(EVENT_EXPOSE)

    @XlibEventHandler(EnterNotify)
    def _event_enternotify(self, event):
        # figure active mouse buttons
        # XXX ignore modifier state?
        state = event.xcrossing.state
        self._mouse.buttons[1] = state & Button1Mask
        self._mouse.buttons[2] = state & Button2Mask
        self._mouse.buttons[3] = state & Button3Mask
        self._mouse.buttons[4] = state & Button4Mask
        self._mouse.buttons[5] = state & Button5Mask

        # mouse position
        x = self._mouse.x = event.xcrossing.x
        y = self._mouse.y = self.height - event.xcrossing.y

        # XXX there may be more we could do here
        self.dispatch_event(EVENT_MOUSE_ENTER, x, y)

    @XlibEventHandler(LeaveNotify)
    def _event_leavenotify(self, event):
        x = self._mouse.x = event.xcrossing.x
        y = self._mouse.y = self.height - event.xcrossing.y
        self.dispatch_event(EVENT_MOUSE_LEAVE, x, y)

    @XlibEventHandler(ConfigureNotify)
    def _event_configurenotify(self, event):
        w, h = event.xconfigure.width, event.xconfigure.height
        x, y = event.xconfigure.x, event.xconfigure.y
        if self._width != w or self._height != h:
            self._width = w
            self._height = h
            self.switch_to()
            glViewport(0, 0, w, h)
            self.dispatch_event(EVENT_RESIZE, w, h)
            self.dispatch_event(EVENT_EXPOSE)
        if self._x != x or self._y != y:
            self.dispatch_event(EVENT_MOVE, x, y)
            self._x = x
            self._y = y

    @XlibEventHandler(FocusIn)
    def _event_focusin(self, event):
        self.dispatch_event(EVENT_ACTIVATE)

    @XlibEventHandler(FocusOut)
    def _event_focusout(self, event):
        self.dispatch_event(EVENT_DEACTIVATE)

    @XlibEventHandler(MapNotify)
    def _event_mapnotify(self, event):
        self._mapped = True
        self.dispatch_event(EVENT_SHOW)

    @XlibEventHandler(UnmapNotify)
    def _event_unmapnotify(self, event):
        self._mapped = False
        self.dispatch_event(EVENT_HIDE)

xlib.XOpenDisplay.restype = POINTER(XlibDisplay)
