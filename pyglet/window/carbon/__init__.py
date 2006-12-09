#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *
import ctypes.util
import os.path
import unicodedata
import warnings

from pyglet.GL.VERSION_1_1 import *
import pyglet.GL.info
from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *
from pyglet.window.carbon.constants import *
from pyglet.window.carbon.key import *
from pyglet.window.carbon.types import *
from pyglet.window.carbon.AGL.VERSION_10_0 import *

class CarbonException(WindowException):
    pass

def _get_framework(*names):
    '''Load a cdll for a framework name.  Optionally can take a list
    of names, giving the path to a subframework.  For example::

        _get_framework('ApplicationServices', 'CoreGraphics')

    '''
    path = ctypes.util.find_library(names[0])
    if not path:
        raise ImportError('%s framework not found' % names[0])
    for sub_framework in names[1:]:
        path = os.path.dirname(path)
        path = os.path.join(path,
                            'Versions/Current/Frameworks/%s.framework/%s' % \
                                (sub_framework, sub_framework))
        if not os.path.exists(path):
            raise ImportError('%s framework not found' % sub_framework)
    return cdll.LoadLibrary(path)

carbon = _get_framework('Carbon')
quicktime = _get_framework('Quicktime')

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
carbon.CGDisplayBounds.argtypes = [c_void_p]
carbon.CGDisplayBounds.restype = CGRect

class CarbonPlatform(BasePlatform):
    def get_screens(self, factory):
        count = CGDisplayCount()
        carbon.CGGetActiveDisplayList(0, None, byref(count))
        displays = (CGDirectDisplayID * count.value)()
        carbon.CGGetActiveDisplayList(count.value, displays, byref(count))
        return [CarbonScreen(id) for id in displays]
    
    def create_configs(self, factory):
        if self._is_version_compatible(10, 3):
            # In Panther and later, we can use a fullscreen context in a
            # window to allow fullscreen and windowed contexts to share
            # objects (necessary for our fullscreen toggle).  Untested
            # in 10.3.  
            # Reference http://developer.apple.com/qa/qa2001/qa1248.html
            factory.set_gl_attribute('fullscreen', True)
        else:
            # Fullscreen toggling while sharing contexts will not be possible
            # in earlier versions of OS X (or when fullscreen is desired
            # on another device).
            factory.set_gl_attribute('fullscreen', factory.get_fullscreen())

        # Set some more default attributes
        factory.set_gl_attribute('all_renderers', True) # support RAGE-II
        factory.set_gl_attribute('maximum_policy', True)
        factory.set_gl_attribute('rgba', True)

        # Construct array of attributes for aglChoosePixelFormat
        attrs = []
        for name, value in factory.get_gl_attributes().items():
            attr = CarbonGLConfig._attribute_ids.get(name, None)
            if not attr:
                warnings.warn('Unknown AGL attribute "%s"' % name)
                continue
            if value or attr not in CarbonGLConfig._boolean_attributes:
                attrs.append(attr)
            if attr not in CarbonGLConfig._boolean_attributes:
                attrs.append(int(value))
        attrs.append(AGL_NONE)
        attrib_list = (c_int * len(attrs))(*attrs)

        # If a screen is specified, use that device, otherwise leave device
        # list empty:
        screen = factory.get_screen()
        if screen:
            device = screen.get_gdevice()
            pformat = aglChoosePixelFormat(byref(device), 1, attrib_list)
        else:
            pformat = aglChoosePixelFormat(c_void_p(), 0, attrib_list)
        _aglcheck()

        if not pformat:
            return []
        else:
            return [CarbonGLConfig(pformat)]

    def create_context(self, factory):
        context_share = factory.get_context_share()
        config = factory.get_config()
        if context_share:
            context = aglCreateContext(config._pformat,
                                       context_share._context)
        else:
            context = aglCreateContext(config._pformat, c_void_p())
        _aglcheck()
        return CarbonGLContext(context)

    def get_window_class(self):
        return CarbonWindow

    def _get_version(self):
        '''Get the version of OS X running.

        Returns a tuple, e.g. (10, 4) for 10.4.x.
        '''
        import platform
        return platform._mac_ver_lookup(('sys1', 'sys2'))

    def _is_version_compatible(self, major, minor):
        version = self._get_version()
        return version[0] > major or \
               (version[0] == major and version[1] >= minor)

class CarbonScreen(BaseScreen):
    def __init__(self, id):
        rect = carbon.CGDisplayBounds(id)
        super(CarbonScreen, self).__init__(
            int(rect.origin.x), int(rect.origin.y),
            int(rect.size.width), int(rect.size.height))
        self.id = id

    def get_gdevice(self):
        gdevice = GDHandle()
        r = carbon.DMGetGDeviceByDisplayID(self.id, byref(gdevice), False)
        _oscheck(r)
        return gdevice

class CarbonGLConfig(BaseGLConfig):
    def __init__(self, pformat):
        super(CarbonGLConfig, self).__init__()
        self._pformat = pformat
        self._attributes = {}

        for name, attr in self._attribute_ids.items():
            value = c_int()
            result = aglDescribePixelFormat(pformat, attr, byref(value))
            if result:
                self._attributes[name] = value.value

    def get_gl_attributes(self):
        return self._attributes

    # Valid names for GL attributes, and their corresponding AGL constant. 
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
        'sample_buffers': AGL_SAMPLE_BUFFERS_ARB,
        'samples': AGL_SAMPLES_ARB,
        'aux_depth_stencil': AGL_AUX_DEPTH_STENCIL,
        'color_float': AGL_COLOR_FLOAT,
        'multisample': AGL_MULTISAMPLE,
        'supersample': AGL_SUPERSAMPLE,
        'sample_alpha': AGL_SAMPLE_ALPHA,
    }

    # AGL constants which do not require a value.
    _boolean_attributes = \
        (AGL_ALL_RENDERERS, 
         AGL_RGBA,
         AGL_DOUBLEBUFFER,
         AGL_STEREO,
         AGL_MINIMUM_POLICY,
         AGL_MAXIMUM_POLICY,
         AGL_OFFSCREEN,
         AGL_FULLSCREEN,
         AGL_AUX_DEPTH_STENCIL,
         AGL_COLOR_FLOAT,
         AGL_MULTISAMPLE,
         AGL_SUPERSAMPLE,
         AGL_SAMPLE_ALPHA)

class CarbonGLContext(BaseGLContext):
    def __init__(self, context):
        self._context = context

    def destroy(self):
        super(CarbonGLContext, self).destroy()
        aglDestroyContext(self._context)

_carbon_event_handler_names = []

def CarbonEventHandler(event_class, event_kind):
    def handler_wrapper(f):
        _carbon_event_handler_names.append(f.__name__)
        if not hasattr(f, '_carbon_handler'):
            f._carbon_handler = []
        f._carbon_handler.append((event_class, event_kind))
        return f
    return handler_wrapper

class CarbonWindow(BaseWindow):
    _window = None                  # Carbon WindowRef
    _agl_context = None             # AGL context ID

    # Window properties
    _minimum_size = None
    _maximum_size = None
    _fullscreen_restore = None
    _event_dispatcher = None
    _current_modifiers = 0
    _mapped_modifers = 0
    _carbon_event_handlers = []
    _carbon_event_handler_refs = []
    _track_ref = 0
    _track_region = None

    def __init__(self):
        super(CarbonWindow, self).__init__()
        self._window = WindowRef()

    def _context_compatible(self, factory):
        '''Determine if the given factory configuration can be used with
        the existing context, if any.

        This allows us to avoid unnecessarily recreating the context for
        minor changes such as the window border.
        '''
        return False

    def create(self, factory):
        # If possible, avoid creating a new context, but in current
        # implementation we need to destroy old context, but share with it
        # while creating new one so as to copy objects across.
        old_context = None
        if self._context_compatible(factory):
            factory.set_context(self.get_context())
        elif self.get_context():
            old_context = self.get_context()
            factory.set_context_share(old_context)

        # Initialize base class only after finished altering factory.
        super(CarbonWindow, self).create(factory)
        context = factory.get_context()
        width, height = factory.get_size()

        # Now that new context is ready, dispose of the old one.
        if old_context:
            old_context.destroy()
            self._agl_context = None

        # Switch out of fullscreen if necessary
        if self._fullscreen_restore and not factory.get_fullscreen():
            quicktime.EndFullScreen(self._fullscreen_restore, 0)

        # Set this _after_ destroying old context to avoid problems with
        # update context event.
        self._agl_context = context._context

        # Destroy old window if necessary
        if self._window:
            self._remove_track_region()
            self._remove_event_handlers()
            carbon.DisposeWindow(self._window)            

        if factory.get_fullscreen():
            # Switch to fullscreen mode with QuickTime
            fs_width = c_short(width)
            fs_height = c_short(height)
            self._fullscreen_restore = c_void_p()
            quicktime.BeginFullScreen(byref(self._fullscreen_restore),
                                      None,
                                      byref(fs_width),
                                      byref(fs_height),
                                      byref(self._window),
                                      None,
                                      0)
            aglSetFullScreen(self._agl_context, width, height, 0, 0)
        else:
            # Create floating window
            location = factory.get_location()
            rect = Rect()
            if location is not LOCATION_DEFAULT:
                rect.left = location[0]
                rect.top = location[1]
            else:
                rect.top = rect.left = 0
            rect.right = rect.left + width
            rect.bottom = rect.top + height

            window_class = kDocumentWindowClass
            window_attributes = (kWindowStandardDocumentAttributes | 
                                 kWindowLiveResizeAttribute)

            carbon.CreateNewWindow(window_class,
                                   window_attributes,
                                   byref(rect),
                                   byref(self._window))
            aglSetDrawable(self._agl_context,
                carbon.GetWindowPort(self._window))

            if location is LOCATION_DEFAULT:
                carbon.RepositionWindow(self._window, c_void_p(),
                    kWindowCascadeOnMainScreen)

        _aglcheck()

        # Get initial state
        self._event_dispatcher = carbon.GetEventDispatcherTarget()
        self._current_modifiers = carbon.GetCurrentKeyModifiers().value
        self._mapped_modifiers = self._map_modifiers(self._current_modifiers)

        # (re)install Carbon event handlers 
        self._install_event_handlers()

        self._create_track_region()

    def _create_track_region(self):
        self._remove_track_region()

        # Create a tracking region for the content part of the window
        # to receive enter/leave events.
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

    def _remove_track_region(self):
        if self._track_region:
            carbon.ReleaseMouseTrackingRegion(self._track_region)
            self._track_region = None

    def close(self):
        super(CarbonWindow, self).close()
        self._agl_context = None
        self._remove_event_handlers()
        self._remove_track_region()

        if self._fullscreen:
            quicktime.EndFullScreen(self._fullscreen_restore, 0)
        carbon.DisposeWindow(self._window)
        self._window = None

    def switch_to(self):
        aglSetCurrentContext(self._agl_context)
        _aglcheck()
        pyglet.GL.info.set_context()

    def flip(self):
        aglSwapBuffers(self._agl_context)
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

    def set_location(self, x, y):
        rect = Rect()
        carbon.GetWindowBounds(self._window, kWindowContentRgn, byref(rect))
        rect.right += x - rect.left
        rect.bottom += y - rect.top
        rect.left = x
        rect.top = y
        carbon.SetWindowBounds(self._window, kWindowContentRgn, byref(rect))

    def get_location(self):
        rect = Rect()
        carbon.GetWindowBounds(self._window, kWindowContentRgn, byref(rect))
        return rect.left, rect.top

    def set_size(self, width, height):
        rect = Rect()
        carbon.GetWindowBounds(self._window, kWindowContentRgn, byref(rect))
        rect.right = rect.left + width
        rect.bottom = rect.top + height
        carbon.SetWindowBounds(self._window, kWindowContentRgn, byref(rect))

    def get_size(self):
        rect = Rect()
        carbon.GetWindowBounds(self._window, kWindowContentRgn, byref(rect))
        return rect.right - rect.left, rect.bottom - rect.top

    def set_minimum_size(self, width, height):
        self._minimum_size = (width, height)
        minimum = HISize()
        minimum.width = width
        minimum.height = height
        if self._maximum_size:
            maximum = HISize()
            maximum.width, maximum.height = self._maximum_size
            maximum = byref(maximum)
        else:
            maximum = None
        carbon.SetWindowResizeLimits(self._window, 
            byref(minimum), maximum)

    def set_maximum_size(self, width, height):
        self._maximum_size = (width, height)
        maximum = HISize()
        maximum.width = width
        maximum.height = height
        if self._minimum_size:
            minimum = HISize()
            minimum.width, minimum.height = self._minimum_size
            minimum = byref(minimum)
        else:
            minimum = None
        carbon.SetWindowResizeLimits(self._window, 
            minimum, byref(maximum))

    def activate(self):
        carbon.ActivateWindow(self._window, 1)

        # Also make the application the "front" application.  TODO
        # maybe don't bring forward all of the application's windows?
        psn = ProcessSerialNumber()
        psn.highLongOfPSN = 0
        psn.lowLongOfPSN = kCurrentProcess
        carbon.SetFrontProcess(byref(psn))

    def set_visible(self, visible=True):
        if visible:
            width, height = self.get_size()
            self.dispatch_event(EVENT_RESIZE, width, height)

            carbon.ShowWindow(self._window)
        else:
            carbon.HideWindow(self._window)

    def minimize(self):
        carbon.CollapseWindow(self._window, True)

    def maximize(self):
        # Maximum "safe" value, gets trimmed to screen size automatically.
        p = Point()
        p.v, p.h = 16000,16000 
        if not carbon.IsWindowInStandardState(self._window, byref(p), None):
            carbon.ZoomWindowIdeal(self._window, inZoomOut, byref(p))

    def set_exclusive_mouse(self, exclusive=True):
        if exclusive:
            # Move mouse to center of window
            rect = Rect()
            carbon.GetWindowBounds(self._window, kWindowContentRgn, byref(rect))
            point = CGPoint()
            point.x = (rect.right + rect.left) / 2
            point.y = (rect.bottom + rect.top) / 2
            carbon.CGWarpMouseCursorPosition(point)
            carbon.CGAssociateMouseAndMouseCursorPosition(False)
            carbon.HideCursor()
        else:
            carbon.CGAssociateMouseAndMouseCursorPosition(True)
            carbon.ShowCursor()

    def set_exclusive_keyboard(self, exclusive=True):
        if exclusive:
            # Note: power switch can also be disabled, with
            # kUIOptionDisableSessionTerminate.  That seems
            # a little extreme though.
            carbon.SetSystemUIMode(kUIModeAllHidden,
                (kUIOptionDisableAppleMenu |
                 kUIOptionDisableProcessSwitch |
                 kUIOptionDisableForceQuit |
                 kUIOptionDisableHide))
        else:
            carbon.SetSystemUIMode(kUIModeNormal, 0)

    # Non-public utilities

    def _update_drawable(self):
        # We can get there after context has been disposed, in which case
        # just do nothing.
        if not self._agl_context:
            return

        aglUpdateContext(self._agl_context)
        _aglcheck()

        # Need a redraw
        self.dispatch_event(EVENT_EXPOSE)

    def _update_track_region(self):
        carbon.GetWindowRegion(self._window, 
            kWindowContentRgn, self._track_region)
        carbon.ChangeMouseTrackingRegion(self._track_ref,
            self._track_region, None)

    def _install_event_handlers(self):
        self._remove_event_handlers()

        if self._fullscreen:
            target = carbon.GetApplicationEventTarget()
        else:
            target = carbon.GetWindowEventTarget(self._window)
        carbon.InstallStandardEventHandler(target)

        self._carbon_event_handlers = []
        self._carbon_event_handler_refs = []

        for func_name in _carbon_event_handler_names:
            if not hasattr(self, func_name):
                continue  # Was added by another class

            func = getattr(self, func_name)
            for event_class, event_kind in func._carbon_handler:
                # TODO: could just build up array of class/kind
                proc = EventHandlerProcPtr(func)
                self._carbon_event_handlers.append(proc)
                upp = carbon.NewEventHandlerUPP(proc)
                types = EventTypeSpec()
                types.eventClass = event_class
                types.eventKind = event_kind
                handler_ref = EventHandlerRef()
                carbon.InstallEventHandler(
                    target,
                    upp,
                    1,
                    byref(types),
                    c_void_p(),
                    byref(handler_ref))
                self._carbon_event_handler_refs.append(handler_ref)

    def _remove_event_handlers(self):
        for ref in self._carbon_event_handler_refs:
            carbon.RemoveEventHandler(ref)
        self._carbon_event_handler_refs = []
        self._carbon_event_handlers = []

    # Carbon event handlers

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
            self.dispatch_event(EVENT_KEY_RELEASE, symbol, modifiers)
        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassKeyboard, kEventRawKeyDown)
    def _on_key_down(self, next_handler, event, data):
        symbol, modifiers = self._get_symbol_and_modifiers(event)
        if symbol:
            self.dispatch_event(EVENT_KEY_PRESS, symbol, modifiers)
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
                    self.dispatch_event(EVENT_KEY_PRESS, 
                        key, self._mapped_modifiers)
                else:
                    self.dispatch_event(EVENT_KEY_RELEASE,
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
        
        # kEventMouseButtonPrimary == MOUSE_LEFT_BUTTON == 1
        # kEventMouseButtonSecondary == MOUSE_MIDDLE_BUTTON == 2
        # kEventMouseButtonTertiary == 3 != MOUSE_RIGHT_BUTTON == 4
        #if button == 3:
        #    button = MOUSE_RIGHT_BUTTON
        # <rj> not on my mouse they're not!
        if button.value == 1: button = MOUSE_LEFT_BUTTON
        elif button.value == 2: button = MOUSE_RIGHT_BUTTON
        elif button.value == 3: button = MOUSE_MIDDLE_BUTTON

        modifiers = c_uint32()
        carbon.GetEventParameter(event, kEventParamKeyModifiers,
            typeUInt32, c_void_p(), sizeof(modifiers), c_void_p(),
            byref(modifiers))

        return button, CarbonWindow._map_modifiers(modifiers.value)

    @CarbonEventHandler(kEventClassMouse, kEventMouseDown)
    def _on_mouse_down(self, next_handler, event, data):
        button, modifiers = self._get_mouse_button_and_modifiers(event)
        x, y = self._get_mouse_position(event)
        if x >= 0 and y >= 0:
            self.dispatch_event(EVENT_MOUSE_PRESS, button, x, y, modifiers)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassMouse, kEventMouseUp)
    def _on_mouse_up(self, next_handler, event, data):
        button, modifiers = self._get_mouse_button_and_modifiers(event)
        x, y = self._get_mouse_position(event)
        if x >= 0 and y >= 0:
            self.dispatch_event(EVENT_MOUSE_RELEASE, button, x, y, modifiers)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassMouse, kEventMouseMoved)
    @CarbonEventHandler(kEventClassMouse, kEventMouseDragged)
    def _on_mouse_moved(self, next_handler, event, data):
        button, modifiers = self._get_mouse_button_and_modifiers(event)
        x, y = self._get_mouse_position(event)
        if x < 0 or y < 0:
            return noErr

        delta = HIPoint()
        carbon.GetEventParameter(event, kEventParamMouseDelta,
            typeHIPoint, c_void_p(), sizeof(delta), c_void_p(),
            byref(delta))

        if button:
            # Drag event
            self.dispatch_event(EVENT_MOUSE_DRAG,
                x, y, delta.x, delta.y, button, modifiers)
        else:
            # Motion event
            self.dispatch_event(EVENT_MOUSE_MOTION, x, y, delta.x, delta.y)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassMouse, kEventMouseEntered)
    def _on_mouse_entered(self, next_handler, event, data):
        x, y = self._get_mouse_position(event)
        self.dispatch_event(EVENT_MOUSE_ENTER, x, y)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassMouse, kEventMouseExited)
    def _on_mouse_exited(self, next_handler, event, data):
        x, y = self._get_mouse_position(event)
        self.dispatch_event(EVENT_MOUSE_LEAVE, x, y)

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

    @CarbonEventHandler(kEventClassWindow, kEventWindowBoundsChanging)
    @CarbonEventHandler(kEventClassWindow, kEventWindowResizeCompleted)
    def _on_window_resize_completed(self, next_handler, event, data):
        rect = Rect()
        carbon.GetWindowBounds(self._window, kWindowContentRgn, byref(rect))
        width = rect.right - rect.left
        height = rect.bottom - rect.top

        self.switch_to()
        glViewport(0, 0, width, height)
        self.dispatch_event(EVENT_RESIZE, width, height)
        self.dispatch_event(EVENT_EXPOSE)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassWindow, kEventWindowDragCompleted)
    def _on_window_drag_completed(self, next_handler, event, data):
        rect = Rect()
        carbon.GetWindowBounds(self._window, kWindowContentRgn, byref(rect))

        self.dispatch_event(EVENT_MOVE, rect.left, rect.top)

        carbon.CallNextEventHandler(next_handler, event)
        return noErr

    @CarbonEventHandler(kEventClassWindow, kEventWindowBoundsChanged)
    def _on_window_bounds_change(self, next_handler, event, data):
        self._update_track_region()
        self._update_drawable()

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
        self._update_drawable()
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

