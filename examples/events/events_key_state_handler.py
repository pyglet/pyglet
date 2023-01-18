#!/usr/bin/env python
"""
This example shows the KeyStateHandler polling approach when it comes to catching keyboard events.
"""

import pyglet

window = pyglet.window.Window()

key_handler = pyglet.window.key.KeyStateHandler()
window.push_handlers(key_handler)


def update(dt):

    if key_handler[pyglet.window.key.A]:
        print('The "A" key was pressed')
    elif key_handler[pyglet.window.key.LEFT]:
        print('The left arrow key was pressed.')
    elif key_handler[pyglet.window.key.ENTER]:
        print('The enter key was pressed.')


@window.event
def on_draw():
    window.clear()


pyglet.clock.schedule_interval(update, 1/60)


if __name__ == '__main__':
    pyglet.app.run()
