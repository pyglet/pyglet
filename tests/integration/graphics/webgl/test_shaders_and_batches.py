from __future__ import annotations

import ctypes
import struct
from typing import TYPE_CHECKING

import pytest
from unittest.mock import Mock

import pyglet

from pyglet.enums import GeometryMode

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pyglet.graphics.shader import ShaderProgram


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


@pytest.fixture
def uniform_array_program(webgl_window, request: pytest.FixtureRequest) -> Iterator[tuple[ShaderProgram, int]]:
    glsl_type, component, width = getattr(request, "param", ("float", "", 1))
    vertex = pyglet.graphics.Shader(VERTEX_SOURCE, "vertex")
    fragment = pyglet.graphics.Shader(f"""#version 300 es
        precision highp float;
        uniform {glsl_type} values[3];
        out vec4 color;
        void main() {{ color = vec4(values[0]{component}, values[1]{component}, values[2]{component}, 1.0); }}
    """, "fragment")
    program = pyglet.graphics.ShaderProgram(vertex, fragment, vertex_layout=None)
    try:
        yield program, width
    finally:
        program.stop()
        program.delete()
        vertex.delete()
        fragment.delete()


@pytest.mark.parametrize("uniform_array_program", [
    ("float", "", 1), ("vec2", ".x", 2), ("mat2", "[0][0]", 4),
], indirect=True)
@pytest.mark.parametrize(("key", "indices"), [
    (0, (0,)), (-1, (2,)), (slice(1, 3), (1, 2)), (slice(None, None, 2), (0, 2)),
])
def test_uniform_array_writes_only_selected_elements(
    webgl_window, uniform_array_program: tuple[ShaderProgram, int], key: int | slice, indices: tuple[int, ...],
) -> None:
    program, width = uniform_array_program
    original = tuple(float(i) if width == 1 else (float(i),) * width for i in (1, 2, 3))
    replacement = 9.0 if width == 1 else (9.0,) * width
    program["values"] = original
    values = program["values"]
    getter = values._gl_getter = Mock(wraps=values._gl_getter)
    program["values"][key] = (replacement,) * len(indices) if isinstance(key, slice) else replacement
    getter.assert_not_called()

    gl = webgl_window.context.gl
    for index, old_value in enumerate(original):
        location = gl.getUniformLocation(program.handle, f"values[{index}]")
        result = gl.getUniform(program.handle, location)
        actual = result if width == 1 else tuple(result)
        assert actual == (replacement if index in indices else old_value)


def test_uniform_array_slice_preserves_external_value(webgl_window, uniform_array_program: tuple[ShaderProgram, int]) -> None:
    program, _ = uniform_array_program
    program["values"] = (1.0, 2.0, 3.0)
    program.use()
    gl = webgl_window.context.gl
    location = gl.getUniformLocation(program.handle, "values[2]")
    gl.uniform1f(location, 9.0)
    program["values"][1:2] = (5.0,)
    assert program["values"][:] == (1.0, 5.0, 9.0)


@pytest.mark.parametrize(("key", "expected", "query_count"), [
    (-1, 3.0, 1), (slice(1, None), (2.0, 3.0), 2), (slice(None), (1.0, 2.0, 3.0), 3),
])
def test_uniform_array_reads_only_selected_elements(
    uniform_array_program: tuple[ShaderProgram, int],
    key: int | slice, expected: float | tuple[float, ...], query_count: int,
) -> None:
    program, _ = uniform_array_program
    program["values"] = (1.0, 2.0, 3.0)
    values = program["values"]
    getter = values._gl_getter = Mock(wraps=values._gl_getter)
    assert len(program["values"]) == 3
    getter.assert_not_called()
    assert program["values"][key] == expected
    assert getter.call_count == query_count


def test_uniform_array_get_refreshes_each_element(uniform_array_program: tuple[ShaderProgram, int]) -> None:
    program, _ = uniform_array_program
    values = program["values"]
    getter = values._gl_getter = Mock(wraps=values._gl_getter)
    assert values.get() is values
    assert getter.call_count == len(values)


def test_uniform_array_caches_element_locations(
    webgl_window, uniform_array_program: tuple[ShaderProgram, int], monkeypatch: pytest.MonkeyPatch,
) -> None:
    program, _ = uniform_array_program
    gl_spy = Mock(wraps=webgl_window.context.gl)
    monkeypatch.setattr(program["values"], "_gl", gl_spy)
    location_lookup = gl_spy.getUniformLocation

    program["values"][-1] = 1.0
    program["values"][2] = 2.0
    assert program["values"][-1] == 2.0
    location_lookup.assert_called_once()
    assert location_lookup.call_args.args[1] == "values[2]"


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
