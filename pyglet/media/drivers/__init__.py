"""Drivers for playing back media."""

import atexit

import pyglet

_debug = pyglet.options['debug_media']


def get_audio_driver():
    """Get the preferred audio driver for the current platform.

    Currently pyglet supports DirectSound, PulseAudio and OpenAL drivers. If
    the platform supports more than one of those audio drivers, the
    application can give its preference with :data:`pyglet.options` ``audio``
    keyword. See the Programming guide, section
    :doc:`/programming_guide/media`.

    Returns:
        AbstractAudioDriver : The concrete implementation of the preferred 
        audio driver for this platform.
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
            elif driver_name == 'xaudio2':
                from pyglet.libs.win32.constants import WINDOWS_8_OR_GREATER
                if WINDOWS_8_OR_GREATER:
                    from . import xaudio2
                    _audio_driver = xaudio2.create_audio_driver()
                    break
            elif driver_name == 'directsound':
                from . import directsound
                _audio_driver = directsound.create_audio_driver()
                break
            elif driver_name == 'openal':
                from . import openal
                _audio_driver = openal.create_audio_driver()
                break
            elif driver_name == 'silent':
                from . import silent
                _audio_driver = silent.create_audio_driver()
                break
        except Exception:
            if _debug:
                print(f'Error importing driver {driver_name}:')
                import traceback
                traceback.print_exc()
    else:
        from . import silent
        _audio_driver = silent.create_audio_driver()

    return _audio_driver


def _delete_audio_driver():
    # First cleanup any remaining spontaneous Player
    from .. import Source
    for p in Source._players:
        # Remove the reference to _on_player_eos which had a closure on the player
        p.on_player_eos = None
        del p

    del Source._players
    global _audio_driver
    _audio_driver = None


_audio_driver = None
atexit.register(_delete_audio_driver)
