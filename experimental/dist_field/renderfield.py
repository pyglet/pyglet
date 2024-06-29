from __future__ import annotations

import sys

import pyglet
from pyglet.gl import (
    GL_BLEND,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_TEXTURE0,
    glActiveTexture,
    glBindTexture,
    glBlendFunc,
    glDisable,
    glEnable,
)
from pyglet.window import key


class DistFieldGroup(pyglet.sprite.SpriteGroup):  # noqa: D101
    def set_state(self) -> None:
        self.program.use()

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)

        self.program['bidirectional'] = enable_bidirectional

        self.program['antialias'] = enable_antialias
        self.program['outline'] = enable_outline
        self.program['outline_width'] = outline_width
        self.program['glow'] = enable_glow
        self.program['glow_width'] = glow_width

        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self) -> None:
        glDisable(GL_BLEND)
        self.program.stop()


class DistFieldSprite(pyglet.sprite.AdvancedSprite):
    """Override sprite to use DistFieldTextureGroup."""
    group_class = DistFieldGroup

    def __init__(self, img, x=0, y=0, z=0, blend_src=GL_SRC_ALPHA, blend_dest=GL_ONE_MINUS_SRC_ALPHA, batch=None,
                 group=None, subpixel=False, program=None) -> None:
        super().__init__(img, x, y, z, blend_src, blend_dest, batch, group, subpixel, program)


window = pyglet.window.Window(resizable=True)


@window.event
def on_resize(width, height):
    scale_width = width / float(image.width)
    scale_height = height / float(image.height)
    sprite.scale = min(scale_width, scale_height)
    sprite.x = width / 2
    sprite.y = height / 2


@window.event
def on_draw():
    window.clear()
    sprite.draw()


@window.event
def on_key_press(symbol, modifiers):
    global enable_bidirectional
    global enable_antialias
    global enable_outline
    global enable_glow
    global outline_width
    global glow_width
    if symbol == key.B:
        enable_bidirectional = not enable_bidirectional
    elif symbol == key.A:
        enable_antialias = not enable_antialias
    elif symbol == key.O:
        enable_outline = not enable_outline
        enable_glow = False
    elif symbol == key.G:
        enable_glow = not enable_glow
        enable_outline = False
    elif symbol == key.PERIOD:
        if enable_glow:
            glow_width += 0.005
        else:
            outline_width += 0.005
    elif symbol == key.COMMA:
        if enable_glow:
            glow_width -= 0.005
        else:
            outline_width -= 0.005

    print('-' * 78)
    print('enable_bidirectional:', enable_bidirectional)
    print('enable_antialias:', enable_antialias)
    print('enable_outline:', enable_outline)
    print('enable_glow:', enable_glow)
    print('outline_width:', outline_width)


vertex_source = """#version 150 core
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

fragment_source = """#version 150 core
    in vec4 vertex_colors;
    in vec3 texture_coords;
    out vec4 final_colors;

    uniform sampler2D sprite_texture;

    uniform bool bidirectional;
    uniform bool antialias;
    uniform bool outline;
    uniform bool glow;
    uniform float outline_width;
    uniform float glow_width;

    const vec4 outline_color = vec4(0.0, 0.0, 1.0, 1.0);
    const vec4 glow_color = vec4(1.0, 0.0, 0.0, 1.0);

    void main()
    {
        float alpha_mask;
        if (bidirectional)
        {
            vec4 field = texture2D(sprite_texture, texture_coords.xy);
            alpha_mask = float(field.r >= 0.5 && field.g >= 0.5);
        }
        else
        {
            alpha_mask = texture2D(sprite_texture, texture_coords.xy).a;
        }
        float alpha_width = fwidth(alpha_mask);
        float intensity = alpha_mask;

        final_colors = vertex_colors;

        if (glow)
        {
            float glow_min = 0.5 - glow_width;
            intensity = (alpha_mask - glow_min) / (0.5 - glow_min);
            float glow_intensity = 0.0;
            if (antialias)
                glow_intensity = 1.0 - smoothstep(0.5 - alpha_width,
                                                  0.5 + alpha_width,
                                                  alpha_mask) * 2.0;
            else
                glow_intensity = float(alpha_mask < 0.5);

            final_colors = mix(final_colors, glow_color, glow_intensity);
        }
        else if (outline)
        {
            float outline_intensity = 0.0;
            float outline_min = 0.5 - outline_width;
            float outline_max = 0.5;
            if (antialias)
            {

                outline_intensity = 1.0 - smoothstep(outline_max - alpha_width,
                                                     outline_max + alpha_width,
                                                     alpha_mask) * 2.0;

                intensity *= smoothstep(outline_min - alpha_width,
                                        outline_min + alpha_width,
                                        alpha_mask) * 2.0;
            }
            else
            {
                outline_intensity =
                    float(alpha_mask >= outline_min && alpha_mask <= outline_max);
                intensity = float(alpha_mask >= outline_min);
            }
            final_colors = mix(final_colors, outline_color, outline_intensity);
        }
        else if (antialias)
        {
            intensity *= smoothstep(0.5 - alpha_width,
                                    0.5 + alpha_width,
                                    alpha_mask) * 2.0;
        }
        else
        {
            intensity = float(alpha_mask >= 0.5);
        }

        final_colors.a = intensity;
    }
"""

enable_bidirectional = False
enable_antialias = False
enable_outline = False
enable_glow = False
outline_width = 0.02
glow_width = 0.1

dist_shader = pyglet.graphics.shader.ShaderProgram(
    pyglet.graphics.shader.Shader(vertex_source, "vertex"),
    pyglet.graphics.shader.Shader(fragment_source, "fragment"),
)

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = 'py.df.png'

controls = """
Following keys modify the shader operation:

    A   Toggle antialiasing
    B   Toggle bidirectional (see below)
    O   Toggle outline
    G   Toggle glow
    ,   Decrease outline/glow
    .   Increase outline/glow
"""
print(controls)

image = pyglet.image.load(filename)

image.anchor_x = image.width // 2
image.anchor_y = image.height // 2
sprite = DistFieldSprite(image, program=dist_shader)

pyglet.app.run()
