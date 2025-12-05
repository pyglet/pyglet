from __future__ import annotations
import pyglet
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.graphics.api import ShaderProgram

vertex_source = """#version 110
    attribute vec2 position;
    attribute vec3 translation;
    attribute vec4 colors;
    attribute float rotation;

    varying vec4 vertex_colors;

    mat4 m_rotation = mat4(1.0);
    mat4 m_translate = mat4(1.0);

    uniform mat4 u_projection;
    uniform mat4 u_view;

    void main()
    {
        m_translate[3][0] = translation.x;
        m_translate[3][1] = translation.y;
        m_rotation[0][0] =  cos(-radians(rotation));
        m_rotation[0][1] =  sin(-radians(rotation));
        m_rotation[1][0] = -sin(-radians(rotation));
        m_rotation[1][1] =  cos(-radians(rotation));

        gl_Position = u_projection * u_view * m_translate * m_rotation * vec4(position, translation.z, 1.0);
        vertex_colors = colors;
    }
"""

fragment_source = """#version 150 core
    varying vec4 vertex_colors;

    void main()
    {
        gl_FragColor = vertex_colors;
    }
"""


def get_default_shader() -> ShaderProgram:
    return pyglet.graphics.api.core.get_cached_shader(
        "default_shapes",
        (vertex_source, 'vertex'),
        (fragment_source, 'fragment'),
    )
