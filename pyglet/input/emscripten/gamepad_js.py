from __future__ import annotations

import re
import warnings
from typing import Literal

import js
from js import console, navigator
from pyodide.ffi import create_proxy

import pyglet
from pyglet.input import Button, Device
from pyglet.input.base import AbsoluteAxis, Button, Controller, ControllerManager, Control
from pyglet.math import Vec2

class TriggerButton(Control):
    """A combination of a Button and an Axis.

    A trigger can behave like an axis between 0 and 1, but many games also want to treat it like a button press for
    fully down or fully released.

    When it reaches the maximum value, it will dispatch ``on_press``, and ``on_release`` on the minimum value.
    """
    def __init__(self, name: str, minimum: float, maximum: float, raw_name: None | str = None, inverted: bool = False) -> None:
        super().__init__(name, raw_name, inverted)
        self.min = minimum
        self.max = maximum

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, newvalue: float) -> None:
        if newvalue == self._value:
            return
        self._value = newvalue
        self.dispatch_event('on_change', bool(newvalue))
        if newvalue >= self.max:
            self.dispatch_event('on_press')
        elif newvalue <= self.min:
            self.dispatch_event('on_release')

_standard_button_map = {
    0: "a",
    1: "b",
    2: "x",
    3: "y",
    4: "leftshoulder",
    5: "rightshoulder",
    6: "lefttrigger",
    7: "righttrigger",
    8: "back",
    9: "start",
    10: "leftstick",
    11: "rightstick",
    12: "dpup",
    13: "dpdown",
    14: "dpleft",
    15: "dpright",
    16: "guide",
    17: "touchpad",  # touchpad button click for ps4.
}

_standard_axis_map = {
    0: "leftx",
    1: "lefty",
    2: "rightx",
    3: "righty",
}

# It's something, but not sure how to type it.
JSPromise = None

class _GamepadActuator:
    """Typing for Javascript Gamepad Actuator object."""
    effects: list[str]

    def playEffect(self,
                   effect_type: Literal["dual-rumble", "trigger-rumble"],
                   duration: int = 0,
                   startDelay: int = 0,
                   strongMagnitude: float = 0,
                   weakMagnitude: float = 0,
                   leftTrigger: float = 0,
                   rightTrigger: float = 0) -> JSPromise:
        """Play a specific vibration effect."""

    def pulse(self, value: float, duration: int) -> JSPromise:
        """Pulse at a certain intensity for a specified duration."""

    def reset(self) -> None:
        """Stop all effects."""


class _GamepadButton:
    """Typing for Javascript GamepadButton object."""
    pressed: bool
    touched: bool  # Some browsers support this, otherwise it may always be False
    value: float

class _Gamepad:
    """Typing for Javascript Gamepad object."""
    id: str
    index: int
    connected: bool
    timestamp: float
    mapping: str  # Typically "standard" or ""
    axes: list[float]
    buttons: list[_GamepadButton]
    vibrationActuator: _GamepadActuator | None


class JavascriptGamepad(Device):
    """Small wrapper over the Gamepad device.

    Do not rely on the gamepad object, as it gets replaced every frame in an update.
    """
    controls: dict[str, Button | AbsoluteAxis]

    def __init__(self, gamepad: _Gamepad) -> None:
        super().__init__(None, f"{gamepad.id}")
        self.index = gamepad.index
        self.connected = gamepad.connected
        self.gamepad = gamepad  # Will get replaced

        self.vendor_id = 0
        self.product_id = 0
        self.device_name = gamepad.id
        self.mapping_name = "standard"

        # Rumble support. Only on Chrome and Edge.
        if hasattr(gamepad, "vibrationActuator") and gamepad.vibrationActuator is not None:
            if "dual-rumble" in gamepad.vibrationActuator.effects:  # weak/strong motors.
                self.vibration = True
                console.log(f"Rumble supported for gamepad: {gamepad.id}")
            else:
                self.vibration = False
                console.log("Trigger rumble support found, but not implemented.")
        else:
            self.vibration = False
            console.log("Rumble not supported.")

        self.vibration = False

        # Some controllers report the Vendor and Product ID:
        match = re.search(r'^(.*?)(?: \((.*?)(?: Vendor: ([0-9a-fA-F]{4}) Product: ([0-9a-fA-F]{4}))?\))?$', gamepad.id)
        if match:
            self.device_name, mapping_name, vendor_id, product_id = match.groups()

            # If a vendor ID and product ID are found.
            if vendor_id and product_id:
                # Convert IDs to little-endian
                vendor_le = vendor_id[2:4] + vendor_id[0:2]
                product_le = product_id[2:4] + product_id[0:2]
                self.guid = f"03000000{vendor_le}0000{product_le}000000000000"
            else:
                warnings.warn("Vendor/Product IDs not found in GamePad ID.")
                self.guid = "STANDARD GAMEPAD"

            self.mapping_name = mapping_name if mapping_name else "standard"
        else:
            warnings.warn(f"Gamepad information could not be parsed from: {gamepad.id}")

        # See layout here: https://w3c.github.io/gamepad/#remapping
        self.controls = {
            'a': Button('a'),  # the “south” face button # 0
            'b': Button('b'),  # the “east” face button  # 1
            'x': Button('x'),  # the “west” face button   # 2
            'y': Button('y'),  # the “north” face button  # 3
            'back': Button('back'), # 8
            'start': Button('start'),  # 9
            'guide': Button('guide'),  # 16
            'leftshoulder': Button('leftshoulder'),  # 4
            'rightshoulder': Button('rightshoulder'),  # 5
            'lefttrigger': TriggerButton('lefttrigger', 0.0, 1.0),  # 6
            'righttrigger': TriggerButton('righttrigger', 0.0, 1.0),  # 7
            'leftstick': Button('leftstick'),  # 10
            'rightstick': Button('rightstick'),  # 11
            'dpup': Button('dpup'),  # 12
            'dpdown': Button('dpdown'),  # 13
            'dpleft': Button('dpleft'),  # 14
            'dpright': Button('dpright'),  # 15

            'leftx': AbsoluteAxis('leftx', -1, 1),  # axis horizontal # 0
            'lefty': AbsoluteAxis('lefty', -1, 1),  # axis vertical  # 1
            'rightx': AbsoluteAxis('rightx', -1, 1),  # axis horizontal 2
            'righty': AbsoluteAxis('righty', -1, 1),  # axis vertical 3

            'touchpad': Button('touchpad'),  # 17 on PS4 controller.
        }

    def get_controls(self) -> list[Control]:
        return list(self.controls.values())

    def get_guid(self) -> str:
        return self.guid


class GamepadController(Controller):
    """Javascript Gamepad Controller object that handles buttons and controls."""
    device: JavascriptGamepad
    def __init__(self, device: JavascriptGamepad, mapping: dict) -> None:
        super().__init__(device, mapping)
        self._last_updated = 0.0

    @property
    def gamepad_device(self) -> _Gamepad:
        return self.device.gamepad

    def _initialize_controls(self) -> None:
        for button_name in _standard_button_map.values():
            control = self.device.controls[button_name]
            self._button_controls.append(control)
            self._add_button(control, button_name)

        for axis_name in _standard_axis_map.values():
            control = self.device.controls[axis_name]
            self._axis_controls.append(control)
            self._add_axis(control, axis_name)

    def update(self, gamepad: _Gamepad) -> None:
        # Disconnect event should catch any disconnects.
        # Save some CPU if event fails by avoiding trying to update the states.
        if not gamepad.connected:
            self.device.connected = False
            return

        # Avoid going through all buttons unless the timestamp has changed on the gamepad data.
        if gamepad.timestamp > self._last_updated:
            self.device.connected = True

            for button_id, button in enumerate(gamepad.buttons):
                name = _standard_button_map[button_id]
                self.device.controls[name].value = button.pressed

            for axes_id, value in enumerate(gamepad.axes):
                name = _standard_axis_map[axes_id]
                self.device.controls[name].value = value

            self._last_updated = gamepad.timestamp

    def _add_axis(self, control: Control, name: str) -> None:
        if name == "lefttrigger":
            @control.event
            def on_change(value):
                setattr(self, name, value)
                self.dispatch_event('on_lefttrigger_motion', self, value)

            @control.event
            def on_press():
                self.dispatch_event('on_button_press', self, name)

            @control.event
            def on_release():
                self.dispatch_event('on_button_release', self, name)

        if name == "righttrigger":
            @control.event
            def on_change(value):
                setattr(self, name, value)
                self.dispatch_event('on_righttrigger_motion', self, value)

            @control.event
            def on_press():
                self.dispatch_event('on_button_press', self, name)

            @control.event
            def on_release():
                self.dispatch_event('on_button_release', self, name)

        elif name in ("leftx", "lefty"):
            @control.event
            def on_change(value):
                normalized_value = value
                setattr(self, name, normalized_value)
                self.dispatch_event('on_leftstick_motion', self, Vec2(self.leftx, -self.lefty))

        elif name in ("rightx", "righty"):
            @control.event
            def on_change(value):
                normalized_value = value
                setattr(self, name, normalized_value)
                self.dispatch_event('on_rightstick_motion', self, Vec2(self.rightx, -self.righty))

    def _add_button(self, control: Control, name: str) -> None:

        if name in ("dpleft", "dpright", "dpup", "dpdown"):
            @control.event
            def on_change(value):
                target, bias = {
                    'dpleft': ('dpadx', -1.0), 'dpright': ('dpadx', 1.0),
                    'dpdown': ('dpady', -1.0), 'dpup': ('dpady', 1.0)
                }[name]
                setattr(self, target, bias * value)
                self.dispatch_event('on_dpad_motion', self, Vec2(self.dpadx, self.dpady))
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

    def rumble_play_weak(self, strength: float=1.0, duration: float=0.5) -> None:
        if self.device.vibration is True:
            strength_clamp = int(max(min(1.0, strength), 0))
            self.gamepad_device.vibrationActuator.playEffect(
                "dual-rumble",
                startDelay=0,
                duration=int(duration*1000),
                weakMagnitude=strength_clamp,
            )

    def rumble_play_strong(self, strength: float=1.0, duration: float=0.5) -> None:
        if self.device.vibration is True:
            strength_clamp = int(max(min(1.0, strength), 0))
            self.gamepad_device.vibrationActuator.playEffect(
                "dual-rumble",
                startDelay=0,
                duration=int(duration*1000),
                strongMagnitude=strength_clamp,
            )

    def rumble_stop_weak(self) -> None:
        if self.device.vibration is True:
            self.gamepad_device.vibrationActuator.reset()

    def rumble_stop_strong(self) -> None:
        if self.device.vibration is True:
            self.gamepad_device.vibrationActuator.reset()


class JavascriptGamepadManager(ControllerManager):
    """Interface between Javascript/Pyodide and Pyglet to manage controllers."""

    _controllers: dict[int, GamepadController]

    def __init__(self):
        self._controllers = {}
        if hasattr(navigator, "getGamepads"):
            console.log("Gamepad API supported")
        else:
            console.log("Gamepad API not supported.")
            raise ImportError("Gamepad API not supported in this browser.")

        # Premake the gamepad objects so they can be kept on the user side.
        self._controllers = {}
        self._connected = set()

        self._proxy_connect = create_proxy(self.on_gamepad_connected)
        self._proxy_disconnect = create_proxy(self.on_gamepad_disconnected)

        # Add event listeners for gamepad connection and disconnection
        js.window.addEventListener("gamepadconnected", self._proxy_connect)
        js.window.addEventListener("gamepaddisconnected", self._proxy_disconnect)

        pyglet.clock.schedule_interval_soft(self._query_pads, 1/60.0)

    def on_gamepad_connected(self, event) -> None:
        console.log(f"Gamepad {event.gamepad.index} connected: {event.gamepad.id}. | Buttons: {len(event.gamepad.buttons)}, | Axis: {len(event.gamepad.axes)}")
        wrapper = JavascriptGamepad(event.gamepad)
        controller = GamepadController(wrapper, {"name": wrapper.device_name, "guid": wrapper.get_guid() })
        self._controllers[event.gamepad.index] = controller
        self.dispatch_event('on_connect', controller)

    def on_gamepad_disconnected(self, event) -> None:
        console.log(f"Gamepad disconnected: {event.gamepad.id}")
        if event.gamepad.index in self._controllers:
            del self._controllers[event.gamepad.index]

    def _query_pads(self, _dt: float) -> None:
        gamepads = navigator.getGamepads()

        for i in range(gamepads.length):
            gamepad = gamepads[i]
            if gamepad is not None:
                self._controllers[i].update(gamepad)

    @property
    def maximum_controllers(self) -> int:
        gamepads = navigator.getGamepads()
        return gamepads.length

    def get_devices(self):
        return []

    def get_controllers(self):
        return list(self._controllers.values())

def get_controllers(display=None):
    return []
