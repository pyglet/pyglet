#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import sys

from base import Device, Control, RelativeAxis, AbsoluteAxis, \
                 Button, Joystick, AppleRemote, Tablet
from base import DeviceException, DeviceOpenException, DeviceExclusiveException

_is_epydoc = hasattr(sys, 'is_epydoc') and sys.is_epydoc

def get_apple_remote(display=None):
    return None

if _is_epydoc:
    def get_devices(display=None):
        '''
        '''

    def get_joysticks(display=None):
        '''
        '''

    def get_tablets(display=None):
        '''
        '''
else:
    def get_tablets(display=None):
        return []

    if sys.platform == 'linux2':
        from x11_xinput import get_devices as xinput_get_devices
        #from x11_xinput import get_tablets
        from evdev import get_devices as evdev_get_devices
        from evdev import get_joysticks
        def get_devices(display=None):
            return (evdev_get_devices(display) +
                    xinput_get_devices(display))
    elif sys.platform in ('cygwin', 'win32'):
        from directinput import get_devices, get_joysticks
        try:
            from wintab import get_tablets
        except:
            pass
    elif sys.platform == 'darwin':
        from darwin_hid import get_devices, get_joysticks, get_apple_remote
        from carbon_tablet import get_tablets
