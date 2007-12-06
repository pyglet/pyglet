
import random
import math

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
car = spryte.Sprite('car.png', layer2, win.width/2, win.height/2,
    rothandle=(16, 16))

layer3 = spryte.Layer()

keyboard = key.KeyStateHandler()
win.push_handlers(keyboard)
def animate(dt):
    # update car rotation & speed
    r = car.rotation
    r += (keyboard[key.LEFT] - keyboard[key.RIGHT]) * 5 * dt
    if r < 0: r += math.pi * 2
    elif r > math.pi * 2: r -= math.pi * 2
    car.rotation = r
    car.dy = (keyboard[key.UP] - keyboard[key.DOWN]) * 200 * dt

    # ... and the rest
    car.update_kinematics(dt)

    # handle balls
    for i, ball in enumerate(balls):
        if not ball.intersects(car): continue
        if ball.width > ball.texture.width * 2:
            # pop!
            explosion = spryte.AnimatedSprite('explosion.png', 2, 8, layer3,
                0, 0, .01)
            explosion.center = balls[i].center
            balls[i].delete()
            balls[i] = spryte.Sprite('ball.png', layer,
                win.width * random.random(), win.height * random.random(),
                dx=-50 + 100*random.random(), dy=-50 + 100*random.random())
        else:
            center = ball.center
            ball.width += 1
            ball.height += 1
            ball.center = center

clock.schedule(animate)

while not win.has_exit:
    clock.tick()
    win.dispatch_events()
    win.clear()

    layer.draw()
    layer2.draw()
    layer3.draw()

    fps.draw()
    win.flip()
win.close()
