#!/usr/bin/python
# $Id:$

import ctypes

import pyglet
from pyglet.input import base
from pyglet.libs import win32
from pyglet.libs.win32 import dinput
from pyglet.libs.win32 import _kernel32


class DirectInputControl(base.Control):
    value = None
    def __init__(self, object_instance):
        self._flags = object_instance.dwFlags
        self._guid = object_instance.guidType
        self._type = object_instance.dwType

        # TODO map name to well-known set
        name = object_instance.tszName
        super(DirectInputControl, self).__init__(name)

    def get_value(self):
        return self.value
        
class DirectInputDevice(base.Device):
    def __init__(self, display, device, device_instance):
        name = device_instance.tszInstanceName
        super(DirectInputDevice, self).__init__(display, name)

        #print self.name, hex(device_instance.dwDevType & 0xff), \
        #                hex(device_instance.dwDevType & 0xff00)
        #print hex(device_instance.wUsagePage), hex(device_instance.wUsage)

        self._device = device
        self._init_controls()
        self._set_format()

    def _init_controls(self):
        self.controls = []
        self._device.EnumObjects(
            dinput.LPDIENUMDEVICEOBJECTSCALLBACK(self._object_enum), 
            None, dinput.DIDFT_ALL)

    def _object_enum(self, object_instance, arg):
        type = object_instance.contents.dwType
        flags = object_instance.contents.dwFlags
        if type & dinput.DIDFT_NODATA:
            return dinput.DIENUM_CONTINUE

        control = DirectInputControl(object_instance.contents)
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

