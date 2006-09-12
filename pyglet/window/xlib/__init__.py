#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *

from pyglet.window import *
from pyglet.window.xlib.constants import *
from pyglet.window.xlib.types import *
from pyglet.window.xlib.glx.VERSION_1_4 import *

# Load X11 library, specify argtypes and restype only when necessary.
Display = c_void_p
xlib = cdll.LoadLibrary('libX11.so')
xlib.XOpenDisplay.argtypes = [c_char_p]
xlib.XOpenDisplay.restype = POINTER(Display)
xlib.XNextEvent.argtypes = [POINTER(Display), POINTER(XEvent)]

# Do we have the November 2000 UTF8 extension?
_have_utf8 = hasattr(xlib, 'Xutf8TextListToTextProperty')

class XlibException(WindowException):
    pass

class XlibWindowFactory(BaseWindowFactory):
    def __init__(self):
        super(XlibWindowFactory, self).__init__()
        self.display = None
        self.config = XlibGLConfig(None)
        self.context = None
        self.context_share = None

    def create_window(self, width=640, height=480):
        display = xlib.XOpenDisplay(self.display)
        if not display:
            raise XlibException('Cannot connect to X server') 

        configs = self.config.get_compatible_list(display)
        if len(configs) == 0:
            raise XlibException('No matching GL configuration available')
        config = configs[0]

        context = glXCreateNewContext(display, 
            config._fbconfig, GLX_RGBA_TYPE, self.context_share, True)
        if context == GLXBadContext:
            raise XlibException('Invalid context share')
        elif context == GLXBadFBConfig:
            raise XlibException('Invalid GL configuration')
        elif context < 0:
            raise XlibException('Could not create GL context')

        window = XlibWindow(width, height, display, config, context)
        return window

class XlibWindow(BaseWindow):
    def __init__(self, width, height, display, config, context):
        self._display = display
        self._config = config
        self._context = context

        black = xlib.XBlackPixel(self._display, 
            xlib.XDefaultScreen(self._display))
        self._window = xlib.XCreateSimpleWindow(self._display,
            xlib.XDefaultRootWindow(self._display), 
            0, 0, width, height, 0, black, black)

        xlib.XSelectInput(self._display, self._window, StructureNotifyMask)
        xlib.XMapWindow(self._display, self._window)

        # Wait for window mapping
        e = XEvent()
        while True:
            xlib.XNextEvent(self._display, e)
            if e.type == MapNotify:
                break

        # Select all events
        xlib.XSelectInput(self._display, self._window, 0x1ffffff)

        # Set GL config and context
        self._glx_window = glXCreateWindow(display,
            config._fbconfig, self._window, None)
        self.switch_to()

        import sys
        self.set_title(sys.argv[0])

    def close(self):
        glXDestroyContext(self._display, self._context)
        glXDestroyWindow(self._display, self._glx_window)
        xlib.XDestroyWindow(self._display, self._window)

    def switch_to(self):
        glXMakeContextCurrent(self._display,
            self._glx_window, self._glx_window, self._context)

    def flip(self):
        glXSwapBuffers(self._display, self._glx_window)

    def get_events(self):
        events = []
        e = XEvent()
        while xlib.XCheckWindowEvent(self._display, 
                                     self._window, 0x1ffffff, byref(e)):

            event_constructor = _event_constructors.get(e.type, None)
            if event_constructor:
                events.append(event_constructor(self, e))
        return events

    def _set_property(self, name, value, allow_utf8=True):
        atom = xlib.XInternAtom(self._display, name, True)
        if not atom:
            raise XlibException('Undefined atom "%s"' % name)
        if type(value) in (str, unicode):
            property = XTextProperty()
            if _have_utf8 and allow_utf8:
                property.buf = create_string_buffer(value.encode('utf8'))
                result = xlib.Xutf8TextListToTextProperty(self._display,
                    byref(pointer(property.buf)), 1, XUTF8StringStyle, 
                    byref(property))
                if result < 0:
                    raise XlibException('Could not create UTF8 text property')
            else:
                property.buf = \
                    create_string_buffer(value.encode('ascii', 'ignore'))
                result = xlib.XStringListToTextProperty( 
                    byref(pointer(property.buf)), 1, byref(property))
                if result < 0:
                    raise XlibException('Could not create text property')
            xlib.XSetTextProperty(self._display, 
                self._window, byref(property), atom)
            xlib.XFree(property.value)

    def set_title(self, title):
        self._title = title
        self._set_property('WM_NAME', title, allow_utf8=False)
        self._set_property('WM_ICON_NAME', title, allow_utf8=False)
        self._set_property('_NET_WM_NAME', title)
        self._set_property('_NET_WM_ICON_NAME', title)

    def get_title(self):
        return self._title

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

class XlibGLConfig(BaseGLConfig):
    def __init__(self, config, **kwargs):
        super(XlibGLConfig, self).__init__(**kwargs)
        self._fbconfig = config

    def get_compatible_list(self, display, screen=0):
        attrs = []
        for name, value in self._attributes.items():
            attr = _attribute_ids.get(name, None)
            if not attr:
                raise XlibException('Unknown GLX attribute "%s"' % name)
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
            screen, attrib_list, byref(elements))
        if configs:
            result = []
            for i in range(elements.value):
                dict = self._get_config_dict(display, configs[i])
                result.append(XlibGLConfig(configs[i], **dict))
            xlib.XFree(configs)
            return result
        else:
            return []

    @staticmethod
    def _get_config_dict(display, config):
        attrs = {}
        for name, attr in _attribute_ids.items():
            value = c_int()
            result = glXGetFBConfigAttrib(display, config, attr, byref(value))
            if result >= 0:
                attrs[name] = value.value
        return attrs

def _key_event(window, event):
    if event.type == KeyPress:
        cls = KeyPressEvent
    else:
        cls = KeyReleaseEvent

    
    return cls(window, event.xkey.serial, event.xkey.keycode)

_event_constructors = {
    KeyPress: _key_event,
    KeyRelease: _key_event,
}
