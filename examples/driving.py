import os
import math

import pyglet.window
from pyglet.window.event import *
from pyglet.window.key import *
import pyglet.clock
from pyglet.euclid import Vector2, Matrix3
from pyglet.scene2d import *

class CarSprite(RotatableSprite):
    speed = 0
    def update(self, dt):
        # handle input and move the car
        self.angle += (keyboard[K_LEFT] - keyboard[K_RIGHT]) * 150 * dt
        self.speed += (keyboard[K_UP] - keyboard[K_DOWN]) * 75 
        if self.speed > 300: self.speed = 300
        if self.speed < -150: self.speed = -150
        r = Matrix3.new_rotate(math.radians(self.angle))
        v = dt * self.speed * (r * Vector2(0, 1))
        self.x += v.x
        self.y += v.y

w = pyglet.window.Window(width=512, height=512)
w.set_exclusive_mouse()

# load the map and car and set up the scene and view
dirname = os.path.dirname(__file__)
m = RectMap.load_xml(os.path.join(dirname, 'road-map.xml'), 'map0')
car = Image2d.load(os.path.join(dirname, 'car.png'))
car = CarSprite.from_image(0, 0, car)
scene = Scene(maps=[m], sprites=[car])
view = FlatView.from_window(scene, w, allow_oob=False)

keyboard = KeyboardStateHandler()
w.push_handlers(keyboard)

clock = pyglet.clock.Clock(fps_limit=30)
clock.schedule(car.update)
while not w.has_exit:
    dt = clock.tick()
    w.dispatch_events()

    # re-focus on the car
    view.fx, view.fy = car.center

    # draw
    view.draw()
    w.flip()
w.close()


