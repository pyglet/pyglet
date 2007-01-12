import os
import math

import pyglet.window
from pyglet.window.event import *
from pyglet.window.key import *
import pyglet.clock
from pyglet.euclid import Vector2, Matrix3
from pyglet.scene2d import *

w = pyglet.window.Window(width=640, height=512)

# load the map and car and set up the scene and view
dirname = os.path.dirname(__file__)
m = RectMap.load_xml(os.path.join(dirname, 'road-map.xml'), 'map0')
car = Sprite.from_image(Image2d.load(os.path.join(dirname, 'car.png')))
scene = pyglet.scene2d.Scene(maps=[m], sprites=[car])
view = pyglet.scene2d.FlatView.from_window(scene, w, allow_oob=False)
w.push_handlers(view.camera)

keyboard = KeyboardStateHandler()
w.push_handlers(keyboard)

speed = 0
clock = pyglet.clock.Clock(fps_limit=30)
while not w.has_exit:
    dt = clock.tick()
    w.dispatch_events()

    # handle input and move the car
    car.angle += (keyboard[K_LEFT] - keyboard[K_RIGHT]) * 150 * dt
    speed += (keyboard[K_UP] - keyboard[K_DOWN]) * 75 
    if speed > 300: speed = 300
    if speed < -150: speed = -150
    r = Matrix3.new_rotate(math.radians(car.angle))
    v = dt * speed * (r * Vector2(0, 1))
    car.x += v.x
    car.y += v.y

    # re-focus on the car
    if speed:
        view.fx, view.fy = car.center

    # draw
    view.draw()
    w.flip()
w.close()


