#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import input

# (usage_page, usage): Device class
'''
device_usage_map = {
    (0x01, 0x01): input.PointerDevice,
    (0x01, 0x01): input.MouseDevice,
    (0x01, 0x04): input.JoystickDevice,
    (0x01, 0x05): input.GamePadDevice,
    (0x01, 0x06): input.KeyboardDevice,
    (0x01, 0x07): input.KeypadDevice,
    (0x01, 0x08): input.MultiAxisControllerDevice,
}
'''

element_usage_names = {
    (0x01, 0x30): 'x',
    (0x01, 0x31): 'y',
    (0x01, 0x32): 'z',
    (0x01, 0x33): 'rx',
    (0x01, 0x34): 'ry',
    (0x01, 0x35): 'rz',
    (0x01, 0x36): 'slider',
    (0x01, 0x37): 'dial',
    (0x01, 0x38): 'wheel',
    (0x01, 0x39): 'hat_switch',
    (0x01, 0x3d): 'start',
    (0x01, 0x3e): 'select',
}

def get_element_usage_known(usage_page, usage):
    if usage_page == 0x09 and usage > 0:
        return True
    
    if (usage_page, usage) in element_usage_names:
        return True

    return False

def get_element_usage_name(usage_page, usage):
    if usage_page == 0x09:
        return 'button%d' % usage

    try:
        return element_usage_names[(usage_page, usage)]
    except KeyError:
        return '(%x, %x)' % (usage_page, usage)
