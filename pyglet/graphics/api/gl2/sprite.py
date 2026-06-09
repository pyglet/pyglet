from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pyglet
from pyglet.graphics.texture import Texture, TextureArray

_is_pyglet_doc_run = hasattr(sys, 'is_pyglet_doc_run') and sys.is_pyglet_doc_run

if TYPE_CHECKING:
    from pyglet.graphics import ShaderProgram


vertex_source: str = """#version 110
    attribute vec3 translate;
    attribute vec4 colors;
    attribute vec3 tex_coords;
    attribute vec2 scale;
    attribute vec3 position;
    attribute float rotation;

    varying vec4 vertex_colors;
    varying vec3 texture_coords;

    uniform mat4 u_projection;
    uniform mat4 u_view;

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

        gl_Position = u_projection * u_view * m_translate * m_rotation * m_scale * vec4(position, 1.0);

        vertex_colors = colors;
        texture_coords = tex_coords;
    }
"""

fragment_source: str = """#version 110
    varying vec4 vertex_colors;
    varying vec3 texture_coords;

    uniform sampler2D sprite_texture;

    void main()
    {
        gl_FragColor = texture2D(sprite_texture, texture_coords.xy) * vertex_colors;
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
    raise NotImplementedError


def get_default_multitexture_shader(layers: dict[str, Texture]) -> ShaderProgram:
    """Create and return the default multi-texture sprite shader."""
    if not layers:
        msg = "Multi-texture sprites require at least one texture layer."
        raise ValueError(msg)

    if any(isinstance(tex, TextureArray) or isinstance(getattr(tex, 'owner', None), TextureArray)
           for tex in layers.values()):
        msg = "The GL2 backend currently supports only GL_TEXTURE_2D layers for multi-texture sprites."
        raise NotImplementedError(msg)

    in_tex_coords = '\n'.join([f"attribute vec3 {name}_coords;" for name in layers])
    out_tex_coords = '\n'.join([f"varying vec3 {name}_coords_frag;" for name in layers])
    tex_coords_assignments = '\n'.join([f"{name}_coords_frag = {name}_coords;" for name in layers])
    layer_in_tex_coords = '\n'.join([f"varying vec3 {name}_coords_frag;" for name in layers])
    layer_uniform_samplers = '\n'.join([f"uniform sampler2D {name};" for name in layers])
    layer_operations = '\n'.join(
        [f"        color = layer(texture2D({name}, {name}_coords_frag.xy), color);" for name in layers],
    )

    vertex_shader_source = f"""#version 110
    attribute vec3 translate;
    attribute vec4 colors;
    attribute vec2 scale;
    attribute vec3 position;
    attribute float rotation;

    {in_tex_coords}

    varying vec4 vertex_colors;
    {out_tex_coords}

    uniform mat4 u_projection;
    uniform mat4 u_view;

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

        gl_Position = u_projection * u_view * m_translate * m_rotation * m_scale * vec4(position, 1.0);
        vertex_colors = colors;

        {tex_coords_assignments}
    }}
    """

    fragment_shader_source = f"""#version 110
    varying vec4 vertex_colors;
    {layer_in_tex_coords}

    {layer_uniform_samplers}

    vec4 layer(vec4 foreground, vec4 background)
    {{
        return foreground * foreground.a + background * (1.0 - foreground.a);
    }}

    void main()
    {{
        vec4 color = vec4(0.0, 0.0, 0.0, 1.0);
        {layer_operations}
        gl_FragColor = color * vertex_colors;
    }}
    """

    shader_key = tuple((name, "sampler2D", ".xy") for name in layers)

    return pyglet.graphics.api.core.get_cached_shader(
        f"default_multitexture_sprite_{shader_key}",
        (vertex_shader_source, 'vertex'),
        (fragment_shader_source, 'fragment'),
    )
