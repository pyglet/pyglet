from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pyglet

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
