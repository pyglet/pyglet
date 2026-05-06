from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pyglet
from pyglet.graphics.texture import Texture, TextureArray

_is_pyglet_doc_run = hasattr(sys, 'is_pyglet_doc_run') and sys.is_pyglet_doc_run

if TYPE_CHECKING:
    from pyglet.graphics.shader import ShaderProgram


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

    uniform sampler2D sprite_texture;

    void main()
    {
        final_colors = texture(sprite_texture, texture_coords.xy) * vertex_colors;
    }
"""

fragment_array_source: str = """#version 150 core
    in vec4 vertex_colors;
    in vec3 texture_coords;
    out vec4 final_colors;

    uniform sampler2DArray sprite_texture;

    void main()
    {
        final_colors = texture(sprite_texture, texture_coords) * vertex_colors;
    }
"""


def get_default_shader() -> ShaderProgram:
    """Create and return the default sprite shader.

    This method allows the module to be imported without an OpenGL Context.
    """
    return pyglet.graphics.api.core.get_cached_shader(
        "default_sprite",
        (vertex_source, 'vertex'),
        (fragment_source, 'fragment'),
    )


def get_default_array_shader() -> ShaderProgram:
    """Create and return the default array sprite shader.

    This method allows the module to be imported without an OpenGL Context.
    """
    return pyglet.graphics.api.core.get_cached_shader(
        "default_sprite_array",
        (vertex_source, 'vertex'),
        (fragment_array_source, 'fragment'),
    )


def get_default_multitexture_shader(layers: dict[str, Texture]) -> ShaderProgram:
    """Create and return the default multi-texture sprite shader."""
    if not layers:
        msg = "Multi-texture sprites require at least one texture layer."
        raise ValueError(msg)

    def _sampler_parts(tex: Texture) -> tuple[str, str]:
        owner = getattr(tex, 'owner', None)
        if isinstance(tex, TextureArray) or isinstance(owner, TextureArray):
            return "sampler2DArray", ""
        if isinstance(tex, Texture):
            return "sampler2D", ".xy"
        msg = f"Unsupported texture type for multi-texture sprite: {type(tex)}"
        raise NotImplementedError(msg)

    in_tex_coords = '\n'.join([f"in vec3 {name}_coords;" for name in layers])
    out_tex_coords = '\n'.join([f"out vec3 {name}_coords_frag;" for name in layers])
    tex_coords_assignments = '\n'.join([f"{name}_coords_frag = {name}_coords;" for name in layers])

    layer_in_tex_coords = '\n'.join([f"in vec3 {name}_coords_frag;" for name in layers])
    layer_uniform_samplers = '\n'.join(
        [f"uniform {_sampler_parts(tex)[0]} {name};" for name, tex in layers.items()],
    )
    layer_operations = '\n'.join(
        [f"        color = layer(texture({name}, {name}_coords_frag{_sampler_parts(tex)[1]}), color);"
         for name, tex in layers.items()],
    )

    vertex_shader_source = f"""#version 150 core
    in vec3 translate;
    in vec4 colors;
    in vec2 scale;
    in vec3 position;
    in float rotation;

    {in_tex_coords}

    out vec4 vertex_colors;
    {out_tex_coords}

    uniform WindowBlock
    {{
        mat4 projection;
        mat4 view;
    }} window;

    mat4 m_scale = mat4(1.0);
    mat4 m_rotation = mat4(1.0);
    mat4 m_translate = mat4(1.0);

    void main()
    {{
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

        {tex_coords_assignments}
    }}
    """

    fragment_shader_source = f"""#version 150 core
    in vec4 vertex_colors;
    {layer_in_tex_coords}

    out vec4 final_colors;
    {layer_uniform_samplers}

    vec4 layer(vec4 foreground, vec4 background)
    {{
        return foreground * foreground.a + background * (1.0 - foreground.a);
    }}

    void main()
    {{
        vec4 color = vec4(0.0, 0.0, 0.0, 1.0);
        {layer_operations}
        final_colors = color * vertex_colors;
    }}
    """

    shader_key = tuple((name, *_sampler_parts(tex)) for name, tex in layers.items())

    return pyglet.graphics.api.core.get_cached_shader(
        f"default_multitexture_sprite_{shader_key}",
        (vertex_shader_source, 'vertex'),
        (fragment_shader_source, 'fragment'),
    )
