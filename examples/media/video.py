#!/usr/bin/env python
"""Simple example of video playback.

Usage::

    video.py <filename>

See the Programming Guide for a partial list of supported video formats.
"""


__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import sys
import pyglet

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)

source = pyglet.media.load(sys.argv[1])
fmt = source.video_format
if not fmt:
    print('No video track in this source.')
    sys.exit(1)

player = pyglet.media.Player()
player.queue(source)
player.play()

window = pyglet.window.Window(width=fmt.width, height=fmt.height)


@window.event
def on_draw():
    player.texture.blit(0, 0)


pyglet.app.run()
