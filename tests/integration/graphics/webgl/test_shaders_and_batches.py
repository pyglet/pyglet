from __future__ import annotations

import ctypes
import struct
from typing import TYPE_CHECKING

import pytest
from unittest.mock import Mock

import pyglet

from pyglet.enums import GeometryMode

if TYPE_CHECKING:
    from pyglet.graphics.api.webgl.webgl_js import WebGLUniformLocation


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


@pytest.mark.parametrize(("glsl_type", "component", "width"), [
    ("float", "", 1), ("vec2", ".x", 2), ("mat2", "[0][0]", 4),
])
def test_uniform_array_base_reads_and_writes_shader_values(
    webgl_window, glsl_type: str, component: str, width: int,
) -> None:
    from pyodide.ffi import to_js

    vertex = pyglet.graphics.Shader(VERTEX_SOURCE, "vertex")
    fragment = pyglet.graphics.Shader(f"""#version 300 es
        precision highp float;
        uniform {glsl_type} values[3];
        out vec4 color;
        void main() {{ color = vec4(values[0]{component}, values[1]{component}, values[2]{component}, 1.0); }}
    """, "fragment")
    program = pyglet.graphics.ShaderProgram(vertex, fragment, vertex_layout=None)
    try:
        initial = tuple(float(i) if width == 1 else (float(i),) * width for i in (1, 2, 3))
        program["values"] = initial
        values = program["values"]
        assert len(values) == 3
        assert tuple(values[:]) == initial

        first, second, last = (float(i) if width == 1 else (float(i),) * width for i in (4, 5, 6))
        ctx = webgl_window.context

        def location_for(index: int) -> WebGLUniformLocation:
            location = ctx.gl.getUniformLocation(program.handle, f"values[{index}]")
            assert location is not None
            return location

        def read_shader_values() -> tuple[float | tuple[float, ...], ...]:
            actual = []
            for index in range(3):
                location = location_for(index)
                value = ctx.gl.getUniform(program.handle, location)
                actual.append(value if width == 1 else tuple(value))
            return tuple(actual)

        assert read_shader_values() == initial
        values[0] = first
        assert read_shader_values() == (first, initial[1], initial[2])
        values[-1] = last
        assert read_shader_values() == (first, initial[1], last)
        values[1:2] = (second,)
        assert read_shader_values() == (first, second, last)

        # Change a nonzero element through the backend and check that get() reads it back.
        program.use()
        location = location_for(2)
        if width == 1:
            ctx.gl.uniform1f(location, 9.0)
        elif width == 2:
            ctx.gl.uniform2fv(location, to_js([9.0] * width))
        else:
            ctx.gl.uniformMatrix2fv(location, False, to_js([9.0] * width))
        assert values.get()[-1] == (9.0 if width == 1 else (9.0,) * width)
    finally:
        program.stop()
        program.delete()
        vertex.delete()
        fragment.delete()


def test_uniform_block_uses_reflected_array_and_matrix_strides(webgl_window) -> None:
    vertex = pyglet.graphics.Shader(VERTEX_SOURCE, "vertex")
    fragment = pyglet.graphics.Shader("""#version 300 es
        precision highp float;
        layout(std140) uniform StrideBlock {
            float values[2];
            mat3 matrices[2];
            layout(row_major) mat2x3 row_matrix;
            mat4 tight_matrix;
        };
        out vec4 color;
        void main() { color = vec4(values[1], matrices[1][2][1], row_matrix[1][2], tight_matrix[0][0]); }
    """, "fragment")
    program = pyglet.graphics.ShaderProgram(vertex, fragment, vertex_layout=None)
    try:
        block = program.uniform_blocks["StrideBlock"]
        data = block.view_cls()
        data.values[:] = (1.0, 2.0)
        data.matrices[1][:] = range(3, 12)
        data.row_matrix[:] = range(12, 18)
        assert type(data.tight_matrix) is ctypes.c_float * 16

        raw = bytes(data)
        assert len(raw) == block.size == 240
        assert struct.unpack_from("=f", raw, 16) == (2.0,)
        assert struct.unpack_from("=3f", raw, 80) == (3.0, 4.0, 5.0)
        assert struct.unpack_from("=3f", raw, 112) == (9.0, 10.0, 11.0)
        assert struct.unpack_from("=2f", raw, 128) == (12.0, 15.0)
        assert struct.unpack_from("=2f", raw, 160) == (14.0, 17.0)
    finally:
        program.delete()
        vertex.delete()
        fragment.delete()


def test_uniform_block_keeps_nested_struct_array_paths_distinct(webgl_window) -> None:

    vertex = pyglet.graphics.Shader(VERTEX_SOURCE, "vertex")
    fragment = pyglet.graphics.Shader("""#version 300 es
        precision highp float;
        struct Entry { float value; };
        struct Left { Entry items[2]; };
        struct Right { Entry items[3]; };
        layout(std140) uniform NestedArrays {
            Left lhs;
            Right rhs;
            float tail;
        };
        out vec4 color;
        void main() { color = vec4(lhs.items[1].value, rhs.items[2].value, tail, 1.0); }
    """, "fragment")
    program = pyglet.graphics.ShaderProgram(vertex, fragment, vertex_layout=None)
    try:
        block = program.uniform_blocks["NestedArrays"]
        data = block.view_cls()
        assert len(data.lhs.items) == 2
        assert len(data.rhs.items) == 3
        data.lhs.items[1].value = 1.0
        data.rhs.items[2].value = 2.0
        data.tail = 3.0

        raw = bytes(data)
        assert len(raw) == block.size
        assert struct.unpack_from("=f", raw, 16) == (1.0,)
        assert struct.unpack_from("=f", raw, 64) == (2.0,)
        assert struct.unpack_from("=f", raw, 80) == (3.0,)
    finally:
        program.delete()
        vertex.delete()
        fragment.delete()


def test_uniform_block_struct_arrays_have_correct_strides_at_both_levels(webgl_window) -> None:
    from pyodide.ffi import to_js

    vertex = pyglet.graphics.Shader(VERTEX_SOURCE, "vertex")
    fragment = pyglet.graphics.Shader("""#version 300 es
        precision highp float;
        struct Inner { vec3 position; vec2 uv; };
        struct Outer { float kind; Inner entries[3]; float marker; };
        layout(std140) uniform NestedStrides {
            Outer groups[2];
            float tail;
        };
        out vec4 color;
        void main() {
            color = vec4(groups[0].entries[0].uv.x, groups[0].entries[1].uv.x,
                         groups[1].entries[0].uv.x, groups[1].entries[2].uv.x + tail);
        }
    """, "fragment")
    program = pyglet.graphics.ShaderProgram(vertex, fragment, vertex_layout=None)
    try:
        block = program.uniform_blocks["NestedStrides"]
        indices_by_name = {uniform[0]: index for index, uniform in block.uniforms.items()}
        indices = [indices_by_name[name] for name in (
            "groups[0].entries[0].uv", "groups[0].entries[1].uv",
            "groups[1].entries[0].uv", "groups[1].entries[2].uv", "tail",
        )]
        browser_gl = webgl_window.context.gl
        offsets = list(browser_gl.getActiveUniforms(program.handle, to_js(indices), browser_gl.UNIFORM_OFFSET))
        assert tuple(offsets) == (32, 64, 160, 224, 256)

        data = block.view_cls()
        assert len(data.groups) == 2
        assert len(data.groups[0].entries) == 3
        assert ctypes.sizeof(data.groups[0].entries[0]) == offsets[1] - offsets[0] == 32
        assert ctypes.sizeof(data.groups[0]) == offsets[2] - offsets[0] == 128

        data.groups[0].entries[0].uv[0] = 1.0
        data.groups[1].entries[2].uv[0] = 2.0
        data.tail = 3.0
        raw = bytes(data)
        assert len(raw) == block.size
        assert struct.unpack_from("=f", raw, offsets[0]) == (1.0,)
        assert struct.unpack_from("=f", raw, offsets[3]) == (2.0,)
        assert struct.unpack_from("=f", raw, offsets[4]) == (3.0,)
    finally:
        program.delete()
        vertex.delete()
        fragment.delete()
