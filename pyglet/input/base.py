#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import sys

from pyglet.event import EventDispatcher

_is_epydoc = hasattr(sys, 'is_epydoc') and sys.is_epydoc

class DeviceException(Exception):
    pass

class DeviceOpenException(DeviceException):
    pass

class DeviceExclusiveException(DeviceException):
    pass

class Device(object):
    is_open = False

    def __init__(self, display, name):
        self.display = display
        self.name = name
        self.manufacturer = None

    def open(self, window=None, exclusive=False):
        if self.is_open:
            raise DeviceOpenException('Device is already open.')

        self.is_open = True

    def close(self):
        self.is_open = False

    def get_controls(self):
        raise NotImplementedError('abstract')

    def __repr__(self):
        return '%s(name=%s)' % (self.__class__.__name__, self.name)

class Control(EventDispatcher):
    '''
    Note that `min` and `max` properties are reported as provided by the
    device; in some cases the control's value will be outside this range.
    '''
    _value = None

    def __init__(self, name, raw_name=None):
        self.name = name
        self.raw_name = raw_name
        self.inverted = False

    def _get_value(self):
        return self._value

    def _set_value(self, value):
        if value == self._value:
            return
        self._value = value
        self.dispatch_event('on_change', value)

    value = property(_get_value)

    def __repr__(self):
        if self.name:
            return '%s(name=%s, raw_name=%s)' % (
                self.__class__.__name__, self.name, self.raw_name)
        else:
            return '%s(raw_name=%s)' % (self.__class__.__name__, self.raw_name)

    if _is_epydoc:
        def on_change(self, value):
            '''
            :event:
            '''

Control.register_event_type('on_change')

class RelativeAxis(Control):
    X = 'x'
    Y = 'y'
    Z = 'z'
    RX = 'rx'
    RY = 'ry'
    RZ = 'rz'
    WHEEL = 'wheel'

class AbsoluteAxis(Control):
    X = 'x'
    Y = 'y'
    Z = 'z'
    RX = 'rx'
    RY = 'ry'
    RZ = 'rz'
    HAT = 'hat'
    HAT_X = 'hat_x'
    HAT_Y = 'hat_y'

    def __init__(self, name, min, max, raw_name=None):
        super(AbsoluteAxis, self).__init__(name, raw_name)
        
        self.min = min
        self.max = max

class Button(Control):
    def _get_value(self):
        return bool(self._value)

    def _set_value(self, value):
        if value == self._value:
            return
        self._value = value
        self.dispatch_event('on_change', bool(value))
        if value:
            self.dispatch_event('on_press')
        else:
            self.dispatch_event('on_release')

    value = property(_get_value)
 
    if _is_epydoc:
        def on_press(self):
            '''
            :event:
            '''

        def on_release(self):
            '''
            :event:
            '''

Button.register_event_type('on_press')
Button.register_event_type('on_release')

class Joystick(object):
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

        def add_axis(control):
            name = control.name
            scale = 2.0 / (control.max - control.min)
            bias = -1.0 - control.min * scale
            if control.inverted:
                scale = -scale
                bias = -bias
            setattr(self, name + '_control', control)

            @control.event
            def on_change(value):
                setattr(self, name, value * scale + bias)

        def add_button(control):
            i = len(self.buttons)
            self.buttons.append(False)
            self.button_controls.append(control)

            @control.event
            def on_change(value):
                self.buttons[i] = value

        def add_hat(control):
            # 8-directional hat encoded as a single control (Windows/Mac)
            self.hat_x_control = control
            self.hat_y_control = control
            
            @control.event
            def on_change(value):
                if value & 0xffff == 0xffff:
                    self.hat_x = self.hat_y = 0
                else:
                    value //= 0xfff
                    if 0 <= value < 8:
                        self.hat_x, self.hat_y = (
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
                        self.hat_x = self.hat_y = 0

        for control in device.get_controls():
            if isinstance(control, AbsoluteAxis):
                if control.name in ('x', 'y', 'z', 'rx', 'ry', 'rz', 
                                    'hat_x', 'hat_y'):
                    add_axis(control)
                elif control.name == 'hat':
                    add_hat(control)
            elif isinstance(control, Button):
                add_button(control)

    def open(self, window=None, exclusive=False):
        self.device.open(window, exclusive)

    def close(self):
        self.device.close()
