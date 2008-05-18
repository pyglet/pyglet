#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import pyglet
pyglet.options['audio'] = ('silent',)

import pulse
pyglet.options['audio'] = ('pulse',)
pulse.driver_init()
pyglet.media.listener = pulse.driver_listener
pyglet.media.audio_player_class = pulse.driver_audio_player_class

if __name__ == '__main__':
    import runpy
    import sys
    sys.modules['test_pulse'] = sys.modules['__main__']

    del sys.argv[0]
    __file__ = sys.argv[0]
    runpy.run_module(sys.argv[0], run_name='__main__', alter_sys=True)
