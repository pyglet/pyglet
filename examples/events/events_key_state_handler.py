"""
This example shows the KeyStateHandler polling approach when it comes to catching keyboard events.
"""

import pyglet

window = pyglet.window.Window()
label = pyglet.text.Label("Press either A, Enter, or Left Arrow", 50, 50, font_size=36)


key_handler = pyglet.window.key.KeyStateHandler()
window.push_handlers(key_handler)


def update(dt):

    if key_handler[pyglet.window.key.A]:
        label.text = 'The "A" key was pressed'
    elif key_handler[pyglet.window.key.LEFT]:
        label.text = 'The "Left Arrow" key was pressed.'
    elif key_handler[pyglet.window.key.ENTER]:
        label.text = 'The "Enter" key was pressed.'
    else:
        label.text = "Press either A, Enter, or Left Arrow"


@window.event
def on_draw():
    window.clear()
    label.draw()


pyglet.clock.schedule_interval(update, 1/60)


if __name__ == '__main__':
    pyglet.app.run()
