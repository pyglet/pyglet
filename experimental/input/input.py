#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import sys

class InputException(Exception):
    pass

class InputDeviceExclusiveException(InputException):
    pass

if sys.platform == 'darwin':
    import osx
    get_devices = osx.get_devices
