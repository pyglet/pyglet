import pytest

import pyglet


def test_shader_ubo_data_structure():
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
        } data_struct;

        uniform sampler2D sprite_texture;

        void main()
        {
            final_colors = texture(sprite_texture, texture_coords.xy) * vertex_colors + data_struct.data[0].color[1].y;
        }
    """

    program = pyglet.graphics.shader.ShaderProgram(
        pyglet.graphics.shader.Shader(vertex_source, "vertex"),
        pyglet.graphics.shader.Shader(fragment_source, "fragment"),
    )

    ubo = program.uniform_blocks['EntityDataBlock'].create_ubo()

    cls_struct = program.uniform_blocks['EntityDataBlock'].view_cls
    
    test_data = (5.0, 1.0, 5125.0, 4.0)
    
    with ubo as block:
        block.data[0].color[1][:] = test_data
        
        # Just test a random deep node.
        assert len(block.data[3].within[2].position[:]) == 3
        
    data_from_buffer = ubo.read()

    verified_structure = cls_struct.from_buffer_copy(data_from_buffer)

    assert tuple(verified_structure.data[0].color[1][:]) == test_data
    
    # Write to a FB to confirm the shader is actually modifying the right data.
    # TODO: Add the projection back to shadow window.
    # image = pyglet.image.ImageData(1, 1, 'RGBA', bytes([0, 0, 0, 255]))
    # sprite = pyglet.sprite.Sprite(image, x=0, y=0, program=program)
    # 
    # fb = pyglet.image.buffer.Framebuffer()
    # texture = pyglet.image.Texture.create(1, 1)
    # fb.attach_texture(texture)
    # fb.bind()
    # sprite.draw()
    # fb.unbind()
    # 
    # # The image should now be white. (y is 1.0)
    # image_data = tuple(texture.get_image_data().get_data('RGBA')[:])
    # assert image_data == (255, 255, 255, 255)


def test_shader_ubo_matrix_data_structure():
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
            final_colors = texture(sprite_texture, texture_coords.xy) * vertex_colors + data_struct.data[1].projection[1][0];
        }
    """

    program = pyglet.graphics.shader.ShaderProgram(
        pyglet.graphics.shader.Shader(vertex_source, "vertex"),
        pyglet.graphics.shader.Shader(fragment_source, "fragment"),
    )

    ubo = program.uniform_blocks['MatrixTest'].create_ubo()

    cls_struct = program.uniform_blocks['MatrixTest'].view_cls
    
    test_data = pyglet.math.Mat4.orthogonal_projection(0, 800, 0, 600, -255, 255)

    with ubo as block:
        block.data[1].projection[1][:] = test_data

    data_from_buffer = ubo.read()

    verified_structure = cls_struct.from_buffer_copy(data_from_buffer)
    
    # Float imprecision's will become apparent, use approx instead...
    for a, b in zip(verified_structure.data[1].projection[1][:], tuple(test_data)):
        assert a == pytest.approx(b)

    # Write to a FB to confirm the shader is actually modifying the right data.
    # TODO: Add the projection back to shadow window.
    # image = pyglet.image.ImageData(1, 1, 'RGBA', bytes([0, 0, 0, 255]))
    # sprite = pyglet.sprite.Sprite(image, x=0, y=0, program=program)
    # 
    # fb = pyglet.image.buffer.Framebuffer()
    # texture = pyglet.image.Texture.create(1, 1)
    # fb.attach_texture(texture)
    # fb.bind()
    # sprite.draw()
    # fb.unbind()
    # 
    # # The image should now be white. (y is 1.0)
    # image_data = tuple(texture.get_image_data().get_data('RGBA')[:])
    # assert image_data == (255, 255, 255, 255)


def test_shader_uniform_block_matrix():
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
            final_colors = texture(sprite_texture, texture_coords.xy) * vertex_colors + data_struct.projection[1][0];
        }
    """

    program = pyglet.graphics.shader.ShaderProgram(
        pyglet.graphics.shader.Shader(vertex_source, "vertex"),
        pyglet.graphics.shader.Shader(fragment_source, "fragment"),
    )

    ubo = program.uniform_blocks['MatrixTest'].create_ubo()

    cls_struct = program.uniform_blocks['MatrixTest'].view_cls

    test_data = pyglet.math.Mat4.orthogonal_projection(0, 800, 0, 600, -255, 255)

    with ubo as block:
        block.projection[1][:] = test_data
        assert len(block.projection) == 5

    data_from_buffer = ubo.read()

    verified_structure = cls_struct.from_buffer_copy(data_from_buffer)

    # Float imprecision's will become apparent, use approx instead...
    for a, b in zip(verified_structure.projection[1][:], tuple(test_data)):
        assert a == pytest.approx(b)

    # Write to a FB to confirm the shader is actually modifying the right data.
    # TODO: Add the projection back to shadow window.
    # image = pyglet.image.ImageData(1, 1, 'RGBA', bytes([0, 0, 0, 255]))
    # sprite = pyglet.sprite.Sprite(image, x=0, y=0, program=program)
    # 
    # fb = pyglet.image.buffer.Framebuffer()
    # texture = pyglet.image.Texture.create(1, 1)
    # fb.attach_texture(texture)
    # fb.bind()
    # sprite.draw()
    # fb.unbind()
    # 
    # # The image should now be white. (y is 1.0)
    # image_data = tuple(texture.get_image_data().get_data('RGBA')[:])
    # assert image_data == (255, 255, 255, 255)

def test_shader_uniform_matrix():
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

    program = pyglet.graphics.shader.ShaderProgram(
        pyglet.graphics.shader.Shader(vertex_source, "vertex"),
        pyglet.graphics.shader.Shader(fragment_source, "fragment"),
    )
    test_data = pyglet.math.Mat4.orthogonal_projection(0, 800, 0, 600, -255, 255)

    with program:
        program['matrix_uniform'] = tuple(test_data)
        
    with program:
        fetched_data = program['matrix_uniform']

    # Float imprecision's will become apparent, use approx instead...
    for a, b in zip(fetched_data, tuple(test_data)):
        assert a == pytest.approx(b)


def test_shader_uniform_matrix_array():
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

    program = pyglet.graphics.shader.ShaderProgram(
        pyglet.graphics.shader.Shader(vertex_source, "vertex"),
        pyglet.graphics.shader.Shader(fragment_source, "fragment"),
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

def test_shader_uniform_float_array():
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

    program = pyglet.graphics.shader.ShaderProgram(
        pyglet.graphics.shader.Shader(vertex_source, "vertex"),
        pyglet.graphics.shader.Shader(fragment_source, "fragment"),
    )
    test_data = 25.5

    with program:
        # Set test data
        program['float_array'][11] = test_data

    with program:
        # fetch from uniform itself.
        fetched_data = program['float_array'][11]

    assert test_data == fetched_data

