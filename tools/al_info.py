#!/usr/bin/env python

'''Print OpenAL driver information.

Options:
  -d <device>   Optionally specify device to query.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes
import optparse
import sys

from pyglet.media.drivers import openal
from pyglet.media.drivers.openal import lib_openal as al
from pyglet.media.drivers.openal import lib_alc as alc

def split_nul_strings(s):
    # NUL-separated list of strings, double-NUL-terminated.
    nul = False
    i = 0
    while True:
        if s[i] == '\0':
            if nul:
                break
            else:
                nul = True
        else:
            nul = False
        i += 1
    s = s[:i - 1]
    return s.split('\0')

if __name__ == '__main__':
    op = optparse.OptionParser()
    op.add_option('-d', '--device', dest='device',
                  help='use device DEVICE', metavar='DEVICE')
    (options, args) = op.parse_args(sys.argv[1:])

    default_device = ctypes.cast(
        alc.alcGetString(None, alc.ALC_DEFAULT_DEVICE_SPECIFIER),
        ctypes.c_char_p).value
    capture_default_device = ctypes.cast(
        alc.alcGetString(None, alc.ALC_CAPTURE_DEFAULT_DEVICE_SPECIFIER),
        ctypes.c_char_p).value

    print 'Default device:         %s' % default_device
    print 'Default capture device: %s' % capture_default_device

    if alc.alcIsExtensionPresent(None, 'ALC_ENUMERATION_EXT'):
        # Hmm, actually not allowed to pass NULL to alcIsExtension present..
        # how is this supposed to work?
        devices = split_nul_strings(
            alc.alcGetString(None, alc.ALC_DEVICE_SPECIFIER))
        capture_devices = split_nul_strings(
            alc.alcGetString(None, alc.ALC_CAPTURE_DEVICE_SPECIFIER))

    print 'Devices:                %s' % ', '.join(devices)
    print 'Capture devices:        %s' % ', '.join(capture_devices)
    print


    if options.device:
        print 'Using device "%s"...' % options.device
        openal.driver_init(options.device)
    else:
        print 'Using default device...'
        openal.driver_init()

    print 'OpenAL version %d.%d' % openal.get_version()
    print 'Extensions:              %s' % ', '.join(openal.get_extensions())
