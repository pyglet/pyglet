import time
import ctypes
import weakref
import threading

import pyglet
from pyglet import com
from pyglet.libs.win32.types import *
from pyglet.libs.win32 import _ole32 as ole32, _oleaut32 as oleaut32
from pyglet.libs.win32.constants import CLSCTX_INPROC_SERVER
from pyglet.input.base import Device, Button, AbsoluteAxis

# Incase you want to force DirectInput on all devices for whatever reason.
if pyglet.options["xinput_controllers"] is not True:
    raise ImportError("Not available.")


lib = pyglet.lib.load_library('xinput1_4')
# TODO Add: xinput1_3 and xinput9_1_0 support

library_name = lib._name


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


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ('wButtons', WORD),
        ('bLeftTrigger', BYTE),
        ('bRightTrigger', BYTE),
        ('sThumbLX', SHORT),
        ('sThumbLY', SHORT),
        ('sThumbRX', SHORT),
        ('sThumbRY', SHORT),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ('dwPacketNumber', DWORD),
        ('Gamepad', XINPUT_GAMEPAD)
    ]


class XINPUT_VIBRATION(Structure):
    _fields_ = [
        ("wLeftMotorSpeed", WORD),
        ("wRightMotorSpeed", WORD),
    ]


class XINPUT_CAPABILITIES(ctypes.Structure):
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


class XINPUT_CAPABILITIES_EX(ctypes.Structure):
    _fields_ = [
        ('Capabilities', XINPUT_CAPABILITIES),
        ('vendorId', WORD),
        ('productId', WORD),
        ('revisionId', WORD),
        ('a4', DWORD)
    ]


XInputGetState = lib.XInputGetState
XInputGetState.restype = DWORD
XInputGetState.argtypes = [DWORD, POINTER(XINPUT_STATE)]

XInputSetState = lib.XInputSetState
XInputSetState.argtypes = [DWORD, POINTER(XINPUT_VIBRATION)]
XInputSetState.restype = DWORD

XInputGetCapabilities = lib.XInputGetCapabilities
XInputGetCapabilities.restype = DWORD
XInputGetCapabilities.argtypes = [DWORD, DWORD, POINTER(XINPUT_CAPABILITIES)]

# Hidden function
XInputGetCapabilitiesEx = lib[108]
XInputGetCapabilitiesEx.restype = DWORD
XInputGetCapabilitiesEx.argtypes = [DWORD, DWORD, DWORD, POINTER(XINPUT_CAPABILITIES_EX)]

# Only available for 1.4+
if library_name == "xinput1_4":
    XInputGetBatteryInformation = lib.XInputGetBatteryInformation
    XInputGetBatteryInformation.argtypes = [DWORD, BYTE, POINTER(XINPUT_BATTERY_INFORMATION)]
    XInputGetBatteryInformation.restype = DWORD
else:
    XInputGetBatteryInformation = None

# wbemcli #################################################

LONG = ctypes.wintypes.LONG
ULONG = ctypes.wintypes.ULONG
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
    ole32.CoInitialize(None)

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
        hr = enum_devices.Next(10000, len(devices), devices, byref(returned))
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

    oleaut32.VariantClear(var)
    ole32.CoUninitialize()
    return guids_found

# #########################################################

controller_api_to_pyglet = {
    XINPUT_GAMEPAD_DPAD_UP: "dpup",
    XINPUT_GAMEPAD_DPAD_DOWN: "dpdown",
    XINPUT_GAMEPAD_DPAD_LEFT: "dpleft",
    XINPUT_GAMEPAD_DPAD_RIGHT: "dpright",
    XINPUT_GAMEPAD_START: "start",
    XINPUT_GAMEPAD_BACK: "back",
    XINPUT_GAMEPAD_LEFT_THUMB: "leftstick",
    XINPUT_GAMEPAD_RIGHT_THUMB: "rightstick",
    XINPUT_GAMEPAD_LEFT_SHOULDER: "leftshoulder",
    XINPUT_GAMEPAD_RIGHT_SHOULDER: "rightshoulder",
    XINPUT_GAMEPAD_A: "a",
    XINPUT_GAMEPAD_B: "b",
    XINPUT_GAMEPAD_X: "x",
    XINPUT_GAMEPAD_Y: "y",
}


class XInputManager:

    def __init__(self):
        self._available_idx = []
        self._open_devices = set()
        self._devices = [XInputDevice(i, self) for i in range(XUSER_MAX_COUNT)]

        self._exit = threading.Event()
        self._dev_lock = threading.Lock()
        self._thread = threading.Thread(target=self._check_state, daemon=True)
        self._thread.start()

    def create_device(self):
        with self._dev_lock:
            try:
                index = self._available_idx.pop(0)
                return self._devices[index]
            except IndexError:
                raise IndexError('No available devices')

    def open(self, device):
        with self._dev_lock:
            self._open_devices.add(device)

    def close(self, device):
        with self._dev_lock:
            if device in self._open_devices:
                self._open_devices.remove(device)

    def _check_state(self):
        while not self._exit.is_set():
            self._dev_lock.acquire()

            for i in range(XUSER_MAX_COUNT):
                controller = self._devices[i]
                controller.current_state = XINPUT_STATE()

                result = XInputGetState(i, byref(controller.current_state))

                if result == ERROR_DEVICE_NOT_CONNECTED:
                    if i in self._available_idx:
                        self._available_idx.remove(i)
                    if controller.connected:
                        print(f"Controller #{controller} was disconnected.")
                        controller.connected = False
                        continue

                elif result == ERROR_SUCCESS:
                    if i not in self._available_idx:
                        self._available_idx.append(i)

                    if not controller.connected:
                        controller.connected = True
                        print(f"Controller #{controller} was connected.")

                        # Just testing
                        capabilities = XINPUT_CAPABILITIES_EX()
                        result = XInputGetCapabilitiesEx(1, i, 0, byref(capabilities))
                        print(capabilities.vendorId, capabilities.revisionId, capabilities.productId)


                    # TODO: skip not-open devices

                    for button, name in controller_api_to_pyglet.items():
                        controller.controls[name].value = controller.current_state.Gamepad.wButtons & button

                    controller.controls['lefttrigger'].value = controller.current_state.Gamepad.bLeftTrigger
                    controller.controls['righttrigger'].value = controller.current_state.Gamepad.bRightTrigger
                    controller.controls['leftx'].value = controller.current_state.Gamepad.sThumbLX
                    controller.controls['lefty'].value = controller.current_state.Gamepad.sThumbLY
                    controller.controls['rightx'].value = controller.current_state.Gamepad.sThumbRX
                    controller.controls['righty'].value = controller.current_state.Gamepad.sThumbRY

            self._dev_lock.release()
            time.sleep(0.016)


class XInputDevice(Device):

    def __init__(self, index, manager, display=None):
        super().__init__(display, f'XInput Controller {index}')
        self._manager = weakref.proxy(manager)
        self.index = index
        self.current_state = None
        self.connected = False

        self.controls = {
            'a': Button('a'),
            'b': Button('b'),
            'x': Button('x'),
            'y': Button('y'),
            'back': Button('back'),
            'start': Button('start'),
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

    def open(self, window=None, exclusive=False):
        super().open(window, exclusive)
        self._manager.open(self)

    def close(self):
        self._manager.close(self)
        super().close()

    def get_controls(self):
        return list(self.controls.values())

    def get_guid(self):
        return "XINPUTCONTROLLER"
