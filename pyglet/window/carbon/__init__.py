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
carbon.NewRgn.restype = RgnHandle

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

_carbon_event_handler_types = []

def CarbonEventHandler(event_class, event_kind):
    def handler_wrapper(f):
        handler = (event_class, event_kind, f.__name__)
        _carbon_event_handler_types.append(handler)
        return f
    return handler_wrapper

class CarbonWindow(BaseWindow):
    def __init__(self, width, height):
        super(CarbonWindow, self).__init__(width, height)
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

        # Get initial state
        self._current_modifiers = carbon.GetCurrentKeyModifiers().value
        self._mapped_modifiers = self._map_modifiers(self._current_modifiers)

        # Install Carbon event handlers 
        self._carbon_event_handlers = []
        self._install_event_handlers()

        carbon.ShowWindow(self._window)

        # Create a tracking region for the content part of the window
        # to receive enter/leave events.
        # TODO: update this region when window is resized. 
        track_id = MouseTrackingRegionID()
        track_id.signature = DEFAULT_CREATOR_CODE
        track_id.id = 1
        self._track_ref = MouseTrackingRef()
        self._track_region = carbon.NewRgn()
        carbon.GetWindowRegion(self._window, 
            kWindowContentRgn, self._track_region)
        carbon.CreateMouseTrackingRegion(self._window,  
            self._track_region, None, kMouseTrackingOptionsGlobalClip,
            track_id, None, None,
            byref(self._track_ref))

    def close(self):
        # TODO: there's more stuff to clean up here.
        carbon.DisposeWindow(self._window)
        self._window = None

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

    def set_caption(self, title):
        super(CarbonWindow, self).set_caption(title)
        s = _create_cfstring(title)
        carbon.SetWindowTitleWithCFString(self._window, s)
        carbon.CFRelease(s)

    # Carbon event handlers

    def _install_event_handlers(self):
        for event_class, event_kind, func_name in _carbon_event_handler_types:
            func = getattr(self, func_name)
            proc = EventHandlerProcPtr(func)
            self._carbon_event_handlers.append(proc)
            upp = carbon.NewEventHandlerUPP(proc)
            types = EventTypeSpec()
            types.eventClass = event_class
            types.eventKind = event_kind
            carbon.InstallEventHandler(
                carbon.GetWindowEventTarget(self._window),
                upp,
                1,
                byref(types),
                c_void_p(), c_void_p())

    @CarbonEventHandler(kEventClassTextInput, kEventTextInputUnicodeForKeyEvent)
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
        if ((unicodedata.category(text[0]) != 'Cc' or text == u'\r') and
            not (modifiers.value & cmdKey)):
            self.dispatch_event(EVENT_TEXT, text)
        return noErr

    @CarbonEventHandler(kEventClassKeyboard, kEventRawKeyUp)
    def _on_key_up(self, next_handler, event, data):
        symbol, modifiers = self._get_symbol_and_modifiers(event)
        if symbol:
            self.dispatch_event(EVENT_KEYRELEASE, symbol, modifiers)
        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassKeyboard, kEventRawKeyDown)
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

    @CarbonEventHandler(kEventClassKeyboard, kEventRawKeyModifiersChanged)
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

    def _get_mouse_position(self, event):
        position = HIPoint()
        carbon.GetEventParameter(event, kEventParamMouseLocation,
            typeHIPoint, c_void_p(), sizeof(position), c_void_p(),
            byref(position))

        bounds = Rect()
        carbon.GetWindowBounds(self._window, kWindowContentRgn, byref(bounds))
        return position.x - bounds.left, position.y - bounds.top

    @staticmethod
    def _get_mouse_button_and_modifiers(event):
        button = EventMouseButton()
        carbon.GetEventParameter(event, kEventParamMouseButton,
            typeMouseButton, c_void_p(), sizeof(button), c_void_p(),
            byref(button))

        modifiers = c_uint32()
        carbon.GetEventParameter(event, kEventParamKeyModifiers,
            typeUInt32, c_void_p(), sizeof(modifiers), c_void_p(),
            byref(modifiers)) 

        return button.value, CarbonWindow._map_modifiers(modifiers.value)

    @CarbonEventHandler(kEventClassMouse, kEventMouseDown)
    def _on_mouse_down(self, next_handler, event, data):
        button, modifiers = self._get_mouse_button_and_modifiers(event)
        x, y = self._get_mouse_position(event)
        if x >= 0 and y >= 0:
            self.dispatch_event(EVENT_BUTTONPRESS, button, x, y, modifiers)
            self.mouse.x = x
            self.mouse.y = y

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassMouse, kEventMouseUp)
    def _on_mouse_up(self, next_handler, event, data):
        button, modifiers = self._get_mouse_button_and_modifiers(event)
        x, y = self._get_mouse_position(event)
        if x >= 0 and y >= 0:
            self.dispatch_event(EVENT_BUTTONRELEASE, button, x, y, modifiers)
            self.mouse.x = x
            self.mouse.y = y

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassMouse, kEventMouseMoved)
    def _on_mouse_moved(self, next_handler, event, data):
        button, modifiers = self._get_mouse_button_and_modifiers(event)
        x, y = self._get_mouse_position(event)
        if x >= 0 and y >= 0:
            dx = x - self.mouse.x
            dy = y - self.mouse.y
            self.mouse.x = x
            self.mouse.y = y
            self.dispatch_event(EVENT_MOUSEMOTION, x, y, dx, dy)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassMouse, kEventMouseDragged)
    def _on_mouse_dragged(self, next_handler, event, data):
        return self._on_mouse_moved(next_handler, event, data)

    @CarbonEventHandler(kEventClassMouse, kEventMouseEntered)
    def _on_mouse_entered(self, next_handler, event, data):
        x, y = self._get_mouse_position(event)
        if x >= 0 and y >= 0:
            self.mouse.x = x
            self.mouse.y = y
        self.dispatch_event(EVENT_ENTER, x, y)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassMouse, kEventMouseExited)
    def _on_mouse_exited(self, next_handler, event, data):
        x, y = self._get_mouse_position(event)
        if x >= 0 and y >= 0:
            self.mouse.x = x
            self.mouse.y = y
        self.dispatch_event(EVENT_LEAVE, x, y)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassMouse, kEventMouseWheelMoved)
    def _on_mouse_wheel_moved(self, next_handler, event, data):
        axis = EventMouseWheelAxis()
        carbon.GetEventParameter(event, kEventParamMouseWheelAxis,
            typeMouseWheelAxis, c_void_p(), sizeof(axis), c_void_p(),
            byref(axis))
        delta = c_long()
        carbon.GetEventParameter(event, kEventParamMouseWheelDelta,
            typeSInt32, c_void_p(), sizeof(delta), c_void_p(),
            byref(delta))
        if axis.value == kEventMouseWheelAxisX:
            self.dispatch_event(EVENT_MOUSE_SCROLL, float(delta.value), 0.)
        else:
            self.dispatch_event(EVENT_MOUSE_SCROLL, 0., float(delta.value))
                
        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassWindow, kEventWindowClose)
    def _on_window_close(self, next_handler, event, data):
        self.dispatch_event(EVENT_CLOSE)

        # Presumably the next event handler is the one that closes
        # the window; don't do that here. 
        #carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassWindow, kEventWindowResizeCompleted)
    def _on_window_resize_completed(self, next_handler, event, data):
        rect = Rect()
        carbon.GetWindowBounds(self._window, kWindowContentRgn, byref(rect))
        width = rect.right - rect.left
        height = rect.bottom - rect.top

        self.dispatch_event(EVENT_RESIZE, width, height)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassWindow, kEventWindowDragCompleted)
    def _on_window_drag_completed(self, next_handler, event, data):
        rect = Rect()
        carbon.GetWindowBounds(self._window, kWindowContentRgn, byref(rect))

        self.dispatch_event(EVENT_MOVE, rect.left, rect.top)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassWindow, kEventWindowZoomed)
    def _on_window_zoomed(self, next_handler, event, data):
        rect = Rect()
        carbon.GetWindowBounds(self._window, kWindowContentRgn, byref(rect))
        width = rect.right - rect.left
        height = rect.bottom - rect.top

        self.dispatch_event(EVENT_MOVE, rect.left, rect.top)
        self.dispatch_event(EVENT_RESIZE, width, height)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassWindow, kEventWindowActivated)
    def _on_window_activated(self, next_handler, event, data):
        self.dispatch_event(EVENT_ACTIVATE)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassWindow, kEventWindowDeactivated)
    def _on_window_deactivated(self, next_handler, event, data):
        self.dispatch_event(EVENT_DEACTIVATE)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr
        
    @CarbonEventHandler(kEventClassWindow, kEventWindowShown)
    @CarbonEventHandler(kEventClassWindow, kEventWindowExpanded)
    def _on_window_shown(self, next_handler, event, data):
        self.dispatch_event(EVENT_SHOW)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassWindow, kEventWindowHidden)
    @CarbonEventHandler(kEventClassWindow, kEventWindowCollapsed)
    def _on_window_hidden(self, next_handler, event, data):
        self.dispatch_event(EVENT_HIDE)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassWindow, kEventWindowDrawContent)
    def _on_window_draw_content(self, next_handler, event, data):
        self.dispatch_event(EVENT_EXPOSE)

        carbon.CallNextEventHandler(next_handler, event)
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
