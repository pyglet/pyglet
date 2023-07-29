import math
import sys
import arcade
import pyglet
import pyglet.experimental.geoshader_sprite
import random
import time
import statprof
import psutil
import os

# Does not work on Windows.  Might work on Linux
use_statprof = False

is_arcade = False
is_pyglet_geosprite = True

# The block below allows toggling between against pyglet's vanilla Sprite or arcade's Sprite w/SpriteList
# It is commented out to be compatible with bench.sh, where our goal is *not* to
# compare against arcade, but rather, to compare pyglet agaist itself with
# different code changes.

# print(sys.argv)
# is_pyglet_geosprite = False
# if sys.argv[1] == 'arcade':
#     is_arcade = True
# elif sys.argv[1] == 'pyglet_sprite':
#     is_arcade = False
# elif sys.argv[1] == 'pyglet_geosprite':
#     is_arcade = False
#     is_pyglet_geosprite = True
# else:
#     raise Exception('')


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

WALL_DIM_MIN = 10
WALL_DIM_MAX = 200
WALLS_COUNT = 10

BULLET_VELOCITY_MIN = 1/60
BULLET_VELOCITY_MAX = 10/60
BULLETS_PER_BATCH = 4500
BATCH_COUNT = 2

SIMULATE_MINUTES = 3
SIMULATE_FPS = 60

# Predictable randomization so that each benchmark is identical
rng = random.Random(0)

bullets = []

window = arcade.Window()

# Seed chosen manually to create a wall distribution that looked good enough,
# like something I might create in a game.
rng.seed(2)

dir_path = os.path.dirname(os.path.realpath(__file__))
png_path = f'{dir_path}/image.png'

arcade_texture = arcade.load_texture(png_path)
arcade_sprite_lists = [arcade.SpriteList(use_spatial_hash=False) for _ in range(BATCH_COUNT)]
def create_bullet_arcade():
    # Create a new bullet
    new_bullet = arcade.Sprite(path_or_texture=arcade_texture)
    new_bullet.position = (rng.randint(0, SCREEN_WIDTH), rng.randint(0, SCREEN_HEIGHT))
    speed = rng.random() * (BULLET_VELOCITY_MAX - BULLET_VELOCITY_MIN) + BULLET_VELOCITY_MIN
    angle = rng.random() * math.pi * 2
    new_bullet.velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
    # Half of bullets are rotated, to test those code paths
    if rng.random() > 0.5:
        new_bullet.angle = 45
    return new_bullet

pyglet_batches = [pyglet.graphics.Batch() for _ in range(BATCH_COUNT)]
pyglet_image = pyglet.image.load(png_path)

class MyPygletSprite(pyglet.experimental.geoshader_sprite.Sprite):
    __slots__ = ['velocity']

PygletSpriteImpl = MyPygletSprite if is_pyglet_geosprite else pyglet.sprite.Sprite
def create_bullet_pyglet(batch):
    # Create a new bullet
    new_bullet = PygletSpriteImpl(img=pyglet_image, batch=batch, subpixel=True)
    new_bullet.position = (rng.randint(0, SCREEN_WIDTH), rng.randint(0, SCREEN_HEIGHT), 0)
    speed = rng.random() * (BULLET_VELOCITY_MAX - BULLET_VELOCITY_MIN) + BULLET_VELOCITY_MIN
    angle = rng.random() * math.pi * 2
    new_bullet.velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
    # Half of bullets are rotated, to test those code paths
    if rng.random() > 0.5:
        new_bullet.rotation = 45
    return new_bullet

def create_bullets_arcade():
    for _ in range(0, BULLETS_PER_BATCH):
        for sprite_list in arcade_sprite_lists:
            bullet = create_bullet_arcade()
            sprite_list.append(bullet)
            bullets.append(bullet)

def create_bullets_pyglet():
    # intentionally create in 2x batches alternating such that our `position=`
    # assignments alternate between both batches
    for _ in range(0, BULLETS_PER_BATCH):
        for batch in pyglet_batches:
            bullets.append(create_bullet_pyglet(batch))

def move_bullets_arcade():
    # Move all bullets
    for bullet in bullets:
        x, y = bullet.position
        bullet.position = (x + bullet.velocity[0], y + bullet.velocity[1])
def move_bullets_pyglet():
    # Move all bullets
    for bullet in bullets:
        x, y, _ = bullet.position
        bullet.position = (x + bullet.velocity[0], y + bullet.velocity[1], 0)


def draw_bullets_arcade():
    for list in arcade_sprite_lists:
        list.draw()

def draw_bullets_pyglet():
    for batch in pyglet_batches:
        batch.draw()

create_bullets = create_bullets_arcade if is_arcade else create_bullets_pyglet
move_bullets = move_bullets_arcade if is_arcade else move_bullets_pyglet
draw_bullets = draw_bullets_arcade if is_arcade else draw_bullets_pyglet

create_bullets()
if use_statprof:
    statprof.start()

for i in range(0, int(SIMULATE_MINUTES * 60 * SIMULATE_FPS)):
    pyglet.clock.tick()

    window.switch_to()
    window.dispatch_events()

    move_bullets()
    window.dispatch_event('on_draw')

    window.clear(color=arcade.color.WHITE)
    draw_bullets()
    window.flip()

if use_statprof:
    statprof.stop()
    statprof.display()

print(psutil.Process().memory_info().rss / (1024 * 1024))
