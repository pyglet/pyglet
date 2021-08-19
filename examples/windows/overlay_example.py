"""
Demonstrates creation of a basic overlay window in pyglet
"""
from pyglet.graphics import Batch
from pyglet.window import Window
from pyglet.text import Label
from pyglet.app import run


batch = Batch()
window = Window(500, 500, style=Window.WINDOW_STYLE_OVERLAY)
label1 = Label("Test", x=100, y=250, batch=batch, font_size=72,
               color=(255, 255, 0, 255))


@window.event
def on_draw():
    window.clear()
    batch.draw()


run()
