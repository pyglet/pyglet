#!/usr/bin/env python
"""Prints all window events to stdout.
"""

import pyglet

window = pyglet.window.Window(resizable=True)


@window.event
def on_draw():
    window.clear()


# A logger class, which prints events to stdout or to a file:
win_event_logger = pyglet.window.event.WindowEventLogger()
window.push_handlers(win_event_logger)

pyglet.app.run()
