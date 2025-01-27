from __future__ import annotations
import pyglet
from pyglet.graphics.api.gl.enums import blend_factor_map
from pyglet.graphics.draw import Group
from pyglet.graphics.api.gl import (
    GL_BLEND,
    glBlendFunc,
    glDisable,
    glEnable,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.enums import BlendFactor
    from pyglet.graphics.api import ShaderProgram

vertex_source = """#version 110
    attribute vec2 position;
    attribute vec2 translation;
    attribute vec4 colors;
    attribute float rotation;

    varying vec4 vertex_colors;

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

        gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * m_translate * m_rotation * vec4(position, 0.0, 1.0);
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
    return pyglet.graphics.api.global_backend.get_cached_shader(
        "default_shapes",
        (vertex_source, 'vertex'),
        (fragment_source, 'fragment'),
    )



class _ShapeGroup(Group):
    """Shared Shape rendering Group.

    The group is automatically coalesced with other shape groups
    sharing the same parent group and blend parameters.
    """
    blend_src: int
    blend_dest: int

    def __init__(self, blend_src: BlendFactor, blend_dest: BlendFactor, program: ShaderProgram,
                 parent: Group | None = None) -> None:
        """Create a Shape group.

        The group is created internally. Usually you do not
        need to explicitly create it.

        Args:
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            program:
                The ShaderProgram to use.
            parent:
                Optional parent group.
        """
        super().__init__(parent=parent)
        self.set_shader_program(program)
        self.set_blend(blend_src, blend_dest)