import weakref

from math import cos, sin, radians

import pyglet

from pyglet.gl import glEnable, GL_DEPTH_TEST, GL_CULL_FACE
from pyglet.math import Mat4, Vec3, clamp


window = pyglet.window.Window(width=720, height=480, resizable=True)
batch = pyglet.graphics.Batch()
time = 0


class FPSCamera:
    def __init__(self, window, position=Vec3(0, 0, 0), target=Vec3(0, 0, -1), up=Vec3(0, 1, 0)):
        self.position = position
        self.target = target
        self.up = up

        self.speed = 3

        # TODO: calculate these values from the passed Vectors
        self.pitch = 0
        self.yaw = 2705
        self.roll = 0

        self.input_map = {
            pyglet.window.key.W: "forward",
            pyglet.window.key.S: "backward",
            pyglet.window.key.A: "left",
            pyglet.window.key.D: "right",
        }

        self.forward = False
        self.backward = False
        self.left = False
        self.right = False

        self._window = weakref.proxy(window)
        self._window.view = Mat4.look_at(position, target, up)
        self._window.push_handlers(self)

    def on_resize(self, width, height):
        self._window.viewport = (0, 0, *window.get_framebuffer_size())
        self._window.projection = Mat4.perspective_projection(window.aspect_ratio, z_near=0.1, z_far=100, fov=45)
        return pyglet.event.EVENT_HANDLED

    def on_refresh(self, dt):
        # Movement
        speed = self.speed * dt
        if self.forward:
            self.position += (self.target * speed)
        if self.backward:
            self.position -= (self.target * speed)
        if self.left:
            self.position -= (self.target.cross(self.up).normalize() * speed)
        if self.right:
            self.position += (self.target.cross(self.up).normalize() * speed)

        # Look

        yaw = self.yaw * 0.1
        pitch = self.pitch
        self.target = Vec3(cos(radians(yaw)) * cos(radians(pitch)),
                           sin(radians(pitch)),
                           sin(radians(yaw)) * cos(radians(pitch))).normalize()

        self._window.view = Mat4.look_at(self.position, self.position + self.target, self.up)

    # Mouse input

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, mod):
        self.yaw += dx
        self.pitch = clamp(self.pitch + dy, -89.0, 89.0)
        # self.pitch += dy

    # Keyboard input

    def on_key_press(self, symbol, mod):
        if symbol in self.input_map:
            setattr(self, self.input_map[symbol], True)

    def on_key_release(self, symbol, mod):
        if symbol in self.input_map:
            setattr(self, self.input_map[symbol], False)


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
    trans = Mat4.from_translation(Vec3(1.25, 0, 2))
    model_logo.matrix = rot_x @ rot_y @ rot_z @ trans

    rot_x = Mat4.from_rotation(time, Vec3(1, 0, 0))
    rot_y = Mat4.from_rotation(time/3, Vec3(0, 1, 0))
    rot_z = Mat4.from_rotation(time/2, Vec3(0, 0, 1))
    trans = Mat4.from_translation(Vec3(-1.75, 0, 0))
    model_box.matrix = rot_x @ rot_y @ rot_z @ trans


if __name__ == "__main__":
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)

    model_logo = pyglet.model.load("logo3d.obj", batch=batch)
    model_box = pyglet.model.load("box.obj", batch=batch)

    # Set the application wide view matrix (camera):
    # window.view = Mat4.look_at(position=Vec3(0, 0, 5), target=Vec3(0, 0, 0), up=Vec3(0, 1, 0))
    camera = FPSCamera(window, position=Vec3(0, 0, 5))

    pyglet.clock.schedule_interval(animate, 1 / 60)
    pyglet.app.run()
