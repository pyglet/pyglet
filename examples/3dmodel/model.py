import math
import pyglet

from pyglet.gl import glEnable, GL_DEPTH_TEST, GL_CULL_FACE


window = pyglet.window.Window(width=720, height=480)
window.projection = pyglet.window.Mat4.perspective_projection(0, 720, 0, 480, z_near=0.1, z_far=255)

batch = pyglet.graphics.Batch()
time = 0


@window.event
def on_draw():
    window.clear()
    batch.draw()


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    rot = model.rotation
    model.rotation = rot[0], rot[1] + dx / 12, rot[2] - dy / 9

    rot = model2.rotation
    model2.rotation = rot[0], rot[1] + dx / 15, rot[2] - dy / 17


def animate(dt):
    global time
    time += dt

    rot = model.rotation
    model.rotation = rot[0], rot[1] + dt * 27, rot[2] + dt * 35
    model.translation = -1.5, 0, math.sin(time) * 0.7 - 4.0

    rot = model2.rotation
    model2.rotation = rot[0], rot[1] + dt * 20, rot[2] + dt * 45 
    model2.translation = 1.5, 0, math.sin(-time) * 0.7 - 5.0


if __name__ == "__main__":
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)

    model = pyglet.resource.model("logo3d.obj", batch=batch)
    model.translation = 0, 0, -2.2
    model2 = pyglet.resource.model("box.obj", batch=batch)
    model2.translation = 0, 0, -2.2

    pyglet.clock.schedule_interval(animate, 1/60)
    pyglet.app.run()
