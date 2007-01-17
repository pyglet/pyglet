# Lots Of Sprites

'''
Results:
      AMD64/mesa   AMD64/nv68k   MacBook Pro   AMD/nv78k
500:  77.0         63.5          62.4          90.2
1000: 38.3         32.4          31.2          45.5
2000: 18.5         16.4          15.5          22.5
---------------------------------------------------------
us                                             22.0
(us per sprite)
'''

import os
import sys
import random

from pyglet.window import Window
from pyglet.clock import Clock
from pyglet.scene2d import *
from pyglet.GL.VERSION_1_1 import *

w = Window(600, 600, vsync=False)

dirname = os.path.dirname(__file__)
img = Image2d.load(os.path.join(dirname, 'car.png'))

class BouncySprite(Sprite):
    __slots__ = Sprite.__slots__
    def update(self):
        # move, check bounds
        p = self.properties
        self.x += p['dx']; self.y += p['dy']
        if self.x < 0: self.x = 0; p['dx'] = -p['dx']
        elif self.right > 600: self.right = 600; p['dx'] = -p['dx']
        if self.y < 0: self.y = 0; p['dy'] = -p['dy']
        elif self.top > 600: self.top = 600; p['dy'] = -p['dy']

sprites = []
numsprites = int(sys.argv[1])
for i in range(numsprites):
    x = random.randint(0, w.width-img.width)
    y = random.randint(0, w.height-img.height)
    p = {'dx': random.randint(-10, 10), 'dy': random.randint(-10, 10)}
    sprites.append(BouncySprite(x, y, img.width, img.height, img,
        properties=p))

scene = Scene(sprites=sprites)
view = FlatView.from_window(scene, w)
view.fx, view.fy = w.width/2, w.height/2

clock = Clock()
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
    view.clear()
    view.draw()
    w.flip()
    numframes += 1
w.close()


