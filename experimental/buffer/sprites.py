#!/usr/bin/python
# $Id:$

import random
import sys

from pyglet.gl import *
from pyglet import clock
from pyglet import image
from pyglet import window

import buffer

if len(sys.argv) > 1:
    SPRITES = int(sys.argv[1])
else:
    SPRITES = 1000
SPRITE_IMAGE = 'examples/noisy/ball.png'
SPRITE_UPDATE_N = 1

INTERLEAVED = False

win = window.Window(vsync=False)

class Sprite(object):
    width = 32
    height = 32
    
    def __init__(self, allocator):
        self.region = allocator.alloc(4)
        self.x = win.width * random.random()
        self.y = win.height * random.random()
        self.dx = (random.random() - .5) * 200
        self.dy = (random.random() - .5) * 200

        self.region.tex_coords = [
            0, 0,
            1, 0, 
            1, 1,
            0, 1
        ]

        self.update(0)

    def update(self, dt):
        self.x += self.dx * dt
        self.y += self.dy * dt

        if not 0 < self.x < win.width:
            self.dx = -self.dx
            self.x += self.dx * dt * 2
        if not 0  < self.y < win.height:
            self.dy = -self.dy
            self.y += self.dy * dt * 2
        
        x = int(self.x)
        y = int(self.y)
        rx = self.width // 2
        ry = self.height // 2
        self.region.vertices = [
            x - rx, y - ry,
            x + rx, y - ry,
            x + rx, y + rx,
            x - rx, y + rx
        ]

def draw_sprites(allocator, texture):
    glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture.id)
    allocator.draw(GL_QUADS)

    glPopAttrib()

if __name__ == '__main__':
    if INTERLEAVED:
        allocator = buffer.Allocator(('V2F', 'T2F'), ())
    else:
        allocator = buffer.Allocator((), ('V2F', 'T2F'))

    sprites = [Sprite(allocator) for i in range(SPRITES)]
    fps = clock.ClockDisplay(color=(1, 1, 1, 1))

    texture = image.load(SPRITE_IMAGE).texture

    if SPRITE_UPDATE_N:
        update_n = 0
    
    while not win.has_exit:
        dt = clock.tick()

        win.dispatch_events()

        if SPRITE_UPDATE_N > 1:
            # Update every n'th sprite
            for sprite in sprites[update_n::SPRITE_UPDATE_N]:
                sprite.update(dt)
            update_n = (update_n + 1) % SPRITE_UPDATE_N
        elif SPRITE_UPDATE_N:
            # Update all sprites
            for sprite in sprites:
                sprite.update(dt)
        # Otherwise, update no sprites (static)

        win.clear()
        draw_sprites(allocator, texture)
        fps.draw()
        win.flip()
