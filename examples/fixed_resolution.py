#!/usr/bin/env python
# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------
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

        self.framebuffer = pyglet.image.buffer.Framebuffer()
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
viewport = FixedResolution(window, width=320, height=180)


def update(dt):
    global rectangle
    rectangle.rotation += dt * 10


@window.event
def on_draw():
    window.clear()

    # The viewport can be used as a context manager:
    with viewport:
        rectangle.draw()

    # # Alternatively, you can do it manually:
    # viewport.begin()
    # rectangle.draw()
    # viewport.end()


# Create a simple Rectangle to show the effect
rectangle = pyglet.shapes.Rectangle(x=160, y=90, color=(200, 50, 50), width=100, height=100)
rectangle.anchor_position = 50, 50

# Schedule the update function at 60fps
pyglet.clock.schedule_interval(update, 1/60)
pyglet.app.run()

