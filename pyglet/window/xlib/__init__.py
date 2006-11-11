#!/usr/bin/env python

'''
Documentation sources for Xlib programming:

http://tronche.com/gui/x/ (specifically xlib/ and icccm/)

http://users.actcom.co.il/~choo/lupg/tutorials/xlib-programming/xlib-programming.html

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *
from ctypes import util
import unicodedata
import warnings

from pyglet.GL.VERSION_1_1 import *
from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *
from pyglet.window.xlib.constants import *
from pyglet.window.xlib.types import *
from pyglet.window.xlib.glx.VERSION_1_4 import *

# Load X11 library, specify argtypes and restype only when necessary.
Display = c_void_p
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
xlib.XOpenDisplay.restype = POINTER(Display)
xlib.XScreenOfDisplay.restype = POINTER(Screen)
xlib.XInternAtom.restype = Atom
xlib.XNextEvent.argtypes = [POINTER(Display), POINTER(XEvent)]
xlib.XCheckTypedWindowEvent.argtypes = [POINTER(Display),
    c_ulong, c_int, POINTER(XEvent)]
xlib.XPutBackEvent.argtypes = [POINTER(Display), POINTER(XEvent)]

# Do we have the November 2000 UTF8 extension?
_have_utf8 = hasattr(xlib, 'Xutf8TextListToTextProperty')

_attribute_ids = {
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
}

class XlibException(WindowException):
    pass

class XlibPlatform(BasePlatform):
    def get_screens(self, factory):
        display = self._get_display(factory)
        x_screen = xlib.XDefaultScreen(display)
        if _have_xinerama and xinerama.XineramaIsActive(display):
            number = c_int()
            infos = xinerama.XineramaQueryScreens(display, byref(number))
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

        # Construct array of attributes for glXChooseFBConfig
        attrs = []
        for name, value in factory.get_gl_attributes().items():
            attr = _attribute_ids.get(name, None)
            if not attr:
                warnings.warn('Unknown GLX attribute "%s"' % name)
            attrs.append(attr)
            attrs.append(int(value))
        if len(attrs):
            attrs.append(0)
            attrs.append(0)
            attrib_list = (c_int * len(attrs))(*attrs)
        else:
            attrib_list = None
        elements = c_int()
        configs = glXChooseFBConfig(display, 
            screen._x_screen_id, attrib_list, byref(elements))
        if configs:
            result = []
            for i in range(elements.value):
                result.append(XlibGLConfig(display, screen, configs[i]))
            xlib.XFree(configs)
            return result
        else:
            return []

    def create_context(self, factory):
        config = factory.get_config()
        context_share = factory.get_context_share()
        if context_share:
            context_share = context_share._context

        context = glXCreateNewContext(config._display, config._fbconfig, 
            GLX_RGBA_TYPE, context_share, True)

        if context == GLXBadContext:
            raise XlibException('Invalid context share')
        elif context == GLXBadFBConfig:
            raise XlibException('Invalid GL configuration')
        elif context < 0:
            raise XlibException('Could not create GL context') 

        return XlibGLContext(config._display, context)

    def create_window(self):
        return XlibWindow()

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
    def __init__(self, display, screen, fbconfig):
        super(XlibGLConfig, self).__init__()
        self._display = display
        self._screen = screen
        self._fbconfig = fbconfig
        self._attributes = {}
        for name, attr in _attribute_ids.items():
            value = c_int()
            result = glXGetFBConfigAttrib(self._display, 
                self._fbconfig, attr, byref(value))
            if result >= 0:
                self._attributes[name] = value.value

    def get_gl_attributes(self):
        return self._attributes

class XlibGLContext(BaseGLContext):
    def __init__(self, display, context):
        super(XlibGLContext, self).__init__()
        self._display = display
        self._context = context

    def destroy(self):
        # XXX <rj> I don't think this is a good approach. I think we should
        # let GC handle destroying contexts, especially given that they may
        # be shared... Windows should have a reference to XlibGLContext
        # instances. When those instances are not referenced *then* we're
        # safe to destroy the context.
        # We need to make sure we don't delete any OGL objects
        # (textures, lists, ...) *after* this call is made.
        # Perhaps we need to manually maintain a reference count to
        # XlibGLContext and only when a window is manually close()d will we
        # de-reference and possibly destroy the context. We would still
        # possibly need to make sure we don't subsequently free anything
        # belonging to that context.
        # Hell, we have the problem now if there's multiple contexts and
        # python's GC cleans up textures which are allocated to various
        # contexts...

        # <ah> Contexts are _never_ shared.  We need to control deletion of
        # contexts w.r.t. deletion of windows, so I think GC won't work.
        # I also think tying textures to GC is a bad idea... these are
        # external resources, not memory blocks.  A bit of manual memory
        # management never hurt anybody.
        # Alternatively, we can defer freeing of textures and lists etc
        # by queuing them up until the next switch_to, if the context is
        # not already active (as it would be in most single-window apps).

        super(XlibGLContext, self).destroy()
        glXDestroyContext(self._display, self._context)

_xlib_event_handler_types = []

def XlibEventHandler(event):
    def handler_wrapper(f):
        handler = (event, f.__name__)
        _xlib_event_handler_types.append(handler)
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

    _x = 0
    _y = 0                  # Last known window position
    _width = 0
    _height = 0             # Last known window size
    _mouse = None           # Last known mouse position and button state

    _default_event_mask = (0x1ffffff 
        & ~PointerMotionHintMask
        & ~ResizeRedirectMask)

    def __init__(self):
        super(XlibWindow, self).__init__()
        self._mouse = XlibMouse()

        # Bind event handlers
        self._event_handlers = {}
        for event, func_name in _xlib_event_handler_types:
            func = getattr(self, func_name)
            self._event_handlers[event] = func

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
            glXDestroyWindow(self._display, self._glx_window)
            xlib.XDestroyWindow(self._display, self._window)
            self._glx_window = None
            self._window = None

        super(XlibWindow, self).create(factory)
        config = factory.get_config()
        screen = config._screen
        context = factory.get_context()
        fullscreen = factory.get_fullscreen()

        self._display = config._display
        self._screen_id = config._screen._x_screen_id
        self._glx_context = context._context
        self._width, self._height = factory.get_size()

        # Create X window if not already existing.
        if not self._window:
            root = xlib.XRootWindow(self._display, self._screen_id)
            black = xlib.XBlackPixel(self._display, self._screen_id)

            self._window = xlib.XCreateSimpleWindow(self._display, root,
                0, 0, self._width, self._height, 0, black, black)

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

        self._map()
        if fullscreen:
            # Explicitly set focus to window if using override_redirect.
            xlib.XSetInputFocus(self._display, self._window,
                RevertToParent, CurrentTime)

        if not self._glx_window:
            self._glx_window = glXCreateWindow(self._display,
                config._fbconfig, self._window, None)

        self.switch_to()
        self.dispatch_event(EVENT_EXPOSE)

    def _map(self):
        # Map the window, wait for map event before continuing.
        xlib.XSelectInput(self._display, self._window, StructureNotifyMask)
        xlib.XMapRaised(self._display, self._window)
        e = XEvent()
        while True:
            xlib.XNextEvent(self._display, e)
            if e.type == MapNotify:
                break

        xlib.XSelectInput(self._display, self._window, self._default_event_mask)

    def _unmap(self):
        xlib.XSelectInput(self._display, self._window, StructureNotifyMask)
        xlib.XUnmapWindow(self._display, self._window)
        e = XEvent()
        while True:
            xlib.XNextEvent(self._display, e)
            if e.type == UnmapNotify:
                break

        xlib.XSelectInput(self._display, self._window, self._default_event_mask)

    def _get_root(self):
        attributes = XWindowAttributes()
        xlib.XGetWindowAttributes(self._display, self._window,
                                  byref(attributes))
        return attributes.root

    def close(self):
        # XXX <rj> I'm pretty sure we need to invoke
        # glXMakeContextCurrent(self._display, None, None, None) or
        # similar. I did discover that from test to test
        # it's the glXMakeContextCurrent() call for the new window (in
        # switch_to() that makes the old window go away. hence my theory
        # that we need to "release the current context without assigning
        # a new one"... So here's a call... But it doesn't seem to work
        # There might be some subtle ordering of calls that's needed.
        # Remarkably little seems to be written about applications that
        # might want to actually close a glx window cleanly...
        # glXMakeContextCurrent(self._display, None, None, None)
        
        # <ah> I'm pretty sure you're wrong.  GL has no capability for
        # disabling the API, so no point trying to set a null context;
        # just don't do anything after it's destroyed.

        self._unmap()
        glXDestroyWindow(self._display, self._glx_window)
        xlib.XDestroyWindow(self._display, self._window)
        super(XlibWindow, self).close()

        self._window = None
        self._glx_window = None

    def switch_to(self):
        glXMakeContextCurrent(self._display,
            self._glx_window, self._glx_window, self._glx_context)

    def flip(self):
        glXSwapBuffers(self._display, self._glx_window)

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
        child = Window()
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

    # Private utility

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

    def _set_wm_state(self, state, add=True):
        e = XEvent()
        net_wm_state = xlib.XInternAtom(self._display, '_NET_WM_STATE', True)
        net_state = xlib.XInternAtom(self._display, state, True)
        e.xclient.type = ClientMessage
        e.xclient.message_type = net_wm_state
        e.xclient.display = self._display
        e.xclient.window = self._window
        e.xclient.format = 32
        e.xclient.data.l[0] = int(add) 
        e.xclient.data.l[1] = net_state
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
            if result and event.xkey.time == auto_event.xkey.time:
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
        y = event.xmotion.y
        dx = x - self._mouse.x
        dy = y - self._mouse.y
        self._mouse.x = x
        self._mouse.y = y
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
        modifiers = self._translate_modifiers(event.xbutton.state)
        if event.type == ButtonPress:
            if event.xbutton.button == 4:
                self.dispatch_event(EVENT_MOUSE_SCROLL, 0, 1)
            elif event.xbutton.button == 5:
                self.dispatch_event(EVENT_MOUSE_SCROLL, 0, -1)
            else:
                self._mouse.buttons[event.xbutton.button] = True
                self.dispatch_event(EVENT_MOUSE_PRESS, event.xbutton.button,
                    event.xbutton.x, event.xbutton.y, modifiers)
        else:
            if event.xbutton.button < 4:
                self._mouse.buttons[event.xbutton.button] = False
                self.dispatch_event(EVENT_MOUSE_RELEASE, event.xbutton.button,
                    event.xbutton.x, event.xbutton.y, modifiers)

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
        y = self._mouse.y = event.xcrossing.y

        # XXX there may be more we could do here
        self.dispatch_event(EVENT_MOUSE_ENTER, x, y)

    @XlibEventHandler(LeaveNotify)
    def _event_leavenotify(self, event):
        x = self._mouse.x = event.xcrossing.x
        y = self._mouse.y = event.xcrossing.y
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


