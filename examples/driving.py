import os

import pyglet.window
import pyglet.window.event
import pyglet.clock
from pyglet.scene2d import *
from pyglet.GL.VERSION_1_1 import *

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

dx, dy = (10, 5)

glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glEnable(GL_BLEND)
glEnable(GL_COLOR_MATERIAL)

while running:
    w.dispatch_events()

    # move, check bounds
    car.x += dx; car.y += dy
    if car.left < 0: car.left = 0; dx = -dx
    elif car.right > w.width: car.right = w.width; dx = -dx
    if car.bottom < 0: car.bottom = 0; dy = -dy
    elif car.top > w.height: car.top = w.height; dy = -dy

    glClear(GL_COLOR_BUFFER_BIT)
    view.draw()
    w.flip()
w.close()


