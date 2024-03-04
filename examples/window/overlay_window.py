"""Demonstrates creation of a transparent overlay window in pyglet
"""

import pyglet

from pyglet.graphics import Batch
from pyglet.window import Window


batch = Batch()
window = Window(500, 500, style=Window.WINDOW_STYLE_OVERLAY)
window.set_caption("Overlay Window")

circle = pyglet.shapes.Circle(250, 250, 100, color=(255, 255, 0), batch=batch)


@window.event
def on_draw():
    window.clear()
    batch.draw()


pyglet.app.run()
