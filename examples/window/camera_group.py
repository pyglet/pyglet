""" Camera class similar to that of camera.py, this time implemented as a graphics Group.
Interface is much more simplified, with only a position and zoom implemented, but is easily
extended to add other features such as autoscroll.

    camera = CameraGroup(x=0, y=0, zoom=1)

    world_object = pyglet.some_renderable(batch=batch, group=camera)
    ui_object = pyglet.some_renderable(batch=batch)  # <-- Using the same batch here

    @window.event
    def on_draw():
        window.clear()
        batch.draw()  # Only one batch necessary

A centered camera class is also provided, where the position of the camera is the center of
the screen instead of the bottom left.

    centered_camera = CenteredCameraGroup(window, x=0, y=0, zoom=1)

Demo:

Use arrow keys to move the camera around the scene.
Note that everything in the window can be added to the same batch, as a group is used to
seperate things in world space from things in "UI" space.
"""

import pyglet
from pyglet.graphics import Group
from pyglet.math import Vec2



class CameraGroup(Group):
    """ Graphics group emulating the behaviour of a camera in 2D space. """

    def __init__(self, window, x, y, zoom=1.0, order=0, parent=None):
        super().__init__(order, parent)
        self._window = window
        self.x = x
        self.y = y
        self.zoom = zoom

    @property
    def position(self) -> Vec2:
        """Query the current offset."""
        return Vec2(self.x, self.y)

    @position.setter
    def position(self, new_position: Vec2):
        """Set the scroll offset directly."""
        self.x, self.y = new_position

    def set_state(self):
        """ Apply zoom and camera offset to view matrix. """

        # Translate using the offset.
        view_matrix = self._window.view.translate(-self.x * self.zoom, -self.y * self.zoom, 0)
        # Scale by zoom level.
        view_matrix = view_matrix.scale(self.zoom, self.zoom, 1)

        self._window.view = view_matrix

    def unset_state(self):
        """ Revert zoom and camera offset from view matrix. """
        # Since this is a matrix, you will need to reverse the translate after rendering otherwise
        # it will multiply the current offset every draw update pushing it further and further away.

        # Use inverse zoom to reverse zoom
        view_matrix = self._window.view.scale(1 / self.zoom, 1 / self.zoom, 1)
        # Reverse translate.
        view_matrix = view_matrix.translate(self.x * self.zoom, self.y * self.zoom, 0)

        self._window.view = view_matrix


class CenteredCameraGroup(CameraGroup):
    """ Alternative centered camera group.

    (0, 0) will be the center of the screen, as opposed to the bottom left.
    """

    def set_state(self):
        # Translate almost the same as normal, but add the center offset
        x = -self._window.width // 2 / self.zoom + self.x
        y = -self._window.height // 2 / self.zoom + self.y

        view_matrix = self._window.view.translate((-x * self.zoom, -y * self.zoom, 0))
        view_matrix = view_matrix.scale((self.zoom, self.zoom, 1))
        self._window.view = view_matrix

    def unset_state(self):

        x = -self._window.width // 2 / self.zoom + self.x
        y = -self._window.height // 2 / self.zoom + self.y

        view_matrix = self._window.view.scale((1 / self.zoom, 1 / self.zoom, 1))
        view_matrix = view_matrix.translate((x * self.zoom, y * self.zoom, 0))
        self._window.view = view_matrix


if __name__ == "__main__":
    from pyglet.window import key

    # Create a window and a batch
    window = pyglet.window.Window(resizable=True)
    batch = pyglet.graphics.Batch()

    # Key handler for movement
    keys = key.KeyStateHandler()
    window.push_handlers(keys)

    # Use centered
    camera = CenteredCameraGroup(window, 0, 0)
    # Use un-centered
    # camera = CameraGroup(0, 0)

    # Create a scene
    rect = pyglet.shapes.Rectangle(-25, -25, 50, 50, batch=batch, group=camera)
    text = pyglet.text.Label("Text works too!", x=0, y=-50, anchor_x="center", batch=batch, group=camera)

    # Create some "UI"
    ui_text = pyglet.text.Label(
        "Simply don't add to the group to make UI static (like this)",
        anchor_y="bottom", batch=batch,
    )
    position_text = pyglet.text.Label(
        "",
        x=window.width,
        anchor_x="right", anchor_y="bottom",
        batch=batch,
    )

    @window.event
    def on_draw():
        # Draw our scene
        window.clear()
        batch.draw()

    @window.event
    def on_resize(width: float, height: float):
        # Keep position text label to the right
        position_text.x = width

    def on_update(dt: float):
        # Move camera with arrow keys
        if keys[key.UP]:
            camera.y += 50*dt
        if keys[key.DOWN]:
            camera.y -= 50*dt
        if keys[key.LEFT]:
            camera.x -= 50*dt
        if keys[key.RIGHT]:
            camera.x += 50*dt

        # Update position text label
        position_text.text = repr(round(camera.position))

    # Start the demo
    pyglet.clock.schedule(on_update)
    pyglet.app.run()
