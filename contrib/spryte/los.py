# Lots Of Sprites

'''
Results for 2000 sprites:

platform                                      us per sprite per frame
---------------------------------------------------------------------
Intel C2Quad Q6600 (2.4GHz), GeForce 7800     18.2478245656
Intel C2Duo T7500 (2.2GHz), GeForce 8400M GS  19.115903827
AMD 64 3500+ (1.8GHz), GeForce 7800           23.6
EEE PC                                        73.5
'''

import os
import sys
import random

from pyglet import options
options['debug_gl'] = False

from pyglet import window
from pyglet import clock
from pyglet import resource
import spryte
from pyglet.gl import *

w = window.Window(600, 600, vsync=False)

class BouncySprite(spryte.Sprite):
    def update(self):
        # move, check bounds
        self.position = (self.x + self.dx, self.y + self.dy)
        if self.x < 0: self.x = 0; self.dx = -self.dx
        elif self.right > 600: self.right = 600; self.dx = -self.dx
        if self.y < 0: self.y = 0; self.dy = -self.dy
        elif self.top > 600: self.top = 600; self.dy = -self.dy

batch = spryte.SpriteBatch()

numsprites = int(sys.argv[1])
resource.path.append('examples/noisy')
ball = resource.image('ball.png')
for i in range(numsprites):
    x = random.randint(0, w.width - ball.width)
    y = random.randint(0, w.height - ball.height)
    BouncySprite(ball, x, y, batch=batch,
        dx=random.randint(-10, 10), dy=random.randint(-10, 10))

t = 0
numframes = 0
while 1:
    if w.has_exit:
        print 'FPS:', clock.get_fps()
        print 'us per sprite:', float(t) / (numsprites * numframes) * 1000000

        break
    t += clock.tick()
    w.dispatch_events()
    for s in batch: s.update()
    w.clear()
    batch.draw()
    w.flip()
    numframes += 1
w.close()

