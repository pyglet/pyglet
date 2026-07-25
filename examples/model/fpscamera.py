"""A basic first-person camera example using :mod:`pyglet.window.camera`."""

from __future__ import annotations

import random
import weakref

import pyglet
from pyglet.math import Vec2, Vec3
from pyglet.window import key as _key
from pyglet.window.camera import FPSCamera


class FPSCameraControls:
    """First-person controls from the old example, driving a camera object."""

    def __init__(self, window: pyglet.window.Window, camera: FPSCamera) -> None:
        """Initialize the controls."""
        self._window = weakref.proxy(window)
        self.camera = camera
        self._exclusive_mouse = False

        # Input from keyboard and controller
        self.keyboard_move = Vec2()
        self.mouse_look = Vec2()

        self.controller_move = Vec2()
        self.controller_look = Vec2()
        self.dead_zone = 0.1
        self._elevation = 0.0

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

        self._window.push_handlers(self)
        self.on_refresh(0.0)

    @property
    def position(self) -> Vec3:
        return self.camera.position

    @position.setter
    def position(self, value: Vec3) -> None:
        self.camera.position = value

    @property
    def pitch(self) -> float:
        return self.camera.pitch

    @pitch.setter
    def pitch(self, value: float) -> None:
        self.camera.pitch = value

    @property
    def yaw(self) -> float:
        return self.camera.yaw

    @yaw.setter
    def yaw(self, value: float) -> None:
        self.camera.yaw = value

    @property
    def field_of_view(self) -> float:
        return self.camera.field_of_view

    @field_of_view.setter
    def field_of_view(self, value: float) -> None:
        self.camera.field_of_view = value

    @property
    def near(self) -> float:
        return self.camera.near

    @near.setter
    def near(self, value: float) -> None:
        self.camera.near = value

    @property
    def far(self) -> float:
        return self.camera.far

    @far.setter
    def far(self, value: float) -> None:
        self.camera.far = value

    @property
    def walk_speed(self) -> float:
        return self.camera.walk_speed

    @walk_speed.setter
    def walk_speed(self, value: float) -> None:
        self.camera.walk_speed = value

    @property
    def look_speed(self) -> float:
        return self.camera.look_speed

    @look_speed.setter
    def look_speed(self, value: float) -> None:
        self.camera.look_speed = value

    def on_refresh(self, delta_time: float) -> None:
        """Called before the window content is drawn.

        Runs every frame applying the camera movement.
        """
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

        movement = Vec2()

        # Translation - keyboard
        if self.keyboard_move:
            movement += self.keyboard_move

        # Translation - controller
        if self.controller_move:
            movement += self.controller_move

        if movement:
            movement = movement.normalize()

        self.camera.apply_movement_input(movement, self._elevation, delta_time)

    def on_deactivate(self) -> None:
        """Reset the movement states when the window loses focus."""
        self.controller_look = Vec2()
        self.controller_move = Vec2()

    def teleport(self, position: Vec3, target: Vec3 | None = None) -> None:
        """Teleport the camera to a new position."""
        self.camera.teleport(position, target)

    # --- Mouse input ---

    def on_mouse_motion(self, _x: int, _y: int, dx: int, dy: int) -> None:
        """Read the mouse input and update the camera's yaw and pitch."""
        if not self._exclusive_mouse:
            return

        self.mouse_look = Vec2(dx, dy)

    def on_mouse_press(self, _x: int, _y: int, _button: int, _modifiers: int) -> None:
        """Capture the mouse input when the window is clicked."""
        if not self._exclusive_mouse:
            self._exclusive_mouse = True
            self._window.set_exclusive_mouse(True)

    # --- Keyboard input ---

    def on_key_press(self, symbol: int, _modifiers: int) -> bool:
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

    def on_key_release(self, symbol: int, _modifiers: int) -> bool:
        """Handle keyboard input release."""
        if direction := self.input_map.get(symbol):
            self.inputs[direction] = False
            forward, backward, left, right, up, down = self.inputs.values()
            self.keyboard_move = Vec2(-float(left) + float(right), float(forward) + -float(backward)).normalize()
            self._elevation = float(up) + -float(down)
            return pyglet.event.EVENT_HANDLED

        return False

    # --- Controller input ---

    def on_leftstick_motion(self, _controller: pyglet.input.Controller, vector: Vec2) -> None:
        """Right Controller stick controlls the camera position."""
        if vector.length() < self.dead_zone:
            self.controller_move = Vec2()
        else:
            self.controller_move = vector

    def on_rightstick_motion(self, _controller: pyglet.input.Controller, vector: Vec2) -> None:
        """Right Controller stick controlls the camera rotation."""
        if vector.length() >= self.dead_zone:
            self.controller_look = vector
        else:
            self.controller_look = Vec2()

    def on_lefttrigger_motion(self, _controller: pyglet.input.Controller, value: float) -> None:
        """Left trigger lowers the elevation."""
        self._elevation = -value

    def on_righttrigger_motion(self, _controller: pyglet.input.Controller, value: float) -> None:
        """Right trigger raises the elevation."""
        self._elevation = value


window = pyglet.window.Window(resizable=True)
batch = pyglet.graphics.Batch()

# These .obj files only have a single model in the scene:
logo_model = pyglet.resource.scene("logo3d.obj").create_models(batch=batch)[0]
box_model = pyglet.resource.scene("box.obj").create_models(batch=batch)[0]

# You have to make at least one instance of a model for it to appear:
box_instance = box_model.create_instance(translation=Vec3(2.0, 0.0, 0.0))

# You can make as many instances as you want, with their own translation:
logo_instances = []
for _ in range(500):
    x, y, z = random.uniform(-100, 100), random.uniform(1.0, 5.0), random.uniform(-100, 100)
    logo_instances.append(logo_model.create_instance(translation=Vec3(x, y, z)))

# Create some sphere shapes (their centers are at y==0.0):
sphere_model = pyglet.model.Sphere(4.0, color=(0.3, 0.3, 1.0, 0.3), batch=batch)
sphere_instances = []
for _ in range(500):
    x = random.uniform(-100, 100)
    y = random.uniform(1.0, 5.0)
    z = random.uniform(-100, 100)
    sphere_instances.append(sphere_model.create_instance(translation=Vec3(x, y, z)))

# Create some capsule shapes (their bottoms start at y==0.0):
capsule_model = pyglet.model.Capsule(1.0, height=3.0, batch=batch)
capsule_instances = []
for _ in range(500):
    x = random.uniform(-100, 100)
    y = random.uniform(0.0, 5.0)
    z = random.uniform(-100, 100)
    capsule_instances.append(capsule_model.create_instance(translation=Vec3(x, y, z)))

# Make a "floor", positioned so its top is at y==0.0:
floor_model = pyglet.model.Cube(width=999, height=1.0, depth=999, batch=batch)
floor_instance = floor_model.create_instance(translation=Vec3(0.0, -1.5, 0.0))

# Create the FPSCamera instance, which controls the global projection & view matrixes.
# Start with the position a bit back, and looking at the center of the scene:
# Click the window to capture the mouse. Use WASD to move, E/Q for vertical movement,
# and Esc to release the mouse or exit when the mouse is already released.
camera = FPSCamera(
    window,
    position=Vec3(0.0, 1.0, 6.0),
    target=Vec3(0.0, 1.0, 0.0),
)
controls = FPSCameraControls(window, camera)
if controllers := pyglet.input.get_controllers():
    controller = controllers[0]
    controller.open()
    controller.push_handlers(controls)

# def update(dt):
#     update.elapsed += dt
#     box_instance.rotation = Quaternion.from_rotation(0.1 * update.elapsed, Vec3(1.0, 0.0, 0.0))
# 
# 
# update.elapsed = 0.0
# 
# pyglet.clock.schedule_interval(update, 1/33)

@window.event
def on_draw() -> None:
    window.clear()
    with batch.draw_with_options() as options:
        options.camera = camera

pyglet.app.run()
