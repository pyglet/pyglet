from __future__ import annotations

import pytest

import pyglet

from pyglet.enums import GeometryMode


VERTEX_SOURCE = """#version 300 es
in vec2 position;
void main() {
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

FRAGMENT_SOURCE = """#version 300 es
precision mediump float;
uniform vec4 tint;
out vec4 final_color;
void main() {
    final_color = tint;
}
"""


def test_custom_shaders_uniforms_and_indexed_batch(webgl_window):
    vertex_shader = pyglet.graphics.Shader(VERTEX_SOURCE, "vertex")
    fragment_shader = pyglet.graphics.Shader(FRAGMENT_SOURCE, "fragment")
    program = pyglet.graphics.ShaderProgram(vertex_shader, fragment_shader)
    batch = pyglet.graphics.Batch()
    vertex_list = program.vertex_list_indexed(
        3,
        GeometryMode.TRIANGLES,
        [0, 1, 2],
        batch=batch,
        position=(-0.75, -0.75, 0.75, -0.75, 0.0, 0.75),
    )

    try:
        program["tint"] = (0.25, 0.5, 0.75, 1.0)
        assert tuple(program["tint"]) == pytest.approx((0.25, 0.5, 0.75, 1.0))
        webgl_window.clear()
        batch.draw()
    finally:
        vertex_list.delete()
        program.delete()
        vertex_shader.delete()
        fragment_shader.delete()
