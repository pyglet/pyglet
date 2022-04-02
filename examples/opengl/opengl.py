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

"""Displays a rotating torus using the pyglet.graphics API.

This example uses the pyglet.graphics API to render an indexed vertex
list. The vertex list is added to a batch, allowing easy rendered
alongside other vertex lists with minimal overhead.

This example demonstrates:

 * Setting a 3D projection on a window by overriding the default
   on_resize handler
 * Enabling multisampling if available
 * Drawing simple 3D primitives using the pyglet.graphics API
 * Fixed-pipeline lighting
"""

from math import pi, sin, cos

import pyglet
from pyglet.gl import *

try:
    # Try and create a window with multisampling (antialiasing)
    config = Config(sample_buffers=1, samples=4, depth_size=16, double_buffer=True)
    window = pyglet.window.Window(width=960, height=540, resizable=True, config=config)
except pyglet.window.NoSuchConfigException:
    # Fall back to no multisampling if not supported
    window = pyglet.window.Window(resizable=True)

# Change the window projection to 3D:
window.projection = pyglet.math.Mat4.perspective_projection(0, 960, 0, 540, z_near=0.1, z_far=255)


@window.event
def on_draw():
    window.clear()
    batch.draw()


def update(dt):
    rx, ry, rz = torus_model.rotation
    rx += dt * 1
    ry += dt * 80
    rz += dt * 30
    rx %= 360
    ry %= 360
    rz %= 360
    torus_model.rotation = rx, ry, rz


def setup():
    # One-time GL setup
    glClearColor(1, 1, 1, 1)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)

    # Uncomment this line for a wireframe view:
    # glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)


def create_torus(radius, inner_radius, slices, inner_slices, shader, batch):

    # Create the vertex and normal arrays.
    vertices = []
    normals = []

    u_step = 2 * pi / (slices - 1)
    v_step = 2 * pi / (inner_slices - 1)
    u = 0.
    for i in range(slices):
        cos_u = cos(u)
        sin_u = sin(u)
        v = 0.
        for j in range(inner_slices):
            cos_v = cos(v)
            sin_v = sin(v)

            d = (radius + inner_radius * cos_v)
            x = d * cos_u
            y = d * sin_u
            z = inner_radius * sin_v

            nx = cos_u * cos_v
            ny = sin_u * cos_v
            nz = sin_v

            vertices.extend([x, y, z])
            normals.extend([nx, ny, nz])
            v += v_step
        u += u_step

    # Create a list of triangle indices.
    indices = []
    for i in range(slices - 1):
        for j in range(inner_slices - 1):
            p = i * inner_slices + j
            indices.extend([p, p + inner_slices, p + inner_slices + 1])
            indices.extend([p, p + inner_slices + 1, p + 1])

    # Create a Material and Group for the Model
    diffuse = [0.5, 0.0, 0.3, 1.0]
    ambient = [0.5, 0.0, 0.3, 1.0]
    specular = [1.0, 1.0, 1.0, 1.0]
    emission = [0.0, 0.0, 0.0, 1.0]
    shininess = 50

    material = pyglet.model.Material("custom", diffuse, ambient, specular, emission, shininess)
    group = pyglet.model.MaterialGroup(material=material)

    vertex_list = shader.vertex_list_indexed(len(vertices)//3, GL_TRIANGLES, indices, batch, group,
                                             vertices=('f', vertices),
                                             normals=('f', normals),
                                             colors=('f', material.diffuse * (len(vertices) // 3)))

    return pyglet.model.Model([vertex_list], [group], batch)


setup()
batch = pyglet.graphics.Batch()
shader = pyglet.model.get_default_shader()


torus_model = create_torus(1, 0.3, 50, 30, shader, batch)
torus_model.translation = 0, 0, -4

pyglet.clock.schedule(update)
pyglet.app.run()
