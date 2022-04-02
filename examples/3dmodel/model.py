import pyglet

from pyglet.gl import glEnable, GL_DEPTH_TEST, GL_CULL_FACE
from pyglet.math import Mat4, Vec3


window = pyglet.window.Window(width=720, height=480)
batch = pyglet.graphics.Batch()
time = 0


@window.event
def on_resize(width, height):
    window.projection = pyglet.window.Mat4.perspective_projection(0, width, 0, height, z_near=0.1, z_far=255)
    return pyglet.event.EVENT_HANDLED


@window.event
def on_draw():
    window.clear()
    batch.draw()


@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):

    matrix = model.matrix
    model.matrix = matrix.rotate(0.01, Vec3(dx, dy, 0).normalize())

    matrix = model2.matrix
    model2.matrix = matrix.rotate(0.01, Vec3(-dx, -dy, 0).normalize())


def animate(dt):
    global time
    time += dt

    matrix = model.matrix
    matrix = matrix.rotate(dt/2, Vec3(0, 0, 1))
    matrix = matrix.rotate(dt/2, Vec3(0, 1, 0))
    matrix = matrix.rotate(dt/2, Vec3(1, 0, 0))
    model.matrix = matrix

    matrix = model2.matrix
    matrix = matrix.rotate(dt*2, Vec3(0, 0, 1))
    matrix = matrix.rotate(dt*2, Vec3(0, 1, 0))
    matrix = matrix.rotate(dt*2, Vec3(1, 0, 0))
    model2.matrix = matrix


if __name__ == "__main__":
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)

    model = pyglet.resource.model("logo3d.obj", batch=batch)
    model.matrix = Mat4.from_translation(Vec3(3, 0, 0))

    model2 = pyglet.resource.model("box.obj", batch=batch)
    model2.matrix = Mat4.from_translation(Vec3(-3, 0, 0))

    # Set the application wide view matrix to "zoom out":
    window.view = Mat4.from_translation(Vec3(0, 0, -5))

    pyglet.clock.schedule_interval(animate, 1/60)
    pyglet.app.run()
