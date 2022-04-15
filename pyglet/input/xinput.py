import time
import ctypes
import threading

import pyglet

from pyglet.libs.win32.types import *
from base import Device, Button, AbsoluteAxis


lib = pyglet.lib.load_library('xinput1_4')


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

# /*
#  * How many joysticks can be used with this library. Games that
#  * use the xinput library will not go over this number.
#  */

XUSER_MAX_COUNT = 4
XUSER_INDEX_ANY = 0x000000FF


# define XUSER_INDEX_ANY                 0x000000FF

# define XINPUT_CAPS_FFB_SUPPORTED       0x0001
# define XINPUT_CAPS_WIRELESS            0x0002
# define XINPUT_CAPS_PMD_SUPPORTED       0x0008
# define XINPUT_CAPS_NO_NAVIGATION       0x0010

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
XInputGetBatteryInformation = lib.XInputGetBatteryInformation
XInputGetBatteryInformation.argtypes = [DWORD, BYTE, POINTER(XINPUT_BATTERY_INFORMATION)]
XInputGetBatteryInformation.restype = DWORD


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


class XinputManager:

    def __init__(self):
        self._thread = threading.Thread(target=self._check_state, daemon=True)
        self._exit = threading.Event()
        self._dev_lock = threading.Lock()

        # TODO: update the available IDs based on actual available devices
        self._available_ids = [0, 1, 2, 3]
        self._devices = set()
        self._open_devices = set()

    def create_device(self):
        if not self._available_ids:
            # TODO: some better exception, etc.
            raise Exception('No available devices')
        with self._dev_lock:
            dev_id = self._available_ids.pop()
            device = XinputDevice(dev_id, self)
            self._devices.add(device)

    def open(self, device):
        with self._dev_lock:
            self._devices.remove(device)
            self._open_devices.add(device)

    def close(self, device):
        with self._dev_lock:
            if device in self._devices:
                self._devices.remove(device)
            if device in self._open_devices:
                self._open_devices.remove(device)

        self._available_ids.append(device.index)

    def _check_state(self):
        while not self._exit.is_set():
            self._dev_lock.acquire()

            for controller in self._open_devices:
                time.sleep(0.0016)
                controller.current_state = XINPUT_STATE()
                result = XInputGetState(controller.index, byref(controller.current_state))
                if result == ERROR_DEVICE_NOT_CONNECTED:
                    if controller.connected:
                        print(f"Controller #{controller} was disconnected.")
                        controller.connected = False
                        continue

                elif result == ERROR_SUCCESS:
                    # No errors.
                    if not controller.connected:
                        controller.connected = True
                        print(f"Controller #{controller} was connected.")

                        # Just testing
                        capabilities = XINPUT_CAPABILITIES_EX()
                        result = XInputGetCapabilitiesEx(1, controller.index, 0, byref(capabilities))
                        print(capabilities.vendorId, capabilities.revisionId, capabilities.productId)

                    # Check for any changes on controller
                    if controller.last_state:
                        # Verify buttons haven't changed.
                        current_state_buttons = controller.current_state.Gamepad.wButtons
                        last_state_buttons = controller.last_state.Gamepad.wButtons

                        if current_state_buttons != last_state_buttons:
                            difference = current_state_buttons ^ last_state_buttons
                            for button, property in controller_api_to_pyglet.items():
                                # Check all flags for button changes/
                                # Factor in XINPUT_GAMEPAD_TRIGGER_THRESHOLD?
                                if difference & button:
                                    if difference & button & current_state_buttons:
                                        controller.dispatch_event('on_button_press', controller, property)
                                    else:
                                        controller.dispatch_event('on_button_release', controller, property)

                        if controller.current_state.Gamepad.bLeftTrigger != controller.last_state.Gamepad.bLeftTrigger:
                            # Take threshhold/deadzone into account somehow?
                            normalized_value = controller.current_state.Gamepad.bLeftTrigger
                            controller.dispatch_event('on_trigger_motion', controller, "lefttrigger", normalized_value)

                        if controller.current_state.Gamepad.bRightTrigger != controller.last_state.Gamepad.bRightTrigger:
                            # Take threshhold/deadzone into account somehow?
                            normalized_value = controller.current_state.Gamepad.bRightTrigger
                            controller.dispatch_event('on_trigger_motion', controller, "righttrigger", normalized_value)

                        last_thumb_lx = controller.last_state.Gamepad.sThumbLX
                        last_thumb_ly = controller.last_state.Gamepad.sThumbLY
                        current_thumb_lx = controller.current_state.Gamepad.sThumbLX
                        current_thumb_ly = controller.current_state.Gamepad.sThumbLX
                        if last_thumb_lx != current_thumb_lx or last_thumb_ly != current_thumb_ly:
                            # Factor in XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE?
                            controller.dispatch_event('on_stick_motion', controller, "leftstick", current_thumb_lx,
                                                      current_thumb_ly)

                        last_thumb_rx = controller.last_state.Gamepad.sThumbRX
                        last_thumb_ry = controller.last_state.Gamepad.sThumbRY
                        current_thumb_rx = controller.current_state.Gamepad.sThumbRX
                        current_thumb_ry = controller.current_state.Gamepad.sThumbRX
                        if last_thumb_rx != current_thumb_rx or last_thumb_ry != current_thumb_ry:
                            # Factor in XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE?
                            controller.dispatch_event('on_stick_motion', controller, "rightstick", current_thumb_rx,
                                                      current_thumb_ry)

                controller.last_state = controller.current_state

                self._dev_lock.release()


class XinputDevice(Device):

    def __init__(self, index, manager, display=None):
        super().__init__(display, f'XInput Controller {index}')
        self._manager = manager
        self.user_idx = index
        self.last_state = None
        self.current_state = None
        self.connected = False

        self.controls = {
            'a': bool,
            'b': bool,
            'x': bool,
            'y': bool,
            'back': bool,
            'start': bool,
            'guide': bool,
            'leftshoulder': bool,
            'rightshoulder': bool,
            'leftstick': bool,
            'rightstick': bool,

            'leftx': bool,
            'lefty': bool,
            'rightx': bool,
            'righty': bool,
            'lefttrigger': bool,
            'righttrigger': bool,

            'dpup': bool,
            'dpdown': bool,
            'dpleft': bool,
            'dpright': bool
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
