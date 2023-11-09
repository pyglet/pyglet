import weakref

from math import cos, sin, radians

import pyglet

from pyglet.gl import glEnable, GL_DEPTH_TEST, GL_CULL_FACE
from pyglet.math import Vec2, Vec3, Mat4, clamp


class FPSCamera:
    """A 3D projection "first person" camera example.

    Windows in pyglet contain `view` and `projection` matrices,
    which are shared with all default shaders in a `WindowBlock` UBO.
    This Camera class handles events from the mouse & keyboard and
    Controller, and updates these Window matrices.

    Note mouse input will be captured once you click on the Window,
    which sets the mouse as exclusive. Pressing ESC once will set
    the mouse as non-exclusive.
    """
    def __init__(self, window, position=Vec3(0, 0, 0), target=Vec3(0, 0, -1), up=Vec3(0, 1, 0)):
        self.position = position
        self.target = target
        self.up = up

        self.speed = 6
        self.deadzone = 0.1

        # TODO: calculate these values from the passed Vectors
        self.pitch = 0
        self.yaw = 270
        self.roll = 0

        self.input_map = {pyglet.window.key.W: "forward",
                          pyglet.window.key.S: "backward",
                          pyglet.window.key.A: "left",
                          pyglet.window.key.D: "right"}

        self.inputs = {direction : False for direction in self.input_map.values()}

        self.mouse_look = Vec2()
        self.keybord_move = Vec3()
        self.controller_look = Vec2()
        self.controller_move = Vec3()

        self._window = weakref.proxy(window)
        self._window.view = Mat4.look_at(position, target, up)
        self._window.push_handlers(self)

        self._exclusive_mouse = False

    def on_deactivate(self):
        # Prevent input from getting "stuck"
        self.keybord_move[:] = 0, 0, 0

    def on_resize(self, width, height):
        self._window.viewport = (0, 0, width, height)
        self._window.projection = Mat4.perspective_projection(self._window.aspect_ratio, z_near=0.1, z_far=100, fov=45)
        return pyglet.event.EVENT_HANDLED

    def on_refresh(self, dt):
        # Look

        if abs(self.controller_look) > self.deadzone:
            # Don't reset the vector to 0,0 because new events don't come
            # in when the analoge stick is held in a steady position.
            self.yaw = self.yaw + self.controller_look.x
            self.pitch = clamp(self.pitch + self.controller_look.y, -89.0, 89.0)

        if abs(self.mouse_look) > 0.0:
            # Reset the vector back to 0 each time, because there is no event
            # for when the mouse stops moving. It will get "stuck" otherwise.
            self.yaw += self.mouse_look.x * 0.1
            self.pitch = clamp(self.pitch + self.mouse_look.y * 0.1, -89.0, 89.0)
            self.mouse_look[:] = 0.0, 0.0

        self.target = Vec3(cos(radians(self.yaw)) * cos(radians(self.pitch)),
                           sin(radians(self.pitch)),
                           sin(radians(self.yaw)) * cos(radians(self.pitch))).normalize()

        # Movement

        speed = self.speed * dt

        if abs(self.controller_move) > self.deadzone:
            self.position += self.controller_move * speed

        if self.inputs["forward"]:
            self.position += (self.target * speed)
        if self.inputs["backward"]:
            self.position -= (self.target * speed)
        if self.inputs["left"]:
            self.position -= (self.target.cross(self.up).normalize() * speed)
        if self.inputs["right"]:
            self.position += (self.target.cross(self.up).normalize() * speed)

        if abs(self.keybord_move) > 0:
            self.position += self.keybord_move * speed

        self._window.view = Mat4.look_at(self.position, self.position + self.target, self.up)

    # Mouse input

    def on_mouse_motion(self, x, y, dx, dy):
        if not self._exclusive_mouse:
            return
        self.mouse_look[:] = dx, dy

    def on_mouse_press(self, x, y, button, modifiers):
        if not self._exclusive_mouse:
            self._exclusive_mouse = True
            self._window.set_exclusive_mouse(True)

    # Keyboard input

    def on_key_press(self, symbol, mod):
        if symbol == pyglet.window.key.ESCAPE:
            self._exclusive_mouse = False
            self._window.set_exclusive_mouse(False)
            return pyglet.event.EVENT_HANDLED

        if symbol in self.input_map:
            direction = self.input_map[symbol]
            self.inputs[direction] = True

    def on_key_release(self, symbol, mod):
        if symbol in self.input_map:
            direction = self.input_map[symbol]
            self.inputs[direction] = False

    # Controller input

    def on_stick_motion(self, _controller, stick, xvalue, yvalue):
        if stick == "leftstick":
            self.controller_move = self.target * yvalue + self.target.cross(self.up).normalize() * xvalue

        elif stick == "rightstick":
            self.controller_look[:] = xvalue, yvalue



if __name__ == "__main__":
    window = pyglet.window.Window(width=964, height=540, resizable=True)
    batch = pyglet.graphics.Batch()

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)

    model_logo = pyglet.model.load("logo3d.obj", batch=batch)
    model_box = pyglet.model.load("box.obj", batch=batch)

    # Camera controls the global projection & view matrixes:
    camera = FPSCamera(window, position=Vec3(0, 0, 5))

    if controllers := pyglet.input.get_controllers():
        controller = controllers[0]
        controller.open()
        controller.push_handlers(camera)

    model_logo.matrix = Mat4.from_translation(Vec3(1.75, 0, 0))
    model_box.matrix = Mat4.from_translation(Vec3(-1.75, 0, 0))

    pyglet.app.run()
