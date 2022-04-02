import pyglet

"""Camera class for easy scrolling and zooming.

A simple example of a Camera class that can be used to easily scroll and
zoom when rendering. For example, you might have a playfield that needs  
to scroll and/or zoom, and a GUI layer that will remain static. For that
scenario, you can create two Camera instances. You can optionally set
the minimum allowed zoom, maximum allowed zoom, and scrolling speed::

    world_camera = Camera(scroll_speed=5, min_zoom=1, max_zoom=4)
    gui_camera = Camera()

After creating Camera instances, the zoom can be easily updated. It will
clamp to the `max_zoom` parameter (default of 4)::

    world_camera.zoom += 1

The scrolling can be set in two different ways. Directly with the
`Camera.position attribute, which can be set with a tuple of absolute
x, y values::

    world_camera.position = 50, 0

Or, it can be updated incrementally with the `Camera.move(x, y)` method.
This will update the camera position by multiplying the passed vector by
the `Camera.scroll_speed` parameter, which can be set on instantiation. 

    world_camera.move(1, 0)
    # If the world_camera.scroll_speed is "5", this will move the camera
    # by 5 pixels right on the x axis. 


During your `Window.on_draw` event, you can set the Camera, and draw the
appropriate objects. For convenience, the Camera class can act as a context
manager, allowing easy use of "with"::

    @window.event
    def on_draw():
        window.clear()
    
        # Draw your world scene using the world camera
        with world_camera:
            batch.draw()
    
        # Can also be written as:
        # camera.begin()
        # batch.draw()
        # camera.end()
    
        # Draw your GUI elements with the GUI camera.
        with gui_camera:
            label.draw()

"""


class Camera:
    """ A simple 2D camera that contains the speed and offset."""

    def __init__(self, window: pyglet.window.Window, scroll_speed=1, min_zoom=1, max_zoom=4):
        assert min_zoom <= max_zoom, "Minimum zoom must not be greater than maximum zoom"
        self._window = window
        self.scroll_speed = scroll_speed
        self.max_zoom = max_zoom
        self.min_zoom = min_zoom
        self.offset_x = 0
        self.offset_y = 0
        self._zoom = max(min(1, self.max_zoom), self.min_zoom)

    @property
    def zoom(self):
        return self._zoom

    @zoom.setter
    def zoom(self, value):
        """ Here we set zoom, clamp value to minimum of min_zoom and max of max_zoom."""
        self._zoom = max(min(value, self.max_zoom), self.min_zoom)

    @property
    def position(self):
        """Query the current offset."""
        return self.offset_x, self.offset_y

    @position.setter
    def position(self, value):
        """Set the scroll offset directly."""
        self.offset_x, self.offset_y = value

    def move(self, axis_x, axis_y):
        """ Move axis direction with scroll_speed.
            Example: Move left -> move(-1, 0)
         """
        self.offset_x += self.scroll_speed * axis_x
        self.offset_y += self.scroll_speed * axis_y

    def begin(self):
        # Set the current camera offset so you can draw your scene.

        # Translate using the offset.
        view_matrix = self._window.view.translate((-self.offset_x * self._zoom, -self.offset_y * self._zoom, 0))
        # Scale by zoom level.
        view_matrix = view_matrix.scale((self._zoom, self._zoom, 1))

        self._window.view = view_matrix

    def end(self):
        # Since this is a matrix, you will need to reverse the translate after rendering otherwise
        # it will multiply the current offset every draw update pushing it further and further away.

        # Reverse scale, since that was the last transform.
        view_matrix = self._window.view.scale((1 / self._zoom, 1 / self._zoom, 1))
        # Reverse translate.
        view_matrix = view_matrix.translate((self.offset_x * self._zoom, self.offset_y * self._zoom, 0))

        self._window.view = view_matrix

    def __enter__(self):
        self.begin()

    def __exit__(self, exception_type, exception_value, traceback):
        self.end()


class CenteredCamera(Camera):
    """A simple 2D camera class. 0, 0 will be the center of the screen, as opposed to the bottom left."""

    def begin(self):
        x = -self._window.width // 2 / self._zoom + self.offset_x
        y = -self._window.height // 2 / self._zoom + self.offset_y

        view_matrix = self._window.view.translate((-x * self._zoom, -y * self._zoom, 0))
        view_matrix = view_matrix.scale((self._zoom, self._zoom, 1))
        self._window.view = view_matrix

    def end(self):
        x = -self._window.width // 2 / self._zoom + self.offset_x
        y = -self._window.height // 2 / self._zoom + self.offset_y

        view_matrix = self._window.view.scale((1 / self._zoom, 1 / self._zoom, 1))
        view_matrix = view_matrix.translate((x * self._zoom, y * self._zoom, 0))
        self._window.view = view_matrix

