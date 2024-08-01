#!/usr/bin/env python
"""A full-screen minute:second timer.  Leave it in charge of your conference
lighting talks.

After 5 minutes, the timer goes red.  This limit is easily adjustable by
hacking the source code.

Press spacebar to start, stop and reset the timer.
"""

import pyglet

window = pyglet.window.Window(fullscreen=True)


class Timer:
    def __init__(self):
        self.label = pyglet.text.Label('00:00', font_size=360,
                                       x=window.width//2, y=window.height//2,
                                       anchor_x='center', anchor_y='center')
        self.reset()

    def reset(self):
        self.time = 0
        self.running = False
        self.label.text = '00:00'
        self.label.color = (255, 255, 255, 255)

    def update(self, dt):
        if self.running:
            self.time += dt
            m, s = divmod(self.time, 60)
            self.label.text = f'{round(m):02}:{round(s):02}'
            if m >= 5:
                self.label.color = (180, 0, 0, 255)

        window.draw(dt=dt)


@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.SPACE:
        if timer.running:
            timer.running = False
        else:
            if timer.time > 0:
                timer.reset()
            else:
                timer.running = True
    elif symbol == pyglet.window.key.ESCAPE:
        window.close()


@window.event
def on_draw():
    window.clear()
    timer.label.draw()


timer = Timer()

# Set timer and redraw update rate to 30 FPS
pyglet.clock.schedule_interval(timer.update, 1/30.0)

# Launch the application
pyglet.app.run(None)

