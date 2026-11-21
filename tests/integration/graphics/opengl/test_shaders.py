from __future__ import annotations

import ctypes
import struct
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

import pyglet

from tests.annotations import skip_graphics_api, GraphicsAPIGroups

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pyglet.graphics.shader import ShaderProgram

_MATRIX_UNIFORMS = (
    ("mat2", 4),
    ("mat3", 9),
    ("mat4", 16),
    ("mat2x3", 6),
    ("mat2x4", 8),
    ("mat3x2", 6),
    ("mat3x4", 12),
    ("mat4x2", 8),
    ("mat4x3", 12),
)


def _is_gles2_context(test_window) -> bool:
    if pyglet.options.backend == "gles2":
        return True

    info = test_window.context.get_info()
    return info.get_opengl_api() == "gles2" and not info.have_version(3, 0)


def _skip_unsupported_matrix_uniform(test_window, matrix_type: str) -> None:
    # GLSL ES 1.00 (GLES2) supports only square matrices.
    if _is_gles2_context(test_window) and matrix_type not in {"mat2", "mat3", "mat4"}:
        pytest.skip(f"{matrix_type} uniform requires GLES 3.0+.")


def _build_matrix_fragment_source(test_window, matrix_decl: str, value_expr: str) -> str:
    if _is_gles2_context(test_window):
        return f"""#version 150 core
        {matrix_decl}

        void main()
        {{
            gl_FragColor = vec4({value_expr});
        }}
    """

    return f"""#version 150 core
        out vec4 final_colors;

        {matrix_decl}

        void main()
        {{
            final_colors = vec4({value_expr});
        }}
    """


def _render_program_to_pixel(program) -> bytes:
    from pyglet.graphics.api.gl import gl
    image = pyglet.image.ImageData(1, 1, 'RGBA', bytes([0, 0, 0, 255]))
    sprite = pyglet.sprite.Sprite(image, x=0, y=0, program=program)

    fb = pyglet.graphics.framebuffer.Framebuffer()
    texture = pyglet.graphics.Texture.create(1, 1)
    fb.attach_texture(texture)

    fb.bind()
    gl.glViewport(0, 0, 1, 1)
    gl.glDisable(gl.GL_DEPTH_TEST)
    gl.glDisable(gl.GL_BLEND)
    gl.glClearColor(0.0, 0.0, 0.0, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    window_block = program.uniform_blocks['WindowBlock']
    ubo = window_block.create_ubo()
    window_block.bind(ubo)
    with ubo as block:
        block.view[:] = pyglet.math.Mat4()
        block.projection[:] = pyglet.math.Mat4.orthogonal_projection(0, 1, 0, 1, -1, 1)

    sprite.draw()
    fb.unbind()
    sprite.delete()

    return texture.get_image_data().get_bytes('RGBA', 4)


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_shader_ubo_data_structure(test_window):
    """Test to make sure the Structure that is created is correct for UBO's.
    
    Includes nested structure and structure array.
    """

    vertex_source: str = """#version 150 core
        in vec3 translate;
        in vec4 colors;
        in vec3 tex_coords;
        in vec2 scale;
        in vec3 position;
        in float rotation;

        out vec4 vertex_colors;
        out vec3 texture_coords;

        uniform WindowBlock
        {
            mat4 projection;
            mat4 view;
        } window;

        mat4 m_scale = mat4(1.0);
        mat4 m_rotation = mat4(1.0);
        mat4 m_translate = mat4(1.0);

        void main()
        {
            m_scale[0][0] = scale.x;
            m_scale[1][1] = scale.y;
            m_translate[3][0] = translate.x;
            m_translate[3][1] = translate.y;
            m_translate[3][2] = translate.z;
            m_rotation[0][0] =  cos(-radians(rotation)); 
            m_rotation[0][1] =  sin(-radians(rotation));
            m_rotation[1][0] = -sin(-radians(rotation));
            m_rotation[1][1] =  cos(-radians(rotation));

            gl_Position = window.projection * window.view * m_translate * m_rotation * m_scale * vec4(position, 1.0);

            vertex_colors = colors;
            texture_coords = tex_coords;
        }
    """

    fragment_source: str = """#version 150 core
        in vec4 vertex_colors;
        in vec3 texture_coords;
        out vec4 final_colors;

        struct Within {
            vec3 position;
            vec2 second;
        };

        struct DataStruct {
            vec2 tester;
            vec4 color[3];
            Within within[4];
        };

        layout(std140) uniform EntityDataBlock {
             DataStruct data[5];
             float simple_type;
             vec2 vec_type;
        } data_struct;

        uniform sampler2D sprite_texture;

        void main()
        {
            final_colors = texture(sprite_texture, texture_coords.xy) * vertex_colors + data_struct.data[0].color[1].y;
        }
    """

    program = pyglet.graphics.ShaderProgram(
        pyglet.graphics.Shader(vertex_source, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
        vertex_layout=None,
    )

    entity_block = program.uniform_blocks['EntityDataBlock']
    ubo = entity_block.create_ubo()
    entity_block.bind(ubo)

    cls_struct = entity_block.view_cls
    test_data = (5.0, 1.0, 5125.0, 4.0)
    with ubo as block:
        block.data[0].color[1][:] = test_data
        block.simple_type = 1.0
        block.vec_type[:] = (1.0, 2.0)

        # Just test a random deep node.
        assert len(block.data[3].within[2].position[:]) == 3

    data_from_buffer = ubo.read()

    verified_structure = cls_struct.from_buffer_copy(data_from_buffer)

    assert tuple(verified_structure.data[0].color[1][:]) == test_data

    # Write to a FB to confirm the shader is actually modifying the right data.
    test_window.switch_to()
    image_data = _render_program_to_pixel(program)
    # The image should now be white. (y is 1.0)
    assert all(channel == 255 for channel in image_data)


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_shader_ubo_uses_reflected_array_and_matrix_strides(test_window) -> None:
    test_window.switch_to()
    vertex = pyglet.graphics.Shader("""#version 150 core
        void main() { gl_Position = vec4(0.0); }
    """, "vertex")
    fragment = pyglet.graphics.Shader("""#version 150 core
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


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_uniform_block_keeps_nested_struct_array_paths_distinct(test_window) -> None:
    test_window.switch_to()

    vertex = pyglet.graphics.Shader("""#version 150 core
        void main() { gl_Position = vec4(0.0); }
    """, "vertex")
    fragment = pyglet.graphics.Shader("""#version 150 core
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


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_uniform_block_struct_arrays_have_correct_strides_at_both_levels(test_window) -> None:
    from pyglet.graphics.api.gl import gl

    test_window.switch_to()
    vertex = pyglet.graphics.Shader("""#version 150 core
        void main() { gl_Position = vec4(0.0); }
    """, "vertex")
    fragment = pyglet.graphics.Shader("""#version 150 core
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
        gl_indices = (gl.GLuint * len(indices))(*indices)
        offsets = (gl.GLint * len(indices))()
        test_window.context.glGetActiveUniformsiv(
            program.handle, len(indices), gl_indices, gl.GL_UNIFORM_OFFSET, offsets,
        )
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


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_shader_ubo_matrix_data_structure(test_window):
    """Test UBO structure with matrix."""

    vertex_source: str = """#version 150 core
        in vec3 translate;
        in vec4 colors;
        in vec3 tex_coords;
        in vec2 scale;
        in vec3 position;
        in float rotation;

        out vec4 vertex_colors;
        out vec3 texture_coords;

        uniform WindowBlock
        {
            mat4 projection;
            mat4 view;
        } window;

        mat4 m_scale = mat4(1.0);
        mat4 m_rotation = mat4(1.0);
        mat4 m_translate = mat4(1.0);

        void main()
        {
            m_scale[0][0] = scale.x;
            m_scale[1][1] = scale.y;
            m_translate[3][0] = translate.x;
            m_translate[3][1] = translate.y;
            m_translate[3][2] = translate.z;
            m_rotation[0][0] =  cos(-radians(rotation)); 
            m_rotation[0][1] =  sin(-radians(rotation));
            m_rotation[1][0] = -sin(-radians(rotation));
            m_rotation[1][1] =  cos(-radians(rotation));

            gl_Position = window.projection * window.view * m_translate * m_rotation * m_scale * vec4(position, 1.0);

            vertex_colors = colors;
            texture_coords = tex_coords;
        }
    """

    fragment_source: str = """#version 150 core
        in vec4 vertex_colors;
        in vec3 texture_coords;
        out vec4 final_colors;

        struct DataStruct {
            mat4 projection[5];
            vec4 color[3];
        };

        layout(std140) uniform MatrixTest {
             DataStruct data[5];
        } data_struct;

        uniform sampler2D sprite_texture;

        void main()
        {
            float v = data_struct.data[1].projection[1][0][0];
            final_colors = texture(sprite_texture, texture_coords.xy) * vertex_colors + vec4(v);
        }
    """

    program = pyglet.graphics.ShaderProgram(
        pyglet.graphics.Shader(vertex_source, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
        vertex_layout=None,
    )

    matrix_block = program.uniform_blocks['MatrixTest']
    ubo = matrix_block.create_ubo()
    matrix_block.bind(ubo)
    cls_struct = matrix_block.view_cls

    test_data = pyglet.math.Mat4(
        1.0, 1.0, 1.0, 0.0,
        1.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    )

    with ubo as block:
        block.data[1].projection[1][:] = test_data

    data_from_buffer = ubo.read()

    verified_structure = cls_struct.from_buffer_copy(data_from_buffer)

    # Float imprecision's will become apparent, use approx instead...
    for a, b in zip(verified_structure.data[1].projection[1][:], tuple(test_data)):
        assert a == pytest.approx(b)

    # Write to a FB to confirm the shader is actually modifying the right data.
    test_window.switch_to()
    image_data = _render_program_to_pixel(program)
    # The image should now be white. (projection[1][0] is 1.0)
    assert all(channel == 255 for channel in image_data)


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_shader_uniform_block_matrix(test_window):
    vertex_source: str = """#version 150 core
        in vec3 translate;
        in vec4 colors;
        in vec3 tex_coords;
        in vec2 scale;
        in vec3 position;
        in float rotation;

        out vec4 vertex_colors;
        out vec3 texture_coords;

        uniform WindowBlock
        {
            mat4 projection;
            mat4 view;
        } window;

        mat4 m_scale = mat4(1.0);
        mat4 m_rotation = mat4(1.0);
        mat4 m_translate = mat4(1.0);

        void main()
        {
            m_scale[0][0] = scale.x;
            m_scale[1][1] = scale.y;
            m_translate[3][0] = translate.x;
            m_translate[3][1] = translate.y;
            m_translate[3][2] = translate.z;
            m_rotation[0][0] =  cos(-radians(rotation)); 
            m_rotation[0][1] =  sin(-radians(rotation));
            m_rotation[1][0] = -sin(-radians(rotation));
            m_rotation[1][1] =  cos(-radians(rotation));

            gl_Position = window.projection * window.view * m_translate * m_rotation * m_scale * vec4(position, 1.0);

            vertex_colors = colors;
            texture_coords = tex_coords;
        }
    """

    fragment_source: str = """#version 150 core
        in vec4 vertex_colors;
        in vec3 texture_coords;
        out vec4 final_colors;

        layout(std140) uniform MatrixTest {
             mat4 projection[5];
        } data_struct;

        uniform sampler2D sprite_texture;

        void main()
        {
            float v = data_struct.projection[1][0][0];
            final_colors = texture(sprite_texture, texture_coords.xy) * vertex_colors + vec4(v);
        }
    """

    program = pyglet.graphics.ShaderProgram(
        pyglet.graphics.Shader(vertex_source, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
        vertex_layout=None,
    )

    matrix_block = program.uniform_blocks['MatrixTest']
    if matrix_block.binding == 0:
        matrix_block.set_binding(1)
    ubo = matrix_block.create_ubo()
    matrix_block.bind(ubo)
    cls_struct = matrix_block.view_cls

    test_data = pyglet.math.Mat4(
        1.0, 1.0, 1.0, 1.0,
        1.0, 1.0, 1.0, 1.0,
        1.0, 1.0, 1.0, 1.0,
        1.0, 1.0, 1.0, 1.0,
    )

    with ubo as block:
        block.projection[1][:] = test_data
        assert len(block.projection) == 5

    data_from_buffer = ubo.read()

    verified_structure = cls_struct.from_buffer_copy(data_from_buffer)

    # Float imprecision's will become apparent, use approx instead...
    for a, b in zip(verified_structure.projection[1][:], tuple(test_data)):
        assert a == pytest.approx(b)

    # Write to a FB to confirm the shader is actually modifying the right data.
    test_window.switch_to()
    image_data = _render_program_to_pixel(program)
    # The image should now be white. (projection[1][0] is 1.0)
    assert all(channel == 255 for channel in image_data)


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_shader_uniform_matrix(test_window):
    vertex_source: str = """#version 150 core
        in vec3 translate;
        in vec4 colors;
        in vec3 tex_coords;
        in vec2 scale;
        in vec3 position;
        in float rotation;

        out vec4 vertex_colors;
        out vec3 texture_coords;

        uniform WindowBlock
        {
            mat4 projection;
            mat4 view;
        } window;

        mat4 m_scale = mat4(1.0);
        mat4 m_rotation = mat4(1.0);
        mat4 m_translate = mat4(1.0);

        void main()
        {
            m_scale[0][0] = scale.x;
            m_scale[1][1] = scale.y;
            m_translate[3][0] = translate.x;
            m_translate[3][1] = translate.y;
            m_translate[3][2] = translate.z;
            m_rotation[0][0] =  cos(-radians(rotation)); 
            m_rotation[0][1] =  sin(-radians(rotation));
            m_rotation[1][0] = -sin(-radians(rotation));
            m_rotation[1][1] =  cos(-radians(rotation));

            gl_Position = window.projection * window.view * m_translate * m_rotation * m_scale * vec4(position, 1.0);

            vertex_colors = colors;
            texture_coords = tex_coords;
        }
    """

    fragment_source: str = """#version 150 core
        in vec4 vertex_colors;
        in vec3 texture_coords;
        out vec4 final_colors;

        uniform mat4 matrix_uniform;

        uniform sampler2D sprite_texture;

        void main()
        {
            final_colors = texture(sprite_texture, texture_coords.xy) * vertex_colors + matrix_uniform[1];
        }
    """

    program = pyglet.graphics.ShaderProgram(
        pyglet.graphics.Shader(vertex_source, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
        vertex_layout=None,
    )
    test_data = pyglet.math.Mat4.orthogonal_projection(0, 800, 0, 600, -255, 255)

    with program:
        program['matrix_uniform'] = tuple(test_data)

    with program:
        fetched_data = program['matrix_uniform']

    # Float imprecision's will become apparent, use approx instead...
    for a, b in zip(fetched_data, tuple(test_data)):
        assert a == pytest.approx(b, abs=1e-06)


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_shader_uniform_matrix_array(test_window):
    vertex_source: str = """#version 150 core
        in vec3 translate;
        in vec4 colors;
        in vec3 tex_coords;
        in vec2 scale;
        in vec3 position;
        in float rotation;

        out vec4 vertex_colors;
        out vec3 texture_coords;

        uniform WindowBlock
        {
            mat4 projection;
            mat4 view;
        } window;

        mat4 m_scale = mat4(1.0);
        mat4 m_rotation = mat4(1.0);
        mat4 m_translate = mat4(1.0);

        void main()
        {
            m_scale[0][0] = scale.x;
            m_scale[1][1] = scale.y;
            m_translate[3][0] = translate.x;
            m_translate[3][1] = translate.y;
            m_translate[3][2] = translate.z;
            m_rotation[0][0] =  cos(-radians(rotation)); 
            m_rotation[0][1] =  sin(-radians(rotation));
            m_rotation[1][0] = -sin(-radians(rotation));
            m_rotation[1][1] =  cos(-radians(rotation));

            gl_Position = window.projection * window.view * m_translate * m_rotation * m_scale * vec4(position, 1.0);

            vertex_colors = colors;
            texture_coords = tex_coords;
        }
    """

    fragment_source: str = """#version 150 core
        in vec4 vertex_colors;
        in vec3 texture_coords;
        out vec4 final_colors;

        uniform mat4 matrice_array[25];

        uniform sampler2D sprite_texture;

        void main()
        {
            final_colors = texture(sprite_texture, texture_coords.xy) * vertex_colors + matrice_array[18][0];
        }
    """

    program = pyglet.graphics.ShaderProgram(
        pyglet.graphics.Shader(vertex_source, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
        vertex_layout=None,
    )
    test_data = pyglet.math.Mat4.orthogonal_projection(0, 800, 0, 600, -255, 255)

    with program:
        # Set test data
        program['matrice_array'][18] = tuple(test_data)

    with program:
        # fetch from uniform itself.
        fetched_data = program['matrice_array'].get()

    # Float imprecision's will become apparent, use approx instead...
    for a, b in zip(fetched_data[18], tuple(test_data)):
        assert a == pytest.approx(b)


@pytest.fixture
def uniform_array_program(test_window, request: pytest.FixtureRequest) -> Iterator[tuple[ShaderProgram, int]]:
    glsl_type, component, width = getattr(request, "param", ("float", "", 1))
    test_window.switch_to()
    vertex = pyglet.graphics.Shader("""#version 150 core
        void main() { gl_Position = vec4(0.0); }
    """, "vertex")
    fragment = pyglet.graphics.Shader(f"""#version 150 core
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


@skip_graphics_api(GraphicsAPIGroups.GL2)
@pytest.mark.parametrize("uniform_array_program", [
    ("float", "", 1), ("vec2", ".x", 2), ("mat2", "[0][0]", 4),
], indirect=True)
@pytest.mark.parametrize(("key", "indices"), [
    (0, (0,)), (-1, (2,)), (slice(1, 3), (1, 2)), (slice(None, None, 2), (0, 2)),
])
def test_uniform_array_writes_only_selected_elements(
    test_window, uniform_array_program: tuple[ShaderProgram, int], key: int | slice, indices: tuple[int, ...],
) -> None:
    program, width = uniform_array_program
    original = tuple(float(i) if width == 1 else (float(i),) * width for i in (1, 2, 3))
    replacement = 9.0 if width == 1 else (9.0,) * width
    program["values"] = original
    values = program["values"]
    getter = values._gl_getter = Mock(wraps=values._gl_getter)
    program["values"][key] = (replacement,) * len(indices) if isinstance(key, slice) else replacement
    getter.assert_not_called()

    ctx = test_window.context
    for index, old_value in enumerate(original):
        location = ctx.glGetUniformLocation(program.handle, f"values[{index}]".encode())
        result = (ctypes.c_float * width)()
        ctx.glGetUniformfv(program.handle, location, result)
        actual = result[0] if width == 1 else tuple(result)
        assert actual == (replacement if index in indices else old_value)


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_uniform_array_slice_preserves_external_value(test_window, uniform_array_program: tuple[ShaderProgram, int]) -> None:
    program, _ = uniform_array_program
    program["values"] = (1.0, 2.0, 3.0)
    program.use()
    ctx = test_window.context
    location = ctx.glGetUniformLocation(program.handle, b"values[2]")
    ctx.glUniform1fv(location, 1, (ctypes.c_float * 1)(9.0))
    program["values"][1:2] = (5.0,)
    assert program["values"][:] == (1.0, 5.0, 9.0)


@skip_graphics_api(GraphicsAPIGroups.GL2)
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


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_uniform_array_get_refreshes_each_element(uniform_array_program: tuple[ShaderProgram, int]) -> None:
    program, _ = uniform_array_program
    values = program["values"]
    getter = values._gl_getter = Mock(wraps=values._gl_getter)
    assert values.get() is values
    assert getter.call_count == len(values)


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_uniform_array_caches_element_locations(
    test_window, uniform_array_program: tuple[ShaderProgram, int], monkeypatch: pytest.MonkeyPatch,
) -> None:
    program, _ = uniform_array_program
    ctx = test_window.context
    location_lookup = Mock(wraps=ctx.glGetUniformLocation)
    monkeypatch.setattr(ctx, "glGetUniformLocation", location_lookup)

    program["values"][-1] = 1.0
    program["values"][2] = 2.0
    assert program["values"][-1] == 2.0
    location_lookup.assert_called_once()
    assert location_lookup.call_args.args[1].value == b"values[2]"


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_shader_uniform_float_array(test_window):
    vertex_source: str = """#version 150 core
        in vec3 translate;
        in vec4 colors;
        in vec3 tex_coords;
        in vec2 scale;
        in vec3 position;
        in float rotation;

        out vec4 vertex_colors;
        out vec3 texture_coords;

        uniform WindowBlock
        {
            mat4 projection;
            mat4 view;
        } window;

        mat4 m_scale = mat4(1.0);
        mat4 m_rotation = mat4(1.0);
        mat4 m_translate = mat4(1.0);

        void main()
        {
            m_scale[0][0] = scale.x;
            m_scale[1][1] = scale.y;
            m_translate[3][0] = translate.x;
            m_translate[3][1] = translate.y;
            m_translate[3][2] = translate.z;
            m_rotation[0][0] =  cos(-radians(rotation)); 
            m_rotation[0][1] =  sin(-radians(rotation));
            m_rotation[1][0] = -sin(-radians(rotation));
            m_rotation[1][1] =  cos(-radians(rotation));

            gl_Position = window.projection * window.view * m_translate * m_rotation * m_scale * vec4(position, 1.0);

            vertex_colors = colors;
            texture_coords = tex_coords;
        }
    """

    fragment_source: str = """#version 150 core
        in vec4 vertex_colors;
        in vec3 texture_coords;
        out vec4 final_colors;

        uniform float float_array[15];

        uniform sampler2D sprite_texture;

        void main()
        {
            final_colors = texture(sprite_texture, texture_coords.xy) * vertex_colors + float_array[11];
        }
    """

    program = pyglet.graphics.ShaderProgram(
        pyglet.graphics.Shader(vertex_source, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
        vertex_layout=None,
    )
    test_data = 25.5

    with program:
        # Set test data
        program['float_array'][11] = test_data

    with program:
        # fetch from uniform itself.
        fetched_data = program['float_array'][11]

    assert test_data == fetched_data


@pytest.mark.parametrize(("matrix_type", "matrix_length"), _MATRIX_UNIFORMS)
def test_shader_uniform_matrix_types(test_window, matrix_type, matrix_length):
    test_window.switch_to()
    _skip_unsupported_matrix_uniform(test_window, matrix_type)

    vertex_source: str = """#version 150 core
        void main()
        {
            gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
        }
    """

    fragment_source: str = _build_matrix_fragment_source(
        test_window,
        f"uniform {matrix_type} matrix_uniform;",
        "matrix_uniform[0][0]",
    )

    program = pyglet.graphics.ShaderProgram(
        pyglet.graphics.Shader(vertex_source, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
        vertex_layout=None,
    )

    test_data = tuple((index + 1) / 10.0 for index in range(matrix_length))

    with program:
        program['matrix_uniform'] = test_data
        fetched_data = program['matrix_uniform']

    assert len(fetched_data) == matrix_length
    for actual, expected in zip(fetched_data, test_data):
        assert actual == pytest.approx(expected, abs=1e-06)


@pytest.mark.parametrize(("matrix_type", "matrix_length"), _MATRIX_UNIFORMS)
def test_shader_uniform_matrix_array_types(test_window, matrix_type, matrix_length):
    test_window.switch_to()
    _skip_unsupported_matrix_uniform(test_window, matrix_type)

    vertex_source: str = """#version 150 core
        void main()
        {
            gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
        }
    """

    fragment_source: str = _build_matrix_fragment_source(
        test_window,
        f"uniform {matrix_type} matrix_uniform[4];",
        "matrix_uniform[2][0][0]",
    )

    program = pyglet.graphics.ShaderProgram(
        pyglet.graphics.Shader(vertex_source, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
        vertex_layout=None,
    )

    test_data = tuple((index + 1) / 10.0 for index in range(matrix_length))

    with program:
        program['matrix_uniform'][2] = test_data
        fetched_data = program['matrix_uniform'].get()

    assert len(fetched_data[2]) == matrix_length
    for actual, expected in zip(fetched_data[2], test_data):
        assert actual == pytest.approx(expected, abs=1e-06)


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_transform_feedback_shader_program_varyings_are_linked(test_window):
    vertex_source = """#version 150 core
        in vec3 position;
        out vec3 tf_position;

        void main()
        {
            gl_Position = vec4(position, 1.0);
            tf_position = position;
        }
    """

    fragment_source = """#version 150 core
        out vec4 final_colors;

        void main()
        {
            final_colors = vec4(1.0);
        }
    """

    program = pyglet.graphics.TransformFeedbackShaderProgram(
        pyglet.graphics.Shader(vertex_source, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
        varyings=["tf_position"],
        vertex_layout=None,
    )

    from pyglet.graphics.api.gl import gl

    link_status = gl.GLint(0)
    tf_count = gl.GLint(0)
    ctx = pyglet.graphics.api.core.current_context
    ctx.glGetProgramiv(program.handle, gl.GL_LINK_STATUS, link_status)
    ctx.glGetProgramiv(program.handle, gl.GL_TRANSFORM_FEEDBACK_VARYINGS, tf_count)
    link_status = link_status.value
    tf_count = tf_count.value

    assert link_status == 1
    assert tf_count == 1
