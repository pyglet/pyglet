from __future__ import annotations
import weakref
from pathlib import Path
from math import cos, sin, radians, degrees, atan2, sqrt, asin

import pyglet
from pyglet.window import key as _key

from pyglet.gl import glEnable, GL_DEPTH_TEST, GL_CULL_FACE
from pyglet.math import Vec2, Vec3, Mat4, clamp

MODULE_PATH = Path(__file__).parent


def from_pitch_yaw(pitch: float, yaw: float) -> Vec3:
    """Create a unit vector from pitch and yaw in radians.

    The the returned vector is normalized.
    """
    return Vec3(
        cos(yaw) * cos(pitch),
        sin(pitch),
        sin(yaw) * cos(pitch),
    ).normalize()


def get_pitch_yaw(vector: Vec3) -> tuple[float, float]:
    """Get the pitch and yaw angles from a unit vector in radians."""
    return asin(vector.y), atan2(vector.z, vector.x)


class FPSCamera:
    """A 3D projection "first person" camera example.

    Windows in pyglet contain `view` and `projection` matrices,
    which are shared with all default shaders in a `WindowBlock` UBO.
    This Camera class handles events from the mouse & keyboard and
    Controller, and updates these Window matrices.

    Note:  mouse input will be captured once you click on the Window,
    which sets the mouse as exclusive. Pressing ESC once will set
    the mouse as non-exclusive.

    Args:
        window (pyglet.window.Window): The window to attach the camera to.

    Keyword Args:
        position (Vec3, optional): The position of the camera. Defaults to Vec3(0, 0, 0).
        target (Vec3, optional): The target of the camera. Defaults to Vec3(0, 0, -1).
        near (float, optional): The near plane of the camera. Defaults to 0.1.
        far (float, optional): The far plane of the camera. Defaults to 1000.
        field_of_view (float, optional): The field of view of the camera. Defaults to 45.0 degrees.
    """
    STILL = 0
    POSITIVE = 1
    NEGATIVE = -1
    UP = Vec3(0.0, 1.0, 0.0)

    def __init__(
        self,
        window: pyglet.window.Window,
        position: Vec3 | None = None,
        target: Vec3 | None = None,
        near: float = 0.1,
        far: float = 1000,
        field_of_view: float = 60.0,
    ) -> None:
        """Initialize the camera."""
        self._window = weakref.proxy(window)
        self.position = position or Vec3(0.0, 0.0, 0.0)

        # Frustum
        self.near = near
        self.far = far
        self.field_of_view = field_of_view

        # Camera speed
        self.walk_speed = 10.0  # Speed of translation
        self.look_speed = 0.35  # Speed of rotation

        # Pitch, yaw in degrees. We update the camera based on these values.
        self.pitch = 0
        self.yaw = -90

        # Keyboard states
        # Tack what axis the player is moving on (local space)
        self._x_state = self.STILL
        # self._y_state = self.STILL
        self._z_state = self.STILL

        # Mouse states
        self._exclusive_mouse = False

        # Make the camera point and the initial target
        if target is None:
            target = Vec3(0.0, 0.0, -1.0)

        # Point the camera in the configured initial direction
        initial_direction = target - self.position
        pitch, yaw = get_pitch_yaw(initial_direction)
        self.yaw = degrees(yaw)
        self.pitch = degrees(pitch)

        self._window.push_handlers(self)

    def on_deactivate(self) -> None:
        # Prevent input from getting "stuck"
        # self.keyboard_move = Vec2()
        pass

    def on_resize(self, width: int, height: int) -> bool:
        self._window.viewport = (0, 0, *self._window.get_framebuffer_size())
        self._window.projection = Mat4.perspective_projection(
            self._window.aspect_ratio,
            z_near=self.near,
            z_far=self.far,
            fov=self.field_of_view,
        )
        return pyglet.event.EVENT_HANDLED

    def on_refresh(self, delta_time: float) -> None:
        """Called before the window content is drawn."""
        # Calculate the forward and right vectors from the pitch and yaw
        forward = from_pitch_yaw(radians(self.pitch), radians(self.yaw))
        right = forward.cross(self.UP).normalize()
        up = right.cross(forward).normalize()

        # Calculate movement
        offset = forward * (self._z_state * self.walk_speed * delta_time)
        offset += right * (self._x_state * self.walk_speed * delta_time)
        self.position += offset

        # We could construct our own matrix from the vectors, but it's
        # easier to use the look_at function.
        self._window.view = Mat4.look_at(self.position, self.position + forward, self.UP)

    # Mouse input

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        """Read the mouse input and update the camera's yaw and pitch."""
        if not self._exclusive_mouse:
            return

        self.pitch = clamp(self.pitch + dy * self.look_speed, -85.0, 85.0)
        self.yaw += dx * self.look_speed

    def on_mouse_press(self, x: int, y: int, button, modifiers) -> None:
        """Capture the mouse input when the window is clicked."""
        if not self._exclusive_mouse:
            self._exclusive_mouse = True
            self._window.set_exclusive_mouse(True)

    # Keyboard input

    def on_key_press(self, symbol: int, mod: int) -> bool:
        """Handle keyboard input."""
        if symbol == pyglet.window.key.ESCAPE:
            if not self._exclusive_mouse:
                pyglet.app.exit()
            self._exclusive_mouse = False
            self._window.set_exclusive_mouse(False)
            return pyglet.event.EVENT_HANDLED

        if symbol == pyglet.window.key.W:  # Forward
            self._z_state = self.POSITIVE
            return True
        if symbol == pyglet.window.key.S:  # Backward
            self._z_state = self.NEGATIVE
            return True
        if symbol == pyglet.window.key.A:  # Left
            self._x_state = self.NEGATIVE
            return True
        if symbol == pyglet.window.key.D:  # Right
            self._x_state = self.POSITIVE
            return True

        return False

    def on_key_release(self, symbol: int, mod: int) -> bool:
        """Handle keyboard input release."""
        # Reset movement states
        if symbol in (_key.W, _key.S):
            self._z_state = self.STILL
            return True
        if symbol in (_key.A, _key.D):
            self._x_state = self.STILL
            return True

        return False

    def on_stick_motion(self, _controller, stick, vector):
        print(controller, stick, vector)
        # if stick == "leftstick":
            # self.controller_move = self.target * vector.y + self.target.cross(self.up).normalize() * vector.x

        # elif stick == "rightstick":
        #     self.controller_look = vector


# class FPSCamera:
#     """A 3D projection "first person" camera example.

#     Windows in pyglet contain `view` and `projection` matrices,
#     which are shared with all default shaders in a `WindowBlock` UBO.
#     This Camera class handles events from the mouse & keyboard and
#     Controller, and updates these Window matrices.

#     Note:  mouse input will be captured once you click on the Window,
#     which sets the mouse as exclusive. Pressing ESC once will set
#     the mouse as non-exclusive.
#     """
#     def __init__(self, window, position=Vec3(0, 0, 0), target=Vec3(0, 0, -1), up=Vec3(0, 1, 0)):
#         self.position = position
#         self.target = target
#         self.up = up

#         self.walk_speed = 10.0
#         self.look_speed = 10.0
#         self.deadzone = 0.1

#         # TODO: calculate these values from the passed Vectors
#         self.pitch = 0
#         self.yaw = 270
#         self.roll = 0

#         self.input_map = {pyglet.window.key.W: "forward",
#                           pyglet.window.key.S: "backward",
#                           pyglet.window.key.A: "left",
#                           pyglet.window.key.D: "right"}

#         self.inputs = {direction: False for direction in self.input_map.values()}

#         self.mouse_look = Vec2()
#         self.keyboard_move = Vec2()
#         self.controller_look = Vec2()
#         self.controller_move = Vec2()

#         self._window = weakref.proxy(window)
#         self._window.view = Mat4.look_at(position, target, up)
#         self._window.push_handlers(self)

#         self._exclusive_mouse = False

#     def on_deactivate(self):
#         # Prevent input from getting "stuck"
#         self.keyboard_move = Vec2()

#     def on_resize(self, width: int, height: int) -> bool:
#         self._window.viewport = (0, 0, width, height)
#         self._window.projection = Mat4.perspective_projection(self._window.aspect_ratio, z_near=0.1, z_far=1000, fov=45)
#         return pyglet.event.EVENT_HANDLED

#     def on_refresh(self, dt):
#         walk_speed = self.walk_speed * dt
#         norm_target = self.target.normalize()

#         # Look

#         if self.controller_look.length() > self.deadzone:
#             # Don't reset the vector to 0,0 because new events don't come
#             # in when the analoge stick is held in a steady position.
#             look_speed = self.look_speed ** 2 * dt
#             self.yaw += self.controller_look.x * look_speed
#             self.pitch = clamp(self.pitch + self.controller_look.y * look_speed, -89.0, 89.0)

#         if self.mouse_look.length() > 0.0:
#             # Reset the vector back to 0 each time, because there is no event
#             # for when the mouse stops moving. It will get "stuck" otherwise.
#             look_speed = self.look_speed * dt
#             self.yaw += self.mouse_look.x * look_speed
#             self.pitch = clamp(self.pitch + self.mouse_look.y * look_speed, -89.0, 89.0)
#             self.mouse_look = Vec2()

#         self.target = Vec3(cos(radians(self.yaw)) * cos(radians(self.pitch)),
#                            sin(radians(self.pitch)),
#                            sin(radians(self.yaw)) * cos(radians(self.pitch))).normalize()

#         # Movement

#         if self.controller_move.length() > self.deadzone:
#             self.position += (norm_target * self.controller_move.y +
#                               norm_target.cross(self.up).normalize() * self.controller_move.x) * walk_speed

#         if self.keyboard_move.length() > 0:
#             self.position += (norm_target * self.keyboard_move.y +
#                               norm_target.cross(self.up).normalize() * self.keyboard_move.x) * walk_speed

#         self._window.view = Mat4.look_at(self.position, self.position + self.target, self.up)

#     # Mouse input

#     def on_mouse_motion(self, x, y, dx, dy):
#         if not self._exclusive_mouse:
#             return
#         self.mouse_look = Vec2(dx, dy)

#     def on_mouse_press(self, x, y, button, modifiers):
#         if not self._exclusive_mouse:
#             self._exclusive_mouse = True
#             self._window.set_exclusive_mouse(True)

#     # Keyboard input

#     def on_key_press(self, symbol, mod):
#         if symbol == pyglet.window.key.ESCAPE:
#             if not self._exclusive_mouse:
#                 pyglet.app.exit()
#             self._exclusive_mouse = False
#             self._window.set_exclusive_mouse(False)
#             return pyglet.event.EVENT_HANDLED

#         if direction := self.input_map.get(symbol):
#             self.inputs[direction] = True
#             f, b, l, r = self.inputs.values()
#             self.keyboard_move = Vec2(-float(l) + float(r), float(f) + -float(b)).normalize()

#     def on_key_release(self, symbol, mod):
#         if direction := self.input_map.get(symbol):
#             self.inputs[direction] = False
#             f, b, l, r = self.inputs.values()
#             self.keyboard_move = Vec2(-float(l) + float(r), float(f) + -float(b)).normalize()

#     # Controller input

#     def on_stick_motion(self, _controller, stick, vector):
#         if stick == "leftstick":
#             self.controller_move = self.target * vector.y + self.target.cross(self.up).normalize() * vector.x

#         elif stick == "rightstick":
#             self.controller_look = vector


if __name__ == "__main__":
    window = pyglet.window.Window(resizable=True)
    batch = pyglet.graphics.Batch()

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)

    model_logo = pyglet.model.load(MODULE_PATH / "logo3d.obj", batch=batch)
    model_box = pyglet.model.load(MODULE_PATH / "box.obj", batch=batch)

    # Camera controls the global projection & view matrixes:
    camera = FPSCamera(window, position=Vec3(0.0, 0.0, 5.0))

    # If a controller is connected, use it:
    if controllers := pyglet.input.get_controllers():
        controller = controllers[0]
        controller.open()
        controller.push_handlers(camera)

    model_logo.matrix = Mat4.from_translation(Vec3(1.75, 0, 0))
    model_box.matrix = Mat4.from_translation(Vec3(-1.75, 0, 0))

    pyglet.app.run()
