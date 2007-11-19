

# Number    MacBook
# 500       59.1715965271
# 1000      29.5857982635
# 2000      19.8412704468


import os
import sys
import random

import pygame
import pygame.time
from pygame.locals import *


pygame.init()
win = pygame.display.set_mode((600, 600))
ww, wh = win.get_size()

img = pygame.image.load('examples/noisy/ball.png')

class BouncySprite(pygame.sprite.Sprite):
    def update(self, dt):
        # move, check bounds
        p = self.properties
        self.rect.x += p['dx']; self.rect.y += p['dy']
        if self.rect.left < 0: self.rect.left = 0; p['dx'] = -p['dx']
        elif self.rect.right > 600: self.rect.right = 600; p['dx'] = -p['dx']
        if self.rect.bottom < 0: self.rect.bottom = 0; p['dy'] = -p['dy']
        elif self.rect.top > 600: self.rect.top = 600; p['dy'] = -p['dy']

group = pygame.sprite.Group()
numsprites = int(sys.argv[1])
iw, ih = img.get_size()
for i in range(numsprites):
    x = random.randint(0, ww - iw)
    y = random.randint(0, wh - ih)
    s = BouncySprite(group)
    s.image = img
    s.rect = pygame.Rect(x, y, iw, ih)
    s.properties = {'dx': random.randint(-10, 10),
        'dy': random.randint(-10, 10)}

clock = pygame.time.Clock()
t = 0
numframes = 0
while 1:
    dt = clock.tick()
    for event in pygame.event.get():
        if event.type in (QUIT, KEYDOWN, MOUSEBUTTONDOWN):
            print 'FPS:', clock.get_fps()
            print 'us per sprite:', float(t) / (numsprites * numframes) * 1000
            sys.exit(0)
    group.update(dt)
    win.fill((0,0,0))
    group.draw(win)
    pygame.display.flip()
    t += dt
    numframes += 1

