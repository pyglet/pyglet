#!/usr/bin/env python3

import pyglet
from pyglet.experimental import multitexture_sprite

window = pyglet.window.Window()
window.set_size(400, 400)

pyglet.resource.path = ['../../examples/resources']
pyglet.resource.reindex()

# Batching allows rendering groups of objects all at once instead of drawing one by one.
batch = pyglet.graphics.Batch()

brick_grid = pyglet.image.ImageGrid(pyglet.resource.image("Brick1Gray.png", atlas=False), 1, 6)
brick_gray = pyglet.image.Animation.from_image_sequence(brick_grid, 1.0 / 10.0)
# Load 2 animation images for our sprites
brick_grid = pyglet.image.ImageGrid(pyglet.resource.image("Brick1Blue.png"), 1, 6)
brick_animation = pyglet.image.Animation.from_image_sequence(brick_grid, 1.0 / 10.0)
crack_grid = pyglet.image.ImageGrid(pyglet.resource.image("Brick1Crack3.png"), 1, 3)
crack_animation = pyglet.image.Animation.from_image_sequence(crack_grid, 1.0, False)
shader_images = {'brick': brick_animation, 'crack': crack_animation}

sprite = multitexture_sprite.MultiTextureSprite(shader_images,
                                                x=0,
                                                y=0,
                                                batch=batch)
sprite2 = multitexture_sprite.MultiTextureSprite({'brick': brick_animation, 'crack': crack_animation},
                                                 x=100,
                                                 y=100,
                                                 batch=batch)

# Custom shaders can also be used with the multi-texture sprite.  You must follow the naming
# convention for samplers and other uniforms.
custom_vertex_source = """#version 150 core
    in vec3 translate;
    in vec4 colors;

    // The MultiTextureSprite class expects the texture coordinates for each texture
    // to follow the naming convention {name}_coords
    in vec3 kitten_coords;
    in vec3 logo_coords;

    in vec2 scale;
    in vec3 position;
    in float rotation;

    out vec4 vertex_colors;

    // The MultiTextureSprite class expects the texture coordinates for each texture
    // going to the fragment shader to follow the naming convention {name}_coords_frag
    out vec3 kitten_coords_frag;
    out vec3 logo_coords_frag;

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
        kitten_coords_frag = kitten_coords;
        logo_coords_frag = logo_coords;
    }
"""

custom_fragment_source = """#version 150 core
    in vec4 vertex_colors;

    // The MultiTextureSprite class expects the texture coordinates for each texture
    // to follow the naming convention {name}_coords_frag in the fragment shader
    in vec3 kitten_coords_frag;
    in vec3 logo_coords_frag;

    out vec4 final_colors;

    // The MultiTextureSprite class expects the sampler for each texture
    // to follow the naming convention {name}
    uniform sampler2D kitten;
    uniform sampler2D logo;

    void main()
    {
        final_colors = texture(kitten, kitten_coords_frag.xy) * texture(logo, logo_coords_frag.xy) * vertex_colors;
    }
"""

logo = pyglet.resource.image("pyglet.png")
kitten = pyglet.resource.image("kitten.jpg")
multi_vert_shader = pyglet.graphics.shader.Shader(custom_vertex_source, 'vertex')
multi_frag_shader = pyglet.graphics.shader.Shader(custom_fragment_source, 'fragment')
multitex_shader_program = pyglet.graphics.shader.ShaderProgram(multi_vert_shader, multi_frag_shader)
sprite3 = multitexture_sprite.MultiTextureSprite({'kitten': kitten, 'logo': logo},
                                                 x=150,
                                                 y=150,
                                                 batch=batch,
                                                 program=multitex_shader_program)
sprite3.scale = 0.2

f = 0


@window.event
def on_draw():
    window.clear()
    batch.draw()


def crack(dt):
    """Change frames for the second layer.
    """
    global f
    f = (f + 1) % 3
    sprite.set_frame_index('crack', f)
    pyglet.clock.schedule_once(crack, 1.0)


def pause(dt):
    print(f"Current paused value of sprite2 {sprite2.paused}")
    sprite2.paused = not sprite2.paused
    pyglet.clock.schedule_once(pause, 3.5)


def swap_animation(dt):
    sprite.set_layer('brick', brick_gray)


pyglet.clock.schedule_once(crack, 1.0)
pyglet.clock.schedule_once(pause, 3.5)
pyglet.clock.schedule_once(swap_animation, 5)

pyglet.app.run()
