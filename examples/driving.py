import os
import math

import pyglet.window
import pyglet.window.event
import pyglet.clock
from pyglet.scene2d import *

dirname = os.path.dirname(__file__)

w = pyglet.window.Window(width=640, height=512)
m = RectMap.load_xml(os.path.join(dirname, 'road-map.xml'))

car = Image2d.load(os.path.join(dirname, 'car.png'))
car = Sprite(0, 0, 64, 64, car)
scene = pyglet.scene2d.Scene(maps=[m], sprites=[car])
view = pyglet.scene2d.FlatView(scene, 0, 0, w.width, w.height, allow_oob=False)
w.push_handlers(view.camera)

class running(pyglet.window.event.ExitHandler):
    def __init__(self, fps=30):
        self.clock = pyglet.clock.Clock(fps)
    def __nonzero__(self):
        if self.exit: return False
        self.clock.tick()
        return True

running = running()
w.push_handlers(running)

class InputHandler(object):
    up = down = left = right = 0
    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.K_UP: self.up = 5
        if symbol == pyglet.window.key.K_DOWN: self.down = -5
        if symbol == pyglet.window.key.K_LEFT: self.left = -5
        if symbol == pyglet.window.key.K_RIGHT: self.right = 5
        return pyglet.window.event.EVENT_UNHANDLED
    def on_key_release(self, symbol, modifiers):
        if symbol == pyglet.window.key.K_UP: self.up = 0
        if symbol == pyglet.window.key.K_DOWN: self.down = 0
        if symbol == pyglet.window.key.K_LEFT: self.left = 0
        if symbol == pyglet.window.key.K_RIGHT: self.right = 0
        return pyglet.window.event.EVENT_UNHANDLED

input = InputHandler()
w.push_handlers(input)

speed = 0

while running:
    w.dispatch_events()

    # move
    car.angle -= input.left + input.right
    speed += input.up + input.down
    if speed > 10: speed = 10
    if speed < -5: speed = -5

    rad = car.angle * math.pi / 180
    car.x += -speed*math.sin(rad)
    car.y += speed*math.cos(rad)

    view.fx = car.x
    view.fy = car.y

    view.draw()
    w.flip()
w.close()


