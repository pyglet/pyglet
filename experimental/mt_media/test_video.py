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

window = pyglet.window.Window(width=source.video_format.width,
                              height=source.video_format.height)

@window.event
def on_draw():
    texture = player.get_texture()
    if texture:
        texture.get_transform(flip_y=True).blit(0, window.height)

player = mt_media.Player()
player.queue(source)
player.play()
player.on_eos = lambda: pyglet.app.exit()

pyglet.app.run()
