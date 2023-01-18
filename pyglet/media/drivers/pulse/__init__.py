from .adaptation import PulseAudioDriver

import pyglet

_debug = pyglet.options['debug_media']


def create_audio_driver():
    driver = PulseAudioDriver()
    driver.connect()
    if _debug:
        driver.dump_debug_info()
    return driver
