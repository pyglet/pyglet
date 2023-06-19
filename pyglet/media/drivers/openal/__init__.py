from .adaptation import OpenALDriver

import pyglet

_debug = pyglet.options['debug_media']
_debug_buffers = pyglet.options.get('debug_media_buffers', False)


def create_audio_driver(device_name=None):
    _driver = OpenALDriver(device_name)
    if _debug:
        print('OpenAL', _driver.get_version())
    return _driver
