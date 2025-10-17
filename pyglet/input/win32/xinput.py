import threading
import time
import weakref
from ctypes import POINTER, Structure, byref, c_void_p, windll
from ctypes.wintypes import DWORD, LONG, LPCWSTR, SHORT, ULONG, WORD

import pyglet
from pyglet.event import EventDispatcher
from pyglet.input.base import AbsoluteAxis, Button, Controller, ControllerManager, Device
from pyglet.libs.win32 import _ole32 as ole32
from pyglet.libs.win32 import _oleaut32 as oleaut32
from pyglet.libs.win32 import com
from pyglet.libs.win32.constants import CLSCTX_INPROC_SERVER
from pyglet.libs.win32.types import BYTE, VARIANT
from pyglet.math import Vec2

for library_name in ['xinput1_4', 'xinput9_1_0', 'xinput1_3']:
    try:
        lib = windll.LoadLibrary(library_name)
        break
    except OSError:
        continue
else:
    raise OSError('Could not import XInput')


XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE = 7849
XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE = 8689
XINPUT_GAMEPAD_TRIGGER_THRESHOLD = 30

BATTERY_DEVTYPE_GAMEPAD = 0x00
BATTERY_DEVTYPE_HEADSET = 0x01
BATTERY_TYPE_DISCONNECTED = 0x00
BATTERY_TYPE_WIRED = 0x01
BATTERY_TYPE_ALKALINE = 0x02
BATTERY_TYPE_NIMH = 0x03
BATTERY_TYPE_UNKNOWN = 0xFF

BATTERY_LEVEL_EMPTY = 0x00
BATTERY_LEVEL_LOW = 0x01
BATTERY_LEVEL_MEDIUM = 0x02
BATTERY_LEVEL_FULL = 0x03

XINPUT_GAMEPAD_DPAD_UP = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT = 0x0008
XINPUT_GAMEPAD_START = 0x0010
XINPUT_GAMEPAD_BACK = 0x0020
XINPUT_GAMEPAD_LEFT_THUMB = 0x0040
XINPUT_GAMEPAD_RIGHT_THUMB = 0x0080
XINPUT_GAMEPAD_LEFT_SHOULDER = 0x0100
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200
XINPUT_GAMEPAD_GUIDE = 0x0400
XINPUT_GAMEPAD_A = 0x1000
XINPUT_GAMEPAD_B = 0x2000
XINPUT_GAMEPAD_X = 0x4000
XINPUT_GAMEPAD_Y = 0x8000

XINPUT_KEYSTROKE_KEYDOWN = 0x0001
XINPUT_KEYSTROKE_KEYUP = 0x0002
XINPUT_KEYSTROKE_REPEAT = 0x0004

XINPUT_DEVTYPE_GAMEPAD = 0x01
XINPUT_DEVSUBTYPE_GAMEPAD = 0x01
XINPUT_DEVSUBTYPE_WHEEL = 0x02
XINPUT_DEVSUBTYPE_ARCADE_STICK = 0x03
XINPUT_DEVSUBTYPE_FLIGHT_SICK = 0x04
XINPUT_DEVSUBTYPE_DANCE_PAD = 0x05
XINPUT_DEVSUBTYPE_GUITAR = 0x06
XINPUT_DEVSUBTYPE_DRUM_KIT = 0x08

VK_PAD_A = 0x5800
VK_PAD_B = 0x5801
VK_PAD_X = 0x5802
VK_PAD_Y = 0x5803
VK_PAD_RSHOULDER = 0x5804
VK_PAD_LSHOULDER = 0x5805
VK_PAD_LTRIGGER = 0x5806
VK_PAD_RTRIGGER = 0x5807
VK_PAD_DPAD_UP = 0x5810
VK_PAD_DPAD_DOWN = 0x5811
VK_PAD_DPAD_LEFT = 0x5812
VK_PAD_DPAD_RIGHT = 0x5813
VK_PAD_START = 0x5814
VK_PAD_BACK = 0x5815
VK_PAD_LTHUMB_PRESS = 0x5816
VK_PAD_RTHUMB_PRESS = 0x5817
VK_PAD_LTHUMB_UP = 0x5820
VK_PAD_LTHUMB_DOWN = 0x5821
VK_PAD_LTHUMB_RIGHT = 0x5822
VK_PAD_LTHUMB_LEFT = 0x5823
VK_PAD_LTHUMB_UPLEFT = 0x5824
VK_PAD_LTHUMB_UPRIGHT = 0x5825
VK_PAD_LTHUMB_DOWNRIGHT = 0x5826
VK_PAD_LTHUMB_DOWNLEFT = 0x5827
VK_PAD_RTHUMB_UP = 0x5830
VK_PAD_RTHUMB_DOWN = 0x5831
VK_PAD_RTHUMB_RIGHT = 0x5832
VK_PAD_RTHUMB_LEFT = 0x5833
VK_PAD_RTHUMB_UPLEFT = 0x5834
VK_PAD_RTHUMB_UPRIGHT = 0x5835
VK_PAD_RTHUMB_DOWNRIGHT = 0x5836
VK_PAD_RTHUMB_DOWNLEFT = 0x5837

XUSER_MAX_COUNT = 4  # Cannot go over this number.
XUSER_INDEX_ANY = 0x000000FF


ERROR_DEVICE_NOT_CONNECTED = 1167
ERROR_EMPTY = 4306
ERROR_SUCCESS = 0


class XINPUT_GAMEPAD(Structure):
    _fields_ = [
        ('wButtons', WORD),
        ('bLeftTrigger', BYTE),
        ('bRightTrigger', BYTE),
        ('sThumbLX', SHORT),
        ('sThumbLY', SHORT),
        ('sThumbRX', SHORT),
        ('sThumbRY', SHORT),
    ]


class XINPUT_STATE(Structure):
    _fields_ = [
        ('dwPacketNumber', DWORD),
        ('Gamepad', XINPUT_GAMEPAD)
    ]


class XINPUT_VIBRATION(Structure):
    _fields_ = [
        ("wLeftMotorSpeed", WORD),
        ("wRightMotorSpeed", WORD),
    ]


class XINPUT_CAPABILITIES(Structure):
    _fields_ = [
        ('Type', BYTE),
        ('SubType', BYTE),
        ('Flags', WORD),
        ('Gamepad', XINPUT_GAMEPAD),
        ('Vibration', XINPUT_VIBRATION)
    ]


class XINPUT_BATTERY_INFORMATION(Structure):
    _fields_ = [
        ("BatteryType", BYTE),
        ("BatteryLevel", BYTE),
    ]


class XINPUT_CAPABILITIES_EX(Structure):
    _fields_ = [
        ('Capabilities', XINPUT_CAPABILITIES),
        ('vendorId', WORD),
        ('productId', WORD),
        ('revisionId', WORD),
        ('a4', DWORD)
    ]


if library_name == "xinput1_4":
    # Only available for 1.4+
    XInputGetBatteryInformation = lib.XInputGetBatteryInformation
    XInputGetBatteryInformation.argtypes = [DWORD, BYTE, POINTER(XINPUT_BATTERY_INFORMATION)]
    XInputGetBatteryInformation.restype = DWORD

    XInputGetState = lib[100]
    XInputGetState.restype = DWORD
    XInputGetState.argtypes = [DWORD, POINTER(XINPUT_STATE)]

    # Hidden function
    XInputGetCapabilities = lib[108]
    XInputGetCapabilities.restype = DWORD
    XInputGetCapabilities.argtypes = [DWORD, DWORD, DWORD, POINTER(XINPUT_CAPABILITIES_EX)]

else:
    XInputGetBatteryInformation = None

    XInputGetState = lib.XInputGetState
    XInputGetState.restype = DWORD
    XInputGetState.argtypes = [DWORD, POINTER(XINPUT_STATE)]

    XInputGetCapabilities = lib.XInputGetCapabilities
    XInputGetCapabilities.restype = DWORD
    XInputGetCapabilities.argtypes = [DWORD, DWORD, POINTER(XINPUT_CAPABILITIES)]


XInputSetState = lib.XInputSetState
XInputSetState.argtypes = [DWORD, POINTER(XINPUT_VIBRATION)]
XInputSetState.restype = DWORD


# wbemcli #################################################

BSTR = LPCWSTR
IWbemContext = c_void_p

RPC_C_AUTHN_WINNT = 10
RPC_C_AUTHZ_NONE = 0
RPC_C_AUTHN_LEVEL_CALL = 0x03
RPC_C_IMP_LEVEL_IMPERSONATE = 3
EOAC_NONE = 0
VT_BSTR = 8

CLSID_WbemLocator = com.GUID(0x4590f811, 0x1d3a, 0x11d0, 0x89, 0x1f, 0x00, 0xaa, 0x00, 0x4b, 0x2e, 0x24)
IID_IWbemLocator = com.GUID(0xdc12a687, 0x737f, 0x11cf, 0x88, 0x4d, 0x00, 0xaa, 0x00, 0x4b, 0x2e, 0x24)


class IWbemClassObject(com.pIUnknown):
    _methods_ = [
        ('GetQualifierSet',
         com.STDMETHOD()),
        ('Get',
         com.STDMETHOD(BSTR, LONG, POINTER(VARIANT), c_void_p, c_void_p))
        # ... long, unneeded
    ]


class IEnumWbemClassObject(com.pIUnknown):
    _methods_ = [
        ('Reset',
         com.STDMETHOD()),
        ('Next',
         com.STDMETHOD(LONG, ULONG, POINTER(IWbemClassObject), POINTER(ULONG))),
        ('NextAsync',
         com.STDMETHOD()),
        ('Clone',
         com.STDMETHOD()),
        ('Skip',
         com.STDMETHOD())
    ]


class IWbemServices(com.pIUnknown):
    _methods_ = [
        ('OpenNamespace',
         com.STDMETHOD()),
        ('CancelAsyncCall',
         com.STDMETHOD()),
        ('QueryObjectSink',
         com.STDMETHOD()),
        ('GetObject',
         com.STDMETHOD()),
        ('GetObjectAsync',
         com.STDMETHOD()),
        ('PutClass',
         com.STDMETHOD()),
        ('PutClassAsync',
         com.STDMETHOD()),
        ('DeleteClass',
         com.STDMETHOD()),
        ('DeleteClassAsync',
         com.STDMETHOD()),
        ('CreateClassEnum',
         com.STDMETHOD()),
        ('CreateClassEnumAsync',
         com.STDMETHOD()),
        ('PutInstance',
         com.STDMETHOD()),
        ('PutInstanceAsync',
         com.STDMETHOD()),
        ('DeleteInstance',
         com.STDMETHOD()),
        ('DeleteInstanceAsync',
         com.STDMETHOD()),
        ('CreateInstanceEnum',
         com.STDMETHOD(BSTR, LONG, IWbemContext, POINTER(IEnumWbemClassObject))),
        ('CreateInstanceEnumAsync',
         com.STDMETHOD()),
        # ... much more.
    ]


class IWbemLocator(com.pIUnknown):
    _methods_ = [
        ('ConnectServer',
         com.STDMETHOD(BSTR, BSTR, BSTR, LONG, LONG, BSTR, IWbemContext, POINTER(IWbemServices))),
    ]


def get_xinput_guids():
    """We iterate over all devices in the system looking for IG_ in the device ID, which indicates it's an
    XInput device. Returns a list of strings containing pid/vid.
    Monstrosity found at: https://docs.microsoft.com/en-us/windows/win32/xinput/xinput-and-directinput
    """
    guids_found = []

    locator = IWbemLocator()
    services = IWbemServices()
    enum_devices = IEnumWbemClassObject()
    devices = (IWbemClassObject * 20)()

    ole32.CoCreateInstance(CLSID_WbemLocator, None, CLSCTX_INPROC_SERVER, IID_IWbemLocator, byref(locator))

    name_space = BSTR("\\\\.\\root\\cimv2")
    class_name = BSTR("Win32_PNPEntity")
    device_id = BSTR("DeviceID")

    # Connect to WMI
    hr = locator.ConnectServer(name_space, None, None, 0, 0, None, None, byref(services))
    if hr != 0:
        return guids_found

    # Switch security level to IMPERSONATE.
    hr = ole32.CoSetProxyBlanket(services, RPC_C_AUTHN_WINNT, RPC_C_AUTHZ_NONE, None, RPC_C_AUTHN_LEVEL_CALL,
                                 RPC_C_IMP_LEVEL_IMPERSONATE, None, EOAC_NONE)

    if hr != 0:
        return guids_found

    hr = services.CreateInstanceEnum(class_name, 0, None, byref(enum_devices))

    if hr != 0:
        return guids_found

    var = VARIANT()
    oleaut32.VariantInit(byref(var))

    while True:
        returned = ULONG()
        _hr = enum_devices.Next(10000, len(devices), devices, byref(returned))
        if returned.value == 0:
            break
        for i in range(returned.value):
            result = devices[i].Get(device_id, 0, byref(var), None, None)
            if result == 0:
                if var.vt == VT_BSTR and var.bstrVal != "":
                    if 'IG_' in var.bstrVal:
                        guid = var.bstrVal

                        pid_start = guid.index("PID_") + 4
                        dev_pid = guid[pid_start:pid_start + 4]

                        vid_start = guid.index("VID_") + 4
                        dev_vid = guid[vid_start:vid_start + 4]

                        sdl_guid = f"{dev_pid}{dev_vid}".lower()

                        if sdl_guid not in guids_found:
                            guids_found.append(sdl_guid)

    oleaut32.VariantClear(byref(var))
    return guids_found


# #########################################################

controller_api_to_pyglet = {
    XINPUT_GAMEPAD_DPAD_UP: "dpup",
    XINPUT_GAMEPAD_DPAD_DOWN: "dpdown",
    XINPUT_GAMEPAD_DPAD_LEFT: "dpleft",
    XINPUT_GAMEPAD_DPAD_RIGHT: "dpright",
    XINPUT_GAMEPAD_START: "start",
    XINPUT_GAMEPAD_BACK: "back",
    XINPUT_GAMEPAD_GUIDE: "guide",
    XINPUT_GAMEPAD_LEFT_THUMB: "leftstick",
    XINPUT_GAMEPAD_RIGHT_THUMB: "rightstick",
    XINPUT_GAMEPAD_LEFT_SHOULDER: "leftshoulder",
    XINPUT_GAMEPAD_RIGHT_SHOULDER: "rightshoulder",
    XINPUT_GAMEPAD_A: "a",
    XINPUT_GAMEPAD_B: "b",
    XINPUT_GAMEPAD_X: "x",
    XINPUT_GAMEPAD_Y: "y",
}


class XInputDevice(Device):

    def __init__(self, index, manager):
        super().__init__(None, f"XInput{index}")
        self.index = index
        self._manager = weakref.proxy(manager)
        self.connected = False

        self.xinput_state = XINPUT_STATE()
        self.packet_number = 0

        self.vibration = XINPUT_VIBRATION()
        self.weak_duration = None
        self.strong_duration = None

        self.controls = {
            'a': Button('a'),
            'b': Button('b'),
            'x': Button('x'),
            'y': Button('y'),
            'back': Button('back'),
            'start': Button('start'),
            'guide': Button('guide'),
            'leftshoulder': Button('leftshoulder'),
            'rightshoulder': Button('rightshoulder'),
            'leftstick': Button('leftstick'),
            'rightstick': Button('rightstick'),
            'dpup': Button('dpup'),
            'dpdown': Button('dpdown'),
            'dpleft': Button('dpleft'),
            'dpright': Button('dpright'),

            'leftx': AbsoluteAxis('leftx', -32768, 32768),
            'lefty': AbsoluteAxis('lefty', -32768, 32768),
            'rightx': AbsoluteAxis('rightx', -32768, 32768),
            'righty': AbsoluteAxis('righty', -32768, 32768),
            'lefttrigger': AbsoluteAxis('lefttrigger', 0, 255),
            'righttrigger': AbsoluteAxis('righttrigger', 0, 255)
        }

    def set_rumble_state(self):
        XInputSetState(self.index, byref(self.vibration))

    def get_controls(self):
        return list(self.controls.values())

    def get_guid(self):
        return "XINPUTCONTROLLER"


class XInputDeviceManager(EventDispatcher):

    def __init__(self):
        self.all_devices = [XInputDevice(i, self) for i in range(XUSER_MAX_COUNT)]
        self._connected_devices = set()

        for i in range(XUSER_MAX_COUNT):
            device = self.all_devices[i]
            if XInputGetState(i, byref(device.xinput_state)) == ERROR_DEVICE_NOT_CONNECTED:
                continue
            device.connected = True
            self._connected_devices.add(i)

        self._polling_rate = 0.016
        self._detection_rate = 2.0
        self._exit = threading.Event()
        self._dev_lock = threading.Lock()
        self._thread = threading.Thread(target=self._get_state, daemon=True)
        self._thread.start()

    def get_devices(self):
        with self._dev_lock:
            return [dev for dev in self.all_devices if dev.connected]

    # Threaded method:
    def _get_state(self):
        xuser_max_count = set(range(XUSER_MAX_COUNT))     # {0, 1, 2, 3}
        polling_rate = self._polling_rate
        detect_rate = self._detection_rate
        elapsed = 0.0

        while not self._exit.is_set():
            self._dev_lock.acquire()
            elapsed += polling_rate

            # Every few seconds check for new connections:
            if elapsed >= detect_rate:
                # Only check if not currently connected:
                for i in xuser_max_count - self._connected_devices:
                    device = self.all_devices[i]
                    if XInputGetState(i, byref(device.xinput_state)) == ERROR_DEVICE_NOT_CONNECTED:
                        continue

                    # Found a new connection:
                    device.connected = True
                    self._connected_devices.add(i)
                    # Dispatch event in main thread:
                    pyglet.app.platform_event_loop.post_event(self, 'on_connect', device)

                elapsed = 0.0

            # At the set polling rate, update all connected and
            # opened devices. Skip unopened devices to save CPU:
            for i in self._connected_devices.copy():
                device = self.all_devices[i]
                result = XInputGetState(i, byref(device.xinput_state))

                if result == ERROR_DEVICE_NOT_CONNECTED:
                    # Newly disconnected device:
                    if device.connected:
                        device.connected = False
                        device.close()
                        self._connected_devices.remove(i)
                        # Dispatch event in main thread:
                        pyglet.app.platform_event_loop.post_event(self, 'on_disconnect', device)
                        continue

                elif result == ERROR_SUCCESS and device.is_open:

                    # Stop Rumble effects if a duration is set:
                    if device.weak_duration is not None:
                        device.weak_duration -= polling_rate
                        if device.weak_duration <= 0:
                            device.weak_duration = None
                            device.vibration.wRightMotorSpeed = 0
                            device.set_rumble_state()
                    if device.strong_duration is not None:
                        device.strong_duration -= polling_rate
                        if device.strong_duration <= 0:
                            device.strong_duration = None
                            device.vibration.wLeftMotorSpeed = 0
                            device.set_rumble_state()

                    # Don't update the Control values if XInput has no new input:
                    if device.xinput_state.dwPacketNumber == device.packet_number:
                        continue

                    # Post in main thread to avoid potential GL state issues
                    pyglet.app.platform_event_loop.post_event(self, '_on_state_change', device)

            self._dev_lock.release()
            time.sleep(polling_rate)

    @staticmethod
    def _on_state_change(device):
        # Handler to ensure Controller events are dispatched in the main thread.
        # The _get_state method dispatches this by posting to the platform event loop.
        for button, name in controller_api_to_pyglet.items():
            device.controls[name].value = device.xinput_state.Gamepad.wButtons & button

        device.controls['lefttrigger'].value = device.xinput_state.Gamepad.bLeftTrigger
        device.controls['righttrigger'].value = device.xinput_state.Gamepad.bRightTrigger
        device.controls['leftx'].value = device.xinput_state.Gamepad.sThumbLX
        device.controls['lefty'].value = device.xinput_state.Gamepad.sThumbLY
        device.controls['rightx'].value = device.xinput_state.Gamepad.sThumbRX
        device.controls['righty'].value = device.xinput_state.Gamepad.sThumbRY
        device.packet_number = device.xinput_state.dwPacketNumber

    def on_connect(self, device):
        """A device was connected."""

    def on_disconnect(self, device):
        """A device was disconnected"""


XInputDeviceManager.register_event_type('on_connect')
XInputDeviceManager.register_event_type('on_disconnect')
XInputDeviceManager.register_event_type('_on_state_change')


_device_manager = XInputDeviceManager()


class XInputController(Controller):

    def _initialize_controls(self):

        for button_name in controller_api_to_pyglet.values():
            control = self.device.controls[button_name]
            self._button_controls.append(control)
            self._add_button(control, button_name)

        for axis_name in "leftx", "lefty", "rightx", "righty", "lefttrigger", "righttrigger":
            control = self.device.controls[axis_name]
            self._axis_controls.append(control)
            self._add_axis(control, axis_name)

    def _add_axis(self, control, name):
        tscale = 1.0 / (control.max - control.min)
        scale = 2.0 / (control.max - control.min)
        bias = -1.0 - control.min * scale

        if name in ("lefttrigger", "righttrigger"):
            @control.event
            def on_change(value):
                normalized_value = value * tscale
                setattr(self, name, normalized_value)
                self.dispatch_event('on_trigger_motion', self, name, normalized_value)

        elif name in ("leftx", "lefty"):
            @control.event
            def on_change(value):
                normalized_value = value * scale + bias
                setattr(self, name, normalized_value)
                self.leftanalog = Vec2(self.leftx, self.lefty)
                self.dispatch_event('on_stick_motion', self, "leftstick", self.leftanalog)

        elif name in ("rightx", "righty"):
            @control.event
            def on_change(value):
                normalized_value = value * scale + bias
                setattr(self, name, normalized_value)
                self.rightanalog = Vec2(self.rightx, self.righty)
                self.dispatch_event('on_stick_motion', self, "rightstick", self.rightanalog)

    def _add_button(self, control, name):

        if name in ("dpleft", "dpright", "dpup", "dpdown"):
            @control.event
            def on_change(value):
                target, bias = {'dpleft': ('dpadx', -1.0), 'dpright': ('dpadx', 1.0),
                                'dpdown': ('dpady', -1.0), 'dpup': ('dpady', 1.0)}[name]
                setattr(self, target, bias * value)
                self.dpad = Vec2(self.dpadx, self.dpady)
                self.dispatch_event('on_dpad_motion', self, self.dpad)
        else:
            @control.event
            def on_change(value):
                setattr(self, name, value)

            @control.event
            def on_press():
                self.dispatch_event('on_button_press', self, name)

            @control.event
            def on_release():
                self.dispatch_event('on_button_release', self, name)

    def rumble_play_weak(self, strength=1.0, duration=0.5):
        self.device.vibration.wRightMotorSpeed = int(max(min(1.0, strength), 0) * 0xFFFF)
        self.device.weak_duration = duration
        self.device.set_rumble_state()

    def rumble_play_strong(self, strength=1.0, duration=0.5):
        self.device.vibration.wLeftMotorSpeed = int(max(min(1.0, strength), 0) * 0xFFFF)
        self.device.strong_duration = duration
        self.device.set_rumble_state()

    def rumble_stop_weak(self):
        self.device.vibration.wRightMotorSpeed = 0
        self.device.set_rumble_state()

    def rumble_stop_strong(self):
        self.device.vibration.wLeftMotorSpeed = 0
        self.device.set_rumble_state()


class XInputControllerManager(ControllerManager):

    def __init__(self):
        self._controllers = {}

        for device in _device_manager.all_devices:
            meta = {'name': device.name, 'guid': "XINPUTCONTROLLER"}
            self._controllers[device] = XInputController(device, meta)

        @_device_manager.event
        def on_connect(xdevice):
            self.dispatch_event('on_connect', self._controllers[xdevice])

        @_device_manager.event
        def on_disconnect(xdevice):
            self.dispatch_event('on_disconnect', self._controllers[xdevice])

    def get_controllers(self):
        return [ctlr for ctlr in self._controllers.values() if ctlr.device.connected]


def get_devices():
    return _device_manager.get_devices()


def get_controllers():
    return [XInputController(device, {'name': device.name, 'guid': device.get_guid()}) for device in get_devices()]
