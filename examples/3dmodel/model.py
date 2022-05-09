import pyglet

from pyglet.gl import glEnable, GL_DEPTH_TEST, GL_CULL_FACE
from pyglet.math import Mat4, Vec3


window = pyglet.window.Window(width=720, height=480, resizable=True)
batch = pyglet.graphics.Batch()
time = 0


@window.event
def on_resize(width, height):
    window.on_resize(width, height)
    window.projection = Mat4.perspective_projection(0, width, 0, height, z_near=0.1, z_far=255)
    return pyglet.event.EVENT_HANDLED


@window.event
def on_draw():
    window.clear()
    batch.draw()


def animate(dt):
    global time
    time += dt

    rot_x = Mat4.from_rotation(time, Vec3(1, 0, 0))
    rot_y = Mat4.from_rotation(time/2, Vec3(0, 1, 0))
    rot_z = Mat4.from_rotation(time/3, Vec3(0, 0, 1))
    trans = Mat4.from_translation((1.25, 0, 2))
    model_logo.matrix = rot_x @ rot_y @ rot_z @ trans

    rot_x = Mat4.from_rotation(time, Vec3(1, 0, 0))
    rot_y = Mat4.from_rotation(time/3, Vec3(0, 1, 0))
    rot_z = Mat4.from_rotation(time/2, Vec3(0, 0, 1))
    trans = Mat4.from_translation(Vec3(-1.75, 0, 0))
    model_box.matrix = rot_x @ rot_y @ rot_z @ trans


if __name__ == "__main__":
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)

    model_logo = pyglet.resource.model("logo3d.obj", batch=batch)
    model_box = pyglet.resource.model("box.obj", batch=batch)

    # Set the application wide view matrix to "zoom out" (camera):
    window.view = Mat4.from_translation(Vec3(0, 0, -5))

    pyglet.clock.schedule_interval(animate, 1 / 60)
    pyglet.app.run()
