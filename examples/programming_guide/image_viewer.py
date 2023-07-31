#!/usr/bin/env python
"""
"""

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pyglet

window = pyglet.window.Window()
image = pyglet.resource.image('kitten.jpg')


@window.event
def on_draw():
    window.clear()
    image.blit(0, 0)


# Redraw at 60 FPS
pyglet.clock.schedule_interval(window.draw, 1 / 60)

# Run the application
pyglet.app.run()
