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
        self.counter, self.duration = 0.0, duration

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
        self.counter += dt
        if self.counter >= self.duration:
            self.counter -= self.duration
            self.next_frame()


pyglet.image.Texture.default_mag_filter = pyglet.gl.GL_NEAREST
pyglet.image.Texture.default_min_filter = pyglet.gl.GL_NEAREST
window = pyglet.window.Window(width=800, height=360, resizable=True)
pyglet.gl.glClearColor(0.5, 0.5, 0.5, 1.0)
sprites = []
counter = 0.0
last_modified = 0

@window.event
def on_draw():
    window.clear()
    for sprite in sprites:
        sprite.draw()


def update(dt):
    for sprite in sprites:
        sprite.update_sprite_region()
        sprite.update(dt)
    global counter
    counter += dt
    if counter >= 0.8:
        reload_sprites()
        counter = 0.0

def reload_sprites():
    global last_modified
    filename = os.path.dirname(__file__) + "character.png"
    mtime = os.stat(filename).st_mtime
    if mtime == last_modified:
        return
    print("Sprite changed, refreshing!")
    last_modified = mtime
    global sprites
    sprites = []
    x, y = 0, 100
    for row in range(4):
        sprite = AnimatedSprite(filename, 4, 3, 10)
        sprite.sprite.x, sprite.sprite.y = x, y
        sprite.row = row
        x += 200
        sprites.append(sprite)

reload_sprites()

pyglet.clock.schedule(update)
pyglet.app.run()
