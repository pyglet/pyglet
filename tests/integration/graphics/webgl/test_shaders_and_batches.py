from __future__ import annotations

import pytest
from unittest.mock import Mock

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


@pytest.mark.parametrize('resource_type, delete_method', [
    ('WebGLShader', 'deleteShader'),
    ('WebGLShaderProgram', 'deleteProgram'),
])
def test_shader_resource_cleanup(webgl_window, resource_type: str, delete_method: str) -> None:
    from pyglet.graphics.api.webgl import shader

    resource = object.__new__(getattr(shader, resource_type))
    handle = object()
    resource._id = resource._handle = handle
    resource._context = webgl_window.context
    resource._gl = Mock()
    resource.shader_type = 'vertex'

    resource.__del__()

    getattr(resource._gl, delete_method).assert_called_once_with(handle)
    assert resource._id is None
    assert resource.handle is None


def test_missing_uniform_array_location(webgl_window) -> None:
    from pyglet.graphics.api.webgl.shader import _UniformArray
    from pyglet.graphics.shader import ShaderException

    array = object.__new__(_UniformArray)
    array._gl = Mock()
    array._gl.getUniformLocation.return_value = None
    array._uniform = Mock(name='uniform')

    with pytest.raises(ShaderException, match='not found'):
        array._get_location_for_index(0)


def test_custom_shaders_uniforms_and_indexed_batch(webgl_window):
    vertex_shader = pyglet.graphics.Shader(VERTEX_SOURCE, "vertex")
    fragment_shader = pyglet.graphics.Shader(FRAGMENT_SOURCE, "fragment")
    program = pyglet.graphics.ShaderProgram(vertex_shader, fragment_shader, vertex_layout=None)
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
