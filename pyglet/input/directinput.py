# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

import ctypes

import pyglet
from pyglet.input import base
from pyglet.libs import win32
from pyglet.libs.win32 import dinput
from pyglet.libs.win32 import _kernel32
from .controller import get_mapping

# These instance names are not defined anywhere, obtained by experiment.  The
# GUID names (which seem to be ideally what are needed) are wrong/missing for
# most of my devices.

_abs_instance_names = {
    0: 'x',
    1: 'y',
    2: 'z',
    3: 'rx', 
    4: 'ry',
    5: 'rz',
}

_rel_instance_names = {
    0: 'x',
    1: 'y',
    2: 'wheel',
}

_btn_instance_names = {}


def _create_control(object_instance):
    raw_name = object_instance.tszName
    ctrl_type = object_instance.dwType
    instance = dinput.DIDFT_GETINSTANCE(ctrl_type)

    if ctrl_type & dinput.DIDFT_ABSAXIS:
        name = _abs_instance_names.get(instance)
        control = base.AbsoluteAxis(name, 0, 0xffff, raw_name)
    elif ctrl_type & dinput.DIDFT_RELAXIS:
        name = _rel_instance_names.get(instance)
        control = base.RelativeAxis(name, raw_name)
    elif ctrl_type & dinput.DIDFT_BUTTON:
        name = _btn_instance_names.get(instance)
        control = base.Button(name, raw_name)
    elif ctrl_type & dinput.DIDFT_POV:
        control = base.AbsoluteAxis(base.AbsoluteAxis.HAT, 0, 0xffffffff, raw_name)
    else:
        return

    control._type = object_instance.dwType
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

        self.id_name = device_instance.tszProductName
        self.id_product_guid = format(device_instance.guidProduct.Data1, "08x")

    def __del__(self):
        self._device.Release()

    def get_guid(self):
        """Generate an SDL2 style GUID from the product guid."""
        first = self.id_product_guid[6:8] + self.id_product_guid[4:6]
        second = self.id_product_guid[2:4] + self.id_product_guid[0:2]
        return f"03000000{first}0000{second}000000000000"

    def _init_controls(self):
        self.controls = []
        self._device.EnumObjects(dinput.LPDIENUMDEVICEOBJECTSCALLBACK(self._object_enum), None, dinput.DIDFT_ALL)

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

        fmt = dinput.DIDATAFORMAT()
        fmt.dwSize = ctypes.sizeof(fmt)
        fmt.dwObjSize = ctypes.sizeof(dinput.DIOBJECTDATAFORMAT)
        fmt.dwFlags = 0
        fmt.dwDataSize = offset
        fmt.dwNumObjs = len(object_formats)
        fmt.rgodf = ctypes.cast(ctypes.pointer(object_formats), dinput.LPDIOBJECTDATAFORMAT)
        self._device.SetDataFormat(fmt)

        prop = dinput.DIPROPDWORD()
        prop.diph.dwSize = ctypes.sizeof(prop)
        prop.diph.dwHeaderSize = ctypes.sizeof(prop.diph)
        prop.diph.dwObj = 0
        prop.diph.dwHow = dinput.DIPH_DEVICE
        prop.dwData = 64 * ctypes.sizeof(dinput.DIDATAFORMAT)
        self._device.SetProperty(dinput.DIPROP_BUFFERSIZE, ctypes.byref(prop.diph))

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
        pyglet.app.platform_event_loop.add_wait_object(self._wait_object, self._dispatch_events)

        self._device.SetCooperativeLevel(window._hwnd, flags)
        self._device.Acquire()

    def close(self):
        if not self.controls:
            return

        pyglet.app.platform_event_loop.remove_wait_object(self._wait_object)

        self._device.Unacquire()
        self._device.SetEventNotification(None)

        _kernel32.CloseHandle(self._wait_object)

    def get_controls(self):
        return self.controls

    def _dispatch_events(self):
        if not self.controls:
            return
        
        events = (dinput.DIDEVICEOBJECTDATA * 64)()
        n_events = win32.DWORD(len(events))
        try:
            self._device.GetDeviceData(ctypes.sizeof(dinput.DIDEVICEOBJECTDATA),
                                       ctypes.cast(ctypes.pointer(events),
                                                   dinput.LPDIDEVICEOBJECTDATA),
                                       ctypes.byref(n_events),
                                       0)
        except OSError:
            return

        for event in events[:n_events.value]:
            index = event.dwOfs // 4
            self.controls[index].value = event.dwData


_i_dinput = None


def _init_directinput():
    global _i_dinput
    if _i_dinput:
        return
    
    _i_dinput = dinput.IDirectInput8()
    module_handle = _kernel32.GetModuleHandleW(None)
    dinput.DirectInput8Create(module_handle,
                              dinput.DIRECTINPUT_VERSION,
                              dinput.IID_IDirectInput8W, 
                              ctypes.byref(_i_dinput),
                              None)


def get_devices(display=None):
    _init_directinput()
    _devices = []
    _xinput_devices = []
    if pyglet.options["xinput_controllers"]:
        try:
            from .xinput import get_xinput_guids
            _xinput_devices = get_xinput_guids()
        except ImportError:
            pass

    def _device_enum(device_instance, arg):
        guid_id = format(device_instance.contents.guidProduct.Data1, "08x")
        # Only XInput should handle DirectInput devices if enabled. Filter them out.
        if guid_id in _xinput_devices:
            # Log somewhere?
            return dinput.DIENUM_CONTINUE

        device = dinput.IDirectInputDevice8()
        _i_dinput.CreateDevice(device_instance.contents.guidInstance, ctypes.byref(device), None)
        _devices.append(DirectInputDevice(display, device, device_instance.contents))
        return dinput.DIENUM_CONTINUE

    _i_dinput.EnumDevices(dinput.DI8DEVCLASS_ALL, 
                          dinput.LPDIENUMDEVICESCALLBACK(_device_enum), 
                          None,
                          dinput.DIEDFL_ATTACHEDONLY)
    return _devices


def _create_joystick(device):
    if device._type in (dinput.DI8DEVTYPE_JOYSTICK,
                        dinput.DI8DEVTYPE_1STPERSON,
                        dinput.DI8DEVTYPE_GAMEPAD,
                        dinput.DI8DEVTYPE_SUPPLEMENTAL):
        return base.Joystick(device)


def get_joysticks(display=None):
    return [joystick for joystick in
            [_create_joystick(device) for device in get_devices(display)]
            if joystick is not None]


def _create_controller(device):
    mapping = get_mapping(device.get_guid())
    if mapping is not None and device._type in (dinput.DI8DEVTYPE_JOYSTICK,
                                                dinput.DI8DEVTYPE_1STPERSON,
                                                dinput.DI8DEVTYPE_GAMEPAD):
        return base.Controller(device, mapping)


def get_controllers(display=None):
    return [controller for controller in
            [_create_controller(device) for device in get_devices(display)]
            if controller is not None]
