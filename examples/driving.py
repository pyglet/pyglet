import os
import math

import pyglet.window
from pyglet.window.event import *
from pyglet.window.key import *
import pyglet.clock
from pyglet.scene2d import *

w = pyglet.window.Window(width=640, height=512)

# load the map and car and set up the scene and view
dirname = os.path.dirname(__file__)
m = RectMap.load_xml(os.path.join(dirname, 'road-map.xml'))
car = Sprite.from_image(Image2d.load(os.path.join(dirname, 'car.png')))
scene = pyglet.scene2d.Scene(maps=[m], sprites=[car])
view = pyglet.scene2d.FlatView.from_window(scene, w, allow_oob=False)
w.push_handlers(view.camera)

class running(ExitHandler):
    def __init__(self, fps=30):
        self.clock = pyglet.clock.Clock(fps)
    def __nonzero__(self):
        if self.exit: return False
        self.clock.tick()
        return True
running = running()
w.push_handlers(running)

keyboard = KeyboardStateHandler()
w.push_handlers(keyboard)

speed = 0
while running:
    w.dispatch_events()

    # handle input and move the car
    car.angle += (keyboard[K_LEFT] - keyboard[K_RIGHT]) * 5
    speed += (keyboard[K_UP] - keyboard[K_DOWN]) * 2.5
    if speed > 10: speed = 10
    if speed < -5: speed = -5
    angle = math.radians(car.angle)
    car.x += -speed * math.sin(angle)
    car.y += speed * math.cos(angle)

    # re-focus on the car
    view.fx, view.fy = car.center

    # draw
    view.draw()
    w.flip()
w.close()


