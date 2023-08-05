import pyglet

from pyglet.window import key

window = pyglet.window.Window(vsync=False)
fps = pyglet.window.FPSDisplay(window=window)
batch = pyglet.graphics.Batch()
label = pyglet.text.Label("Press a number from 1-0 to change redraw rate * 10", x=10, y=50, batch=batch)

circle = pyglet.shapes.Circle(200, 200, 25, color=(200, 60, 130), batch=batch)
MOVEMENT_SPEED = 600


@window.event
def on_key_press(keycode, mod):
    rates = {key._1: 1/10, key._2: 1/20, key._3: 1/30, key._4: 1/40, key._5: 1/50,
             key._6: 1/60, key._7: 1/70, key._8: 1/80, key._9: 1/90, key._0: 1/100}

    redraw_rate = rates.get(keycode)

    if redraw_rate:
        pyglet.clock.unschedule(window.draw)
        pyglet.clock.schedule_interval(window.draw, redraw_rate)
        fps._delta_times.clear()


@window.event
def on_refresh(dt):
    global MOVEMENT_SPEED

    window.clear()

    if circle.x > window.width or circle.x < 0:
        MOVEMENT_SPEED = -MOVEMENT_SPEED

    circle.x += MOVEMENT_SPEED * dt

    batch.draw()
    fps.draw()


# Set the initial frame rate to 60 FPS
pyglet.clock.schedule_interval(window.draw, 1/60)

# Start the application
pyglet.app.run()
