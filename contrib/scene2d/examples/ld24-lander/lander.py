import sys

sys.path.insert(0, '/home/richard/src/pyglet.googlecode.com/trunk')

import os
import math

import pyglet.window
from resource import *
from pyglet.window import key
from pyglet import clock
from scene2d import *
from scene2d.textsprite import *
from pyglet import font
from layout import *

class RocketSprite(Sprite):
    def update(self, dt):
        p = self.properties
        p['dx'] += (keyboard[key.RIGHT] - keyboard[key.LEFT]) * 25 * dt
        p['dx'] = min(300, max(-300, p['dx']))
        if keyboard[key.SPACE]:
            if flame not in effectlayer.sprites:
                effectlayer.sprites.append(flame)
            p['dy'] += 50 * dt
        elif flame in effectlayer.sprites:
            effectlayer.sprites.remove(flame)
        p['dy'] = min(300, max(-300, p['dy']))

        gravity = 25
        # don't need topleft or topright until I get a ceiling
        for point in (self.bottomleft, self.bottomright):
            cell = r['level1'].get(*map(int, point))
            if cell is None or cell.tile is None: continue
            if 'pad' in cell.tile.properties:
                p['done'] = 1
                gravity = 0
                if p['dy'] < 0: p['dy'] = 0
                p['dx'] = 0
                self.bottom = cell.top - 1
            elif 'open' not in cell.tile.properties:
                p['done'] = 2
                clock.unschedule(self.update)
                if flame in effectlayer.sprites:
                    effectlayer.sprites.remove(flame)
                boom.center = self.midbottom
                if boom not in effectlayer.sprites:
                    effectlayer.sprites.append(boom)

        p['dy'] -= gravity * dt

        self.y += p['dy']
        self.x += p['dx']
        flame.midtop = self.midbottom

class AnimatedSprite(Sprite):
    def update(self, dt):
        p = self.properties
        p['t'] += dt
        if p['t'] > .1:
            p['t'] = 0
            p['frame'] = (p['frame'] + 1) % len(p['frames'])
            self.image = p['frames'][p['frame']]
            # XXX hack to ensure we use the new image
            self._style = None

# open window
w = pyglet.window.Window(width=1280, height=1024, fullscreen=True)
#w = pyglet.window.Window(width=800, height=600)
w.set_exclusive_mouse()
clock.set_fps_limit(60)
keyboard = key.KeyStateHandler()
w.push_handlers(keyboard)

class SaveHandler:
    def on_text(self, text):
        if text == 's':
            image = pyglet.image.BufferImage().get_raw_image()
            fn = 'screenshot.png'
            n = 1
            while os.path.exists(fn):
                fn = 'screenshot' + str(n) + '.png'
                n += 1
            print "Saving to '%s'"%fn
            image.save(fn)
w.push_handlers(SaveHandler())

font = font.load('Bitstream Vera Sans', 24)

# load the sprites & level
dirname = os.path.dirname(__file__)
r = Resource.load(os.path.join(dirname, 'lander.xml'))
rocket = RocketSprite.from_image(0, 0, r['rocket'], offset=(18, 0),
    properties=dict(dx=0, dy=0, done=0))
rocket.width = 92

frames = [r['flame%d'%i] for i in range(1, 7)]
flame = AnimatedSprite.from_image(0, 0, frames[0],
    properties=dict(frame=0, t=0, frames=frames))
clock.schedule(flame.update)

frames = [r['boom%d'%i] for i in range(1, 4)]
boom = AnimatedSprite.from_image(0, 0, frames[0],
    properties=dict(frame=0, t=0, frames=frames))
clock.schedule(boom.update)

fps = clock.ClockDisplay(color=(1., .5, .5, .5))

effectlayer = SpriteLayer(5)
rocketlayer = SpriteLayer(1, [rocket])

def play(level):
    view = FlatView.from_window(w, layers=[level, effectlayer, rocketlayer])

    # set rocket start
    for col in level.cells:
        for cell in col:
            if 'player-start' in cell.properties:
                rocket.midtop = cell.midtop


    clock.schedule(rocket.update)
    rocket.properties.update(dict(dx=0, dy=0, done=0))

    # run game
    while not (w.has_exit or rocket.properties['done']):
        dt = clock.tick()
        w.dispatch_events()
        view.fx, view.fy = rocket.center
        view.clear((.2, .2, .2, .2))
        view.draw()
        fps.draw()
        w.flip()

    # put up a message
    done = rocket.properties['done']
    if not done: return
    if done == 1: text = 'YAY YOU LANDED!'
    if done == 2: text = 'BOO YOU CRASHED!'
    text += '  (press [escape] to continue)'
    sprite = TextSprite(font, text, color=(1., 1., 1., 1.))
    sprite.x, sprite.y = w.width/2 - sprite.width/2, w.height/2 - sprite.height/2
    w.has_exit = False
    while not w.has_exit:
        dt = clock.tick()
        w.dispatch_events()
        view.clear((.2, .2, .2, .2))
        view.draw()
        sprite.draw()
        w.flip()

    clock.unschedule(rocket.update)
    if boom in effectlayer.sprites:
        effectlayer.sprites.remove(boom)

data = '''<?xml version="1.0"?><html><head>
<style>
h1 {border-bottom: 1px solid;}
body {background-color: black; color: white; font-family: sans-serif; font-size: 150%;}
tt {background-color: #aaa; color: black;}
</style></head><body>
<h1>Lunar Lander (yet another clone)</h1>
<p><b>Controls:</b></p>
<p><tt>[space]</tt> fires the rocket's motors</p>
<p><tt>[left/right arrows]</tt> push the rocket left or right</p>
<p></p>
<p>Press <tt>[space]</tt> to play or <tt>[escape]</tt> to quit.</p>
</body></html>'''

layout = Layout()
layout.set_xhtml(data)
layout.on_resize(w.width, w.height)

def menu():
    w.has_exit = False
    glClearColor(0, 0, 0, 0)
    while not w.has_exit:
        dt = clock.tick()
        w.dispatch_events()
        if keyboard[key.SPACE]: return True
        glClear(GL_COLOR_BUFFER_BIT)
        layout.draw()
        w.flip()
    return False

while 1:
    if not menu():
        break
    play(r['level1'])
w.close()

