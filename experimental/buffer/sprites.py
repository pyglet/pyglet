#!/usr/bin/python
# $Id:$

import random
import sys

from pyglet.gl import *
from pyglet import clock
from pyglet import image
from pyglet import window
from pyglet.graphics import vertexdomain


if len(sys.argv) > 1:
    SPRITES = int(sys.argv[1])
else:
    SPRITES = 2000
SPRITE_IMAGE = 'examples/noisy/ball.png'

# How many sprites to move each frame.  e.g.
#   0 -- all sprites are static
#   1 -- all sprites move every frame (all are dynamic)
#   2 -- only 2 sprites move every frame
#  50 -- 50 sprites move every frame
SPRITE_UPDATE_N = 1

win = window.Window(vsync=False)

class Sprite(object):
    width = 32
    height = 32
    
    def __init__(self, domain):
        self.primitive = domain.create(4)
        self.x = win.width * random.random()
        self.y = win.height * random.random()
        self.dx = (random.random() - .5) * 200
        self.dy = (random.random() - .5) * 200

        self.primitive.tex_coords = [
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
        
        x = self.x
        y = self.y
        rx = self.width // 2
        ry = self.height // 2
        self.primitive.vertices = [
            x - rx, y - ry,
            x + rx, y - ry,
            x + rx, y + rx,
            x - rx, y + rx
        ]

def draw_sprites(domain, texture):
    glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT)

    glEnable(GL_BLEND)
    glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(.2, .2, .2, .2)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture.id)
    domain.draw(GL_QUADS)

    glPopAttrib()

if __name__ == '__main__':
    domain = vertexdomain.create_domain('v2f/static', 't2f/static')

    sprites = [Sprite(domain) for i in range(SPRITES)]
    fps = clock.ClockDisplay(color=(1, 1, 1, 1))

    texture = image.load(SPRITE_IMAGE).texture

    if SPRITE_UPDATE_N:
        update_n = 0
    
    while not win.has_exit:
        dt = clock.tick()
        if dt == 0:
            dt = 0.01

        win.dispatch_events()

        if SPRITE_UPDATE_N > 1:
            # Update small number of sprites
            for sprite in sprites[update_n:update_n+SPRITE_UPDATE_N]:
                sprite.update(dt)
            update_n = (update_n + SPRITE_UPDATE_N) % len(sprites)
        elif SPRITE_UPDATE_N:
            # Update all sprites
            for sprite in sprites:
                sprite.update(dt)
        # Otherwise, update no sprites (static)

        win.clear()
        draw_sprites(domain, texture)
        fps.draw()
        win.flip()
