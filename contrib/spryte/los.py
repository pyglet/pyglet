# Lots Of Sprites

'''
Results (us per sprite per frame):
sprites  AMD64/mesa   AMD64/nv6.6k   MacBook Pro   AMD/nv7.8k
2000     28.3         29.3          20.6          22.0

after __slots__ removal
sprites  AMD64/mesa   AMD64/nv6.6k   MacBook Pro   AMD/nv7.8k
2000
'''

import os
import sys
import random

from pyglet import options
options['debug_gl'] = False

from pyglet.window import Window
from pyglet import clock
from spryte import *
from pyglet.gl import *

w = Window(600, 600, vsync=False)

class BouncySprite(Sprite):
    def update(self):
        # move, check bounds
        self.pos = (self.x + self.dx, self.y + self.dy)
        if self.x < 0: self.x = 0; self.dx = -self.dx
        elif self.right > 600: self.right = 600; self.dx = -self.dx
        if self.y < 0: self.y = 0; self.dy = -self.dy
        elif self.top > 600: self.top = 600; self.dy = -self.dy

layer = Layer()

sprites = []
numsprites = int(sys.argv[1])
for i in range(numsprites):
    s = BouncySprite('examples/noisy/ball.png', layer, 0, 0,
        dx=random.randint(-10, 10), dy=random.randint(-10, 10))
    s.x = random.randint(0, w.width - s.width)
    s.y = random.randint(0, w.height - s.height)
    sprites.append(s)

t = 0
numframes = 0
while 1:
    if w.has_exit:
        print 'FPS:', clock.get_fps()
        print 'us per sprite:', float(t) / (numsprites * numframes) * 1000000

        break
    t += clock.tick()
    w.dispatch_events()
    for s in sprites: s.update()
    w.clear()
    layer.draw()
    w.flip()
    numframes += 1
w.close()

