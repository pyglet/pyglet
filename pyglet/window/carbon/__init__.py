#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *
import ctypes.util
import unicodedata

from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *
from pyglet.window.carbon.constants import *
from pyglet.window.carbon.key import *
from pyglet.window.carbon.types import *
from pyglet.window.carbon.AGL.VERSION_10_0 import *

class CarbonException(WindowException):
    pass

carbon_path = ctypes.util.find_library('Carbon')
if not carbon_path:
    raise ImportError('Carbon framework not found')
carbon = cdll.LoadLibrary(carbon_path)

import MacOS
if not MacOS.WMAvailable():
    raise CarbonException('Window manager is not available.  ' \
                          'Ensure you run "pythonw", not "python"')

carbon.GetEventDispatcherTarget.restype = EventTargetRef
carbon.ReceiveNextEvent.argtypes = \
    [c_uint32, c_void_p, c_double, c_ubyte, POINTER(EventRef)]
carbon.GetWindowPort.restype = c_void_p
EventHandlerProcPtr = CFUNCTYPE(c_int, c_int, c_void_p, c_void_p)
carbon.NewEventHandlerUPP.restype = c_void_p
carbon.GetCurrentKeyModifiers = c_uint32

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

def _name(name):
    return ord(name[0]) << 24 | \
           ord(name[1]) << 16 | \
           ord(name[2]) << 8 | \
           ord(name[3])

class CarbonWindow(BaseWindow):
    def __init__(self, width, height):
        super(CarbonWindow, self).__init__()
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
        self._event_dispatcher = carbon.GetEventDispatcherTarget()

        carbon.RepositionWindow(self._window, c_void_p(),
            kWindowCascadeOnMainScreen)
        carbon.InstallStandardEventHandler(\
            carbon.GetWindowEventTarget(self._window))

        # Install Carbon event handlers 
        self._current_modifiers = carbon.GetCurrentKeyModifiers().value
        self._mapped_modifiers = self._map_modifiers(self._current_modifiers)
        self._event_handlers = []
        self._install_event_handler(kEventClassTextInput,
                                    kEventTextInputUnicodeForKeyEvent,
                                    self._on_text_input)

        self._install_event_handler(kEventClassKeyboard,
                                    kEventRawKeyDown,
                                    self._on_key_down)

        self._install_event_handler(kEventClassKeyboard,
                                    kEventRawKeyUp,
                                    self._on_key_up)
        
        self._install_event_handler(kEventClassKeyboard,
                                    kEventRawKeyModifiersChanged,
                                    self._on_modifiers_changed)
        carbon.ShowWindow(self._window)

    def close(self):
        pass

    def switch_to(self):
        aglSetCurrentContext(self.context)
        _aglcheck()

    def flip(self):
        aglSwapBuffers(self.context)
        _aglcheck()

    def dispatch_events(self):
        e = EventRef()
        result = carbon.ReceiveNextEvent(0, c_void_p(), 0, True, byref(e))
        if result == noErr:
            carbon.SendEventToEventTarget(e, self._event_dispatcher)
            carbon.ReleaseEvent(e)
        elif result != eventLoopTimedOutErr:
            raise 'Error %d' % result

    def set_title(self, title):
        super(CarbonWindow, self).set_title(title)
        s = _create_cfstring(title)
        carbon.SetWindowTitleWithCFString(self._window, s)
        carbon.CFRelease(s)

    # Carbon event handlers

    def _install_event_handler(self, cls, kind, handler):
        proc = EventHandlerProcPtr(handler)
        self._event_handlers.append(proc)
        upp = carbon.NewEventHandlerUPP(proc)
        types = EventTypeSpec()
        types.eventClass = cls
        types.eventKind = kind 
        carbon.InstallEventHandler(
            carbon.GetWindowEventTarget(self._window),
            upp,
            1,
            byref(types),
            c_void_p(), c_void_p())

    def _on_text_input(self, next_handler, event, data):
        size = c_uint32()
        carbon.GetEventParameter(event, kEventParamTextInputSendText,
            typeUTF8Text, c_void_p(), 0, byref(size), c_void_p())
        text = create_string_buffer(size.value)
        carbon.GetEventParameter(event, kEventParamTextInputSendText,
            typeUTF8Text, c_void_p(), size.value, c_void_p(), byref(text))
        text = text.value.decode('utf8')

        modifiers = c_uint32()
        raw_event = EventRef()
        carbon.GetEventParameter(event, kEventParamTextInputSendKeyboardEvent,
            typeEventRef, c_void_p(), sizeof(raw_event), c_void_p(),
            byref(raw_event))
        carbon.GetEventParameter(raw_event, kEventParamKeyModifiers,
            typeUInt32, c_void_p(), sizeof(modifiers), c_void_p(),
            byref(modifiers))

        # Don't send command code points.   
        if ((unicodedata.category(text) != 'Cc' or text == u'\r') and
            not (modifiers.value & cmdKey)):
            self.dispatch_event(EVENT_TEXT, text)
        return noErr

    def _on_key_up(self, next_handler, event, data):
        symbol, modifiers = self._get_symbol_and_modifiers(event)
        if symbol: 
            self.dispatch_event(EVENT_KEYRELEASE, symbol, modifiers)
        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    def _on_key_down(self, next_handler, event, data):
        symbol, modifiers = self._get_symbol_and_modifiers(event)
        if symbol: 
            self.dispatch_event(EVENT_KEYPRESS, symbol, modifiers)
        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @staticmethod
    def _get_symbol_and_modifiers(event):
        symbol = c_uint32()
        carbon.GetEventParameter(event, kEventParamKeyCode,
            typeUInt32, c_void_p(), sizeof(symbol), c_void_p(), byref(symbol))
        modifiers = c_uint32()
        carbon.GetEventParameter(event, kEventParamKeyModifiers,
            typeUInt32, c_void_p(), sizeof(modifiers), c_void_p(),
            byref(modifiers))

        return (keymap.get(symbol.value, None), 
                CarbonWindow._map_modifiers(modifiers.value))

    @staticmethod
    def _map_modifiers(modifiers):
        mapped_modifiers = 0
        if modifiers & (shiftKey | rightShiftKey):
            mapped_modifiers |= MOD_SHIFT
        if modifiers & (controlKey | rightControlKey):
            mapped_modifiers |= MOD_CTRL
        if modifiers & (optionKey | rightOptionKey):
            mapped_modifiers |= MOD_OPTION
        if modifiers & alphaLock:
            mapped_modifiers |= MOD_CAPSLOCK
        if modifiers & cmdKey:
            mapped_modifiers |= MOD_COMMAND

        return mapped_modifiers

    def _on_modifiers_changed(self, next_handler, event, data):
        modifiers = c_uint32()
        carbon.GetEventParameter(event, kEventParamKeyModifiers,
            typeUInt32, c_void_p(), sizeof(modifiers), c_void_p(),
            byref(modifiers))
        modifiers = modifiers.value
        deltas = modifiers ^ self._current_modifiers
        for mask, key in [
            (controlKey, K_LCTRL),
            (shiftKey, K_LSHIFT),
            (cmdKey, K_LCOMMAND),
            (optionKey, K_LOPTION),
            (rightShiftKey, K_RSHIFT),
            (rightOptionKey, K_ROPTION),
            (rightControlKey, K_RCTRL),
            (alphaLock, K_CAPSLOCK),
            (numLock, K_NUMLOCK)]:
            if deltas & mask:
                if modifiers & mask:
                    self.dispatch_event(EVENT_KEYPRESS, 
                        key, self._mapped_modifiers)
                else:
                    self.dispatch_event(EVENT_KEYRELEASE,
                        key, self._mapped_modifiers)
        carbon.CallNextEventHandler(next_handler, event)

        self._mapped_modifiers = self._map_modifiers(modifiers)
        self._current_modifiers = modifiers
        return noErr

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

def _keydown_event(window, e):
    return KeyPressEvent(window, 0, 0, 0, None)

def _keyup_event(window, e):
    return KeyReleaseEvent(window, 0, 0, 0, None)

_event_constructors = {
    (kEventClassTextInput, kEventTextInputUnicodeForKeyEvent): _keydown_event,
    #(kEventClassKeyboard, kEventRawKeyUp): _keyup_event,
}
