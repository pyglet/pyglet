"""A simple demonstration of the HTMLLabel class, as it might be used on a
help or introductory screen.
"""

import os
import pyglet

html = """
<h1>HTML labels in pyglet</h1>

<p align="center"><img src="pyglet.png" /></p>

<p>HTML labels are a simple way to add formatted text to your application.
Different <font face="Helvetica,Arial" size=+2>fonts</font>, <em>styles</em>,
<u>underlines</u>, and <font color=maroon>colours</font> are supported.

<p>This window has been made resizable; text will reflow to fit the new size.
"""

window = pyglet.window.Window(resizable=True)
location = pyglet.resource.FileLocation(os.path.dirname(__file__))
label = pyglet.text.HTMLLabel(html, location=location,
                              width=window.width,
                              multiline=True, anchor_y='center')


@window.event
def on_resize(width, height):
    # Wrap text to the width of the window
    label.width = window.width

    # Keep text vertically centered in the window
    label.y = window.height // 2


@window.event
def on_draw():
    window.clear()
    label.draw()


pyglet.gl.glClearColor(1, 1, 1, 1)
pyglet.app.run()
