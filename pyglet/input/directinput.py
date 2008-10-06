#!/usr/bin/python
# $Id:$

import ctypes

import pyglet
from pyglet.input import base
from pyglet.libs import win32
from pyglet.libs.win32 import dinput
from pyglet.libs.win32 import _kernel32

def _create_control(object_instance):
    name = object_instance.tszName
    type = object_instance.dwType

    if type & dinput.DIDFT_NODATA:
        return
    elif type & dinput.DIDFT_BUTTON:
        control = base.Button(name, 0, 0x8000)
    else:
        control = base.Control(name, 0, 0xffff)

    control._flags = object_instance.dwFlags
    control._guid = object_instance.guidType # useless
    control._type = object_instance.dwType
    control._usage_page = object_instance.wUsagePage
    control._usage = object_instance.wUsage
    return control
        
class DirectInputDevice(base.Device):
    def __init__(self, display, device, device_instance):
        name = device_instance.tszInstanceName
        super(DirectInputDevice, self).__init__(display, name)

        self._type = device_instance.dwDevType & 0xff
        self._subtype = device_instance.dwDevType & 0xff00

        self._device = device
        self._init_controls()
        self._set_format()

    def _init_controls(self):
        self.controls = []
        self._device.EnumObjects(
            dinput.LPDIENUMDEVICEOBJECTSCALLBACK(self._object_enum), 
            None, dinput.DIDFT_ALL)

    def _object_enum(self, object_instance, arg):
        control = _create_control(object_instance.contents)
        if control:
            self.controls.append(control)        
        return dinput.DIENUM_CONTINUE

    def _set_format(self):
        if not self.controls:
            return

        object_formats = (dinput.DIOBJECTDATAFORMAT * len(self.controls))()
        offset = 0
        for object_format, control in zip(object_formats, self.controls):
            object_format.dwOfs = offset
            object_format.dwType = control._type
            offset += 4
             
        format = dinput.DIDATAFORMAT()
        format.dwSize = ctypes.sizeof(format)
        format.dwObjSize = ctypes.sizeof(dinput.DIOBJECTDATAFORMAT)
        format.dwFlags = 0
        format.dwDataSize = offset
        format.dwNumObjs = len(object_formats)
        format.rgodf = ctypes.cast(ctypes.pointer(object_formats),
                                   dinput.LPDIOBJECTDATAFORMAT)
        self._device.SetDataFormat(format)

        prop = dinput.DIPROPDWORD()
        prop.diph.dwSize = ctypes.sizeof(prop)
        prop.diph.dwHeaderSize = ctypes.sizeof(prop.diph)
        prop.diph.dwObj = 0
        prop.diph.dwHow = dinput.DIPH_DEVICE
        prop.dwData = 64 * ctypes.sizeof(dinput.DIDATAFORMAT)
        self._device.SetProperty(dinput.DIPROP_BUFFERSIZE, 
                                 ctypes.byref(prop.diph))

    def open(self, window=None, exclusive=False):
        if not self.controls:
            return

        if window is None:
            # Pick any open window, or the shadow window if no windows
            # have been created yet.
            window = pyglet.gl._shadow_window
            for window in pyglet.app.windows:
                break

        flags = dinput.DISCL_BACKGROUND
        if exclusive:
            flags |= dinput.DISCL_EXCLUSIVE
        else:
            flags |= dinput.DISCL_NONEXCLUSIVE
        
        self._wait_object = _kernel32.CreateEventW(None, False, False, None)
        self._device.SetEventNotification(self._wait_object)
        pyglet.app.event_loop.add_wait_object(self._wait_object, 
                                              self._dispatch_events)

        self._device.SetCooperativeLevel(window._hwnd, flags)
        self._device.Acquire()

    def close(self):
        if not self.controls:
            return

        pyglet.app.event_loop.remove_wait_object(self._wait_object)

        self._device.SetEventNotification(None)
        self._device.Unacquire()

        _kernel32.CloseHandle(self._wait_object)

    def get_controls(self):
        return self.controls

    def _dispatch_events(self):
        if not self.controls:
            return
        
        events = (dinput.DIDEVICEOBJECTDATA * 64)()
        n_events = win32.DWORD(len(events))
        self._device.GetDeviceData(ctypes.sizeof(dinput.DIDEVICEOBJECTDATA),
                                   ctypes.cast(ctypes.pointer(events), 
                                               dinput.LPDIDEVICEOBJECTDATA),
                                   ctypes.byref(n_events),
                                   0)
        for event in events[:n_events.value]:
            index = event.dwOfs // 4
            self.controls[index]._set_value(event.dwData)

def _create_joystick(device):
    if device._type not in (dinput.DI8DEVTYPE_JOYSTICK, 
                            dinput.DI8DEVTYPE_GAMEPAD):
        return

    joystick = base.Joystick(device)

    def add_control(name, control):
        scale = 2.0 / (control.max - control.min)
        bias = -1.0 - control.min * scale
        @control.event
        def on_change(value):
            setattr(joystick, name, value * scale + bias)
        setattr(joystick, name + '_control', control)

    def add_button(i, control):
        nn = i + 1 - len(joystick.buttons)
        if nn > 0:
            joystick.buttons.extend([False] * nn)
            joystick.button_controls.extend([None] * nn)
        joystick.button_controls[i] = control
        @control.event
        def on_change(value):
            joystick.buttons[i] = bool(value)

    def add_hat(control):
        joystick.hat_x_control = control
        joystick.hat_y_control = control
        @control.event
        def on_change(value):
            if value & 0xffff == 0xffff:
                joystick.hat_x = joystick.hat_y = 0
            else:
                value //= 0xfff
                if 0 <= value < 8:
                    joystick.hat_x, joystick.hat_y = (
                        ( 0,  1),
                        ( 1,  1),
                        ( 1,  0),
                        ( 1, -1),
                        ( 0, -1),
                        (-1, -1),
                        (-1,  0),
                        (-1,  1),
                    )[value]
                else:
                    # Out of range
                    joystick.hat_x = joystick.hat_y = 0

    for control in device.get_controls():
        type = control._type
        instance = dinput.DIDFT_GETINSTANCE(type)
        if type & dinput.DIDFT_ABSAXIS and instance == 0:
            add_control('x', control)
        elif type & dinput.DIDFT_ABSAXIS and instance == 1:
            add_control('y', control)
        elif type & dinput.DIDFT_ABSAXIS and instance == 2:
            add_control('z', control)
        elif type & dinput.DIDFT_ABSAXIS and instance == 5:
            add_control('rz', control)
        elif type & dinput.DIDFT_POV:
            add_hat(control)
        elif type & dinput.DIDFT_BUTTON:
            add_button(instance, control) 

    return joystick

_i_dinput = None

def _init_directinput():
    global _i_dinput
    if _i_dinput:
        return
    
    _i_dinput = dinput.IDirectInput8()
    module = _kernel32.GetModuleHandleW(None)
    dinput.DirectInput8Create(module, dinput.DIRECTINPUT_VERSION,
                              dinput.IID_IDirectInput8W, 
                              ctypes.byref(_i_dinput), None)

def get_devices(display=None):
    _init_directinput()
    _devices = []

    def _device_enum(device_instance, arg):
        device = dinput.IDirectInputDevice8()
        _i_dinput.CreateDevice(device_instance.contents.guidInstance,
                               ctypes.byref(device),
                               None)
        _devices.append(DirectInputDevice(display, 
                                          device, device_instance.contents))
        
        return dinput.DIENUM_CONTINUE

    _i_dinput.EnumDevices(dinput.DI8DEVCLASS_ALL, 
                          dinput.LPDIENUMDEVICESCALLBACK(_device_enum), 
                          None, dinput.DIEDFL_ATTACHEDONLY)
    return _devices

def get_joysticks(display=None):
    return filter(None, [_create_joystick(d) for d in get_devices(display)])
