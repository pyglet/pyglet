
import random

from pyglet import window, clock, gl, event
from pyglet.window import key

import spryte

win = window.Window(vsync=False)
fps = clock.ClockDisplay(color=(1, 1, 1, 1))

layer = spryte.Layer()
balls = []
for i in range(200):
    balls.append(spryte.Sprite('ball.png', layer,
        (win.width - 64) * random.random(), (win.height - 64) * random.random(),
        dx=-50 + 100*random.random(), dy=-50 + 100*random.random(),
        dead=False))

def animate(dt):
    for ball in balls:
        ball.x += ball.dx * dt
        ball.y += ball.dy * dt

        if ball.x + ball.width > win.width or ball.x < 0: ball.dx *= -1
        if ball.y + ball.height > win.height or ball.y < 0: ball.dy *= -1
clock.schedule(animate)

layer2 = spryte.Layer()
car = spryte.Sprite('car.png', layer2, win.width/2, win.height/2)

keyboard = key.KeyStateHandler()
win.push_handlers(keyboard)
def animate(dt):
    car.x += (keyboard[key.RIGHT] - keyboard[key.LEFT]) * 200 * dt
    car.y += (keyboard[key.UP] - keyboard[key.DOWN]) * 200 * dt
    for i, ball in enumerate(balls):
        if ball.intersects(car):
            if ball.width > ball.image.width * 2:
                # pop!
                balls[i].delete()
                balls[i] = spryte.Sprite('ball.png', layer,
                    win.width * random.random(), win.height * random.random(),
                    dx=-50 + 100*random.random(), dy=-50 + 100*random.random())
            else:
                ball.width += 1
                ball.height += 1

clock.schedule(animate)

while not win.has_exit:
    clock.tick()
    win.dispatch_events()
    win.clear()

    gl.glPushAttrib(gl.GL_ENABLE_BIT)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    layer.draw()
    layer2.draw()
    gl.glPopAttrib()

    fps.draw()
    win.flip()

