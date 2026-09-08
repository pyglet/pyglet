from .adaptation import PipeWireDriver

import pyglet

_debug = pyglet.options.debug_media


def create_audio_driver():
    driver = PipeWireDriver()
    driver.connect()
    if _debug:
        driver.dump_debug_info()
    return driver