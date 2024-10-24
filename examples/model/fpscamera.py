"""
A basic first-person camera example.

This is ideal for inspecting 3D models/scenes and can be adapted
to your needs for first person games.

* Supports mouse and keyboard input with WASD + QE for up/down.
* Supports controller input for movement and rotation including left and right triggers
  to move up and down,
"""

from __future__ import annotations

import weakref

from math import radians, degrees

import pyglet

from pyglet.gl import glEnable, GL_DEPTH_TEST, GL_CULL_FACE
from pyglet.math import Vec2, Vec3, Mat4, clamp
from pyglet.window import key as _key


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
        position (Vec3, optional):
            The position of the camera. Defaults to Vec3(0, 0, 0).
        target (Vec3, optional):
            The target of the camera. Defaults to Vec3(0, 0, -1).
        near (float, optional):
            The near plane of the camera. Defaults to 0.1.
        far (float, optional):
            The far plane of the camera. Defaults to 1000.
        field_of_view (float, optional):
            The field of view of the camera in degrees. Defaults to 45.0 degrees.
    """
    UP = Vec3(0.0, 1.0, 0.0)
    ZERO = Vec3(0.0, 0.0, 0.0)

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
        self._exclusive_mouse = False

        # Frustum
        self._near = near
        self._far = far
        self._field_of_view = field_of_view

        # Camera speed
        self.walk_speed = 10.0  # Speed of translation
        self.look_speed = 10.0  # Speed of rotation

        # Pitch, yaw in degrees. We update the camera based on these values.
        self._pitch = 0.0
        self._yaw = -90.0
        self._roll = 0.0
        self._elevation = 0.0

        # Input from keyboard and controller
        self.keyboard_move = Vec2()
        self.mouse_look = Vec2()

        self.controller_move = Vec2()
        self.controller_look = Vec2()
        self.dead_zone = 0.1

        # Keyboard input maps
        self.input_map = {  # Look up direction based on key symbol
            _key.W: "forward",
            _key.S: "backward",
            _key.A: "left",
            _key.D: "right",
            _key.E: "up",
            _key.Q: "down",
        }
        # Stores the direction string and the state of the direction
        self.inputs = {direction: False for direction in self.input_map.values()}

        # Make the camera point to the initial target.
        # We point it down the negative z-axis if no target is provided.
        if target is None:
            target = position + Vec3(0.0, 0.0, -1.0)

        self.teleport(position, target)

        self._window.push_handlers(self)
        self.on_refresh(0.0)

    @property
    def pitch(self) -> float:
        """Get or set the pitch of the camera in degrees.

        Pitch is the rotation around the local x-axis meaning
        that a positive pitch will look up and a negative pitch
        will look down.

        These values are clamped between -85 and 85 degrees to
        mimic the behavior of most first-person cameras.
        """
        return self._pitch
    
    @pitch.setter
    def pitch(self, value: float) -> None:
        self._pitch = clamp(value, -85.0, 85.0)

    @property
    def yaw(self) -> float:
        """The yaw of the camera in degrees.

        This is the local rotation around the global y-axis
        meaning that a positive yaw will look to the right
        and a negative yaw will look to the left.
        """
        return self._yaw

    @yaw.setter
    def yaw(self, value: float) -> None:
        self._yaw = value

    @property
    def field_of_view(self) -> float:
        """Get or set the field of view of the camera in degrees.

        Setting the value will update the projection matrix.
        """
        return self._field_of_view

    @field_of_view.setter
    def field_of_view(self, value: float) -> None:
        self._field_of_view = value
        self._update_projection()

    @property
    def near(self) -> float:
        """Get or set the near plane of the camera.

        Setting the value will update the projection matrix.
        """
        return self._near

    @near.setter
    def near(self, value: float) -> None:
        self._near = value
        self._update_projection()

    @property
    def far(self) -> float:
        """Get or set the far plane of the camera.

        Setting the value will update the projection matrix.
        """
        return self._far

    @far.setter
    def far(self, value: float) -> None:
        self._far = value
        self._update_projection()

    def on_resize(self, width: int, height: int) -> bool:
        """Update the viewport and projection matrix on window resize."""
        self._window.viewport = (0, 0, *self._window.get_framebuffer_size())
        self._update_projection()
        return pyglet.event.EVENT_HANDLED

    def on_refresh(self, delta_time: float) -> None:
        """Called before the window content is drawn.

        Runs every frame applying the camera movement.
        """
        walk_speed = self.walk_speed * delta_time
        look_speed = self.look_speed * delta_time

        # Rotation - mouse
        if self.mouse_look:
            self.yaw += self.mouse_look.x * look_speed
            self.pitch += self.mouse_look.y * look_speed
            # Reset the relative mouse movement when done.
            self.mouse_look = Vec2()

        # Rotation - controller
        if self.controller_look:
            self.yaw += self.controller_look.x * look_speed * 20
            self.pitch += self.controller_look.y * look_speed * 20

        # Calculate the local forward, right and up vectors from pitch and yaw
        forward = Vec3.from_pitch_yaw(radians(self.pitch), radians(self.yaw))
        right = forward.cross(self.UP).normalize()
        up = right.cross(forward).normalize()
        translation = Vec3()

        # Translation - keyboard
        if self.keyboard_move:
            translation += forward * self.keyboard_move.y + right * self.keyboard_move.x

        # Translation - controller
        if self.controller_move:
            translation += forward * self.controller_move.y + right * self.controller_move.x

        # self.position += translation.normalize() * walk_speed + up * self._elevation * walk_speed
        self.position += (translation + up * self._elevation).normalize() * walk_speed

        # Look forward from the new position
        self._window.view = Mat4.look_at(self.position, self.position + forward, self.UP)

    def on_deactivate(self) -> None:
        """Reset the movement states when the window loses focus."""
        self.controller_look = Vec2()
        self.controller_move = Vec2()

    def teleport(self, position: Vec3, target: Vec3 | None = None) -> None:
        """Teleport the camera to a new position.

        An optional new view target can be provided. If no target is
        provided, the camera will look in the same direction as before.
        """
        if target is not None:
            direction = (target - self.position).normalize()
            pitch, yaw = direction.get_pitch_yaw()
            self.yaw = degrees(yaw)
            self.pitch = degrees(pitch)

        self.position = position

    # --- Mouse input ---

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        """Read the mouse input and update the camera's yaw and pitch."""
        if not self._exclusive_mouse:
            return

        self.mouse_look = Vec2(dx, dy)

    def on_mouse_press(self, x: int, y: int, button, modifiers) -> None:
        """Capture the mouse input when the window is clicked."""
        if not self._exclusive_mouse:
            self._exclusive_mouse = True
            self._window.set_exclusive_mouse(True)

    # --- Keyboard input ---

    def on_key_press(self, symbol: int, mod: int) -> bool:
        """Handle keyboard input."""
        if direction := self.input_map.get(symbol):
            self.inputs[direction] = True
            forward, backward, left, right, up, down = self.inputs.values()
            self.keyboard_move = Vec2(-float(left) + float(right), float(forward) + -float(backward)).normalize()
            self._elevation = float(up) + -float(down)
            return pyglet.event.EVENT_HANDLED

        if symbol == pyglet.window.key.ESCAPE:
            if not self._exclusive_mouse:
                pyglet.app.exit()
            self._exclusive_mouse = False
            self._window.set_exclusive_mouse(False)
            return pyglet.event.EVENT_HANDLED

        return False

    def on_key_release(self, symbol: int, mod: int) -> bool:
        """Handle keyboard input release."""
        if direction := self.input_map.get(symbol):
            self.inputs[direction] = False
            forward, backward, left, right, up, down = self.inputs.values()
            self.keyboard_move = Vec2(-float(left) + float(right), float(forward) + -float(backward)).normalize()
            self._elevation = float(up) + -float(down)
            return pyglet.event.EVENT_HANDLED

        return False

    # --- Controller input ---

    def on_stick_motion(self, _controller, stick: str, vector: Vec2):
        """Handle controller input.

        The left stick controls the camera position, and the right stick
        controls the camera rotation.
        """
        # Translation
        if stick == "leftstick":
            if vector.length() < self.dead_zone:
                self.controller_move = Vec2()
            else:
                self.controller_move = vector

        # Camera rotation
        if stick == "rightstick":
            if vector.length() >= self.dead_zone:
                self.controller_look = vector
            else:
                self.controller_look = Vec2()

    def on_trigger_motion(self, controller, trigger: str, value: float):
        """Handle the controller trigger input."""
        if trigger == "lefttrigger":
            self._elevation = -value
        if trigger == "righttrigger":
            self._elevation = value

    # -- Private methods --

    def _update_projection(self):
        """Update the projection matrix"""
        self._window.projection = Mat4.perspective_projection(
            self._window.aspect_ratio,
            z_near=self.near,
            z_far=self.far,
            fov=self.field_of_view,
        )


if __name__ == "__main__":
    window = pyglet.window.Window(resizable=True)
    batch = pyglet.graphics.Batch()

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)

    model_logo = pyglet.resource.model("logo3d.obj", batch=batch)
    model_box = pyglet.resource.model("box.obj", batch=batch)

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
