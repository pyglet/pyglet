# Lots Of Sprites

'''
Results for 2000 sprites:

platform                                      us per sprite per frame
---------------------------------------------------------------------
Intel C2Quad Q6600 (2.4GHz), GeForce 7800     18.2478245656
Intel C2Duo T7500 (2.2GHz), GeForce 8400M GS  19.115903827
AMD 64 3500+ (1.8GHz), GeForce 7800           23.6
EEE PC                                        75.0
'''

import os
import sys
import random
import time

from pyglet import options
options['debug_gl'] = False

import pyglet
import spryte

w = pyglet.window.Window(600, 600, vsync=False)

class BouncySprite(spryte.Sprite):
    def update(self):
        # micro-optimisation: only access properties once
        x, y = self.x, self.y

        # move
        self.position = (x + self.dx, y + self.dy)

        # check bounds
        if x < 0: self.x = 0; self.dx = -self.dx
        elif self.right > 600: self.dx = -self.dx; self.right = 600
        if y < 0: self.y = 0; self.dy = -self.dy
        elif self.top > 600: self.dy = -self.dy; self.top = 600

batch = spryte.SpriteBatch()

numsprites = int(sys.argv[1])
pyglet.resource.path.append('examples/noisy')
ball = pyglet.resource.image('ball.png')
for i in range(numsprites):
    x = random.randint(0, w.width - ball.width)
    y = random.randint(0, w.height - ball.height)
    BouncySprite(ball, x, y, batch=batch,
        dx=random.randint(-10, 10), dy=random.randint(-10, 10))

def update(dt):
    for s in batch: s.update()
pyglet.clock.schedule(update)

numframes = 0
sum_numframes = 0
best_fps = 0
def update_stats(dt):
    global numframes, sum_numframes, best_fps
    fps = numframes / dt
    best_fps = max(best_fps, fps)
    sum_numframes += numframes
    numframes = 0
pyglet.clock.schedule_interval(update_stats, 0.5)

@w.event
def on_draw():
    global numframes
    numframes += 1

    w.clear()
    batch.draw()

t = time.time()
pyglet.app.run()

print 'best FPS:', best_fps
print 'best us per sprite:', (1. / best_fps) * 1000000 / numsprites
print 'avg  us per sprite:', float(time.time()-t) / (numsprites * sum_numframes) * 1000000

