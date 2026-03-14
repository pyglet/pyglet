from __future__ import annotations

import re
import sys
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Iterator,
    Pattern,
    Protocol,
)

import pyglet
from pyglet import graphics
from pyglet.font.base import GlyphPosition
from pyglet.gl import (
    GL_BLEND,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_COMPONENT,
    GL_LINES,
    GL_NEAREST,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_TEXTURE0,
    GL_TRIANGLES,
    glActiveTexture,
    glBindTexture,
    glBlendFunc,
    glDisable,
    glEnable,
)
from pyglet.graphics import Group
from pyglet.text import runlist

if TYPE_CHECKING:
    from pyglet.customtypes import AnchorX, AnchorY, ContentVAlign, HorizontalAlign
    from pyglet.font.base import Font, Glyph
    from pyglet.graphics import Batch
    from pyglet.graphics.shader import ShaderProgram
    from pyglet.graphics.vertexdomain import VertexList
    from pyglet.image import Texture
    from pyglet.text.document import AbstractDocument, InlineElement
    from pyglet.text.runlist import AbstractRunIterator, RunIterator

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

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

        gl_Position = window.projection * window.view * m_translate * m_anchor * m_rotation * vec4(position + view_translation + v_anchor, 1.0) * visible;

        vert_position = vec4(position + translation + view_translation + v_anchor, 1.0);
        text_colors = colors;
        texture_coords = tex_coords.xy;
    }
"""  # noqa: E501
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

    uniform sampler2D text;
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

        gl_Position = window.projection * window.view * m_translate * m_anchor * m_rotation * vec4(position + view_translation + v_anchor, 1.0) * visible;

        vert_position = vec4(position + translation + view_translation + v_anchor, 1.0);
        vert_colors = colors;
    }
"""  # noqa: E501
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


class _LayoutVertexList(Protocol):
    """Just a Protocol to add completion for VertexLists."""
    position: list
    colors: list
    translation: list
    view_translation: list
    anchor: list
    rotation: list
    visible: list
    count: int

    def delete(self) -> None: ...


def get_default_layout_shader() -> ShaderProgram:
    """The default shader used for all glyphs in the layout."""
    return pyglet.gl.current_context.create_program((layout_vertex_source, "vertex"),
                                                    (layout_fragment_source, "fragment"))


def get_default_image_layout_shader() -> ShaderProgram:
    """The default shader used for an InlineElement image. Used for HTML Labels that insert images via <img> tag."""
    return pyglet.gl.current_context.create_program((layout_vertex_source, "vertex"),
                                                    (layout_fragment_image_source, "fragment"))


def get_default_decoration_shader() -> ShaderProgram:
    """The default shader for underline and background decoration effects in the layout."""
    return pyglet.gl.current_context.create_program((decoration_vertex_source, "vertex"),
                                                    (decoration_fragment_source, "fragment"))


_distance_re: Pattern[str] = re.compile(r"([-0-9.]+)([a-zA-Z]+)")


def _parse_distance(distance: str | float, dpi: int) -> int:
    """Parse a distance string and return corresponding distance in pixels as an integer."""
    if isinstance(distance, int):
        return distance
    if isinstance(distance, float):
        return int(distance)

    match = _distance_re.match(distance)
    assert match, f"Could not parse distance {distance}"
    if not match:
        return 0

    value, unit = match.groups()
    value = float(value)
    if unit == "px":
        return int(value)
    if unit == "pt":
        return int(value * dpi / 72.0)
    if unit == "pc":
        return int(value * dpi / 6.0)
    if unit == "in":
        return int(value * dpi)
    if unit == "mm":
        return int(value * dpi * 0.0393700787)
    if unit == "cm":
        return int(value * dpi * 0.393700787)

    msg = f"Unknown distance unit {unit}"
    raise Exception(msg)


class _Line:
    boxes: list[_AbstractBox]
    vertex_lists: list[VertexList]
    start: int

    align: HorizontalAlign = "left"

    margin_left: int = 0
    margin_right: int = 0

    length: int = 0

    ascent: float = 0
    descent: float = 0
    width: float = 0
    paragraph_begin: bool = False
    paragraph_end: bool = False

    x: int
    y: int

    def __init__(self, start: int) -> None:
        self.start = start
        self.x = 0
        self.y = 0
        self.vertex_lists = []  # Incremental only.
        self.boxes = []

    def __repr__(self) -> str:
        return f"_Line({self.boxes})"

    def add_box(self, box: _AbstractBox) -> None:
        # Boxes are added when lines are flowed.
        self.boxes.append(box)
        self.length += box.length
        self.ascent = max(self.ascent, box.ascent)
        self.descent = min(self.descent, box.descent)
        self.width += box.advance

    def delete(self, layout: TextLayout) -> None:
        # ONLY used by IncrementalTextLayout.
        # Does not actually delete any data of the Line, just vertex lists and boxes. In the case
        # of an InlineElement, it's up to that implementation.

        # When lines go out of visibility of the scissor area, they are culled to have no vertex list. This should
        # perform better on extremely long documents. When they go back into visibility, place() is called again.
        for box in self.boxes:
            box.delete(layout)

        self.vertex_lists.clear()


class _LayoutContext:
    def __init__(self, layout: TextLayout, document: AbstractDocument, colors_iter: RunIterator,
                 background_iter: AbstractRunIterator) -> None:
        self.layout = layout
        self.colors_iter = colors_iter
        underline_iter = document.get_style_runs("underline")
        self.decoration_iter = runlist.ZipRunIterator((background_iter, underline_iter))
        self.baseline_iter = runlist.FilteredRunIterator(
            document.get_style_runs("baseline"),
            lambda value: value is not None, 0)

    @abstractmethod
    def add_list(self, vertex_list: VertexList) -> None:
        ...

    @abstractmethod
    def add_box(self, box: _AbstractBox) -> None:
        ...


class _StaticLayoutContext(_LayoutContext):

    def __init__(self, layout: TextLayout, document: AbstractDocument, colors_iter: RunIterator,
                 background_iter: AbstractRunIterator) -> None:
        super().__init__(layout, document, colors_iter, background_iter)
        self.vertex_lists = layout._vertex_lists  # noqa: SLF001
        self.boxes = layout._boxes  # noqa: SLF001

    def add_list(self, vertex_list: _LayoutVertexList) -> None:
        self.vertex_lists.append(vertex_list)

    def add_box(self, box: _AbstractBox) -> None:
        pass


class _AbstractBox(ABC):
    """A box has two cases, A GlyphBox and an InlineElementBox."""
    owner: Texture | None
    ascent: float
    descent: float
    advance: float
    length: int

    def __init__(self, ascent: float, descent: float, advance: float, length: int) -> None:
        self.owner = None
        self.ascent = ascent
        self.descent = descent
        self.advance = advance
        self.length = length

    @abstractmethod
    def place(self, layout: TextLayout, i: int, x: float, y: float, z: float, line_x: float, line_y: float,
              rotation: float, visible: bool, anchor_x: float, anchor_y: float, context: _LayoutContext) -> None:
        ...

    @abstractmethod
    def update_translation(self, x: float, y: float, z: float) -> None:
        ...

    @abstractmethod
    def update_colors(self, colors: list[int], start: int, end: int) -> None:
        ...

    @abstractmethod
    def update_view_translation(self, translate_x: float, translate_y: float) -> None:
        ...

    @abstractmethod
    def update_rotation(self, rotation: float) -> None:
        ...

    @abstractmethod
    def update_visibility(self, visible: bool) -> None:
        ...

    @abstractmethod
    def update_anchor(self, anchor_x: float, anchor_y: float) -> None:
        ...

    @abstractmethod
    def delete(self, layout: TextLayout) -> None:
        ...

    @abstractmethod
    def get_position_in_box(self, x: float) -> int:
        ...

    @abstractmethod
    def get_point_in_box(self, position: int) -> float:
        ...


class _GlyphBox(_AbstractBox):
    owner: Texture
    font: Font
    glyphs: list[tuple[int, Glyph, GlyphPosition]]
    advance: int
    vertex_lists: list[_LayoutVertexList]

    def __init__(self, owner: Texture, font: Font, glyphs: list[tuple[int, Glyph, GlyphPosition]], advance: int) -> None:
        """Create a run of glyphs sharing the same texture.

        Args:
            owner:
                Texture of all glyphs in this run.
            font:
                Font of all glyphs in this run.
            glyphs:
                Pairs of ``(kern, glyph)``, where ``kern`` gives horizontal
                displacement of the glyph in pixels (typically 0).
            advance:
                Width of glyph run; must correspond to the sum of advances
                and kerns in the glyph list.
            offsets:
                A list of all position transformations done to each glyph.
        """
        super().__init__(font.ascent, font.descent, advance, len(glyphs))
        assert owner
        self.owner = owner
        self.font = font
        self.glyphs = glyphs
        self.advance = advance
        self.vertex_lists = []

    def _add_vertex_list(self, vertex_list: _LayoutVertexList | VertexList, context: _LayoutContext) -> None:
        self.vertex_lists.append(vertex_list)
        context.add_list(vertex_list)

    def place(self, layout: TextLayout, i: int, x: float, y: float, z: float, line_x: float, line_y: float,
              rotation: float, visible: bool, anchor_x: float, anchor_y: float, context: _LayoutContext) -> None:
        # Creates the initial attributes and vertex lists of the glyphs.
        # line_x/line_y are calculated when lines shift. To prevent having to destroy and recalculate the layout
        # every time it moves, they are merged into the vertices. This way the translation can be moved directly.
        assert self.glyphs
        assert not self.vertex_lists
        try:
            group = layout.group_cache[self.owner]
        except KeyError:
            group = layout.group_class(self.owner, layout.program, order=1, parent=layout.group)
            layout.group_cache[self.owner] = group

        n_glyphs = self.length
        vertices = []
        tex_coords = []
        baseline = 0
        x1 = line_x
        for start, end, baseline_ in context.baseline_iter.ranges(i, i + n_glyphs):
            baseline = layout._parse_distance(baseline_)  # noqa: SLF001
            assert len(self.glyphs[start - i:end - i]) == end - start
            for (kern, glyph, glyph_pos) in self.glyphs[start - i:end - i]:
                x1 += kern
                v0, v1, v2, v3 = glyph.vertices
                v0 += x1 + glyph_pos.x_offset
                v2 += x1 + glyph_pos.x_offset
                v1 += line_y + baseline + glyph_pos.y_offset
                v3 += line_y + baseline + glyph_pos.y_offset
                vertices.extend(map(round, [v0, v1, 0, v2, v1, 0, v2, v3, 0, v0, v3, 0]))
                t = glyph.tex_coords
                tex_coords.extend(t)
                x1 += glyph.advance + glyph_pos.x_advance
                v1 += glyph_pos.y_advance
                v3 += glyph_pos.y_advance

        # Text color
        colors = []
        for start, end, color in context.colors_iter.ranges(i, i + n_glyphs):
            if color is None:
                color = (0, 0, 0, 255)  # noqa: PLW2901
            if len(color) != 4:
                msg = f"Color requires 4 values (R, G, B, A). Value received: {color}"
                raise ValueError(msg)
            colors.extend(color * ((end - start) * 4))

        indices = []
        # Create indices for each glyph quad:
        for glyph_idx in range(n_glyphs):
            indices.extend([element + (glyph_idx * 4) for element in [0, 1, 2, 0, 2, 3]])

        t_position = (x, y, z)

        vertex_list = layout.program.vertex_list_indexed(n_glyphs * 4, GL_TRIANGLES, indices, layout.batch, group,
                                                         position=("f", vertices),
                                                         translation=("f", t_position * 4 * n_glyphs),
                                                         colors=("Bn", colors),
                                                         tex_coords=("f", tex_coords),
                                                         rotation=("f", ((rotation,) * 4) * n_glyphs),
                                                         visible=("f", ((visible,) * 4) * n_glyphs),
                                                         anchor=("f", ((anchor_x, anchor_y) * 4) * n_glyphs))
        self._add_vertex_list(vertex_list, context)

        # Decoration (background color and underline)
        # -------------------------------------------
        # Should iterate over baseline too, but in practice any sensible
        # change in baseline will correspond with a change in font size,
        # and thus glyph run as well.  So we cheat and just use whatever
        # baseline was seen last.
        background_vertices = []
        background_colors = []
        underline_vertices = []
        underline_colors = []
        y1 = line_y + self.descent + baseline
        y2 = line_y + self.ascent + baseline
        x1 = line_x

        for start, end, decoration in context.decoration_iter.ranges(i, i + n_glyphs):
            bg, underline = decoration
            x2 = x1
            for (kern, glyph, glyph_pos) in self.glyphs[start - i:end - i]:
                x2 += glyph.advance + kern + glyph_pos.x_advance

            if bg is not None:
                if len(bg) != 4:
                    msg = f"Background color requires 4 values (R, G, B, A). Value received: {bg}"
                    raise ValueError(msg)

                background_vertices.extend([x1, y1, 0, x2, y1, 0, x2, y2, 0, x1, y2, 0])
                background_colors.extend(bg * 4)

            if underline is not None:
                if len(underline) != 4:
                    msg = f"Underline color requires 4 values (R, G, B, A). Value received: {underline}"
                    raise ValueError(msg)

                underline_vertices.extend([x1, line_y + baseline - 2, 0, x2, line_y + baseline - 2, 0])
                underline_colors.extend(underline * 2)

            x1 = x2

        if background_vertices:
            bg_count = len(background_vertices) // 3
            background_indices = [(0, 1, 2, 0, 2, 3)[i % 6] for i in range(bg_count * 3)]
            decoration_program = get_default_decoration_shader()
            background_list = decoration_program.vertex_list_indexed(bg_count, GL_TRIANGLES, background_indices,
                                                                     layout.batch, layout.background_decoration_group,
                                                                     position=("f", background_vertices),
                                                                     translation=("f", t_position * bg_count),
                                                                     colors=("Bn", background_colors),
                                                                     rotation=("f", (rotation,) * bg_count),
                                                                     visible=("f", (visible,) * bg_count),
                                                                     anchor=("f", (anchor_x, anchor_y) * bg_count))
            self._add_vertex_list(background_list, context)

        if underline_vertices:
            ul_count = len(underline_vertices) // 3
            decoration_program = get_default_decoration_shader()
            underline_list = decoration_program.vertex_list(ul_count, GL_LINES,
                                                            layout.batch, layout.foreground_decoration_group,
                                                            position=("f", underline_vertices),
                                                            translation=("f", t_position * ul_count),
                                                            colors=("Bn", underline_colors),
                                                            rotation=("f", (rotation,) * ul_count),
                                                            visible=("f", (visible,) * ul_count),
                                                            anchor=("f", (anchor_x, anchor_y) * ul_count))
            self._add_vertex_list(underline_list, context)

    def update_translation(self, x: float, y: float, z: float) -> None:
        translation = (x, y, z)
        for _vertex_list in self.vertex_lists:
            _vertex_list.translation[:] = translation * _vertex_list.count

    def update_colors(self, colors: list[int], start: int, end: int) -> None:
        """Update the glyph colors only when specified by a single color attribute in set_style.

        Update just the specific range of glyphs with the colors.
        """
        # Receives flattened list of colors based on the count.
        for _vertex_list in self.vertex_lists:
            vertices_per_char = _vertex_list.count // self.length
            # Check length, because underlines and BG's can exist.
            if vertices_per_char == 4:
                color_end_index = (end - start) * 4

                # Calculate the vertex start and end indices for (RGBA)
                vertex_start_index = start * vertices_per_char * 4
                vertex_end_index = end * vertices_per_char * 4

                # Update the vertex colors
                _vertex_list.colors[vertex_start_index:vertex_end_index] = colors[:color_end_index] * vertices_per_char

    def update_view_translation(self, translate_x: float, translate_y: float) -> None:
        view_translation = (-translate_x, -translate_y, 0)
        for _vertex_list in self.vertex_lists:
            _vertex_list.view_translation[:] = view_translation * _vertex_list.count

    def update_rotation(self, rotation: float) -> None:
        rot = (rotation,)
        for _vertex_list in self.vertex_lists:
            _vertex_list.rotation[:] = rot * _vertex_list.count

    def update_visibility(self, visible: bool) -> None:
        visible_tuple = (visible,)
        for _vertex_list in self.vertex_lists:
            _vertex_list.visible[:] = visible_tuple * _vertex_list.count

    def update_anchor(self, anchor_x: float, anchor_y: float) -> None:
        anchor = (anchor_x, anchor_y)
        for _vertex_list in self.vertex_lists:
            _vertex_list.anchor[:] = anchor * _vertex_list.count

    def delete(self, layout: TextLayout) -> None:  # noqa: ARG002
        for _vertex_list in self.vertex_lists:
            _vertex_list.delete()

        self.vertex_lists.clear()

    def get_point_in_box(self, position: int) -> int:
        x = 0
        for (kern, glyph, offset) in self.glyphs:
            if position == 0:
                break
            position -= 1
            x += glyph.advance + kern + offset.x_advance
        return x

    def get_position_in_box(self, x: float) -> int:
        position = 0
        last_glyph_x = 0
        for (kern, glyph, offset) in self.glyphs:
            last_glyph_x += kern
            if last_glyph_x + glyph.advance + offset.x_advance // 2 > x:
                return position
            position += 1
            last_glyph_x += glyph.advance
        return position

    def __repr__(self) -> str:
        return f"_GlyphBox({self.glyphs})"


class _InlineElementBox(_AbstractBox):
    element: InlineElement
    placed: bool

    def __init__(self, element: InlineElement) -> None:
        """Create a glyph run holding a single element."""
        super().__init__(element.ascent, element.descent, element.advance, 1)
        self.element = element

        # Determines if the box is visible.
        self.placed = False

    def place(self, layout: TextLayout, i: int, x: float, y: float, z: float, line_x: float, line_y: float,  # noqa: ARG002
              rotation: float, visible: bool, anchor_x: float, anchor_y: float,
              context: _LayoutContext) -> None:  # noqa: ARG002
        self.element.place(layout, x, y, z, line_x, line_y, rotation, visible, anchor_x, anchor_y)
        self.placed = True

    def update_translation(self, x: float, y: float, z: float) -> None:
        if self.placed:
            self.element.update_translation(x, y, z)

    def update_colors(self, colors: list[int], _start: int, _end: int) -> None:
        if self.placed:
            self.element.update_color(colors)

    def update_view_translation(self, translate_x: float, translate_y: float) -> None:
        if self.placed:
            self.element.update_view_translation(translate_x, translate_y)

    def update_rotation(self, rotation: float) -> None:
        if self.placed:
            self.element.update_rotation(rotation)

    def update_visibility(self, visible: bool) -> None:
        if self.placed:
            self.element.update_visibility(visible)

    def update_anchor(self, anchor_x: float, anchor_y: float) -> None:
        if self.placed:
            self.element.update_anchor(anchor_x, anchor_y)

    def delete(self, layout: TextLayout) -> None:
        if self.placed:
            self.element.remove(layout)
            self.placed = False

    def get_point_in_box(self, position: int) -> float:
        if position == 0:
            return 0

        return self.advance

    def get_position_in_box(self, x: float) -> int:
        if x < self.advance // 2:
            return 0

        return 1

    def __repr__(self) -> str:
        return f"_InlineElementBox({self.element})"


class _InvalidRange:
    start: int
    end: int

    # Used by the IncrementalTextLayout

    def __init__(self) -> None:
        self.start = sys.maxsize
        self.end = 0

    def insert(self, start: int, length: int) -> None:
        if self.start >= start:
            self.start += length
        if self.end >= start:
            self.end += length
        self.invalidate(start, start + length)

    def delete(self, start: int, end: int) -> None:
        if self.start > end:
            self.start -= end - start
        elif self.start > start:
            self.start = start
        if self.end > end:
            self.end -= end - start
        elif self.end > start:
            self.end = start

    def invalidate(self, start: int, end: int) -> None:
        if end <= start:
            return
        self.start = min(self.start, start)
        self.end = max(self.end, end)

    def validate(self) -> tuple[int, int]:
        start, end = self.start, self.end
        self.start = sys.maxsize
        self.end = 0
        return start, end

    def is_invalid(self) -> bool:
        return self.end > self.start


class TextLayoutGroup(graphics.Group):
    """Create a text layout rendering group.

    The group is created internally when a :py:class:`~pyglet.text.Label`
    is created; applications usually do not need to explicitly create it.
    """

    def __init__(self, texture: Texture, program: ShaderProgram, order: int = 1,  # noqa: D107
                 parent: graphics.Group | None = None) -> None:
        super().__init__(order=order, parent=parent)
        self.texture = texture
        self.program = program

    def set_state(self) -> None:
        self.program.use()
        self.program["scissor"] = False

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self) -> None:
        glDisable(GL_BLEND)
        self.program.stop()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.texture})"

    def __eq__(self, other: object) -> bool:
        return (other.__class__ is self.__class__ and
                self.parent is other.parent and
                self.program.id is other.program.id and
                self.order == other.order and
                self.texture.target == other.texture.target and
                self.texture.id == other.texture.id)

    def __hash__(self) -> int:
        return hash((id(self.parent), self.program.id, self.order, self.texture.target, self.texture.id))


class TextDecorationGroup(Group):
    """Create a text decoration rendering group.

    The group is created internally when a :py:class:`~pyglet.text.Label`
    is created; applications usually do not need to explicitly create it.
    """

    def __init__(self, program: ShaderProgram, order: int = 0,  # noqa: D107
                 parent: graphics.Group | None = None) -> None:
        super().__init__(order=order, parent=parent)
        self.program = program

    def set_state(self) -> None:
        self.program.use()
        self.program["scissor"] = False

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self) -> None:
        glDisable(GL_BLEND)
        self.program.stop()


# Just have one object for empty positions in layout. It won't be modified.
_empty_pos = GlyphPosition(0, 0, 0, 0)

class TextLayout:
    """Lay out and display documents.

    This class is intended for displaying documents.

    :py:func:`~pyglet.text.Label` and :py:func:`~pyglet.text.HTMLLabel` provide a convenient interface to this class.

    Some properties may cause the document to be recreated rather than updated. Refer to property documentation for
    details.

    Attributes:
        group_class:
            Default group used to set the state for all glyphs.
        decoration_class:
            Default group used to set the state for all decorations including background colors and underlines.
    """
    _vertex_lists: list[_LayoutVertexList]
    _boxes: list[_AbstractBox]
    group_cache: dict[Texture, graphics.Group]

    _document: AbstractDocument | None = None

    _update_enabled: bool = True
    _own_batch: bool = False

    group_class: ClassVar[type[TextLayoutGroup]] = TextLayoutGroup
    decoration_class: ClassVar[type[TextDecorationGroup]] = TextDecorationGroup

    _ascent: float = 0
    _descent: float = 0
    _line_count: int = 0
    _anchor_left: float = 0
    _anchor_bottom: float = 0
    _x: float
    _y: float
    _z: float
    _rotation: float = 0

    _width: int | None = None
    _height: int | None = None

    _anchor_x: AnchorX = "left"
    _anchor_y: AnchorY = "bottom"
    _content_valign: ContentVAlign = "top"
    _multiline: bool = False
    _visible: bool = True

    def __init__(self, document: AbstractDocument,
                 x: float = 0, y: float = 0, z: float = 0,
                 width: int | None = None, height: int | None = None,
                 anchor_x: AnchorX = 'left', anchor_y: AnchorY = 'bottom', rotation: float = 0,
                 multiline: bool = False, dpi: float | None = None, batch: Batch | None = None,
                 group: graphics.Group | None = None, program: ShaderProgram | None = None,
                 wrap_lines: bool = True, init_document: bool = True) -> None:
        """Create a text layout.

        Args:
            document:
                Document to display.
            x:
                X coordinate of the label.
            y:
                Y coordinate of the label.
            z:
                Z coordinate of the label.
            width:
                Width of the layout in pixels, or None
            height:
                Height of the layout in pixels, or None
            anchor_x:
                Anchor point of the X coordinate.
            anchor_y:
                Anchor point of the Y coordinate.
            rotation:
                The amount to rotate the label in degrees. A positive amount
                will be a clockwise rotation, negative values will result in
                counter-clockwise rotation.
            multiline:
                If False, newline and paragraph characters are ignored, and
                text is not word-wrapped.
                If True, text is wrapped only if the `wrap_lines` is True.
            dpi:
                Font resolution; defaults to 96.
            batch:
                Optional graphics batch to add this layout to.
            group:
                Optional Group to parent all internal Groups that this text
                layout uses.  Note that layouts with the same Groups will
                be rendered simultaneously in a Batch.
            program:
                Optional graphics shader to use. Will affect all glyphs in the layout.
            wrap_lines:
                If True and `multiline` is True, the text is word-wrapped using the specified width.
            init_document:
                If True the document will be initialized. If subclassing then
                you may want to avoid duplicate initializations by changing to False.
        """
        self._x = x
        self._y = y
        self._z = z
        self._width = width
        self._height = height
        self._anchor_x = anchor_x
        self._anchor_y = anchor_y
        self._rotation = rotation
        self._multiline = multiline
        self._dpi = dpi or 96

        self._content_width = 0
        self._content_height = 0

        self._user_group = group

        # Accumulation of all child vertex lists, this is ONLY used for the draw function.
        self._vertex_lists = []

        # Boxes are all existing _AbstractBoxes, these are used to gather line information.
        # Note that this is only relevant to layouts that do not store directly on lines.
        self._boxes = []
        self._lines = []

        #: :meta private:
        self.group_cache = {}

        self._initialize_groups()

        if batch is None:
            batch = graphics.Batch()
            self._own_batch = True
        self._batch = batch

        self._program = program or get_default_layout_shader()

        self._wrap_lines_flag = wrap_lines
        self._wrap_lines_invariant()

        self._set_document(document)
        if init_document:
            self._init_document()

    @property
    def _flow_glyphs(self) -> Callable:
        if self._multiline:
            return self._flow_glyphs_wrap
        return self._flow_glyphs_single_line

    def _initialize_groups(self) -> None:
        decoration_shader = get_default_decoration_shader()
        self.background_decoration_group = self.decoration_class(decoration_shader, order=0, parent=self._user_group)
        self.foreground_decoration_group = self.decoration_class(decoration_shader, order=2, parent=self._user_group)

    @property
    def group(self) -> Group | None:
        """Get the Group specified by the user.

        Changing a group will cause the layout to be recreated.
        """
        return self._user_group

    @group.setter
    def group(self, group: Group) -> None:
        self._user_group = group
        self._initialize_groups()
        self.group_cache.clear()
        self._update()

    @property
    def document(self) -> AbstractDocument:
        """Document to display.

        For :py:class:`~pyglet.text.layout.IncrementalTextLayout` it is
        far more efficient to modify a document in-place than to replace
        the document instance on the layout.
        """
        return self._document

    @document.setter
    def document(self, document: AbstractDocument) -> None:
        self._set_document(document)
        self._init_document()

    def _set_document(self, document: AbstractDocument) -> None:
        if self._document:
            self._document.remove_handlers(self)
            self._uninit_document()
        document.push_handlers(self)
        self._document = document

    @property
    def batch(self) -> Batch:
        """The Batch that this Layout is assigned to.

        If no Batch is assigned, an internal Batch is created and used.
        """
        return self._batch

    @batch.setter
    def batch(self, batch: Batch | None) -> None:
        if self._batch == batch:
            return

        if batch is None:
            self._batch = graphics.Batch()
            self._own_batch = True
            self._update()
        elif batch is not None:
            self._batch = batch
            self._own_batch = False
            self._update()

    @property
    def program(self) -> ShaderProgram:
        """The ShaderProgram that is assigned to this Layout.

        If set, the shader will impact all Glyphs. InlineElements will not be affected.
        """
        return self._program

    @program.setter
    def program(self, shader_program: ShaderProgram) -> None:
        if self._program == shader_program:
            return

        self._program = shader_program
        self._update()

    @property
    def x(self) -> float:
        """X coordinate of the layout.

        See also :py:attr:`~pyglet.text.layout.TextLayout.anchor_x`.
        """
        return self._x

    @x.setter
    def x(self, x: float) -> None:
        self._set_x(x)

    def _set_x(self, x: float) -> None:
        self._x = x
        self._update_translation()

    @property
    def y(self) -> float:
        """Y coordinate of the layout.

        See also :py:attr:`~pyglet.text.layout.TextLayout.anchor_y`.
        """
        return self._y

    @y.setter
    def y(self, y: float) -> None:
        self._set_y(y)

    def _set_y(self, y: float) -> None:
        self._y = y
        self._update_translation()

    @property
    def z(self) -> float:
        """Z coordinate of the layout."""
        return self._z

    @z.setter
    def z(self, z: float) -> None:
        self._set_z(z)

    def _set_z(self, z: float) -> None:
        self._z = z
        self._update_translation()

    @property
    def rotation(self) -> float:
        """Rotation of the layout in degrees. Rotated based on the anchor of the layout.

        Negative values will rotate in reverse.

        See :py:attr:`~pyglet.text.layout.TextLayout.anchor_x`, and :py:attr:`~pyglet.text.layout.TextLayout.anchor_y`.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: float) -> None:
        self._set_rotation(rotation)

    def _set_rotation(self, rotation: float) -> None:
        self._rotation = rotation
        self._update_rotation()

    def _update_rotation(self) -> None:
        for box in self._boxes:
            box.update_rotation(self._rotation)

    @property
    def position(self) -> tuple[float, float, float]:
        """The (X, Y, Z) coordinates of the layout, as a tuple.

        See also :py:attr:`~pyglet.text.layout.TextLayout.anchor_x`,
        and :py:attr:`~pyglet.text.layout.TextLayout.anchor_y`.
        """
        return self._x, self._y, self._z

    @position.setter
    def position(self, position: tuple[float, float, float]) -> None:
        self._set_position(position)

    def _set_position(self, position: tuple[float, float, float]) -> None:
        self._x, self._y, self._z = position
        self._update_translation()

    def _update_translation(self) -> None:
        for box in self._boxes:
            box.update_translation(self._x, self._y, self._z)

    def _update_anchor(self) -> None:
        self._anchor_left = self._get_left_anchor()
        self._anchor_bottom = self._get_bottom_anchor()

        anchor_y = self._get_top_anchor()

        for line in self._lines:
            acc_anchor_x = self._anchor_left
            for box in line.boxes:
                box.update_anchor(acc_anchor_x, anchor_y)
                acc_anchor_x += box.advance

    @property
    def visible(self) -> bool:
        """True if the layout will be visible when drawn."""
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        if value != self._visible:
            self._visible = value

            for box in self._boxes:
                box.update_visibility(value)

    @property
    def content_width(self) -> int:
        """Calculated width of the text in the layout.

        This is the actual width of the text in pixels, not the
        user defined :py:attr:`~pyglet.text.layout.TextLayout.width`.
        The content width may overflow the layout width if word-wrapping
        is not possible.
        """
        return self._content_width

    @property
    def content_height(self) -> int:
        """The calculated height of the text in the layout.

        This is the actual height of the text in pixels, not the
        user defined :py:attr:`~pyglet.text.layout.TextLayout.height`.
        """
        return self._content_height

    @property
    def width(self) -> int | None:
        """The defined maximum width of the layout in pixels, or None.

        If `multiline` and `wrap_lines` is True, the `width` defines where the
        text will be wrapped. If `multiline` is False or `wrap_lines` is False,
        this property has no effect.
        """
        return self._width

    @width.setter
    def width(self, width: int | None) -> None:
        self._width = width
        self._wrap_lines_invariant()
        self._update()

    @property
    def height(self) -> int | None:
        """The defined maximum height of the layout in pixels, or None.

        When `height` is not None, it affects the positioning of the
        text when :py:attr:`~pyglet.text.layout.TextLayout.anchor_y` and
        :py:attr:`~pyglet.text.layout.TextLayout.content_valign` are
        used.
        """
        return self._height

    @height.setter
    def height(self, height: int | None) -> None:
        self._height = height
        self._update()

    @property
    def multiline(self) -> bool:
        """Set if multiline layout is enabled.

        If ``multiline`` is False, newline and paragraph characters are ignored and
        text is not word-wrapped.
        If True, the text is word-wrapped only if the ``wrap_lines`` is True.
        """
        return self._multiline

    @multiline.setter
    def multiline(self, multiline: bool) -> None:
        self._multiline = multiline
        self._wrap_lines_invariant()
        self._update()

    @property
    def anchor_x(self) -> AnchorX:
        """Horizontal anchor alignment.

        This property determines the meaning of the ``x`` coordinate.

        The following values are supported:

        ``"left"`` (default)
            The X coordinate gives the position of the left edge of the layout.
        ``"center"``
            The X coordinate gives the position of the center of the layout.
        ``"right"``
            The X coordinate gives the position of the right edge of the layout.

        For the purposes of calculating the position resulting from this
        alignment, the width of the layout is taken to be ``width`` if ``multiline``
        is True and ``wrap_lines`` is True, otherwise ``content_width``.
        """
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, anchor_x: AnchorX) -> None:
        self._anchor_x = anchor_x
        self._update_anchor()

    @property
    def anchor_y(self) -> AnchorY:
        """Vertical anchor alignment.

        This property determines the meaning of the ``y`` coordinate.

        The following values are supported:

        ``"top"``
            The Y coordinate gives the position of the top edge of the layout.
        ``"center"``
            The Y coordinate gives the position of the center of the layout.
        ``"baseline"``
            The Y coordinate gives the position of the baseline of the first
            line of text in the layout.
        ``"bottom"`` (default)
            The Y coordinate gives the position of the bottom edge of the layout.

        For the purposes of calculating the position resulting from this
        alignment, the height of the layout is taken to be the smallest of
        ``height`` and ``content_height``.

        See also :py:attr:`~pyglet.text.layout.TextLayout.content_valign`.
        """
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, anchor_y: AnchorY) -> None:
        self._anchor_y = anchor_y
        self._update_anchor()

    @property
    def content_valign(self) -> ContentVAlign:
        """Vertical alignment of content within larger layout box.

        This property determines how content is positioned within the layout
        box when ``content_height`` is less than ``height``.

        The following values are supported:

        ``top`` (default)
            Content is aligned to the top of the layout box.
        ``center``
            Content is centered vertically within the layout box.
        ``bottom``
            Content is aligned to the bottom of the layout box.

        This property has no effect when ``content_height`` is greater
        than ``height`` (in which case the content is aligned to the top) or when
        ``height`` is ``None`` (in which case there is no vertical layout box
        dimension).
        """
        return self._content_valign

    @content_valign.setter
    def content_valign(self, content_valign: ContentVAlign) -> None:
        self._content_valign = content_valign
        self._update()

    @property
    def left(self) -> float:
        """The x-coordinate of the left side of the layout."""
        return self._x + self._anchor_left

    @property
    def right(self) -> float:
        """The x-coordinate of the right side of the layout."""
        if self._width is None:
            width = self._content_width
        else:
            width = self._width

        return self.left + width

    @property
    def bottom(self) -> float:
        """The y-coordinate of the bottom side of the layout."""
        return self._y + self._anchor_bottom

    @property
    def top(self) -> float:
        """The y-coordinate of the top side of the layout."""
        if self._height is None:
            height = self._content_height
        else:
            height = self._height

        return self.bottom + height

    def _wrap_lines_invariant(self) -> None:
        self._wrap_lines = self._multiline and self._wrap_lines_flag
        assert not self._wrap_lines or self._width, \
            "When the parameters 'multiline' and 'wrap_lines' are True, the parameter 'width' must be a number."

    def _parse_distance(self, distance: str | int | float | None) -> int | None:  # noqa: PYI041
        if distance is None:
            return None
        return _parse_distance(distance, self._dpi)

    def begin_update(self) -> None:
        """Indicate that a number of changes to the layout or document are about to occur.

        Changes to the layout or document between calls to `begin_update` and
        `end_update` do not trigger any costly relayout of text.  Relayout of
        all changes is performed when `end_update` is called.

        Note that between the `begin_update` and `end_update` calls, values
        such as `content_width` and `content_height` are undefined (i.e., they
        may or may not be updated to reflect the latest changes).
        """
        self._update_enabled = False

    def end_update(self) -> None:
        """Perform pending layout changes since `begin_update`.

        See `begin_update`.
        """
        self._update_enabled = True
        self._update()

    @property
    def dpi(self) -> float:
        """Get DPI used by this layout."""
        return self._dpi

    @dpi.setter
    def dpi(self, value: float) -> None:
        self._dpi = value
        self._update()

    def delete(self) -> None:
        """Deletes all vertices and boxes associated with the layout."""
        for box in self._boxes:
            box.delete(self)

        self._vertex_lists.clear()
        self._boxes.clear()

    def get_as_texture(self, min_filter: int=GL_NEAREST, mag_filter: int=GL_NEAREST) -> Texture:
        """Utilizes a :py:class:`~pyglet.image.framebuffer.Framebuffer` to draw the current layout into a texture.

        .. warning:: Usage is recommended only if you understand how texture generation affects your application.
            Improper use will cause texture memory leaks and performance degradation.

        .. note:: Does not include InlineElements.

        Returns:
            A new texture with the layout drawn into it.

        .. versionadded:: 2.0.11
        """
        framebuffer = pyglet.image.Framebuffer()
        temp_pos = self.position
        width = int(round(self._content_width))
        height = int(round(self._content_height))
        texture = pyglet.image.Texture.create(width, height, min_filter=min_filter, mag_filter=mag_filter)
        depth_buffer = pyglet.image.buffer.Renderbuffer(width, height, GL_DEPTH_COMPONENT)
        framebuffer.attach_texture(texture)
        framebuffer.attach_renderbuffer(depth_buffer, attachment=GL_DEPTH_ATTACHMENT)

        self.position = (0 - self._anchor_left, 0 - self._anchor_bottom, 0)
        framebuffer.bind()
        self.draw()
        framebuffer.unbind()

        self.position = temp_pos
        return texture

    def draw(self) -> None:
        """Draw this text layout.

        .. note:: This method performs very badly if a batch was supplied to the constructor.
            If you add this layout to a batch, you should ideally use only the batch's draw method.

        .. note:: If this is not its own batch, InlineElements will not be drawn.

        """
        if self._own_batch:
            self._batch.draw()
        else:
            self._batch.draw_subset(self._vertex_lists)

    def _get_lines(self) -> list[_Line]:
        len_text = len(self._document.text)
        glyphs, offsets = self._get_glyphs()
        owner_runs = runlist.RunList(len_text, None)
        self._get_owner_runs(owner_runs, glyphs, 0, len_text)
        lines = list(self._flow_glyphs(glyphs, offsets, owner_runs, 0, len_text))
        self._content_width = 0
        self._line_count = len(lines)
        self._flow_lines(lines, 0, self._line_count)
        return lines

    def _update(self) -> None:
        if not self._update_enabled:
            return

        for box in self._boxes:
            box.delete(self)

        self._vertex_lists.clear()
        self._boxes.clear()
        self._lines.clear()
        self.group_cache.clear()

        if not self._document or not self._document.text:
            self._ascent = 0
            self._descent = 0
            self._anchor_left = 0
            self._anchor_bottom = 0
            return

        self._lines = self._get_lines()
        self._ascent = self._lines[0].ascent
        self._descent = self._lines[0].descent

        colors_iter = self._document.get_style_runs("color")

        background_iter = self._document.get_style_runs("background_color")

        self._anchor_left = self._get_left_anchor()
        self._anchor_bottom = self._get_bottom_anchor()
        anchor_top = self._get_top_anchor()

        context = _StaticLayoutContext(self, self._document, colors_iter, background_iter)

        for line in self._lines:
            self._boxes.extend(line.boxes)
            self._create_vertex_lists(line.x, line.y, self._anchor_left, anchor_top, line.start, line.boxes, context)

    def _update_color(self, start: int, end: int) -> None:
        # This function usually is only called by Labels/HTML when updating just colors.
        colors_iter = self._document.get_style_runs("color")

        colors = []
        for iter_start, iter_end, color in colors_iter.ranges(start, end):
            colors.extend(color * (iter_end - iter_start))

        char_index = 0

        # Search all boxes for the characters that are going to be updated.
        for box in self._boxes:
            box_length = box.length  # Number of glyphs in the box

            if char_index + box_length > start and char_index < end:
                box_start = max(0, start - char_index)
                box_end = min(box_length, end - char_index)
                box.update_colors(colors, box_start, box_end)

            char_index += box_length

    def _get_left_anchor(self) -> int:
        """Returns the anchor for the X axis from the left."""
        if self._multiline:
            width = self._width if self._wrap_lines else self._content_width
        else:
            width = self._content_width

        if self._anchor_x == "left":
            return 0
        if self._anchor_x == "center":
            return -(width // 2)
        if self._anchor_x == "right":
            return -width

        msg = '`anchor_x` must be either "left", "center", or "right".'
        raise Exception(msg)

    def _get_top_anchor(self) -> float:
        """Returns the anchor for the Y axis from the top."""
        if self._height is None:
            height = self._content_height
            offset = 0
        else:
            height = self._height
            if self._content_valign == "top":
                offset = 0
            elif self._content_valign == "bottom":
                offset = max(0, self._height - self._content_height)
            elif self._content_valign == "center":
                offset = max(0, self._height - self._content_height) // 2
            else:
                msg = '`content_valign` must be either "top", "bottom", or "center".'
                raise Exception(msg)

        if self._anchor_y == "top":
            return -offset
        if self._anchor_y == "baseline":
            return self._ascent - offset
        if self._anchor_y == "bottom":
            return height - offset
        if self._anchor_y == "center":
            if self._line_count == 1 and self._height is None:
                # This "looks" more centered than considering all of the descent.
                return self._ascent // 2 - self._descent // 4

            return height // 2 - offset

        msg = '`anchor_y` must be either "top", "bottom", "center", or "baseline".'
        raise Exception(msg)

    def _get_bottom_anchor(self) -> float:
        """Returns the anchor for the Y axis from the bottom."""
        if self._height is None:
            height = self._content_height
            offset = 0
        else:
            height = self._height
            if self._content_valign == "top":
                offset = min(0, self._height - self._content_height)
            elif self._content_valign == "bottom":
                offset = 0
            elif self._content_valign == "center":
                offset = min(0, self._height - self._content_height) // 2
            else:
                msg = '`content_valign` must be either "top", "bottom", or "center".'
                raise Exception(msg)

        if self._anchor_y == "top":
            return -height + offset
        if self._anchor_y == "baseline":
            return -height + self._ascent
        if self._anchor_y == "bottom":
            return 0
        if self._anchor_y == "center":
            if self._line_count == 1 and self._height is None:
                # This "looks" more centered than considering all of the descent.
                return (self._ascent // 2 - self._descent // 4) - height

            return offset - height // 2

        msg = '`anchor_y` must be either "top", "bottom", "center", or "baseline".'
        raise Exception(msg)

    def _init_document(self) -> None:
        self._update()

    def _uninit_document(self) -> None:
        pass

    def on_insert_text(self, start: int, text: str) -> None:  # noqa: ARG002
        """Event handler for `AbstractDocument.on_insert_text`.

        The event handler is bound by the text layout; there is no need for
        applications to interact with this method.
        """
        self._init_document()

    def on_delete_text(self, start: int, end: int) -> None:  # noqa: ARG002
        """Event handler for `AbstractDocument.on_delete_text`.

        The event handler is bound by the text layout; there is no need for
        applications to interact with this method.
        """
        self._init_document()

    def on_style_text(self, start: int, end: int, attributes: dict[str, Any]) -> None:
        """Event handler for `AbstractDocument.on_style_text`.

        The event handler is bound by the text layout; there is no need for
        applications to interact with this method.
        """
        # To save performance when lerping colors, only update color values instead of recreating layout.
        if len(attributes) == 1 and "color" in attributes:
            self._update_color(start, end)
        else:
            self._init_document()

    def _get_glyphs(self) -> tuple[list[_InlineElementBox | Glyph], list[tuple[int, int]]]:
        glyphs = []
        offsets = []
        runs = runlist.ZipRunIterator((
            self._document.get_font_runs(dpi=self._dpi),
            self._document.get_element_runs()))
        text = self._document.text
        for start, end, (font, element) in runs.ranges(0, len(text)):
            if element:
                glyphs.append(_InlineElementBox(element))
                offsets.append(_empty_pos)
            else:
                char_glyphs, char_offsets = font.get_glyphs(text[start:end])
                glyphs.extend(char_glyphs)
                offsets.extend(char_offsets)

        return glyphs, offsets

    def _get_owner_runs(self, owner_runs: runlist.RunList, glyphs: list[_InlineElementBox | Glyph], start: int,
                        end: int) -> None:
        owner = glyphs[start].owner
        run_start = start

        # TODO avoid glyph slice on non-incremental
        for i, glyph in enumerate(glyphs[start:end]):
            if owner != glyph.owner:
                owner_runs.set_run(run_start, i + start, owner)
                owner = glyph.owner
                run_start = i + start
        owner_runs.set_run(run_start, end, owner)

    def _flow_glyphs_wrap(self, glyphs: list[_InlineElementBox | Glyph],
                          offsets: list[GlyphPosition],
                          owner_runs: runlist.RunList, start: int,
                          end: int) -> Iterator[_Line]:
        # Word-wrap styled text into lines of fixed width.
        # Fits glyphs in range start to end into Lines which are then yielded.
        owner_iterator = owner_runs.get_run_iterator().ranges(start, end)

        font_iterator = self._document.get_font_runs(dpi=self._dpi)

        align_iterator = runlist.FilteredRunIterator(self._document.get_style_runs("align"),
                                                     lambda value: value in ("left", "right", "center"),
                                                     "left")
        if self._width is None:
            wrap_iterator = runlist.ConstRunIterator(len(self.document.text), False)
        else:
            wrap_iterator = runlist.FilteredRunIterator(self._document.get_style_runs("wrap"),
                                                        lambda value: value in (True, False, "char", "word"),
                                                        True)
        margin_left_iterator = runlist.FilteredRunIterator(self._document.get_style_runs("margin_left"),
                                                           lambda value: value is not None, 0)
        margin_right_iterator = runlist.FilteredRunIterator(self._document.get_style_runs("margin_right"),
                                                            lambda value: value is not None, 0)
        indent_iterator = runlist.FilteredRunIterator(self._document.get_style_runs("indent"),
                                                      lambda value: value is not None, 0)
        kerning_iterator = runlist.FilteredRunIterator(self._document.get_style_runs("kerning"),
                                                       lambda value: value is not None, 0)
        tab_stops_iterator = runlist.FilteredRunIterator(self._document.get_style_runs("tab_stops"),
                                                         lambda value: value is not None, [])
        line = _Line(start)
        line.align = align_iterator[start]
        line.margin_left = self._parse_distance(margin_left_iterator[start])
        line.margin_right = self._parse_distance(margin_right_iterator[start])
        if start == 0 or self.document.text[start - 1] in "\n\u2029":
            line.paragraph_begin = True
            line.margin_left += self._parse_distance(indent_iterator[start])
        wrap = wrap_iterator[start]
        if self._wrap_lines:
            width = self._width - line.margin_left - line.margin_right

        # Current right-most x position in line being laid out.
        x = 0

        # Boxes accumulated but not yet committed to a line.
        run_accum = []
        run_accum_width = 0

        # Amount of whitespace accumulated at end of line
        eol_ws = 0

        # Iterate over glyph owners (texture states); these form GlyphBoxes,
        # but broken into lines.
        font = None
        for start, end, owner in owner_iterator:
            font = font_iterator[start]

            # Glyphs accumulated in this owner but not yet committed to a
            # line.
            owner_accum = []
            owner_accum_width = 0

            # Glyphs accumulated in this owner AND also committed to the
            # current line (some whitespace has followed all of the committed
            # glyphs).
            owner_accum_commit = []
            owner_accum_commit_width = 0

            # Ignore kerning of first glyph on each line
            nokern = True

            # Current glyph index
            index = start

            # Iterate over glyphs in this owner run.  `text` is the
            # corresponding character data for the glyph, and is used to find
            # whitespace and newlines.
            for (text, glyph, offset) in zip(self.document.text[start:end], glyphs[start:end], offsets[start:end]):
                if nokern:
                    kern = 0
                    nokern = False
                else:
                    kern = self._parse_distance(kerning_iterator[index])

                if wrap != "char" and text in "\u0020\u200b\t":
                    # Whitespace: commit pending runs to this line.
                    for run in run_accum:
                        line.add_box(run)
                    run_accum = []
                    run_accum_width = 0

                    if text == "\t":
                        # Fix up kern for this glyph to align to the next tab stop
                        for tab_stop in tab_stops_iterator[index]:
                            tab_stop = self._parse_distance(tab_stop)
                            if tab_stop > x + line.margin_left:
                                break
                        else:
                            # No more tab stops, tab to 100 pixels
                            tab = 50.
                            tab_stop = (((x + line.margin_left) // tab) + 1) * tab
                        kern = int(tab_stop - x - line.margin_left - glyph.advance)

                    owner_accum.append((kern, glyph, offset))
                    owner_accum_commit.extend(owner_accum)
                    owner_accum_commit_width += owner_accum_width + glyph.advance + kern + offset.x_advance
                    eol_ws += glyph.advance + kern + offset.x_advance

                    owner_accum = []
                    owner_accum_width = 0

                    x += glyph.advance + kern + offset.x_advance
                    index += 1

                    # The index at which the next line will begin (the
                    # current index, because this is the current best
                    # breakpoint).
                    next_start = index
                else:
                    new_paragraph = text in "\n\u2029"
                    new_line = (text == "\u2028") or new_paragraph
                    if (wrap and self._wrap_lines and x + kern + glyph.advance + offset.x_advance >= width) or new_line:
                        # Either the pending runs have overflowed the allowed
                        # line width or a newline was encountered.  Either
                        # way, the current line must be flushed.

                        if new_line or wrap == "char":
                            # Forced newline or char-level wrapping.  Commit
                            # everything pending without exception.
                            for run in run_accum:
                                line.add_box(run)
                            run_accum = []
                            run_accum_width = 0
                            owner_accum_commit.extend(owner_accum)
                            owner_accum_commit_width += owner_accum_width
                            owner_accum = []
                            owner_accum_width = 0

                            line.length += 1
                            next_start = index
                            if new_line:
                                next_start += 1

                        # Create the _GlyphBox for the committed glyphs in the
                        # current owner.
                        if owner_accum_commit:
                            line.add_box(_GlyphBox(owner, font, owner_accum_commit, owner_accum_commit_width))
                            owner_accum_commit = []
                            owner_accum_commit_width = 0

                        if new_line and not line.boxes:
                            # Empty line: give it the current font's default
                            # line-height.
                            line.ascent = font.ascent
                            line.descent = font.descent

                        # Flush the line, unless nothing got committed, in
                        # which case it's a really long string of glyphs
                        # without any breakpoints (in which case it will be
                        # flushed at the earliest breakpoint, not before
                        # something is committed).
                        if line.boxes or new_line:
                            # Trim line width of whitespace on right-side.
                            line.width -= eol_ws
                            if new_paragraph:
                                line.paragraph_end = True
                            yield line
                            try:
                                line = _Line(next_start)
                                line.align = align_iterator[next_start]
                                line.margin_left = self._parse_distance(margin_left_iterator[next_start])
                                line.margin_right = self._parse_distance(margin_right_iterator[next_start])
                            except IndexError:
                                # XXX This used to throw StopIteration in some cases, causing the
                                # final part of this method not to be executed. Refactoring
                                # required to fix this
                                return
                            if new_paragraph:
                                line.paragraph_begin = True

                            # Remove kern from first glyph of line
                            if run_accum and hasattr(run_accum, "glyphs") and run_accum.glyphs:
                                k, g = run_accum[0].glyphs[0]
                                run_accum[0].glyphs[0] = (0, g, _empty_pos)
                                run_accum_width -= k
                            elif owner_accum:
                                k, g, _ = owner_accum[0]
                                owner_accum[0] = (0, g, _empty_pos)
                                owner_accum_width -= k
                            else:
                                nokern = True

                            x = run_accum_width + owner_accum_width
                            if self._wrap_lines:
                                width = self._width - line.margin_left - line.margin_right

                    if isinstance(glyph, _AbstractBox):
                        # Glyph is already in a box. XXX Ignore kern?
                        run_accum.append(glyph)
                        run_accum_width += glyph.advance + offset.x_advance
                        x += glyph.advance + offset.x_advance
                    elif new_paragraph:
                        # New paragraph started, update wrap style
                        wrap = wrap_iterator[next_start]
                        line.margin_left += self._parse_distance(indent_iterator[next_start])
                        if self._wrap_lines:
                            width = self._width - line.margin_left - line.margin_right
                    elif not new_line:
                        # If the glyph was any non-whitespace, non-newline
                        # character, add it to the pending run.
                        owner_accum.append((kern, glyph, offset))
                        owner_accum_width += glyph.advance + kern + offset.x_advance
                        x += glyph.advance + kern + offset.x_advance
                    index += 1
                    eol_ws = 0

            # The owner run is finished; create GlyphBoxes for the committed
            # and pending glyphs.
            if owner_accum_commit:
                line.add_box(_GlyphBox(owner, font, owner_accum_commit, owner_accum_commit_width))
            if owner_accum:
                run_accum.append(_GlyphBox(owner, font, owner_accum, owner_accum_width))
                run_accum_width += owner_accum_width

        # All glyphs have been processed: commit everything pending and flush
        # the final line.
        for run in run_accum:
            line.add_box(run)

        if not line.boxes:
            # Empty line gets font's line-height
            if font is None:
                font = self._document.get_font(0, dpi=self._dpi)
            line.ascent = font.ascent
            line.descent = font.descent

        yield line

    def _flow_glyphs_single_line(self, glyphs: list[_InlineElementBox | Glyph],
                                 offsets: list[GlyphPosition],
                                 owner_runs: runlist.RunList,
                                 start: int, end: int) -> Iterator[_Line]:
        owner_iterator = owner_runs.get_run_iterator().ranges(start, end)
        font_iterator = self.document.get_font_runs(dpi=self._dpi)
        kern_iterator = runlist.FilteredRunIterator(self.document.get_style_runs("kerning"),
                                                    lambda value: value is not None, 0)

        line = _Line(start)
        font = font_iterator[0]

        if self._width:
            align_iterator = runlist.FilteredRunIterator(
                self._document.get_style_runs("align"),
                lambda value: value in ("left", "right", "center"),
                "left")
            line.align = align_iterator[start]

        for start, end, owner in owner_iterator:
            font = font_iterator[start]
            width = 0
            owner_glyphs = []
            for kern_start, kern_end, kern in kern_iterator.ranges(start, end):
                gs = glyphs[kern_start:kern_end]
                os = offsets[kern_start:kern_end]
                width += sum([g.advance for g in gs])
                width += kern * (kern_end - kern_start)
                width += sum([o.x_advance for o in os])
                owner_glyphs.extend(zip([kern] * (kern_end - kern_start), gs, os))
            if owner is None:
                # Assume glyphs are already boxes.
                for _, glyph, _ in owner_glyphs:
                    line.add_box(glyph)
            else:
                line.add_box(_GlyphBox(owner, font, owner_glyphs, width))

        if not line.boxes:
            line.ascent = font.ascent
            line.descent = font.descent

        line.paragraph_begin = line.paragraph_end = True

        yield line

    def _flow_lines(self, lines: list[_Line], start: int, end: int) -> int:
        margin_top_iterator = runlist.FilteredRunIterator(self._document.get_style_runs("margin_top"),
                                                          lambda value: value is not None, 0)
        margin_bottom_iterator = runlist.FilteredRunIterator(self._document.get_style_runs("margin_bottom"),
                                                             lambda value: value is not None, 0)
        line_spacing_iterator = self._document.get_style_runs("line_spacing")
        leading_iterator = runlist.FilteredRunIterator(self._document.get_style_runs("leading"),
                                                       lambda value: value is not None, 0)

        if start == 0:
            y = 0
        else:
            line = lines[start - 1]
            line_spacing = self._parse_distance(line_spacing_iterator[line.start])
            leading = self._parse_distance(leading_iterator[line.start])

            y = line.y
            if line_spacing is None:
                y += line.descent
            if line.paragraph_end:
                y -= self._parse_distance(margin_bottom_iterator[line.start])

        line_index = start
        for line in lines[start:]:
            if line.paragraph_begin:
                y -= self._parse_distance(margin_top_iterator[line.start])
                line_spacing = self._parse_distance(line_spacing_iterator[line.start])
                leading = self._parse_distance(leading_iterator[line.start])
            else:
                y -= leading

            if line_spacing is None:
                y -= line.ascent
            else:
                y -= line_spacing
            if line.align == "left" or line.width > self.width:
                line.x = line.margin_left
            elif line.align == "center":
                line.x = (self.width - line.margin_left - line.margin_right - line.width) // 2 + line.margin_left
            elif line.align == "right":
                line.x = self.width - line.margin_right - line.width

            self._content_width = max(self._content_width, line.width + line.margin_left)

            if line.y == y and line_index >= end:
                # Early exit: all invalidated lines have been reflowed and the
                # next line has no change (therefore subsequent lines do not
                # need to be changed).
                break
            line.y = y

            if line_spacing is None:
                y += line.descent
            if line.paragraph_end:
                y -= self._parse_distance(margin_bottom_iterator[line.start])

            line_index += 1
        else:
            self._content_height = -y

        return line_index

    def _create_vertex_lists(self, line_x: float, line_y: float, anchor_x: float, anchor_y: float, i: int,
                             boxes: list[_AbstractBox], context: _LayoutContext) -> None:
        acc_anchor_x = anchor_x
        # GlyphBoxes (boxes) are collection of Glyphs/Inline Elements. A line can have multiple GlyphBoxes.
        for box in boxes:
            box.place(self, i, self._x, self._y, self._z, line_x, line_y, self._rotation, self._visible, acc_anchor_x,
                      anchor_y, context)
            i += box.length
            acc_anchor_x += box.advance

    def get_line_count(self) -> int:
        """Get the number of lines in the text layout."""
        return self._line_count
