#!/usr/bin/env python
"""Demonstrates one way of fixing the display resolution to a certain
size, but rendering to the full screen.

The method used in this example is:

1. Create a Framebuffer object, a Texture, and a depth buffer.
2. Attach the Texture and depth buffer to the Framebuffer.
3. Bind the Framebuffer as the current render target.
4. Render the scene using any OpenGL functions (here, just a shape).
5. Unbind the Framebuffer, and blit the Texture scaled to fill the screen.
"""

from math import floor

import pyglet

from pyglet.enums import TextureFilter, FramebufferAttachment, ComponentFormat
from pyglet.graphics import Texture, Renderbuffer, Framebuffer


class FixedResolution:
    def __init__(self, window, width, height):
        self.window = window
        self.window.set_minimum_size(width, height)
        self.width = width
        self.height = height

        self._mouse_scaling = 0, 0, 1.0, 1.0

        self.framebuffer = Framebuffer(context=window.context)
        # Use a Texture for the Color Buffer:
        self._color_buffer = Texture.create(width, height, filters=TextureFilter.NEAREST)
        self.framebuffer.attach_texture(self._color_buffer)
        # Use a RenderBuffer for the Depth Buffer:
        self._depth_buffer = Renderbuffer(window.context, width, height,
                                          component_format=ComponentFormat.D, bit_size=24)
        self.framebuffer.attach_renderbuffer(self._depth_buffer,
                                             attachment=FramebufferAttachment.DEPTH)

        # Use a Sprite to render the Color Buffer Texture:
        self._sprite = pyglet.sprite.Sprite(self._color_buffer)
        self.window.push_handlers(self)

    def get_mouse_scale(self, x, y, dx, dy):
        offset_x, offset_y, scale_w, scale_h = self._mouse_scaling
        scaled_x = floor((x - offset_x) * scale_w)
        scaled_y = floor((y - offset_y) * scale_h)
        scaled_dx = floor(dx * scale_w)
        scaled_dy = floor(dy * scale_h)
        return scaled_x, scaled_y, scaled_dx, scaled_dy

    def on_resize(self, new_screen_width, new_screen_height):
        """Calculate the various scaling values when resizing the window.

        This method is a bit complex, because it also includes math for
        maintaining the image aspect ratio.  The technique used here will
        add pillar or letter boxes to the edges of the image when necessary.
        There are other techniques, such as allowing the image to maintain
        fixed width or height, but this is one popular method.
        """
        aspect_ratio = self.width / self.height
        aspect_width = new_screen_width
        aspect_height = aspect_width / aspect_ratio + 0.5
        if aspect_height > new_screen_height:
            aspect_height = new_screen_height
            aspect_width = aspect_height * aspect_ratio + 0.5

        offset_x = int((new_screen_width / 2) - (aspect_width / 2))
        offset_y = int((new_screen_height / 2) - (aspect_height / 2))
        render_width = int(aspect_width)
        render_height = int(aspect_height)

        # Reposition and scale the Sprite:
        self._sprite.position = offset_x, offset_y, 0
        self._sprite.scale_x = render_width / self.width
        self._sprite.scale_y = render_height / self.height

        # Calculate values used by mouse scaling:
        width_scale = self.width / new_screen_width
        height_scale = self.height / new_screen_height
        # When resizing beyond the original aspect ratio:
        pillar_scale = new_screen_width / render_width
        letter_scale = new_screen_height / render_height
        # Base scaling values as used by the ``get_mouse_scale`` method:
        self._mouse_scaling = offset_x, offset_y, width_scale * pillar_scale, height_scale * letter_scale

    def __enter__(self):
        self.framebuffer.bind()
        self.window.clear()

    def __exit__(self, *unused):
        self.framebuffer.unbind()
        self._sprite.draw()

    def begin(self):
        self.__enter__()

    def end(self):
        self.__exit__()


###################################
# Simple program using the Viewport:
###################################

if __name__ == '__main__':
    window = pyglet.window.Window(960, 540, resizable=True)

    # Create an instance of the FixedResolution class. Use
    # 320x180 resolution to make the effect completely obvious:
    fixed_res = FixedResolution(window, width=320, height=180)


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

    # Combine update & drawing to avoid stutter from mismatched update rates
    def update(dt):
        rectangle.rotation += dt * 10
        # This method automatically calls any on_draw method registered
        # using @window.event, as we did above.
        window.draw(dt)


    # Create a simple Rectangle to show the effect
    rectangle = pyglet.shapes.Rectangle(x=160, y=90, color=(200, 50, 50), width=100, height=100)
    rectangle.anchor_position = 50, 50

    # Call the combined update & redraw function at ~60 FPS
    pyglet.clock.schedule_interval(update, 1/60)

    # Start the application loop. Pass None, since we're scheduling our own draw calls above.
    pyglet.app.run(None)
