import pyglet

from pyglet.window import key

window = pyglet.window.Window(vsync=False)
fps = pyglet.window.FPSDisplay(window=window)
batch = pyglet.graphics.Batch()
label = pyglet.text.Label("Press a number from 1-0 (or +/-) to change the FPS. (number * 10)", x=10, y=50, batch=batch)

circle = pyglet.shapes.Circle(200, 200, 25, color=(200, 60, 130), batch=batch)
MOVEMENT_SPEED = 600
REDRAW_RATE = 60


@window.event
def on_key_press(keycode, mod):
    global REDRAW_RATE, fps
    new_redraw_rate = REDRAW_RATE

    rates = {key._1: 10, key._2: 20, key._3: 30, key._4: 40, key._5: 50,
             key._6: 60, key._7: 70, key._8: 80, key._9: 90, key._0: 100}

    if redraw_rate := rates.get(keycode):
        new_redraw_rate = redraw_rate
    elif keycode in (key.PLUS, key.EQUAL):
        new_redraw_rate = REDRAW_RATE + 10
    elif keycode == key.MINUS:
        new_redraw_rate = REDRAW_RATE - 10

    if new_redraw_rate != REDRAW_RATE:
        REDRAW_RATE = max(new_redraw_rate, 10)
        pyglet.clock.unschedule(window.draw)
        pyglet.clock.schedule_interval(window.draw, 1/REDRAW_RATE)
        fps = pyglet.window.FPSDisplay(window=window)


@window.event
def on_refresh(dt):
    global MOVEMENT_SPEED

    if circle.x > window.width:
        MOVEMENT_SPEED = -abs(MOVEMENT_SPEED)
    elif circle.x < 0:
        MOVEMENT_SPEED = abs(MOVEMENT_SPEED)

    circle.x += MOVEMENT_SPEED * dt

    window.clear()
    batch.draw()
    fps.draw()


pyglet.clock.schedule_interval(window.draw, 1/60)
pyglet.app.run(None)
