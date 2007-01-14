import os
import math

import pyglet.window
from pyglet.resource import *
from pyglet.window.event import *
from pyglet.window.key import *
import pyglet.clock
from pyglet.euclid import Vector2, Matrix3
from pyglet.scene2d import *

w = pyglet.window.Window(width=512, height=512)

# load the map and car and set up the scene and view
dirname = os.path.dirname(__file__)
r = Resource.load(os.path.join(dirname, 'invaders.xml'))
player = Sprite.from_image(0, 0, r['player'])
scene = Scene(sprites=[player])
view = FlatView.from_window(scene, w, fx=w.width/2, fy=w.height/2)

keyboard = KeyboardStateHandler()
w.push_handlers(keyboard)

dead = False
fired = 0
fire = False
player_bullets = []
enemies = [
    Sprite.from_image(100, 400, r['enemy1'], properties={'dx': 150, 'fired': 0})
]
for enemy in enemies:
    scene.sprites.append(enemy)
enemy_bullets = []

clock = pyglet.clock.Clock(fps_limit=30)
while not (w.has_exit or dead):
    dt = clock.tick()
    w.dispatch_events()
    player.x += (keyboard[K_RIGHT] - keyboard[K_LEFT]) * 200 * dt
    if keyboard[K_SPACE]:
        if not fired: fire = True; fired = 1

    for enemy in enemies:
        enemy.x += enemy.properties['dx'] * dt
        if enemy.right > w.width:
            enemy.right = w.width
            enemy.properties['dx'] *= -1
        if enemy.x < 0:
            enemy.x = 0
            enemy.properties['dx'] *= -1
        if not enemy.properties['fired']:
            enemy.properties['fired'] = 5
            shot = Sprite.from_image(0, 0, r['enemy-bullet1'])
            shot.midtop = enemy.midbottom
            scene.sprites.append(shot)
            enemy_bullets.append(shot)
        else:
            enemy.properties['fired'] = max(0, enemy.properties['fired'] - dt)

    # player bullets
    for shot in list(enemy_bullets):
        shot.y -= 200 * dt
        if shot.overlaps(player):
            print 'YOU LOST!'
            dead = True
            break
        if shot.y < 0:
            enemy_bullets.remove(shot)
            scene.sprites.remove(shot)

    # player bullets
    if fire:
        fire = False
        shot = Sprite.from_image(0, 0, r['player-bullet'])
        shot.midbottom = player.midtop
        scene.sprites.append(shot)
        player_bullets.append(shot)
    if fired:
        fired -= dt
        if fired < 0: fired = 0

    for shot in list(player_bullets):
        shot.y += 200 * dt
        for enemy in list(enemies):
            if shot.overlaps(enemy):
                scene.sprites.remove(enemy)
                enemies.remove(enemy)
        if shot.y > 512:
            player_bullets.remove(shot)
            scene.sprites.remove(shot)

    if not enemies:
        print 'YOU WON!'
        break

    view.clear()
    view.draw()
    w.flip()
w.close()


