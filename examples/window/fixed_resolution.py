#!/usr/bin/env python
"""Demonstrates one way of fixing the display resolution to a certain
size, but rendering to the full screen.

The method used in this example is:

1. Create a Framebuffer object, and a Texture of the desired resolution
2. Attach the Texture to the Framebuffer.
2. Bind the Framebuffer as the current render target.
3. Render the scene using any OpenGL functions (here, just a shape).
4. Unbind the Framebuffer, and blit the Texture scaled to fill the screen.
"""

from pyglet.gl import *
import pyglet


class FixedResolution:
    def __init__(self, window, width, height):
        self.window = window
        self.width = width
        self.height = height

        self._target_area = 0, 0, 0, 0, 0

        self.framebuffer = pyglet.image.Framebuffer()
        self.texture = pyglet.image.Texture.create(width, height, min_filter=GL_NEAREST, mag_filter=GL_NEAREST)
        self.framebuffer.attach_texture(self.texture)

        self.window.push_handlers(self)

    def on_resize(self, width, height):
        self._target_area = self._calculate_area(*self.window.get_framebuffer_size())

    def _calculate_area(self, new_screen_width, new_screen_height):
        aspect_ratio = self.width / self.height
        aspect_width = new_screen_width
        aspect_height = aspect_width / aspect_ratio + 0.5
        if aspect_height > new_screen_height:
            aspect_height = new_screen_height
            aspect_width = aspect_height * aspect_ratio + 0.5

        return (int((new_screen_width / 2) - (aspect_width / 2)),       # x
                int((new_screen_height / 2) - (aspect_height / 2)),     # y
                0,                                                      # z
                int(aspect_width),                                      # width
                int(aspect_height))                                     # height

    def __enter__(self):
        self.framebuffer.bind()
        self.window.clear()

    def __exit__(self, *unused):
        self.framebuffer.unbind()
        self.texture.blit(*self._target_area)

    def begin(self):
        self.__enter__()

    def end(self):
        self.__exit__()


###################################
# Simple program using the Viewport:
###################################

window = pyglet.window.Window(960, 540, resizable=True)

# Create an instance of the FixedResolution class. Use
# 320x180 resolution to make the effect completely obvious:
fixed_res = FixedResolution(window, width=320, height=180)


def update(dt):
    global rectangle
    rectangle.rotation += dt * 10


@window.event
def on_draw():
    window.clear()

    # The FixedResolution instance can be used as a context manager:
    with fixed_res:
        rectangle.draw()

    # # Alternatively, you can do it manually:
    # fixed_res.begin()
    # rectangle.draw()
    # fixed_res.end()


# Create a simple Rectangle to show the effect
rectangle = pyglet.shapes.Rectangle(x=160, y=90, color=(200, 50, 50), width=100, height=100)
rectangle.anchor_position = 50, 50

# Schedule the update function at 60fps
pyglet.clock.schedule_interval(update, 1/60)
pyglet.app.run()

