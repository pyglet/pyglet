#!/usr/bin/env python
import os
import sys
import pyglet

"""Minimal example of 3 frame animation using a PNG sprite sheet and Sprite class

Move with arrow keys.

Meant as a starting point, many things can be improved. Tried hard to keep the
example short (less than 100 lines)."""


class AnimatedSprite:
    def __init__(self, filename, rows, columns, scale=1, duration=0.2):
        self.rows, self.columns = rows, columns
        self.row, self.column, self.direction = 0, 0, 1  # Current, for animation
        self.paused, self.counter, self.duration = True, 0.0, duration

        self.sprite_sheet = pyglet.image.load(filename)
        self.image_grid = pyglet.image.ImageGrid(self.sprite_sheet, rows=4, columns=3)
        self.texture_grid = pyglet.image.TextureGrid(self.image_grid)
        self.sprite = pyglet.sprite.Sprite(img=self.texture_grid[0, 0])
        self.sprite.scale = scale

    def update_sprite_region(self):
        self.sprite.image = self.texture_grid[self.row, self.column]

    def next_frame(self):
        if self.column == 0:
            self.direction = 1
        if self.column == self.columns - 1:
            self.direction = -1
        self.column += self.direction
        self.update_sprite_region()

    def draw(self):
        self.sprite.draw()

    def update(self, dt):
        if self.paused:
            return
        self.counter += dt
        if self.counter >= self.duration:
            self.counter -= self.duration
            self.next_frame()


pyglet.image.Texture.default_mag_filter = pyglet.gl.GL_NEAREST
pyglet.image.Texture.default_min_filter = pyglet.gl.GL_NEAREST
sprite = AnimatedSprite(os.path.dirname(__file__) + "character.png", 4, 3, 10)
window = pyglet.window.Window(width=1280, height=720, resizable=True)
pyglet.gl.glClearColor(0.5, 0.5, 0.5, 1.0)
keys = {}


@window.event
def on_draw():
    window.clear()
    sprite.draw()


@window.event
def on_key_press(symbol, modifiers):
    keys[symbol] = True


@window.event
def on_key_release(symbol, modifiers):
    keys[symbol] = False


def update(dt):
    moving = True
    speed = 160
    if keys.get(pyglet.window.key.UP, False):
        sprite.row = 2
        sprite.sprite.y += dt * speed
    elif keys.get(pyglet.window.key.DOWN, False):
        sprite.row = 3
        sprite.sprite.y -= dt * speed
    elif keys.get(pyglet.window.key.LEFT, False):
        sprite.row = 1
        sprite.sprite.x -= dt * speed
    elif keys.get(pyglet.window.key.RIGHT, False):
        sprite.row = 0
        sprite.sprite.x += dt * speed
    else:
        moving = False
        sprite.column = 1
    sprite.update_sprite_region()
    sprite.paused = not moving
    sprite.update(dt)


pyglet.clock.schedule(update)
pyglet.app.run()
