#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes
import pyglet
from pyglet.input.base import \
    Device, DeviceException, DeviceOpenException, \
    Control, Button, RelativeAxis, AbsoluteAxis
from pyglet.libs.x11 import xlib

try:
    from pyglet.libs.x11 import xinput as xi
    _have_xinput = True
except:
    _have_xinput = False

def ptr_add(ptr, offset):
    address = ctypes.addressof(ptr.contents) + offset
    return ctypes.pointer(type(ptr.contents).from_address(address))

class XInputDevice(Device):
    def __init__(self, display, device_info):
        super(XInputDevice, self).__init__(display, device_info.name)

        self._device_id = device_info.id
        self._device = None

        # Read device info
        self.buttons = []
        self.keys = []
        self.axes = []

        ptr = device_info.inputclassinfo
        for i in range(device_info.num_classes):
            cp = ctypes.cast(ptr, ctypes.POINTER(xi.XAnyClassInfo))
            cls_class = getattr(cp.contents, 'class')

            if cls_class == xi.KeyClass:
                cp = ctypes.cast(ptr, ctypes.POINTER(xi.XKeyInfo))
                self.min_keycode = cp.contents.min_keycode
                num_keys = cp.contents.num_keys
                for i in range(num_keys):
                    self.keys.append(Button('key%d' % i))

            elif cls_class == xi.ButtonClass:
                cp = ctypes.cast(ptr, ctypes.POINTER(xi.XButtonInfo))
                num_buttons = cp.contents.num_buttons
                for i in range(num_buttons):
                    self.buttons.append(Button('button%d' % i))

            elif cls_class == xi.ValuatorClass:
                cp = ctypes.cast(ptr, ctypes.POINTER(xi.XValuatorInfo))
                num_axes = cp.contents.num_axes
                mode = cp.contents.mode
                axes = ctypes.cast(cp.contents.axes,
                                   ctypes.POINTER(xi.XAxisInfo))
                for i in range(num_axes):
                    axis = axes[i]
                    if mode == xi.Absolute:
                        self.axes.append(AbsoluteAxis('axis%d' % i,
                            min=axis.min_value,
                            max=axis.max_value))
                    elif mode == xi.Relative:
                        self.axes.append(RelativeAxis('axis%d' % i))

            cls = cp.contents
            ptr = ptr_add(ptr, cls.length)

        self.controls = self.buttons + self.keys + self.axes

        # Can't detect proximity class event without opening device.  Just
        # assume there is the possibility of a control if there are any axes.
        if self.axes:
            self.proximity_control = Button('proximity')
            self.controls.append(self.proximity_control)
        else:
            self.proximity_control = None

    def get_controls(self):
        return self.controls

    def open(self, window=None, exclusive=False):
        # Checks for is_open and raises if already open.
        # TODO allow opening on multiple windows.
        super(XInputDevice, self).open(window, exclusive)

        if window is None:
            self.is_open = False
            raise DeviceOpenException('XInput devices require a window')

        if window.display._display != self.display._display:
            self.is_open = False
            raise DeviceOpenException('Window and device displays differ')

        if exclusive:
            self.is_open = False
            raise DeviceOpenException('Cannot open XInput device exclusive')

        self._device = xi.XOpenDevice(self.display._display, self._device_id)
        if not self._device:
            self.is_open = False
            raise DeviceOpenException('Cannot open device')
        
        self._install_events(window)

    def close(self):
        super(XInputDevice, self).close()

        if not self._device:
            return

        xi.XCloseDevice(self.display._display, self._device)

    def _install_events(self, window):
        try:
            dispatcher = window.__xinput_window_event_dispatcher
        except AttributeError:
            dispatcher = window.__xinput_window_event_dispatcher = \
                XInputWindowEventDispatcher()
        dispatcher.add_instance(self)

        device = self._device.contents
        if not device.num_classes:
            return

        # Bind matching extended window events to bound instance methods
        # on this object.
        #
        # This is inspired by test.c of xinput package by Frederic
        # Lepied available at x.org.
        #
        # In C, this stuff is normally handled by the macro DeviceKeyPress and
        # friends. Since we don't have access to those macros here, we do it
        # this way.
        events = []

        def add(class_info, event, handler):
            _type = class_info.event_type_base + event
            _class = self._device_id << 8 | _type
            events.append(_class)
            window._event_handlers[_type] = handler

        for i in range(device.num_classes):
            class_info = device.classes[i]
            if class_info.input_class == xi.KeyClass:
                add(class_info, xi._deviceKeyPress,
                    dispatcher._event_xinput_key_press)
                add(class_info, xi._deviceKeyRelease,
                    dispatcher._event_xinput_key_release)

            elif class_info.input_class == xi.ButtonClass:
                add(class_info, xi._deviceButtonPress,
                    dispatcher._event_xinput_button_press)
                add(class_info, xi._deviceButtonRelease,
                    dispatcher._event_xinput_button_release)

            elif class_info.input_class == xi.ValuatorClass:
                add(class_info, xi._deviceMotionNotify,
                    dispatcher._event_xinput_motion)

            elif class_info.input_class == xi.ProximityClass:
                add(class_info, xi._proximityIn,
                    dispatcher._event_xinput_proximity_in)
                add(class_info, xi._proximityOut,
                    dispatcher._event_xinput_proximity_out)

            elif class_info.input_class == xi.FeedbackClass:
                pass

            elif class_info.input_class == xi.FocusClass:
                pass
                
            elif class_info.input_class == xi.OtherClass:
                pass

        array = (xi.XEventClass * len(events))(*events)
        xi.XSelectExtensionEvent(window._x_display,
                                 window._window,
                                 array,
                                 len(array))

class XInputWindowEventDispatcher(object):
    def __init__(self):
        self._instances = {}

    def add_instance(self, instance):
        self._instances[instance._device_id] = instance

    def remove_instance(self, instance):
        del self._instances[instance._device_id]

    def dispatch_instance_event(self, e, *args):
        try:
            instance = self._instances[e.deviceid]
        except KeyError:
            return

        instance.dispatch_event(*args)

    @pyglet.window.xlib.XlibEventHandler(0)
    def _event_xinput_key_press(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XDeviceKeyEvent)).contents

        device = self._instances.get(e.deviceid)
        if device is not None:
            device.keys[e.keycode - device.min_keycode]._set_value(True)

    @pyglet.window.xlib.XlibEventHandler(0)
    def _event_xinput_key_release(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XDeviceKeyEvent)).contents

        device = self._instances.get(e.deviceid)
        if device is not None:
            device.keys[e.keycode - device.min_keycode]._set_value(False)

    @pyglet.window.xlib.XlibEventHandler(0)
    def _event_xinput_button_press(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XDeviceButtonEvent)).contents

        device = self._instances.get(e.deviceid)
        if device is not None:
            device.buttons[e.button]._set_value(True)

    @pyglet.window.xlib.XlibEventHandler(0)
    def _event_xinput_button_release(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XDeviceButtonEvent)).contents

        device = self._instances.get(e.deviceid)
        if device is not None:
            device.buttons[e.button]._set_value(False)

    @pyglet.window.xlib.XlibEventHandler(0)
    def _event_xinput_motion(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XDeviceMotionEvent)).contents

        device = self._instances.get(e.deviceid)
        if device is not None:
            for i in range(e.axes_count):
                device.axes[i]._set_value(e.axis_data[i])

    @pyglet.window.xlib.XlibEventHandler(0)
    def _event_xinput_proximity_in(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XProximityNotifyEvent)).contents

        device = self._instances.get(e.deviceid)
        if device is not None and device.proximity_control:
            device.proximity_control._set_value(True)

    @pyglet.window.xlib.XlibEventHandler(-1)
    def _event_xinput_proximity_out(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XProximityNotifyEvent)).contents

        device = self._instances.get(e.deviceid)
        if device is not None and device.proximity_control:
            device.proximity_control._set_value(False)

def _check_extension(display):
    major_opcode = ctypes.c_int()
    first_event = ctypes.c_int()
    first_error = ctypes.c_int()
    xlib.XQueryExtension(display._display, 'XInputExtension', 
        ctypes.byref(major_opcode), 
        ctypes.byref(first_event),
        ctypes.byref(first_error))
    return bool(major_opcode.value)

def get_devices(display=None):
    if display is None:
        display = pyglet.canvas.get_display()

    if not _have_xinput or not _check_extension(display):
        return []

    devices = []
    count = ctypes.c_int(0)
    device_list = xi.XListInputDevices(display._display, count)

    for i in range(count.value):
        device_info = device_list[i]
        devices.append(XInputDevice(display, device_info))

    xi.XFreeDeviceList(device_list)

    return devices

