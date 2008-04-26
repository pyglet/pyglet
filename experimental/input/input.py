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
elif sys.platform == 'linux2':
    import linux
    get_devices = linux.get_devices
elif sys.platform in ('win32', 'cygwin'):
    import dinput
    get_devices = dinput.get_devices
