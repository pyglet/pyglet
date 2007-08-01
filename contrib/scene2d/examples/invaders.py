import os
import math

import pyglet.window
from resource import *
from pyglet.window import key
from pyglet import clock
from scene2d import *

class PlayerSprite(Sprite):
    bullets = []
    def update(self, dt):
        self.x += (keyboard[key.RIGHT] - keyboard[key.LEFT]) * 200 * dt
        if self.left < 0: self.left = 0
        if self.right > w.width: self.right = w.width
        if self.properties['fired']:
            self.properties['fired'] = max(0, self.properties['fired'] - dt)
        if keyboard[key.SPACE]:
            if not self.properties['fired']:
                self.properties['fired'] = 1
                shot = Sprite.from_image(0, 0, r['player-bullet'])
                shot.midbottom = self.midtop
                view.sprites.append(shot)
                self.bullets.append(shot)

class EnemySprite(Sprite):
    bullets = []
    def update(self, dt):
        self.x += self.properties['dx'] * dt
        if self.right > w.width:
            self.right = w.width
            self.properties['dx'] *= -1
        if self.x < 0:
            self.x = 0
            self.properties['dx'] *= -1
        if not self.properties['fired']:
            self.properties['fired'] = 5
            shot = Sprite.from_image(0, 0, r['enemy-bullet1'])
            shot.midtop = self.midbottom
            view.sprites.append(shot)
            self.bullets.append(shot)
        else:
            self.properties['fired'] = max(0, self.properties['fired'] - dt)

w = pyglet.window.Window(width=512, height=512)
w.set_exclusive_mouse()
clock.set_fps_limit(30)

# load the map and car and set up the view
dirname = os.path.dirname(__file__)
r = Resource.load(os.path.join(dirname, 'invaders.xml'))
player = PlayerSprite.from_image(0, 0, r['player'], properties=dict(fired=0))
clock.schedule(player.update)
view = FlatView.from_window(w, fx=w.width/2, fy=w.height/2,
    sprites=[player])

dead = False
enemies = [
    EnemySprite.from_image(100, 400, r['enemy1'],
        properties={'dx': 150, 'fired': 0})
]
for enemy in enemies:
    view.sprites.append(enemy)
    clock.schedule(enemy.update)

keyboard = key.KeyStateHandler()
w.push_handlers(keyboard)

while not (w.has_exit or dead):
    dt = clock.tick()
    w.dispatch_events()

    # collision detection
    for shot in list(enemies[0].bullets):
        shot.y -= 200 * dt
        if shot.overlaps(player):
            print 'YOU LOST!'
            dead = True
            break
        if shot.y < 0:
            enemies[0].bullets.remove(shot)
            view.sprites.remove(shot)
    for shot in list(player.bullets):
        shot.y += 200 * dt
        for enemy in list(enemies):
            if shot.overlaps(enemy):
                view.sprites.remove(enemy)
                enemies.remove(enemy)
                clock.unschedule(enemy.update)
        if shot.y > 512:
            player.bullets.remove(shot)
            view.sprites.remove(shot)

    # end game
    if not enemies:
        print 'YOU WON!'
        break

    view.clear()
    view.draw()
    w.flip()
w.close()

