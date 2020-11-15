import pyglet
from pyglet.gl import *

window = pyglet.window.Window(width=720, height=480)
window.projection = pyglet.window.Projection3D()
batch = pyglet.graphics.Batch()

@window.event
def on_draw():
    window.clear()
    batch.draw()


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    rot = model.rotation
    model.rotation = rot[0], rot[1] + dx / 10, rot[2] + dy / 10


def rotate(dt):
    dt = dt * 100
    rot = model.rotation
    model.rotation = rot[0], rot[1] + dt, rot[2]


if __name__ == "__main__":
    glEnable(GL_MULTISAMPLE_ARB)
    glEnable(GL_DEPTH_TEST)

    model = pyglet.model.load("logo3d.obj", batch=batch)
    model.translation = 0, 0, -2.2

    pyglet.clock.schedule_interval(rotate, 1/60)
    pyglet.app.run()
