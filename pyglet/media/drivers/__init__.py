"""Drivers for playing back media."""

import sys
import atexit

import pyglet

_debug = pyglet.options['debug_media']
_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


if _is_pyglet_doc_run:
    from . import silent
    _audio_driver = silent.create_audio_driver()

else:

    for driver_name in pyglet.options['audio']:
        try:
            if driver_name == 'pulse':
                from . import pulse

                _audio_driver = pulse.create_audio_driver()
                break
            elif driver_name == 'xaudio2':
                if pyglet.compat_platform in ('win32', 'cygwin'):
                    from pyglet.libs.win32.constants import WINDOWS_8_OR_GREATER

                    if WINDOWS_8_OR_GREATER:
                        from . import xaudio2

                        _audio_driver = xaudio2.create_audio_driver()
                        break
            elif driver_name == 'directsound':
                if pyglet.compat_platform in ('win32', 'cygwin'):
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


def get_audio_driver():
    """Get the preferred audio driver for the current platform.

    See :data:`pyglet.options` ``audio``, and the Programming guide,
    section :doc:`/programming_guide/media` for more information on
    setting the preferred driver.

    Returns:
        AbstractAudioDriver : The concrete implementation of the preferred
                              audio driver for this platform.
    """
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


atexit.register(_delete_audio_driver)
