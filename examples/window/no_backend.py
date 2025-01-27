"""A simple example with just Window creation.

In some cases a user may not want to utilize any backend of pyglet, but just events and windowing.
"""

import pyglet
pyglet.options.backend = None

window = pyglet.window.Window(500, 500)

pyglet.app.run()