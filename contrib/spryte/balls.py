import random
import math

from pyglet import window
from pyglet import image
from pyglet import clock
from pyglet import gl
from pyglet import resource
from pyglet.window import key

import spryte

win = window.Window(width=640, height=400,vsync=False)
fps = clock.ClockDisplay(color=(1, 1, 1, 1))

balls = spryte.SpriteBatch()
ball = resource.image('ball.png')
ball.anchor_x = 16
ball.anchor_y = 16
for i in range(200):
    spryte.Sprite(ball,
        (win.width - 64) * random.random(), (win.height - 64) * random.random(),
        batch=balls,
        dx=-50 + 100*random.random(), dy=-50 + 100*random.random())

car = resource.image('car.png')
car.anchor_x = 16
car.anchor_y = 20
car = spryte.Sprite(car, win.width/2, win.height/2)

class EffectSprite(spryte.Sprite):
    def on_animation_end(self):
        self.delete()

explosions = spryte.SpriteBatch()
explosion_images = resource.image('explosion.png')
explosion_images = image.ImageGrid(explosion_images, 2, 8)
explosion_animation = image.Animation.from_image_sequence(explosion_images,
    .001, loop=False)

keyboard = key.KeyStateHandler()
win.push_handlers(keyboard)
def animate(dt):
    # update car rotation & speed
    r = car.rotation
    r += (keyboard[key.RIGHT] - keyboard[key.LEFT]) * 200 * dt
    if r < 0: r += 360
    elif r > 360: r -= 360
    car.rotation = r
    car.speed = (keyboard[key.UP] - keyboard[key.DOWN]) * 200 * dt

    # ... and the rest
    spryte.update_kinematics(car, dt)

    # handle balls
    for i, s in enumerate(balls):
        # update positions
        s.x += s.dx * dt
        s.y += s.dy * dt

        if s.right > win.width and s.dx > 0: s.dx *= -1; s.right = win.width
        elif s.left < 0 and s.dx < 0: s.dx *= -1; s.left = 0
        if s.top > win.height and s.dy > 0: s.dy *= -1; s.top = win.height
        elif s.bottom < 0 and s.dy < 0: s.dy *= -1; s.bottom = 0

        # handle collisions
        if not s.intersects(car):
            continue

        if s.scale > 2:
            # pop!
            explosion = EffectSprite(explosion_animation, 0, 0,
                batch=explosions)
            explosion.center = s.center
            explosion.push_handlers
            s.delete()
            spryte.Sprite(ball,
                win.width * random.random(), win.height * random.random(),
                batch=balls,
                dx=-50 + 100*random.random(), dy=-50 + 100*random.random())
        else:
            s.scale += .1
            n = min(1, max(0, 2-s.scale))
            s.color = (1, 1, 1, .5+n/2)

clock.schedule(animate)

while not win.has_exit:
    clock.tick()
    win.dispatch_events()
    win.clear()

    explosions.draw()
    balls.draw()
    car.draw()

    fps.draw()
    win.flip()
win.close()

