#!/usr/bin/env python

"""Print OpenAL driver information.

Options:
  -d <device>   Optionally specify device to query.
"""

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes
import optparse
import sys

from pyglet.util import asbytes
from pyglet.media.drivers import openal
from pyglet.media.drivers.openal.interface import alc


def split_nul_strings(s):
    # NUL-separated list of strings, double-NUL-terminated.
    nul = False
    i = 0
    while True:
        if s[i] == b'\x00':
            if nul:
                break
            else:
                nul = True
        else:
            nul = False
        i += 1
    s = s[:i - 1]
    return s.split(b'\x00')


if __name__ == '__main__':
    op = optparse.OptionParser()
    op.add_option('-d', '--device', dest='device',
                  help='use device DEVICE', metavar='DEVICE')
    (options, args) = op.parse_args(sys.argv[1:])

    default_device = ctypes.cast(
        alc.alcGetString(None, alc.ALC_DEFAULT_DEVICE_SPECIFIER), ctypes.c_char_p).value
    capture_default_device = ctypes.cast(
        alc.alcGetString(None, alc.ALC_CAPTURE_DEFAULT_DEVICE_SPECIFIER), ctypes.c_char_p).value

    print('Default device:         %s' % default_device)
    print('Default capture device: %s' % capture_default_device)

    if alc.alcIsExtensionPresent(None, ctypes.create_string_buffer(b'ALC_ENUMERATION_EXT')):
        devices = split_nul_strings(alc.alcGetString(None, alc.ALC_DEVICE_SPECIFIER))
        capture_devices = split_nul_strings(alc.alcGetString(None, alc.ALC_CAPTURE_DEVICE_SPECIFIER))

        print('Devices:                %s' % b', '.join(devices))
        print('Capture devices:        %s\n' % b', '.join(capture_devices))

    if options.device:
        print('Using device "%s"...' % options.device)
        driver = openal.create_audio_driver(asbytes(options.device))
    else:
        print('Using default device...')
        driver = openal.create_audio_driver()

    print('OpenAL version %d.%d' % driver.get_version())
    print('Extensions:              %s' % ', '.join(driver.get_extensions()))
