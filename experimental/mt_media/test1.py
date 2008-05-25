#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import setup_path

import pyglet
import mt_media

import sys
source = mt_media.load(sys.argv[1])

player = mt_media.Player()
player.queue(source)
player.play()
player.on_eos = lambda: pyglet.app.exit()

pyglet.app.run()
