from __future__ import annotations
import pyglet
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.graphics.api.gl.shader import ShaderProgram

vertex_source = """#version 150 core
    in vec2 position;
    in vec3 translation;
    in vec4 colors;
    in float rotation;

    out vec4 vertex_colors;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    mat4 m_rotation = mat4(1.0);
    mat4 m_translate = mat4(1.0);

    void main()
    {
        m_translate[3][0] = translation.x;
        m_translate[3][1] = translation.y;
        m_rotation[0][0] =  cos(-radians(rotation));
        m_rotation[0][1] =  sin(-radians(rotation));
        m_rotation[1][0] = -sin(-radians(rotation));
        m_rotation[1][1] =  cos(-radians(rotation));

        gl_Position = window.projection * window.view * m_translate * m_rotation * vec4(position, translation.z, 1.0);
        vertex_colors = colors;
    }
"""

fragment_source = """#version 150 core
    in vec4 vertex_colors;
    out vec4 final_color;

    void main()
    {
        final_color = vertex_colors;
    }
"""


def get_default_shader() -> ShaderProgram:
    return pyglet.graphics.api.core.get_cached_shader(
        "default_shapes",
        (vertex_source, 'vertex'),
        (fragment_source, 'fragment'),
    )
