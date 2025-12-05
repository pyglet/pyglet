from __future__ import annotations

import time
import warnings
import weakref
from ctypes import cdll, util, c_void_p, byref
from enum import Enum, auto
from typing import Protocol

import pyglet
from pyglet.event import EventDispatcher
from pyglet.libs.darwin import ObjCSubclass, ObjCInstance, send_super, \
    AutoReleasePool, ns_to_py, nsdict_to_py, PyObjectEncoding, nsnum_to_py
from pyglet.libs.darwin.cocoapy.runtime import get_callback_block
from pyglet.math import Vec2

from pyglet.window.cocoa.pyglet_delegate import NSNotification

from pyglet.input.base import Device, Control, Controller, Button, AbsoluteAxis, ControllerManager, Sign

from pyglet.libs.darwin import ObjCClass, get_selector
from pyglet.window.cocoa.pyglet_view import NSNotificationCenter

lib = util.find_library('GameController')

# Hack for compatibility with macOS > 11.0
if lib is None:
    lib = '/System/Library/Frameworks/GameController.framework/GameController'

gc = cdll.LoadLibrary(lib)

NSObject = ObjCClass('NSObject')
GCController = ObjCClass("GCController")
NSArray = ObjCClass('NSArray')


class _GCController(Protocol):
    """Just a type hint to better understand the controller API's"""

    def playerIndex(self) -> int: ...

    def vendorName(self) -> str: ...

    def battery(self): ...

    def haptics(self): ...

    def light(self): ...

    def physicalInputProfile(self): ...


GCControllerDidConnectNotification = c_void_p.in_dll(gc, 'GCControllerDidConnectNotification')
GCControllerDidDisconnectNotification = c_void_p.in_dll(gc, 'GCControllerDidDisconnectNotification')
GCInputDualShockTouchpadButton = c_void_p.in_dll(gc, 'GCInputDualShockTouchpadButton')

GCHapticsLocalityDefault = c_void_p.in_dll(gc, 'GCHapticsLocalityDefault')
GCHapticsLocalityAll = c_void_p.in_dll(gc, 'GCHapticsLocalityAll')
GCHapticsLocalityHandles = c_void_p.in_dll(gc, 'GCHapticsLocalityHandles')
GCHapticsLocalityLeftHandle = c_void_p.in_dll(gc, 'GCHapticsLocalityLeftHandle')
GCHapticsLocalityRightHandle = c_void_p.in_dll(gc, 'GCHapticsLocalityRightHandle')
GCHapticsLocalityTriggers = c_void_p.in_dll(gc, 'GCHapticsLocalityTriggers')
GCHapticsLocalityLeftTrigger = c_void_p.in_dll(gc, 'GCHapticsLocalityLeftTrigger')
GCHapticsLocalityRightTrigger = c_void_p.in_dll(gc, 'GCHapticsLocalityRightTrigger')

CHHapticEventParameterIDHapticSharpness = c_void_p.in_dll(gc, 'CHHapticEventParameterIDHapticSharpness')
CHHapticEventParameterIDHapticIntensity = c_void_p.in_dll(gc, 'CHHapticEventParameterIDHapticIntensity')
CHHapticEventParameterIDDecayTime = c_void_p.in_dll(gc, 'CHHapticEventParameterIDDecayTime')
CHHapticEventParameterIDReleaseTime = c_void_p.in_dll(gc, 'CHHapticEventParameterIDReleaseTime')
CHHapticEventParameterIDSustained = c_void_p.in_dll(gc, 'CHHapticEventParameterIDSustained')

CHHapticEventTypeAudioContinuous = c_void_p.in_dll(gc, 'CHHapticEventTypeAudioContinuous')
CHHapticEventTypeAudioCustom = c_void_p.in_dll(gc, 'CHHapticEventTypeAudioCustom')
CHHapticEventTypeHapticTransient = c_void_p.in_dll(gc, 'CHHapticEventTypeHapticTransient')
CHHapticEventTypeHapticContinuous = c_void_p.in_dll(gc, 'CHHapticEventTypeHapticContinuous')

GCHapticDurationInfinite = c_void_p.in_dll(gc, 'GCHapticDurationInfinite')

GCSystemGestureStateDisabled = 2

CHHapticDynamicParameterIDHapticIntensityControl = c_void_p.in_dll(gc,
                                                                   'CHHapticDynamicParameterIDHapticIntensityControl')

CHHapticEventParameter = ObjCClass('CHHapticEventParameter')
CHHapticEvent = ObjCClass('CHHapticEvent')
CHHapticPattern = ObjCClass('CHHapticPattern')
CHHapticDynamicParameter = ObjCClass('CHHapticDynamicParameter')

GCDeviceBatteryStateUnknown = -1
GCDeviceBatteryStateDischarging = 0
GCDeviceBatteryStateCharging = 1
GCDeviceBatteryStateFull = 2


class BatteryState(Enum):
    UNKNOWN = auto()
    DISCHARGING = auto()
    CHARGING = auto()
    FULL = auto()


_state_mapping = {
    GCDeviceBatteryStateUnknown: BatteryState.UNKNOWN,
    GCDeviceBatteryStateDischarging: BatteryState.DISCHARGING,
    GCDeviceBatteryStateCharging: BatteryState.CHARGING,
    GCDeviceBatteryStateFull: BatteryState.FULL,
}

_button_mapping = {
    "Direction Pad Up": "dpup",
    "Direction Pad Down": "dpdown",
    "Direction Pad Left": "dpleft",
    "Direction Pad Right": "dpright",
    "Button Menu": "start",
    "Button Options": "back",
    "Button Home": "guide",
    "Left Thumbstick Button": "leftthumb",
    "Right Thumbstick Button": "rightthumb",
    "Left Shoulder": "leftshoulder",
    "Right Shoulder": "rightshoulder",
    "Left Trigger": "lefttrigger",
    "Right Trigger": "righttrigger",
    "Button A": "a",
    "Button B": "b",
    "Button X": "x",
    "Button Y": "y",
    # "Touchpad Button": "touchpad",
}

_axis_mapping = {
    "Right Thumbstick Y Axis": "righty",
    "Right Thumbstick X Axis": "rightx",

    "Left Thumbstick X Axis": "leftx",
    "Left Thumbstick Y Axis": "lefty",

    "Left Trigger": "lefttrigger",
    "Right Trigger": "righttrigger",

    # "Direction Pad X Axis": "leftx",
    # "Direction Pad Y Axis": "lefty",

    # "Touchpad 1 Y Axis": "unsupport",
    # "Touchpad 1 X Axis": "unsupport",
    # "Touchpad 2 Y Axis": "unsupport",
    # "Touchpad 2 X Axis": "unsupport",
}

_dpads_mapping = {
    "Direction Pad": AbsoluteAxis.HAT,
    # "Touchpad 2": "unknown",
    # "Touchpad 1": "unknown",
    # "Right Thumbstick": "unknown",
    # "Left Thumbstick": "unknown",
}


class HapticEngine:
    def __init__(self, name: str, engine):
        self.name = name
        self.engine = engine

        # !!! Must retain or it will release on ObjC side.
        self.engine.retain()

        self._player = None
        self.is_playing = False

        self.error = c_void_p()

        self._create_player()

    def _create_player(self):
        with AutoReleasePool():
            event_param = CHHapticEventParameter.alloc().initWithParameterID_value_(
                CHHapticEventParameterIDHapticIntensity, 1.0,
            )
            params_arr = NSArray.arrayWithObject_(event_param)

            self.event = CHHapticEvent.alloc().initWithEventType_parameters_relativeTime_duration_(
                CHHapticEventTypeHapticContinuous,
                params_arr,
                0.0,
                10000.0
            )
            event_arr = NSArray.arrayWithObject_(self.event)
            empty_arr = NSArray.alloc().init()

            pattern = CHHapticPattern.alloc().initWithEvents_parameters_error_(event_arr, empty_arr,
                                                                               byref(self.error))

            if not pattern:
                self.as_nserror()
                return

            self._player = self.engine.createPlayerWithPattern_error_(pattern, byref(self.error))

            if not self._player:
                self.as_nserror()
                return

            self._player.retain()

    def as_nserror(self):
        ns_error = ObjCInstance(self.error.value)
        # print("macos GC error:", ns_error.localizedDescription())

    def trigger_event(self, intensity, sharpness, duration):
        self.is_playing = True

        param = CHHapticDynamicParameter.alloc().initWithParameterID_value_relativeTime_(
            CHHapticDynamicParameterIDHapticIntensityControl, intensity, 0,
        )

        dynam_param_arr = NSArray.arrayWithObject_(param)

        self._player.sendParameters_atTime_error_(dynam_param_arr, 0, byref(self.error))
        if self.error:
            # print("macos GC: Failed to update parameter")
            return

        self._player.startAtTime_error_(0, None)

        pyglet.clock.unschedule(self._schedule_stop)
        pyglet.clock.schedule_once(self._schedule_stop, duration)

    def _schedule_stop(self, dt):
        self.stop_event()

    def stop_event(self):
        if self.is_playing and self._player:
            self._player.stopAtTime_error_(0, None)
        self.is_playing = False

    def delete(self):
        if self._player:
            pyglet.clock.unschedule(self._schedule_stop)
            self.stop_event()
            self._player.cancelAndReturnError_(None)
            self._player.release()
            self._player = None

        if self.engine:
            self.engine.stopWithCompletionHandler_(None)
            self.engine.release()
            self.engine = None

    def __del__(self):
        self.delete()


class AppleGamepad(Device):

    def __init__(self, manager, controller: _GCController) -> None:

        with AutoReleasePool():
            self.manager = weakref.proxy(manager)
            self.device_name = ns_to_py(controller.vendorName())
            self.product_category = ns_to_py(controller.productCategory())

            super().__init__(None, self.device_name)
            self.controller = controller

            self.index = controller.playerIndex()

            self.battery = controller.battery()  # GCDeviceBattery
            self.haptics = controller.haptics()  # GCDeviceHaptics
            self.light = controller.light()  # GCDeviceLight

            self.weak_motor_engine = None
            self.strong_motor_engine = None

            if self.haptics:
                # self.weak_motor_engine = self._get_motor_engine(GCHapticsLocalityDefault)
                self.weak_motor_engine = self._get_motor_engine(GCHapticsLocalityLeftHandle)
                self.strong_motor_engine = self._get_motor_engine(GCHapticsLocalityRightHandle)

                # Can not get a strong or weak motor, just use default.
                if self.weak_motor_engine is None and self.strong_motor_engine is None:
                    engine = self._get_motor_engine(GCHapticsLocalityDefault)
                    self.weak_motor_engine = engine
                    self.strong_motor_engine = engine
                # No weak motor, just use the strong one?
                elif self.weak_motor_engine is None and self.strong_motor_engine is not None:
                    self.weak_motor_engine = self.strong_motor_engine
                # No strong motor, use the weak one?
                elif self.weak_motor_engine is not None and self.strong_motor_engine is None:
                    self.strong_motor_engine = self.weak_motor_engine

            self.profile = controller.physicalInputProfile()

            self.buttons = ns_to_py(self.profile.buttons())
            self.axes = ns_to_py(self.profile.axes())
            self.dpads = ns_to_py(self.profile.dpads())

            self._button_ptrs = {}
            if self.buttons:
                self._button_cb_block = get_callback_block(self._button_changed_callback, encoding=['v', '@', 'f'])
                for button_name, button_objc in self.buttons.items():
                    assert button_objc.ptr.value not in self._button_ptrs
                    pyglet_name = _button_mapping.get(button_name)
                    if not pyglet_name:
                        # print(f"Found: {button_name} button, but does not map to anything. Ignoring.")
                        continue
                    # Try to disable any "gestured" buttons so they can be used like actual buttons.
                    if button_objc.isBoundToSystemGesture():
                        button_objc.setPreferredSystemGestureState_(GCSystemGestureStateDisabled)
                    self._button_ptrs[button_objc.ptr.value] = pyglet_name

                    button_objc.setValueChangedHandler_(self._button_cb_block)

            self._axes_ptrs = {}
            if self.axes:
                self._axes_cb_block = get_callback_block(self._axis_changed_callback, encoding=['v', '@', 'f'])
                for axis_name, axis_obj in self.axes.items():
                    assert axis_obj.ptr.value not in self._axes_ptrs
                    pyglet_name = _axis_mapping.get(axis_name)
                    if not pyglet_name:
                        # print(f"Found: {axis_name} axis, but does not map to anything. Ignoring.")
                        continue
                    self._axes_ptrs[axis_obj.ptr.value] = pyglet_name
                    axis_obj.setValueChangedHandler_(self._axes_cb_block)

            self._dpad_ptrs = {}
            if self.dpads:
                self._dpad_cb_block = get_callback_block(self._dpads_changed_callback, encoding=['v', '@', 'f', 'f'])
                for dpad_name, dpad_obj in self.dpads.items():
                    assert dpad_obj.ptr.value not in self._dpad_ptrs
                    pyglet_name = _dpads_mapping.get(dpad_name)

                    if not pyglet_name:
                        continue
                    self._dpad_ptrs[dpad_obj.ptr.value] = pyglet_name
                    dpad_obj.setValueChangedHandler_(self._dpad_cb_block)

            # print("DEVICE NAME", repr(self.device_name), "index", self.index, self.product_category)

            # We need to store the Block's so callbacks don't get GC'd, as it contains CFUNCTYPES.
            self.cb_blocks = {}

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
                'leftthumb': Button('leftthumb'),
                'rightthumb': Button('rightthumb'),
                'dpup': Button('dpup'),
                'dpdown': Button('dpdown'),
                'dpleft': Button('dpleft'),
                'dpright': Button('dpright'),

                'leftx': AbsoluteAxis('leftx', -1, 1),
                'lefty': AbsoluteAxis('lefty', -1, 1, inverted=True),
                'rightx': AbsoluteAxis('rightx', -1, 1),
                'righty': AbsoluteAxis('righty', -1, 1, inverted=True),
                'lefttrigger': AbsoluteAxis('lefttrigger', 0, 1),
                'righttrigger': AbsoluteAxis('righttrigger', 0, 1),

                "hat": AbsoluteAxis('hat', 0, 1),
            }

    def _axis_changed_callback(self, axes_obj, value):
        name = self._axes_ptrs[axes_obj]
        self.controls[name].value = value

    def _button_changed_callback(self, button_obj, value):
        name = self._button_ptrs[button_obj]
        self.controls[name].value = value

    def _dpads_changed_callback(self, dpads_obj, value, value2):
        name = self._dpad_ptrs[dpads_obj]
        self.controls[name].value = value

    def get_battery_level(self) -> float:
        """Returns the current battery level.

        0.0 being discharged, or 1.0 as 100%. Defaults to 0.0 if not found.
        """
        if self.battery:
            return self.battery.batteryLevel()

        return 0.0

    def get_battery_state(self) -> BatteryState:
        if self.battery:
            battery_state = self.battery.batteryState()
            return _state_mapping.get(battery_state, BatteryState.UNKNOWN)

        return BatteryState.UNKNOWN

    def _get_motor_engine(self, locality):
        if self.haptics is None:
            return None

        locality_str = ns_to_py(ObjCInstance(locality))

        if locality_str not in ns_to_py(self.haptics.supportedLocalities()):
            warnings.warn(f"Controller supports haptics, but not locality: {locality}.")
            return None

        engine = self.haptics.createEngineWithLocality_(locality)
        if not engine:
            warnings.warn("Could not create motor engine.")
            return None

        err = c_void_p()

        error = engine.startAndReturnError_(err)
        if not error:
            # print("Error starting engine")
            return None

        self.haptic_engine = HapticEngine(locality, engine)
        return self.haptic_engine

    def get_controls(self) -> list[Control]:
        return list(self.controls.values())

    def get_guid(self) -> str:
        return "MFI_APPLE_CONTROLLER"


class AppleController(Controller):
    """Javascript Gamepad Controller object that handles buttons and controls."""
    device: AppleGamepad

    def __init__(self, device: AppleGamepad, mapping: dict) -> None:
        super().__init__(device, mapping)
        self._last_updated = 0.0

    def _initialize_controls(self) -> None:
        for button_name in _button_mapping.values():
            # Ignore any controls not mapped by pyglet...
            if button_name not in self.device.controls:
                continue
            control = self.device.controls[button_name]
            self.button_controls.append(control)
            self._bind_button_control(control, button_name)

        for axis_name in _axis_mapping.values():
            control = self.device.controls[axis_name]
            self.relative_axis_controls.append(control)
            self._bind_axis_control(control, axis_name, Sign.DEFAULT)

    def rumble_play_weak(self, strength: float = 1.0, duration: float = 0.5) -> None:
        if self.device and self.device.weak_motor_engine:
            strength_clamp = int(max(min(1.0, strength), 0))
            self.device.weak_motor_engine.trigger_event(strength_clamp, sharpness=1.0, duration=duration)

    def rumble_play_strong(self, strength: float = 1.0, duration: float = 0.5) -> None:
        if self.device and self.device.strong_motor_engine:
            strength_clamp = int(max(min(1.0, strength), 0))
            self.device.strong_motor_engine.trigger_event(strength_clamp, sharpness=1.0, duration=duration)

    def rumble_stop_weak(self) -> None:
        if self.device and self.device.weak_motor_engine:
            self.device.weak_motor_engine.stop_event()

    def rumble_stop_strong(self) -> None:
        if self.device and self.device.strong_motor_engine:
            self.device.strong_motor_engine.stop_event()


class _AppleControllerManager_Implementation(EventDispatcher):
    _PygletAppleControllerManager = ObjCSubclass('NSObject', '_PygletAppleControllerManager')

    @_PygletAppleControllerManager.method(b'@' + PyObjectEncoding)
    def initWithDispatcher(self, dispatcher: _SingletonAppleDispatcher):
        self = ObjCInstance(send_super(self, 'init'))
        if self is None:
            return None

        center = NSNotificationCenter.defaultCenter()
        center.addObserver_selector_name_object_(
            self,
            get_selector("controllerConnected:"),
            GCControllerDidConnectNotification,
            None,
        )
        center.addObserver_selector_name_object_(
            self,
            get_selector("controllerDisconnected:"),
            GCControllerDidDisconnectNotification,
            None,
        )

        controllers = {}
        self.associate("controllers", controllers)

        self.dispatcher = dispatcher

        GCController.startWirelessControllerDiscoveryWithCompletionHandler_(None)
        return self

    @_PygletAppleControllerManager.method('v@')
    def controllerConnected_(self, notification: NSNotification):
        device: GCController = notification.object()

        wrapper = AppleGamepad(self, device)
        controller = AppleController(wrapper, {"name": wrapper.device_name, "guid": "MFI_APPLE_CONTROLLER"})

        self.controllers[device] = controller

        self.dispatcher.dispatch_event('on_connect', controller)

    @_PygletAppleControllerManager.method('v@')
    def controllerDisconnected_(self, notification: NSNotification):
        device: GCController = notification.object()

        if device in self.controllers:
            self.dispatcher.dispatch_event('on_disconnect', self.controllers[device])

            del self.controllers[device]

    def get_controllers(self):
        return list(self.controllers.values())


_PygletAppleControllerManager = ObjCClass('_PygletAppleControllerManager')


class _SingletonAppleDispatcher(EventDispatcher):
    """Only keep this as we only need one."""

    def __init__(self):
        self._obj_mgr = _PygletAppleControllerManager.alloc().initWithDispatcher(self)


_SingletonAppleDispatcher.register_event_type("on_connect")
_SingletonAppleDispatcher.register_event_type("on_disconnect")

_apple_controller = _SingletonAppleDispatcher()


class AppleControllerManager(ControllerManager):

    def __init__(self):
        self._controllers = {}

        @_apple_controller.event
        def on_connect(controller):
            pyglet.app.platform_event_loop.post_event(self, 'on_connect', controller)

        @_apple_controller.event
        def on_disconnect(controller):
            pyglet.app.platform_event_loop.post_event(self, 'on_disconnect', controller)

    def get_controllers(self):
        return list(self._controllers.values())


def get_controllers(display=None):
    return []
