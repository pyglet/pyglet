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

    def create_window(self, factory):
        width, height = factory.get_size()
        window = XlibWindow(factory.get_config(), factory.get_context(), 
                            width, height)
        window._create_window(factory)
        window._set_attributes(factory)
        window._map()
        window._set_glx(factory.get_config())
        return window

    def replace_window(self, factory, window):
        # TODO reparent if changed screens
        window._unmap()
        window._set_attributes(factory)
        window._map()

    def _get_display(self, factory):
        # Get the X display, and resolve name if necessary
        display = factory.get_x_display()
        if not display:
            display = ''
        if type(display) in (str, unicode):
            display = xlib.XOpenDisplay(display)
            if not display:
                raise XlibException('Cannot connect to X server') 
        return display

class XlibScreen(BaseScreen):
    def __init__(self, display, x_screen_id, x, y, width, height, xinerama):
        super(XlibScreen, self).__init__(width, height)
        self._display = display
        self._x_screen_id = x_screen_id
        self._x = x
        self._y = y
        self._xinerama = xinerama

    def __repr__(self):
        return 'XlibScreen(screen=%d, x=%d, y=%d, ' \
               'width=%d, height=%d, xinerama=%d)' % \
            (self._x_screen_id, self._x, self._y, self.width, self.height,
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
        glXDestroyContext(self._display, self._context)

class XlibMouse(object):
    def __init__(self):
        self.x, self.y = 0, 0
        self.buttons = [False] * 6      # mouse buttons index from 1 + 


class XlibWindow(BaseWindow):
    def __init__(self, config, context, width, height):
        super(XlibWindow, self).__init__(config, context, width, height)
        self._display = config._display
        self._screen = config._screen
        self._glx_context = context._context

        # Set by _create_window
        self._window = None

        # Will be set correctly after first configure event.
        self._x = 0
        self._y = 0
        self._mouse = XlibMouse()

    # Creation methods

    def _create_window(self, factory):
        screen = factory.get_screen()
        root = xlib.XDefaultRootWindow(self._display) # XXX correct screen?
        black = xlib.XBlackPixel(self._display, screen._x_screen_id)

        width, height = factory.get_size()
        self._window = xlib.XCreateSimpleWindow(self._display, root,
            0, 0, width, height, 0, black, black)

    def _set_attributes(self, factory):
        fullscreen = factory.get_fullscreen()

        attributes = XSetWindowAttributes()
        attributes_mask = 0

        #####
        # 101 ways to fullscreen a window.

        # Undecorate the window using motif hints
        # XXX.  this doesn't undecorate (toggling out of fullscreen)
        # XXX.  need to raise above taskbar etc.
        '''
        hints = mwmhints_t()
        hints.flags = MWM_HINTS_DECORATIONS
        hints.decorations = MWM_DECOR_BORDER
        prop = xlib.XInternAtom(self._display, '_MOTIF_WM_HINTS', False)
        xlib.XChangeProperty(self._display, self._window,
            prop, prop, 32, PropModeReplace, byref(hints),
            PROP_MWM_HINTS_ELEMENTS)
        '''

        # This works but makes window activation problems.
        #attributes.override_redirect = fullscreen
        #attributes_mask |= CWOverrideRedirect

        # This works, but window size isn't what it's supposed to be.
        # XXX.  apparently not supported on older WMs.
        self._set_wm_state('_NET_WM_STATE_FULLSCREEN', fullscreen)

        #
        ####


        if fullscreen:
            x = self._screen._x
            y = self._screen._y
            width = self._screen.width
            height = self._screen.height
            xlib.XMoveResizeWindow(self._display, self._window, 
                x, y, width, height)
        else:
            width, height = factory.get_size()
            xlib.XResizeWindow(self._display, self._window, width, height)

        xlib.XChangeWindowAttributes(self._display, self._window, 
            attributes_mask, byref(attributes))
        self._fullscreen = fullscreen

    def _map(self):        
        # Listen for WM_DELETE_WINDOW
        wm_delete_window = xlib.XInternAtom(self._display,
            'WM_DELETE_WINDOW', False)
        wm_delete_window = c_ulong(wm_delete_window)
        xlib.XSetWMProtocols(self._display, self._window,
            byref(wm_delete_window), 1)

        # Map the window, listening for the window mapping event
        xlib.XSelectInput(self._display, self._window, StructureNotifyMask)
        xlib.XMapRaised(self._display, self._window)
        e = XEvent()
        while True:
            xlib.XNextEvent(self._display, e)
            if e.type == MapNotify:
                break

        # Now select all events (don't want PointerMotionHintMask)
        xlib.XSelectInput(self._display, self._window, 0x1ffff7f)

    def _unmap(self):
        xlib.XUnmapWindow(self._display, self._window)

    def _set_glx(self, config):
        self._glx_window = glXCreateWindow(self._display,
            config._fbconfig, self._window, None)

    def _get_root(self):
        attributes = XWindowAttributes()
        xlib.XGetWindowAttributes(self._display, self._window,
                                  byref(attributes))
        return attributes.root

    def close(self):
        self._context.destroy()
        glXDestroyWindow(self._display, self._glx_window)
        xlib.XDestroyWindow(self._display, self._window)
        self._window = None

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
        self.width = width
        self.height = height
        xlib.XResizeWindow(self._display, self._window, width, height)

    def get_size(self):
        attributes = XWindowAttributes()
        xlib.XGetWindowAttributes(self._display, self._window,
                                  byref(attributes))
        return attributes.width, attributes.height

    def set_location(self, x, y):
        # Assume the window manager has reparented our top-level window
        # only once, in which case attributes.x/y give the offset from
        # the frame to the content window.  Better solution would be
        # to use _NET_FRAME_EXTENTS, where supported.
        attributes = XWindowAttributes()
        xlib.XGetWindowAttributes(self._display, self._window,
                                  byref(attributes))
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
            event_translator = self.__event_translators.get(e.type)
            if event_translator:
                event_translator(self, e)

        # Now check generic events for this display and manually filter
        # them to see whether they're for this window. sigh.
        # Store off the events we need to push back so we don't confuse
        # XCheckTypedEvent
        push_back = []
        while xlib.XCheckTypedEvent(self._display, ClientMessage, byref(e)):
            if e.xclient.window != self._window:
                push_back.append(e)
                e = XEvent()  # <ah> Let's not break the event we're storing.
            else:
                event_translator = self.__event_translators.get(e.type)
                if event_translator:
                    event_translator(self, e)
        for e in push_back:
            xlib.XPutBackEvent(self._display, byref(e))


    def __translate_key(window, event):
        if event.type == KeyRelease:
            # Look in the queue for a matching KeyPress with same timestamp,
            # indicating an auto-repeat rather than actual key event.
            auto_event = XEvent()
            result = xlib.XCheckTypedWindowEvent(window._display,
                window._window, KeyPress, byref(auto_event))
            if result and event.xkey.time == auto_event.xkey.time:
                buffer = create_string_buffer(16)
                count = xlib.XLookupString(byref(auto_event), 
                                           byref(buffer), 
                                           len(buffer), 
                                           c_void_p(),
                                           c_void_p())
                if count:
                    text = buffer.value[:count]
                    window.dispatch_event(EVENT_TEXT, text)
                return
            elif result:
                # Whoops, put the event back, it's for real.
                xlib.XPutBackEvent(window._display, byref(event))

        # pyglet.window.key keysymbols are identical to X11 keysymbols, no
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
        symbol = xlib.XKeycodeToKeysym(window._display, event.xkey.keycode, 0)

        modifiers = _translate_modifiers(event.xkey.state)

        if event.type == KeyPress:
            window.dispatch_event(EVENT_KEY_PRESS, symbol, modifiers)
            if (text and 
                (unicodedata.category(text) != 'Cc' or text == '\r')):
                window.dispatch_event(EVENT_TEXT, text)
        elif event.type == KeyRelease:
            window.dispatch_event(EVENT_KEY_RELEASE, symbol, modifiers)

    def __translate_motion(window, event):
        x = event.xmotion.x
        y = event.xmotion.y
        dx = x - window._mouse.x
        dy = y - window._mouse.y
        window._mouse.x = x
        window._mouse.y = y
        window.dispatch_event(EVENT_MOUSE_MOTION, x, y, dx, dy)

    def __translate_clientmessage(window, event):
        wm_delete_window = xlib.XInternAtom(event.xclient.display,
            'WM_DELETE_WINDOW', False)
        if event.xclient.data.l[0] == wm_delete_window:
            window.dispatch_event(EVENT_CLOSE)
        else:
            raise NotImplementedError

    def __translate_button(window, event):
        modifiers = _translate_modifiers(event.xbutton.state)
        if event.type == ButtonPress:
            if event.xbutton.button == 4:
                window.dispatch_event(EVENT_MOUSE_SCROLL, 0, 1)
            elif event.xbutton.button == 5:
                window.dispatch_event(EVENT_MOUSE_SCROLL, 0, -1)
            else:
                window._mouse.buttons[event.xbutton.button] = True
                window.dispatch_event(EVENT_MOUSE_PRESS, event.xbutton.button,
                    event.xbutton.x, event.xbutton.y, modifiers)
        else:
            if event.xbutton.button < 4:
                window._mouse.buttons[event.xbutton.button] = False
                window.dispatch_event(EVENT_MOUSE_RELEASE, event.xbutton.button,
                    event.xbutton.x, event.xbutton.y, modifiers)

    def __translate_expose(window, event):
        # Ignore all expose events except the last one. We could be told
        # about exposure rects - but I don't see the point since we're
        # working with OpenGL and we'll just redraw the whole scene.
        if event.xexpose.count > 0: return
        window.dispatch_event(EVENT_EXPOSE)

    def __translate_enter(window, event):
        # figure active mouse buttons
        # XXX ignore modifier state?
        state = event.xcrossing.state
        window._mouse.buttons[1] = state & Button1Mask
        window._mouse.buttons[2] = state & Button2Mask
        window._mouse.buttons[3] = state & Button3Mask
        window._mouse.buttons[4] = state & Button4Mask
        window._mouse.buttons[5] = state & Button5Mask

        # mouse position
        x = window._mouse.x = event.xcrossing.x
        y = window._mouse.y = event.xcrossing.y

        # XXX there may be more we could do here
        window.dispatch_event(EVENT_MOUSE_ENTER, x, y)

    def __translate_leave(window, event):
        # XXX do we care about mouse buttons?
        x = window._mouse.x = event.xcrossing.x
        y = window._mouse.y = event.xcrossing.y
        window.dispatch_event(EVENT_MOUSE_LEAVE, x, y)

    def __translate_configure(window, event):
        w, h = event.xconfigure.width, event.xconfigure.height
        x, y = event.xconfigure.x, event.xconfigure.y
        if window.width != w or window.height != h:
            window.dispatch_event(EVENT_RESIZE, w, h)
            window.width = w
            window.height = h
            window.switch_to()
            glViewport(0, 0, w, h)
            window.dispatch_event(EVENT_EXPOSE)
        if window._x != x or window._y != y:
            window.dispatch_event(EVENT_MOVE, x, y)
            window._x = x
            window._y = y

    __event_translators = {
        KeyPress: __translate_key,
        KeyRelease: __translate_key,
        MotionNotify: __translate_motion,
        ButtonPress: __translate_button,
        ButtonRelease: __translate_button,
        ClientMessage: __translate_clientmessage,
        Expose: __translate_expose,
        EnterNotify: __translate_enter,
        LeaveNotify: __translate_leave,
        ConfigureNotify: __translate_configure,
    }

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


