"""Interface classes for `pyglet.input`.

.. versionadded:: 1.2
"""
from __future__ import annotations

import sys
import enum
import warnings
import operator

from typing import TYPE_CHECKING

from pyglet.event import EventDispatcher

if TYPE_CHECKING:
    from pyglet.window import BaseWindow
    from pyglet.canvas.base import Display
    from pyglet.input.controller import Relation

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


class DeviceException(Exception):
    pass


class DeviceOpenException(DeviceException):
    pass


class DeviceExclusiveException(DeviceException):
    pass


class Sign(enum.Enum):
    POSITIVE = enum.auto()
    NEGATIVE = enum.auto()
    INVERTED = enum.auto()
    DEFAULT = enum.auto()


class Device:
    """Low level input device."""

    def __init__(self, display: Display, name: str) -> None:
        """Create a Device to receive input from.

        Args:
            display:
                The Display this device is connected to.
            name:
                The name of the device, as described by the device firmware.
        """
        self.display = display
        self.name = name

        #: The manufacturer name, if available
        self.manufacturer: str | None = None
        self._is_open: bool = False

    @property
    def is_open(self) -> bool:
        return self._is_open

    def open(self, window: None | BaseWindow = None, exclusive: bool = False) -> None:
        """Open the device to begin receiving input from it.

        Args:
            window:
                Optional window to associate with the device.  The behaviour
                of this parameter is device and operating system dependant.
                It can usually be omitted for most devices.
            exclusive:
                If ``True`` the device will be opened exclusively so that no
                other application can use it.

        Raises:
            DeviceOpenException:
                If the device cannot be opened in exclusive mode, usually
                due to being opened exclusively by another application.
        """

        if self._is_open:
            raise DeviceOpenException('Device is already open.')

        self._is_open = True

    def close(self) -> None:
        """Close the device."""
        self._is_open = False

    def get_controls(self) -> list[Control]:
        """Get a list of controls provided by the device."""
        raise NotImplementedError('abstract')

    def get_guid(self) -> str:
        """Get the device GUID, in SDL2 format.

        Return a str containing a unique device identification
        string. This is generated from the hardware identifiers,
        and is in the same format as was popularized by SDL2.
        GUIDs differ between platforms, but are generally 32
        hexidecimal characters.
        """
        raise NotImplementedError('abstract')

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"


class Control(EventDispatcher):
    """Single value input provided by a device.

    A control's value can be queried when the device is open.  Event handlers
    can be attached to the control to be called when the value changes.

    The ``min`` and ``max`` properties are provided as advertised by the
    device; in some cases the control's value will be outside this range.
    """

    def __init__(self, name: None | str, raw_name: None | str = None, inverted: bool = False):
        """Create a Control to receive input.

        Args:
            name:
                The name of the control, or ``None`` if unknown.
            raw_name:
                Optional unmodified name of the control, as presented by the operating
                system; or ``None`` if unknown.
            inverted:
                If ``True``, the value reported is actually inverted from what the
                device reported; usually this is to provide consistency across
                operating systems.
        """
        self.name = name
        self.raw_name = raw_name
        self.inverted = inverted
        self._value = None

    @property
    def value(self) -> float:
        """Current value of the control.

        The range of the value is device-dependent; for absolute controls
        the range is given by ``min`` and ``max`` (however the value may exceed
        this range); for relative controls the range is undefined.
        """
        return self._value

    @value.setter
    def value(self, newvalue: float):
        if newvalue == self._value:
            return
        self._value = newvalue
        self.dispatch_event('on_change', newvalue)

    def __repr__(self) -> str:
        if self.name:
            return f"{self.__class__.__name__}(name={self.name}, raw_name={self.raw_name})"
        else:
            return f"{self.__class__.__name__}(raw_name={self.raw_name})"

    # Events

    def on_change(self, value) -> float:
        """The value changed."""


Control.register_event_type('on_change')


class RelativeAxis(Control):
    """An axis whose value represents a relative change from the previous value.

    This type of axis is used for controls that can scroll or move
    continuously, such as a scrolling or pointing input. The value
    is read as a delta change from the previous value.
    """
    X: str = 'x'
    Y: str = 'y'
    Z: str = 'z'
    RX: str = 'rx'
    RY: str = 'ry'
    RZ: str = 'rz'
    WHEEL: str = 'wheel'

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, value: float):
        self._value = value
        self.dispatch_event('on_change', value)


class AbsoluteAxis(Control):
    """An axis whose value represents the current measurement from the device.

    This type of axis is used for controls that have minimum and maximum
    positions. The value is a range between the ``min`` and ``max``.
    """
    X: str = 'x'
    Y: str = 'y'
    Z: str = 'z'
    RX: str = 'rx'
    RY: str = 'ry'
    RZ: str = 'rz'
    HAT: str = 'hat'
    HAT_X: str = 'hat_x'
    HAT_Y: str = 'hat_y'

    def __init__(self, name: str, minimum: float, maximum: float, raw_name: None | str = None, inverted: bool = False):
        super().__init__(name, raw_name, inverted)
        self.min = minimum
        self.max = maximum


class Button(Control):
    """A control whose value is boolean. """

    @property
    def value(self) -> bool:
        return bool(self._value)

    @value.setter
    def value(self, newvalue: bool | int):
        if newvalue == self._value:
            return
        self._value = newvalue
        self.dispatch_event('on_change', bool(newvalue))
        if newvalue:
            self.dispatch_event('on_press')
        else:
            self.dispatch_event('on_release')

    if _is_pyglet_doc_run:
        # Events

        def on_press(self):
            """The button was pressed."""

        def on_release(self):
            """The button was released."""


Button.register_event_type('on_press')
Button.register_event_type('on_release')


class Joystick(EventDispatcher):
    """High-level interface for joystick-like devices.  This includes a wide
    range of analog and digital joysticks, gamepads, controllers, and possibly
    even steering wheels and other input devices. There is unfortunately no
    easy way to distinguish between most of these different device types.

    For a simplified subset of Joysticks, see the :py:class:`~pyglet.input.Controller`
    interface. This covers a variety of popular game console controllers. Unlike
    Joysticks, Controllers have strictly defined layouts and inputs.

    To use a joystick, first call `open`, then in your game loop examine
    the values of `x`, `y`, and so on.  These values are normalized to the
    range [-1.0, 1.0]. 

    To receive events when the value of an axis changes, attach an
    on_joyaxis_motion event handler to the joystick. The :py:class:`~pyglet.input.Joystick`
    instance, axis name, and current value are passed as parameters to this event.

    To handle button events, you should attach on_joybutton_press and on_joy_button_release
    event handlers to the joystick. Both the :py:class:`~pyglet.input.Joystick` instance
    and the index of the changed button are passed as parameters to these events.

    Alternately, you may attach event handlers to each individual button in 
    `button_controls` to receive on_press or on_release events.
    
    To use the hat switch, attach an on_joyhat_motion event handler to the joystick.
    The handler will be called with both the hat_x and hat_y values whenever the value
    of the hat switch changes.

    The device name can be queried to get the name of the joystick.
    """
    #: :The underlying device used by this joystick interface.
    device: Device

    #: :Current X (horizontal) value ranging from -1.0 (left) to 1.0 (right).
    x: float
    #: :Current y (vertical) value ranging from -1.0 (top) to 1.0 (bottom).
    y: float
    #: :Current Z value ranging from -1.0 to 1.0.  On joysticks the Z value is usually the
    #: :throttle control. On controllers the Z value is usually the secondary thumb vertical axis.
    z: float

    #: :Current rotational X value ranging from -1.0 to 1.0.
    rx: float
    #: :Current rotational Y value ranging from -1.0 to 1.0.
    ry: float
    #: :Current rotational Z value ranging from -1.0 to 1.0.  On joysticks the RZ value
    #: :is usually the twist of the stick.  On game controllers the RZ value is usually
    #: :the secondary thumb horizontal axis.
    rz: float

    #: :Current hat (POV) horizontal position; one of -1 (left), 0 (centered) or 1 (right).
    hat_x: int
    #: :Current hat (POV) vertical position; one of -1 (bottom), 0 (centered) or 1 (top).
    hat_y: int

    #: :List of boolean values representing current states of the buttons. These
    #: :are in order, so that button 1 has value at ``buttons[0]``, and so on.
    buttons: list[bool]

    #: :Underlying control for ``x`` value, or ``None`` if not available.
    x_control: None | AbsoluteAxis
    #: :Underlying control for ``y`` value, or ``None`` if not available.
    y_control: None | AbsoluteAxis
    #: :Underlying control for ``z`` value, or ``None`` if not available.
    z_control: None | AbsoluteAxis

    #: :Underlying control for ``rx`` value, or ``None`` if not available.
    rx_control: None | AbsoluteAxis
    #: :Underlying control for ``ry`` value, or ``None`` if not available.
    ry_control: None | AbsoluteAxis
    #: :Underlying control for ``rz`` value, or ``None`` if not available.
    rz_control: None | AbsoluteAxis

    #: :Underlying control for ``hat_x`` value, or ``None`` if not available.
    hat_x_control: None | AbsoluteAxis
    #: :Underlying control for ``hat_y`` value, or ``None`` if not available.
    hat_y_control: None | AbsoluteAxis

    #: Underlying controls for ``buttons`` values.
    button_controls: list[Button]

    def __init__(self, device):
        self.device = device

        self.x = 0
        self.y = 0
        self.z = 0
        self.rx = 0
        self.ry = 0
        self.rz = 0
        self.hat_x = 0
        self.hat_y = 0
        self.buttons = []

        self.x_control = None
        self.y_control = None
        self.z_control = None
        self.rx_control = None
        self.ry_control = None
        self.rz_control = None
        self.hat_x_control = None
        self.hat_y_control = None
        self.button_controls = []

        def add_axis(control: AbsoluteAxis):
            if not (control.min or control.max):
                warnings.warn(f"Control('{control.name}') min & max values are both 0. Skipping.")
                return
            name = control.name
            scale = 2.0 / (control.max - control.min)
            bias = -1.0 - control.min * scale
            if control.inverted:
                scale = -scale
                bias = -bias
            setattr(self, name + '_control', control)

            @control.event
            def on_change(value):
                normalized_value = value * scale + bias
                setattr(self, name, normalized_value)
                self.dispatch_event('on_joyaxis_motion', self, name, normalized_value)

        def add_button(control: Button):
            i = len(self.buttons)
            self.buttons.append(False)
            self.button_controls.append(control)

            @control.event
            def on_change(value):
                self.buttons[i] = value

            @control.event
            def on_press():
                self.dispatch_event('on_joybutton_press', self, i)

            @control.event
            def on_release():
                self.dispatch_event('on_joybutton_release', self, i)

        def add_hat(control: AbsoluteAxis):
            # 8-directional hat encoded as a single control (Windows/Mac)
            self.hat_x_control = control
            self.hat_y_control = control

            @control.event
            def on_change(value):
                if value & 0xffff == 0xffff:
                    self.hat_x = self.hat_y = 0
                else:
                    if control.max > 8:  # DirectInput: scale value
                        value //= 0xfff
                    if 0 <= value < 8:
                        self.hat_x, self.hat_y = (( 0,  1),
                                                  ( 1,  1),
                                                  ( 1,  0),
                                                  ( 1, -1),
                                                  ( 0, -1),
                                                  (-1, -1),
                                                  (-1,  0),
                                                  (-1,  1))[value]
                    else:
                        # Out of range
                        self.hat_x = self.hat_y = 0
                self.dispatch_event('on_joyhat_motion', self, self.hat_x, self.hat_y)

        for ctrl in device.get_controls():
            if isinstance(ctrl, AbsoluteAxis):
                if ctrl.name in ('x', 'y', 'z', 'rx', 'ry', 'rz', 'hat_x', 'hat_y'):
                    add_axis(ctrl)
                elif ctrl.name == 'hat':
                    add_hat(ctrl)
            elif isinstance(ctrl, Button):
                add_button(ctrl)

    def open(self, window: BaseWindow | None = None, exclusive: bool = False) -> None:
        """Open the joystick device.  See `Device.open`. """
        self.device.open(window, exclusive)

    def close(self) -> None:
        """Close the joystick device.  See `Device.close`. """
        self.device.close()

    # Events

    def on_joyaxis_motion(self, joystick: Joystick, axis: str, value: float):
        """The value of a joystick axis changed.

        Args:
            joystick:
                The joystick device whose axis changed.
            axis:
                The name of the axis that changed.
            value:
                The current value of the axis, normalized to [-1, 1].
        """

    def on_joybutton_press(self, joystick: Joystick, button: int):
        """A button on the joystick was pressed.

        Args:
            joystick:
                The joystick device whose button was pressed.
            button:
                The index (in `button_controls`) of the button that was pressed.
        """

    def on_joybutton_release(self, joystick: Joystick, button: int):
        """A button on the joystick was released.

        Args:
            joystick:
                The joystick device whose button was released.
            button:
                The index (in `button_controls`) of the button that was released.
        """

    def on_joyhat_motion(self, joystick: Joystick, hat_x: float, hat_y: float):
        """The value of the joystick hat switch changed.

        Args:
            joystick:
                The joystick device whose hat control changed.
            hat_x:
                Current hat (POV) horizontal position; one of -1.0 (left), 0.0
                (centered) or 1.0 (right).
            hat_y:
                Current hat (POV) vertical position; one of -1.0 (bottom), 0.0
                (centered) or 1.0 (top).
        """

    def __repr__(self) -> str:
        return f"Joystick(device={self.device.name})"


Joystick.register_event_type('on_joyaxis_motion')
Joystick.register_event_type('on_joybutton_press')
Joystick.register_event_type('on_joybutton_release')
Joystick.register_event_type('on_joyhat_motion')


class Controller(EventDispatcher):
    """High-level interface for Game Controllers.

    Unlike Joysticks, Controllers have a strictly defined set of inputs
    that matches the layout of popular home video game console Controllers.
    This includes a variety of face and shoulder buttons, analog sticks and
    triggers, a directional pad, and optional rumble (force feedback) effects.

    To use a Controller, you must first call ``open``. Controllers will then
    dispatch various events whenever the inputs change. They can also be polled
    manually at any time to find the current value of any inputs. Analog stick
    inputs are normalized to the range [-1.0, 1.0], and triggers are normalized
    to the range [0.0, 1.0]. All other inputs are digital.

    Note: A running application event loop is required

    The following event types are dispatched:
        `on_button_press`
        `on_button_release`
        `on_stick_motion`
        `on_dpad_motion`
        `on_trigger_motion`

    """

    def __init__(self, device: Device, mapping: dict):
        """Create a Controller instace mapped to a Device.

        .. versionadded:: 2.0
        """

        #: The underlying Device:
        self.device: Device = device
        self._mapping = mapping

        #: The logical device name
        self.name: str = mapping.get('name')
        #: The unique guid for this Device
        self.guid: str = mapping.get('guid')

        self.a: bool = False
        self.b: bool = False
        self.x: bool = False
        self.y: bool = False
        self.back: bool = False
        self.start: bool = False
        self.guide: bool = False
        self.leftshoulder: bool = False
        self.rightshoulder: bool = False
        self.leftstick: bool = False          # stick press button
        self.rightstick: bool = False         # stick press button
        self.lefttrigger: float = 0
        self.righttrigger: float = 0
        self.leftx: float = 0
        self.lefty: float = 0
        self.rightx: float = 0
        self.righty: float = 0
        self.dpup: bool = False
        self.dpdown: bool = False
        self.dpleft: bool = False
        self.dpright: bool = False

        # Default signs if bound to axis:
        self._dpup_sign = Sign.POSITIVE
        self._dpdown_sign = Sign.NEGATIVE
        self._dpleft_sign = Sign.NEGATIVE
        self._dpright_sign = Sign.POSITIVE

        self._button_controls = []
        self._axis_controls = []
        self._hat_control = None
        self._hat_x_control = None
        self._hat_y_control = None

        self._initialize_controls()

    def _bind_axis_control(self, relation: Relation, control: AbsoluteAxis, axis_name: str) -> None:
        if not (control.min or control.max):
            warnings.warn(f"Control('{control.name}') min & max values are both 0. Skipping.")
            return

        tscale = 1.0 / (control.max - control.min)
        scale = 2.0 / (control.max - control.min)
        bias = -1.0 - control.min * scale
        if control.inverted:
            scale = -scale
            bias = -bias

        # Track if any axis are reversed in the mappings
        if relation.sign in (Sign.POSITIVE, Sign.NEGATIVE):
            setattr(self, f"_{axis_name}_sign", relation.sign)

        # Analog to digital comparison operators and actuation limits
        dpad_comparison_map = {Sign.NEGATIVE: (operator.lt, -0.1), Sign.POSITIVE: (operator.gt, 0.1)}

        if axis_name in ("dpup", "dpdown"):
            @control.event
            def on_change(value):
                normalized_value = value * scale + bias
                compare, limit = dpad_comparison_map[self._dpup_sign]
                setattr(self, 'dpup', compare(normalized_value, limit))
                compare, limit = dpad_comparison_map[self._dpdown_sign]
                setattr(self, 'dpdown', compare(normalized_value, limit))
                self.dispatch_event('on_dpad_motion', self, self.dpleft, self.dpright, self.dpup, self.dpdown)

        elif axis_name in ("dpleft", "dpright"):
            @control.event
            def on_change(value):
                normalized_value = value * scale + bias
                compare, limit = dpad_comparison_map[self._dpleft_sign]
                setattr(self, 'dpleft', compare(normalized_value, limit))
                compare, limit = dpad_comparison_map[self._dpright_sign]
                setattr(self, 'dpright', compare(normalized_value, limit))
                self.dispatch_event('on_dpad_motion', self, self.dpleft, self.dpright, self.dpup, self.dpdown)

        elif axis_name in ("lefttrigger", "righttrigger"):
            @control.event
            def on_change(value):
                normalized_value = value * tscale
                setattr(self, axis_name, normalized_value)
                self.dispatch_event('on_trigger_motion', self, axis_name, normalized_value)

        elif axis_name in ("leftx", "lefty"):
            @control.event
            def on_change(value):
                setattr(self, axis_name, value * scale + bias)  # normalized value
                self.dispatch_event('on_stick_motion', self, "leftstick", self.leftx, -self.lefty)

        elif axis_name in ("rightx", "righty"):
            @control.event
            def on_change(value):
                setattr(self, axis_name, value * scale + bias)  # normalized value
                self.dispatch_event('on_stick_motion', self, "rightstick", self.rightx, -self.righty)

    def _bind_button_control(self, relation: Relation, control: Button, button_name: str) -> None:
        if button_name in ("dpleft", "dpright", "dpup", "dpdown"):
            @control.event
            def on_change(value):
                setattr(self, button_name, value)
                self.dispatch_event('on_dpad_motion', self, self.dpleft, self.dpright, self.dpup, self.dpdown)
        else:
            @control.event
            def on_change(value):
                setattr(self, button_name, value)

            @control.event
            def on_press():
                self.dispatch_event('on_button_press', self, button_name)

            @control.event
            def on_release():
                self.dispatch_event('on_button_release', self, button_name)

    def _bind_dedicated_hat(self, relation: Relation, control: AbsoluteAxis) -> None:
        # 8-directional hat encoded as a single control (Windows/Mac)
        @control.event
        def on_change(value):
            if value & 0xffff == 0xffff:
                self.dpleft = self.dpright = self.dpup = self.dpdown = False
            else:
                if control.max > 8:  # DirectInput: scale value
                    value //= 0xfff
                if 0 <= value < 8:
                    self.dpleft, self.dpright, self.dpup, self.dpdown = (
                        (False, False, True,  False),
                        (False, True,  True,  False),
                        (False, True,  False, False),
                        (False, True,  False, True),
                        (False, False, False, True),
                        (True,  False, False, True),
                        (True,  False, False, False),
                        (True,  False, True,  False))[value]
                else:
                    # Out of range
                    self.dpleft = self.dpright = self.dpup = self.dpdown = False

            self.dispatch_event('on_dpad_motion', self, self.dpleft, self.dpright, self.dpup, self.dpdown)

    def _initialize_controls(self) -> None:
        """Initialize and bind the Device Controls

        This method first categorizes all the Device Controls,
        then binds them to the appropriate "virtual" controls
        as defined in the mapped relations.
        """

        for ctrl in self.device.get_controls():
            # Categorize the various control types
            if isinstance(ctrl, Button):
                self._button_controls.append(ctrl)

            elif isinstance(ctrl, AbsoluteAxis):
                if ctrl.name == "hat_x":
                    self._hat_x_control = ctrl
                elif ctrl.name == "hat_y":
                    self._hat_y_control = ctrl
                elif ctrl.name == "hat":
                    self._hat_control = ctrl
                else:
                    self._axis_controls.append(ctrl)

        for name, relation in self._mapping.items():

            if relation is None or type(relation) is str:
                continue

            try:
                if relation.control_type == "button":
                    self._bind_button_control(relation, self._button_controls[relation.index], name)

                elif relation.control_type == "axis":
                    self._bind_axis_control(relation, self._axis_controls[relation.index], name)

                elif relation.control_type == "hat0":
                    if self._hat_control:
                        self._bind_dedicated_hat(relation, self._hat_control)
                    else:
                        control, dpname = {1: (self._hat_y_control, 'dpup'),
                                           2: (self._hat_x_control, 'dpright'),
                                           4: (self._hat_y_control, 'dpdown'),
                                           8: (self._hat_x_control, 'dpleft')}[relation.index]

                        self._bind_axis_control(relation, control, dpname)

            except IndexError:
                warnings.warn(f"Could not find control '{name}' with index '{relation.index}'.")
                continue

    def open(self, window: None | BaseWindow = None, exclusive: bool = False) -> None:
        """Open the controller.  See `Device.open`. """
        self.device.open(window, exclusive)

    def close(self) -> None:
        """Close the controller.  See `Device.close`. """
        self.device.close()

    def rumble_play_weak(self, strength: float = 1.0, duration: float = 0.5) -> None:
        """Play a rumble effect on the weak motor.

        Args:
            strength:
                The strength of the effect, from 0 to 1.
            duration:
                The duration of the effect in seconds.
        """

    def rumble_play_strong(self, strength: float = 1.0, duration: float = 0.5) -> None:
        """Play a rumble effect on the strong motor.

        Args:
            strength:
                The strength of the effect, from 0 to 1.
            duration:
                The duration of the effect in seconds.
        """

    def rumble_stop_weak(self) -> None:
        """Stop playing rumble effects on the weak motor."""

    def rumble_stop_strong(self) -> None:
        """Stop playing rumble effects on the strong motor."""

    # Events

    def on_stick_motion(self, controller: Controller, stick: str, xvalue: float, yvalue: float):
        """The value of a controller analogue stick changed.

        Args:
            controller:
                The controller whose analogue stick changed.
            stick:
                The name of the stick that changed.
            xvalue:
                The current X axis value, normalized to [-1, 1].
            yvalue:
                The current Y axis value, normalized to [-1, 1].
        """

    def on_dpad_motion(self, controller: Controller, dpleft: bool, dpright: bool, dpup: bool, dpdown: bool):
        """The direction pad of the controller changed.

        Args:
            controller:
                The controller whose hat control changed.
            dpleft:
                True if left is pressed on the directional pad.
            dpright:
                True if right is pressed on the directional pad.
            dpup:
                True if up is pressed on the directional pad.
            dpdown:
                True if down is pressed on the directional pad.
        """

    def on_trigger_motion(self, controller: Controller, trigger: str, value: float):
        """The value of a controller analogue stick changed.

        Args:
            controller:
                The controller whose analogue stick changed.
            trigger:
                The name of the trigger that changed.
            value:
                The current value of the trigger, normalized to [0, 1].
        """

    def on_button_press(self, controller: Controller, button: str):
        """A button on the controller was pressed.

        Args:
            controller:
                The controller whose button was pressed.
            button:
                The name of the button that was pressed.
        """

    def on_button_release(self, controller: Controller, button: str):
        """A button on the joystick was released.

        Args:
            controller:
                The controller whose button was released.
            button:
                The name of the button that was released.
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"


Controller.register_event_type('on_button_press')
Controller.register_event_type('on_button_release')
Controller.register_event_type('on_stick_motion')
Controller.register_event_type('on_dpad_motion')
Controller.register_event_type('on_trigger_motion')


class AppleRemote(EventDispatcher):
    """High-level interface for Apple remote control.

    This interface provides access to the 6 button controls on the remote.
    Pressing and holding certain buttons on the remote is interpreted as
    a separate control.
    """

    device: Device
    left_control: Button
    left_hold_control: Button
    right_control: Button
    right_hold_control: Button
    up_control: Button
    down_control: Button
    select_control: Button
    select_hold_control: Button
    menu_control: Button
    menu_hold_control: Button

    def __init__(self, device):
        self.device = device

        def _add_button(button: Button):
            setattr(self, button.name + '_control', button)

            @button.event
            def on_press():
                self.dispatch_event('on_button_press', button.name)

            @button.event
            def on_release():
                self.dispatch_event('on_button_release', button.name)

        for control in device.get_controls():
            if control.name in ('left', 'left_hold', 'right', 'right_hold', 'up', 'down',
                                'menu', 'select', 'menu_hold', 'select_hold'):
                _add_button(control)

    def open(self, window: BaseWindow, exclusive: bool = False):
        """Open the device.  See `Device.open`. """
        self.device.open(window, exclusive)

    def close(self):
        """Close the device.  See `Device.close`. """
        self.device.close()

    # Events

    def on_button_press(self, button: str):
        """A button on the remote was pressed.

        Only the 'up' and 'down' buttons will generate an event when the
        button is first pressed.  All other buttons on the remote will wait
        until the button is released and then send both the press and release
        events at the same time.

        Args:
            button:
                The name of the button that was pressed. The valid names are
                'up', 'down', 'left', 'right', 'left_hold', 'right_hold',
                'menu', 'menu_hold', 'select', and 'select_hold'
        """

    def on_button_release(self, button: str):
        """A button on the remote was released.

        The 'select_hold' and 'menu_hold' button release events are sent
        immediately after the corresponding press events regardless of
        whether the user has released the button.

        Args:
            button:
                The name of the button that was released. The valid names are
                'up', 'down', 'left', 'right', 'left_hold', 'right_hold',
                'menu', 'menu_hold', 'select', and 'select_hold'
        """


AppleRemote.register_event_type('on_button_press')
AppleRemote.register_event_type('on_button_release')


class Tablet:
    """High-level interface to tablet devices.

    Unlike other devices, tablets must be opened for a specific window,
    and cannot be opened exclusively.  The `open` method returns a
    `TabletCanvas` object, which supports the events provided by the tablet.

    Currently only one tablet device can be used, though it can be opened on
    multiple windows.  If more than one tablet is connected, the behaviour is
    undefined.
    """

    def open(self, window: BaseWindow) -> TabletCanvas:
        """Open a tablet device for a window.

        Args:
            window:
                The window on which the tablet will be used.
        """
        raise NotImplementedError('abstract')


class TabletCanvas(EventDispatcher):
    """Event dispatcher for tablets.

    Use `Tablet.open` to obtain this object for a particular tablet device and
    window.  Events may be generated even if the tablet stylus is outside of
    the window; this is operating-system dependent.

    The events each provide the `TabletCursor` that was used to generate the
    event; for example, to distinguish between a stylus and an eraser.  Only
    one cursor can be used at a time, otherwise the results are undefined.
    """

    # OS X: Active window receives tablet events only when cursor is in window
    # Windows: Active window receives all tablet events
    #
    # Note that this means enter/leave pairs are not always consistent (normal
    # usage).

    def __init__(self, window: BaseWindow):
        """Create a TabletCanvas.

        Args:
            window:
                The window on which this tablet was opened.
        """
        self.window = window

    def close(self) -> None:
        """Close the tablet device for this window."""
        raise NotImplementedError('abstract')

    if _is_pyglet_doc_run:
        # Events

        def on_enter(self, cursor: TabletCursor):
            """A cursor entered the proximity of the window.  The cursor may
            be hovering above the tablet surface, but outside the window
            bounds, or it may have entered the window bounds.

            Note that you cannot rely on `on_enter` and `on_leave` events to
            be generated in pairs; some events may be lost if the cursor was
            out of the window bounds at the time.

            :event:
            """

        def on_leave(self, cursor: TabletCursor):
            """A cursor left the proximity of the window.  The cursor may have
            moved too high above the tablet surface to be detected, or it may
            have left the bounds of the window.

            Note that you cannot rely on `on_enter` and `on_leave` events to
            be generated in pairs; some events may be lost if the cursor was
            out of the window bounds at the time.
            """

        def on_motion(self, cursor: TabletCursor, x: int, y: int,
                      pressure: float, tilt_x: float, tilt_y: float, buttons: int):
            """The cursor moved on the tablet surface.

            If `pressure` is 0, then the cursor is actually hovering above the
            tablet surface, not in contact.

            Args:
                cursor:
                    The cursor that moved.
                x:
                    The X position of the cursor, in window coordinates.
                y:
                    The Y position of the cursor, in window coordinates.
                pressure:
                    The pressure applied to the cursor, in range 0.0
                    (no pressure) to 1.0 (full pressure).
                tilt_x:
                    Currently undefined.
                tilt_y:
                    Currently undefined.
                buttons:
                    Button state may be provided if the platform supports it.
                    Supported on: Windows
            """


TabletCanvas.register_event_type('on_enter')
TabletCanvas.register_event_type('on_leave')
TabletCanvas.register_event_type('on_motion')


class TabletCursor:
    """A distinct cursor used on a Tablet device.

    Most tablets support at least a ``stylus`` and an ``erasor`` cursor;
    this object is used to distinguish them when tablet events are generated.
    """

    # TODO well-defined names for stylus and eraser.

    def __init__(self, name: str):
        """Create a cursor object.

        Args:
            name:
                The name of the cursor.
        """
        self.name = name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"


class ControllerManager(EventDispatcher):
    """High level interface for managing game Controllers.

    This class provides a convenient way to handle the
    connection and disconnection of devices. A list of all
    connected Controllers can be queried at any time with the
    `get_controllers` method. For hot-plugging, events are
    dispatched for `on_connect` and `on_disconnect`.
    To use the ControllerManager, first make an instance::

        controller_man = pyglet.input.ControllerManager()

    At the start of your game, query for any Controllers
    that are already connected::

        controllers = controller_man.get_controllers()

    To handle Controllers that are connected or disconnected
    after the start of your game, register handlers for the
    appropriate events::

        @controller_man.event
        def on_connect(controller):
            # code to handle newly connected
            # (or re-connected) controllers
            controller.open()
            print("Connect:", controller)

        @controller_man.event
        def on_disconnect(controller):
            # code to handle disconnected Controller
            print("Disconnect:", controller)

    .. versionadded:: 1.2
    """

    def get_controllers(self) -> list[Controller]:
        """Get a list of all connected Controllers"""
        raise NotImplementedError

    # Events

    def on_connect(self, controller) -> Controller:
        """A Controller has been connected. If this is
        a previously dissconnected Controller that is
        being re-connected, the same Controller instance
        will be returned.
        """

    def on_disconnect(self, controller) -> Controller:
        """A Controller has been disconnected."""


ControllerManager.register_event_type('on_connect')
ControllerManager.register_event_type('on_disconnect')
