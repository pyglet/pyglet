"""Drivers for playing back media."""
from __future__ import print_function
from __future__ import absolute_import
from builtins import str

import atexit

import pyglet

_debug = pyglet.options['debug_media']


def get_audio_driver():
    """Get the preferred audio driver for the current platform. 

    Currently pyglet supports DirectSound, PulseAudio and OpenAL drivers. If
    the platform supports more than one of those audio drivers, the
    application can give its preference with :data:`pyglet.options` ``audio``
    keyword. See the Programming guide, section
    :doc:`/programming_guide/media`

    :rtype: pyglet.media.drivers.base.AbstractAudioDriver
    :return: The concrete implementation of the preferred audio driver for
        this platform.
    """
    global _audio_driver

    if _audio_driver:
        return _audio_driver

    _audio_driver = None

    for driver_name in pyglet.options['audio']:
        try:
            if driver_name == 'pulse':
                from . import pulse
                _audio_driver = pulse.create_audio_driver()
                break
            elif driver_name == 'openal':
                from . import openal
                _audio_driver = openal.create_audio_driver()
                break
            elif driver_name == 'directsound':
                from . import directsound
                _audio_driver = directsound.create_audio_driver()
                break
            elif driver_name == 'silent':
                _audio_driver = None
                break
        except Exception as exp:
            if _debug:
                print('Error importing driver %s:' % driver_name)
                import traceback
                traceback.print_exc()
    return _audio_driver


def _delete_audio_driver():
    global _audio_driver
    _audio_driver = None

_audio_driver = None
atexit.register(_delete_audio_driver)
