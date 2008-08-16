#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import setup_path

import sys

import pyglet
import mt_media
import mt_procedural as procedural

player = mt_media.Player()
player.queue(procedural.Sine(0.5, 300))
player.queue(procedural.Sine(0.5, 330))
player.queue(procedural.Sine(0.5, 390))
player.queue(procedural.Sine(0.5, 300, sample_rate=44100))
player.queue(procedural.Sine(0.5, 330, sample_rate=44100))
player.queue(procedural.Sine(0.5, 390, sample_rate=44100))
player.play()
player.on_eos = lambda: sys.stdout.write('eos\n')
player.on_player_eos = lambda: pyglet.app.exit()

pyglet.app.run()
