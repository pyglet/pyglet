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

    def __init__(self, name, min, max):
        self.name = name
        self.min = min
        self.max = max

    def _get_value(self):
        return self._value

    def _set_value(self, value):
        if value == self._value:
            return
        self._value = value
        self.dispatch_event('on_change', value)

    value = property(_get_value)

    def __repr__(self):
        return '%s(name=%s)' % (self.__class__.__name__, self.name)

    if _is_epydoc:
        def on_change(self, value):
            '''
            :event:
            '''

Control.register_event_type('on_change')

class Button(Control):
    def _get_value(self):
        return self._value

    def _set_value(self, value):
        if value == self._value:
            return
        self._value = value
        self.dispatch_event('on_change', value)
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

class Joystick(Device):
    def __init__(self, display, name):
        super(Joystick, self).__init__(display, name)

        # Default controls... provide default values as well?
        self.x = Control('x')
        self.y = Control('y')
        self.z = Control('z')
        self.ry = Control('ry')
        self.hat_x = Control('hat_x')
        self.hat_y = Control('hat_y')
        self.buttons = []
