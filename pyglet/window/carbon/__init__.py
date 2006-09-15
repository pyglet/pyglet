#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *
import ctypes.util

from pyglet.window import *
from pyglet.window.carbon.constants import *
from pyglet.window.carbon.types import *
from pyglet.window.carbon.AGL.VERSION_10_0 import *

carbon_path = ctypes.util.find_library('Carbon')
if not carbon_path:
    raise ImportError('Carbon framework not found')
carbon = cdll.LoadLibrary(carbon_path)

carbon.GetEventDispatcherTarget.restype = EventTargetRef
carbon.ReceiveNextEvent.argtypes = \
    [c_uint32, c_void_p, c_double, c_ubyte, POINTER(EventRef)]
carbon.GetWindowPort.restype = c_void_p

class CarbonException(WindowException):
    pass

class CarbonWindowFactory(BaseWindowFactory):
    def __init__(self):
        super(CarbonWindowFactory, self).__init__()
        self.context = None
        self.context_share = None

    def create_config_prototype(self):
        return CarbonGLConfig()

    def create_window(self, width, height):
        return CarbonWindow(width, height)

    def get_config_matches(self, window):
        return self.config.get_matches()

    def create_context(self, window, config, share_context=None):
        context = aglCreateContext(config._pformat, c_void_p())
        aglSetDrawable(context, carbon.GetWindowPort(window._window))
        _aglcheck()
        return context

class CarbonWindow(BaseWindow):
    def __init__(self, width, height):
        rect = Rect()
        rect.top = 0
        rect.left = 0
        rect.right = width
        rect.bottom = height

        window_class = kDocumentWindowClass
        window_attributes = kWindowStandardDocumentAttributes

        window = WindowRef()
        result = carbon.CreateNewWindow(window_class,
                                        window_attributes,
                                        byref(rect),
                                        byref(window))
        self._window = window.value
        self._event_target = carbon.GetEventDispatcherTarget()

        carbon.RepositionWindow(self._window, c_void_p(),
            kWindowCascadeOnMainScreen)
        carbon.InstallStandardEventHandler(\
            carbon.GetWindowEventTarget(self._window))

        carbon.ShowWindow(self._window)

    def close(self):
        pass

    def switch_to(self):
        aglSetCurrentContext(self.context)
        _aglcheck()

    def flip(self):
        aglSwapBuffers(self.context)
        _aglcheck()

    def get_events(self):
        events = []
        e = EventRef()
        result = carbon.ReceiveNextEvent(0, c_void_p(), 0, True, byref(e))
        if result == noErr:
            carbon.SendEventToEventTarget(e, self._event_target)
            carbon.ReleaseEvent(e)
        elif result != eventLoopTimedOutErr:
            raise 'Error %d' % result

        return events

    def set_title(self, title):
        super(CarbonWindow, self).set_title(title)
        s = _create_cfstring(title)
        carbon.SetWindowTitleWithCFString(self._window, s)
        carbon.CFRelease(s)

_attribute_ids = {
    'all_renderers': AGL_ALL_RENDERERS,
    'buffer_size': AGL_BUFFER_SIZE,
    'level': AGL_LEVEL,
    'rgba': AGL_RGBA,
    'doublebuffer': AGL_DOUBLEBUFFER,
    'stereo': AGL_STEREO,
    'aux_buffers': AGL_AUX_BUFFERS,
    'red_size': AGL_RED_SIZE,
    'green_size': AGL_GREEN_SIZE,
    'blue_size': AGL_BLUE_SIZE,
    'alpha_size': AGL_ALPHA_SIZE,
    'depth_size': AGL_DEPTH_SIZE,
    'stencil_size': AGL_STENCIL_SIZE,
    'accum_red_size': AGL_ACCUM_RED_SIZE,
    'accum_green_size': AGL_ACCUM_GREEN_SIZE,
    'accum_blue_size': AGL_ACCUM_BLUE_SIZE,
    'accum_alpha_size': AGL_ACCUM_ALPHA_SIZE,
    'pixel_size': AGL_PIXEL_SIZE,
    'minimum_policy': AGL_MINIMUM_POLICY,
    'maximum_policy': AGL_MAXIMUM_POLICY,
    'offscreen': AGL_OFFSCREEN,
    'fullscreen': AGL_FULLSCREEN,
    'sample_buffers_arb': AGL_SAMPLE_BUFFERS_ARB,
    'samples_arb': AGL_SAMPLES_ARB,
    'aux_depth_stencil': AGL_AUX_DEPTH_STENCIL,
    'color_float': AGL_COLOR_FLOAT,
    'multisample': AGL_MULTISAMPLE,
    'supersample': AGL_SUPERSAMPLE,
    'sample_alpha': AGL_SAMPLE_ALPHA,
}

_boolean_attributes = \
    (AGL_ALL_RENDERERS, 
     AGL_RGBA,
     AGL_DOUBLEBUFFER,
     AGL_STEREO,
     AGL_MINIMUM_POLICY,
     AGL_MAXIMUM_POLICY,
     AGL_OFFSCREEN,
     AGL_FULLSCREEN,
     AGL_COLOR_FLOAT,
     AGL_MULTISAMPLE,
     AGL_SUPERSAMPLE,
     AGL_SAMPLE_ALPHA)

class CarbonGLConfig(BaseGLConfig):
    def __init__(self, _pformat=None):
        super(CarbonGLConfig, self).__init__()
        self._pformat = _pformat
        if _pformat:
            for name, attr in _attribute_ids.items():
                value = c_int()
                result = aglDescribePixelFormat(_pformat, attr, byref(value))
                if result:
                    self._attributes[name] = value.value
        else:
            # Defaults
            self._attributes['maximum_policy'] = True
            self._attributes['rgba'] = True

    def get_matches(self):
        attrs = []
        for name, value in self._attributes.items():
            attr = _attribute_ids.get(name, None)
            if not attr:
                raise CarbonException('Unknown AGL attribute "%s"' % name)
            if value or attr not in _boolean_attributes:
                attrs.append(attr)
            if attr not in _boolean_attributes:
                attrs.append(int(value))
        attrs.append(AGL_NONE)
        attrib_list = (c_int * len(attrs))(*attrs)
        pformat = aglChoosePixelFormat(c_void_p(), 0, attrib_list)
        _aglcheck()
        if not pformat:
            return []
        else:
            return [CarbonGLConfig(pformat)]

def _create_cfstring(text):
    return carbon.CFStringCreateWithCString(c_void_p(), 
                                            text.encode('utf8'),
                                            kCFStringEncodingUTF8)

def _oscheck(result):
    if result != noErr:
        raise 'Carbon error %d' % result

def _aglcheck():
    err = aglGetError()
    if err != AGL_NO_ERROR:
        raise CarbonException(aglErrorString(err))
