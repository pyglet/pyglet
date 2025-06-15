from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import pyglet
from pyglet.enums import BlendFactor
from pyglet.graphics.draw import Group

if TYPE_CHECKING:
    from pyglet.graphics.api.webgl import ShaderProgram
    from pyglet.image.base import TextureBase

layout_vertex_source = """#version 330 core
    in vec3 position;
    in vec4 colors;
    in vec3 tex_coords;
    in vec3 translation;
    in vec3 view_translation;
    in vec2 anchor;
    in float rotation;
    in float visible;

    out vec4 text_colors;
    out vec2 texture_coords;
    out vec4 vert_position;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        mat4 m_rotation = mat4(1.0);
        vec3 v_anchor = vec3(anchor.x, anchor.y, 0);
        mat4 m_anchor = mat4(1.0);
        mat4 m_translate = mat4(1.0);

        m_translate[3][0] = translation.x;
        m_translate[3][1] = translation.y;
        m_translate[3][2] = translation.z;

        m_rotation[0][0] =  cos(-radians(rotation));
        m_rotation[0][1] =  sin(-radians(rotation));
        m_rotation[1][0] = -sin(-radians(rotation));
        m_rotation[1][1] =  cos(-radians(rotation));

        gl_Position = window.projection * window.view * m_translate * m_anchor * m_rotation * vec4(position + 
        view_translation + v_anchor, 1.0) * visible;

        vert_position = vec4(position + translation + view_translation + v_anchor, 1.0);
        text_colors = colors;
        texture_coords = tex_coords.xy;
    }
"""

layout_fragment_source = """#version 330 core
    in vec4 text_colors;
    in vec2 texture_coords;
    in vec4 vert_position;

    out vec4 final_colors;

    uniform sampler2D text;
    uniform bool scissor;
    uniform vec4 scissor_area;

    void main()
    {
        final_colors = texture(text, texture_coords) * text_colors;
        if (scissor == true) {
            if (vert_position.x < scissor_area[0]) discard;                     // left
            if (vert_position.y < scissor_area[1]) discard;                     // bottom
            if (vert_position.x > scissor_area[0] + scissor_area[2]) discard;   // right
            if (vert_position.y > scissor_area[1] + scissor_area[3]) discard;   // top
        }
    }
"""
layout_fragment_image_source = """#version 330 core
    in vec4 text_colors;
    in vec2 texture_coords;
    in vec4 vert_position;

    uniform sampler2D image_texture;

    out vec4 final_colors;

    uniform bool scissor;
    uniform vec4 scissor_area;

    void main()
    {
        final_colors = texture(image_texture, texture_coords.xy);
        if (scissor == true) {
            if (vert_position.x < scissor_area[0]) discard;                     // left
            if (vert_position.y < scissor_area[1]) discard;                     // bottom
            if (vert_position.x > scissor_area[0] + scissor_area[2]) discard;   // right
            if (vert_position.y > scissor_area[1] + scissor_area[3]) discard;   // top
        }
    }
"""
decoration_vertex_source = """#version 330 core
    in vec3 position;
    in vec4 colors;
    in vec3 translation;
    in vec3 view_translation;
    in vec2 anchor;
    in float rotation;
    in float visible;

    out vec4 vert_colors;
    out vec4 vert_position;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        mat4 m_rotation = mat4(1.0);
        vec3 v_anchor = vec3(anchor.x, anchor.y, 0);
        mat4 m_anchor = mat4(1.0);
        mat4 m_translate = mat4(1.0);

        m_translate[3][0] = translation.x;
        m_translate[3][1] = translation.y;
        m_translate[3][2] = translation.z;

        m_rotation[0][0] =  cos(-radians(rotation));
        m_rotation[0][1] =  sin(-radians(rotation));
        m_rotation[1][0] = -sin(-radians(rotation));
        m_rotation[1][1] =  cos(-radians(rotation));

        gl_Position = window.projection * window.view * m_translate * m_anchor * m_rotation * vec4(position + 
        view_translation + v_anchor, 1.0) * visible;

        vert_position = vec4(position + translation + view_translation + v_anchor, 1.0);
        vert_colors = colors;
    }
"""
decoration_fragment_source = """#version 330 core
    in vec4 vert_colors;
    in vec4 vert_position;

    out vec4 final_colors;

    uniform bool scissor;
    uniform vec4 scissor_area;

    void main()
    {
        final_colors = vert_colors;
        if (scissor == true) {
            if (vert_position.x < scissor_area[0]) discard;                     // left
            if (vert_position.y < scissor_area[1]) discard;                     // bottom
            if (vert_position.x > scissor_area[0] + scissor_area[2]) discard;   // right
            if (vert_position.y > scissor_area[1] + scissor_area[3]) discard;   // top
        }
    }
"""


def get_default_layout_shader() -> ShaderProgram:
    """The default shader used for all glyphs in the layout."""
    return pyglet.graphics.api.core.get_cached_shader(
        "default_text_layout",
        (layout_vertex_source, "vertex"),
        (layout_fragment_source, "fragment"),
    )


def get_default_image_layout_shader() -> ShaderProgram:
    """The default shader used for an InlineElement image. Used for HTML Labels that insert images via <img> tag."""
    return pyglet.graphics.api.core.get_cached_shader(
        "default_text_image",
        (layout_vertex_source, "vertex"),
        (layout_fragment_image_source, "fragment"),
    )


def get_default_decoration_shader() -> ShaderProgram:
    """The default shader for underline and background decoration effects in the layout."""
    return pyglet.graphics.api.core.get_cached_shader(
        "default_text_decoration",
        (decoration_vertex_source, "vertex"),
        (decoration_fragment_source, "fragment"),
    )


class TextLayoutGroup(Group):
    """Create a text layout rendering group.

    The group is created internally when a :py:class:`~pyglet.text.Label`
    is created; applications usually do not need to explicitly create it.
    """

    def __init__(
        self,
        texture: TextureBase,
        program: ShaderProgram,
        order: int = 1,
        parent: Group | None = None,
    ) -> None:
        super().__init__(order=order, parent=parent)
        self.texture = texture
        self.set_shader_program(program)
        self.set_blend(BlendFactor.SRC_ALPHA, BlendFactor.ONE_MINUS_SRC_ALPHA)
        self.set_texture(texture, 0)
        self.set_shader_uniform(program, "scissor", False)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.texture})"


class TextDecorationGroup(Group):
    """Create a text decoration rendering group.

    The group is created internally when a :py:class:`~pyglet.text.Label`
    is created; applications usually do not need to explicitly create it.
    """

    def __init__(
        self,
        program: ShaderProgram,
        order: int = 0,
        parent: Group | None = None,
    ) -> None:
        super().__init__(order=order, parent=parent)
        self.set_shader_program(program)
        self.set_blend(BlendFactor.SRC_ALPHA, BlendFactor.ONE_MINUS_SRC_ALPHA)
        self.set_shader_uniform(program,"scissor", False)


# ====== SCROLLING TEXT


class ScrollableTextLayoutGroup(Group):
    """Default rendering group for :py:class:`~pyglet.text.layout.ScrollableTextLayout`.

    The group maintains internal state for specifying the viewable
    area, and for scrolling. Because the group has internal state
    specific to the text layout, the group is never shared.
    """

    scissor_area: ClassVar[tuple[int, int, int, int]] = 0, 0, 0, 0

    def __init__(
        self,
        texture: TextureBase,
        program: ShaderProgram,
        order: int = 1,
        parent: Group | None = None,
    ) -> None:
        super().__init__(order=order, parent=parent)
        self.texture = texture
        self.set_shader_program(program)
        self.set_blend(BlendFactor.SRC_ALPHA, BlendFactor.ONE_MINUS_SRC_ALPHA)
        self.set_texture(texture, 0)
        self.set_shader_uniform(program,"scissor", True)
        self.set_shader_uniform(program,"scissor_area", self.scissor_area)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.texture})"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


class ScrollableTextDecorationGroup(Group):
    """Create a text decoration rendering group.

    The group is created internally when a :py:class:`~pyglet.text.Label`
    is created; applications usually do not need to explicitly create it.
    """

    scissor_area: ClassVar[tuple[int, int, int, int]] = 0, 0, 0, 0

    def __init__(self, program: ShaderProgram, order: int = 0, parent: Group | None = None) -> None:  # noqa: D107
        super().__init__(order=order, parent=parent)
        self.program = program
        self.set_shader_program(program)
        self.set_blend(BlendFactor.SRC_ALPHA, BlendFactor.ONE_MINUS_SRC_ALPHA)
        self.set_shader_uniform(program, "scissor", True)
        self.set_shader_uniform(program,"scissor_area", self.scissor_area)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(scissor={self.scissor_area})"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)
