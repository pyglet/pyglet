# Lots Of Sprites

'''
Results:
      AMD64/mesa   AMD64/nvidia   MacBook Pro
500:  77.0         63.5           46.7
1000: 38.3         32.4           23.5
2000: 18.5         16.4           11.8
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
ball = Image2d.load(os.path.join(dirname, 'ball-small.png'))

class BouncySprite(Sprite):
    def update(self):
        # move, check bounds
        p = self.properties
        self.x += p['dx']; self.y += p['dy']
        if self.left < 0: self.left = 0; p['dx'] = -p['dx']
        elif self.right > w.width: self.right = w.width; p['dx'] = -p['dx']
        if self.bottom < 0: self.bottom = 0; p['dy'] = -p['dy']
        elif self.top > w.height: self.top = w.height; p['dy'] = -p['dy']

sprites = []
for i in range(int(sys.argv[1])):
    x = random.randint(0, w.width - ball.width)
    y = random.randint(0, w.height - ball.height)
    p = {'dx': random.randint(-10, 10), 'dy': random.randint(-10, 10)}
    sprites.append(BouncySprite(x, y, 8, 8, ball, properties=p))

scene = Scene(sprites=sprites)
view = FlatView.from_window(scene, w)
view.fx, view.fy = w.width/2, w.height/2

clock = Clock(fps_limit=1000)
while 1:
    if w.has_exit:
        print 'FPS:', clock.get_fps()
        break
    clock.tick()
    w.dispatch_events()
    for s in sprites: s.update()
    view.clear()
    view.draw()
    w.flip()
w.close()


