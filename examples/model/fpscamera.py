"""
A basic first-person camera example.

* Supports mouse and keyboard input with AWSD + QE for up/down.
* Supports controller input for movement and rotation.

This can be copied and adapted to your own project.
"""

from __future__ import annotations
import weakref
from pathlib import Path
from math import cos, sin, radians, degrees, atan2, sqrt, asin

import pyglet
from pyglet.window import key as _key

from pyglet.gl import glEnable, GL_DEPTH_TEST, GL_CULL_FACE
from pyglet.math import Vec2, Vec3, Mat4, clamp

MODULE_PATH = Path(__file__).parent


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
        self.walk_speed = 5.0  # Speed of translation
        self.look_speed = 0.2  # Speed of rotation
        self.controller_look_speed = 1.0  # Speed of controller rotation

        # Pitch, yaw in degrees. We update the camera based on these values.
        self.pitch = 0
        self.yaw = -90
        # Controller rotation input
        self.controller_look = Vec2()

        # Movement states
        # Tack what axis the player is moving on (local space)
        self._x_state = self.STILL  # left/right
        self._z_state = self.STILL  # forward/backwards
        self._y_state = self.STILL  # up/down

        # Mouse states
        self._exclusive_mouse = False

        # Make the camera point and the initial target
        if target is None:
            target = Vec3(0.0, 0.0, -1.0)

        # Point the camera in the configured initial direction
        initial_direction = (target - self.position).normalize()
        pitch, yaw = initial_direction.get_pitch_yaw()
        self.yaw = degrees(yaw)
        self.pitch = degrees(pitch)

        self._window.push_handlers(self)

    def on_resize(self, width: int, height: int) -> bool:
        """Update the viewport and projection matrix on window resize."""
        self._window.viewport = (0, 0, *self._window.get_framebuffer_size())
        self._window.projection = Mat4.perspective_projection(
            self._window.aspect_ratio,
            z_near=self.near,
            z_far=self.far,
            fov=self.field_of_view,
        )
        return pyglet.event.EVENT_HANDLED

    def on_refresh(self, delta_time: float) -> None:
        """Called before the window content is drawn.

        Runs every frame applying the camera movement.,
        """
        # If the controller look is not zero, we update the camera rotation.
        # The right stick only pushes events when the stick is moved so we
        # need to apply the rotation here. We also need the delta_time to
        # make the rotation speed consistent.
        if self.controller_look != Vec2():
            self.yaw += self.controller_look.x * self.controller_look_speed
            self.pitch = clamp(self.pitch + self.controller_look.y * self.controller_look_speed, -89.0, 89.0)

        # Calculate the forward and right vectors from the pitch and yaw
        forward = Vec3.from_pitch_yaw(radians(self.pitch), radians(self.yaw))
        right = forward.cross(self.UP).normalize()
        up = right.cross(forward).normalize()

        # Calculate movement
        offset = forward * (self._z_state * self.walk_speed * delta_time)
        offset += right * (self._x_state * self.walk_speed * delta_time)
        offset += up * (self._y_state * self.walk_speed * delta_time)
        self.position += offset

        # We could construct our own matrix from the vectors, but it's
        # easier to use the look_at function.
        self._window.view = Mat4.look_at(self.position, self.position + forward, self.UP)

    def on_deactivate(self) -> None:
        """Reset the movement states when the window loses focus."""
        self.controller_look = Vec2()
        self._x_state = self.STILL
        self._z_state = self.STILL
        self._y_state = self.STILL

    # --- Mouse input ---

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

    # --- Keyboard input ---

    def on_key_press(self, symbol: int, mod: int) -> bool:
        """Handle keyboard input."""
        if symbol == pyglet.window.key.ESCAPE:
            if not self._exclusive_mouse:
                pyglet.app.exit()
            self._exclusive_mouse = False
            self._window.set_exclusive_mouse(False)
            return pyglet.event.EVENT_HANDLED

        # Update movement states
        if symbol == _key.W:  # Forward
            self._z_state = self.POSITIVE
            return True
        if symbol == _key.S:  # Backward
            self._z_state = self.NEGATIVE
            return True
        if symbol == _key.A:  # Left
            self._x_state = self.NEGATIVE
            return True
        if symbol == _key.D:  # Right
            self._x_state = self.POSITIVE
            return True
        if symbol == _key.E:  # up
            self._y_state = self.POSITIVE
            return True
        if symbol == _key.Q:  # down
            self._y_state = self.NEGATIVE
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
        if symbol in (_key.E, _key.Q):
            self._y_state = self.STILL
            return True
 
        return False

    # --- Controller input ---

    def on_stick_motion(self, _controller, stick, vector):
        """Handle controller input.

        The left stick controls the camera position, and the right stick
        controls the camera rotation.
        """
        if stick == "leftstick":
            self._x_state = vector.x
            self._z_state = vector.y

        if stick == "rightstick":
            self.controller_look = vector


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
