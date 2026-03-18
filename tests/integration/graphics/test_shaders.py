import pytest

import pyglet

from tests.annotations import skip_graphics_api, GraphicsAPI

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


@skip_graphics_api(GraphicsAPI.GL2)
def test_shader_ubo_data_structure(gl3_context):
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
    gl3_context.switch_to()
    image_data = _render_program_to_pixel(program)
    # The image should now be white. (y is 1.0)
    assert all(channel == 255 for channel in image_data)


@skip_graphics_api(GraphicsAPI.GL2)
def test_shader_ubo_matrix_data_structure(gl3_context):
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
    gl3_context.switch_to()
    image_data = _render_program_to_pixel(program)
    # The image should now be white. (projection[1][0] is 1.0)
    assert all(channel == 255 for channel in image_data)


@skip_graphics_api(GraphicsAPI.GL2)
def test_shader_uniform_block_matrix(gl3_context):
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
    gl3_context.switch_to()
    image_data = _render_program_to_pixel(program)
    # The image should now be white. (projection[1][0] is 1.0)
    assert all(channel == 255 for channel in image_data)


@skip_graphics_api(GraphicsAPI.GL2)
def test_shader_uniform_matrix(gl3_context):
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
    )
    test_data = pyglet.math.Mat4.orthogonal_projection(0, 800, 0, 600, -255, 255)

    with program:
        program['matrix_uniform'] = tuple(test_data)

    with program:
        fetched_data = program['matrix_uniform']

    # Float imprecision's will become apparent, use approx instead...
    for a, b in zip(fetched_data, tuple(test_data)):
        assert a == pytest.approx(b, abs=1e-06)


@skip_graphics_api(GraphicsAPI.GL2)
def test_shader_uniform_matrix_array(gl3_context):
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


@skip_graphics_api(GraphicsAPI.GL2)
def test_shader_uniform_float_array(gl3_context):
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
def test_shader_uniform_matrix_types(gl3_context, matrix_type, matrix_length):
    gl3_context.switch_to()

    vertex_source: str = """#version 150 core
        void main()
        {
            gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
        }
    """

    fragment_source: str = f"""#version 150 core
        out vec4 final_colors;

        uniform {matrix_type} matrix_uniform;

        void main()
        {{
            final_colors = vec4(matrix_uniform[0][0]);
        }}
    """

    program = pyglet.graphics.ShaderProgram(
        pyglet.graphics.Shader(vertex_source, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
    )

    test_data = tuple((index + 1) / 10.0 for index in range(matrix_length))

    with program:
        program['matrix_uniform'] = test_data
        fetched_data = program['matrix_uniform']

    assert len(fetched_data) == matrix_length
    for actual, expected in zip(fetched_data, test_data):
        assert actual == pytest.approx(expected, abs=1e-06)


@pytest.mark.parametrize(("matrix_type", "matrix_length"), _MATRIX_UNIFORMS)
def test_shader_uniform_matrix_array_types(gl3_context, matrix_type, matrix_length):
    gl3_context.switch_to()

    vertex_source: str = """#version 150 core
        void main()
        {
            gl_Position = vec4(0.0, 0.0, 0.0, 1.0);
        }
    """

    fragment_source: str = f"""#version 150 core
        out vec4 final_colors;

        uniform {matrix_type} matrix_uniform[4];

        void main()
        {{
            final_colors = vec4(matrix_uniform[2][0][0]);
        }}
    """

    program = pyglet.graphics.ShaderProgram(
        pyglet.graphics.Shader(vertex_source, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
    )

    test_data = tuple((index + 1) / 10.0 for index in range(matrix_length))

    with program:
        program['matrix_uniform'][2] = test_data
        fetched_data = program['matrix_uniform'].get()

    assert len(fetched_data[2]) == matrix_length
    for actual, expected in zip(fetched_data[2], test_data):
        assert actual == pytest.approx(expected, abs=1e-06)
