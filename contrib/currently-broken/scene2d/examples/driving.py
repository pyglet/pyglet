import os
import math

import pyglet.window
from pyglet.window.event import *
from pyglet.window import key
from pyglet import clock
from euclid import Vector2, Matrix3
from scene2d import *

class CarSprite(RotatableSprite):
    def update(self, dt):
        # handle input and move the car
        self.angle += (keyboard[key.LEFT] - keyboard[key.RIGHT]) * 150 * dt
        speed = self.properties.get('speed', 0)
        speed += (keyboard[key.UP] - keyboard[key.DOWN]) * 75 
        if speed > 300: speed = 300
        if speed < -150: speed = -150
        self.properties['speed'] = speed
        r = Matrix3.new_rotate(math.radians(self.get_angle()))
        v = dt * speed * (r * Vector2(0, 1))
        self.x += v.x
        self.y += v.y

w = pyglet.window.Window(width=512, height=512)
w.set_exclusive_mouse()

# load the map and car and set up the scene and view
dirname = os.path.dirname(__file__)
m = RectMap.load_xml(os.path.join(dirname, 'road-map.xml'), 'map0')
car = CarSprite.from_image(0, 0, Image2d.load(os.path.join(dirname, 'car.png')))
view = FlatView.from_window(w, layers=[m], sprites=[car])

keyboard = key.KeyStateHandler()
w.push_handlers(keyboard)

clock.set_fps_limit(30)
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


