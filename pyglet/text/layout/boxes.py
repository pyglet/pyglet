"""Internal text layout boxes, contexts, and line data."""

from __future__ import annotations

import re
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, NamedTuple, Pattern, Protocol, Sequence

from pyglet.enums import GeometryMode
from pyglet.font.base import GlyphPosition
from pyglet.text import runlist
from pyglet.text.effects import LinearGradient

_VertexData = dict[str, Sequence[float | int | bool]]

_BACKGROUND_DEPTH_LAYER = -3
_SHADOW_DEPTH_LAYER = -2
_STROKE_DEPTH_LAYER = -1
_GLYPH_DEPTH_LAYER = 0
_FOREGROUND_DECORATION_DEPTH_LAYER = 1


class _DecorationData(NamedTuple):
    vertices: list[float]
    colors: list[int]


class _DecorationGeometry(NamedTuple):
    background: _DecorationData
    underline: _DecorationData
    strikethrough: _DecorationData


if TYPE_CHECKING:
    from pyglet.customtypes import HorizontalAlign
    from pyglet.font.base import Font, Glyph
    from pyglet.graphics import Texture
    from pyglet.graphics.vertexdomain import VertexList
    from pyglet.text.document import AbstractDocument, InlineElement
    from pyglet.text.runlist import AbstractRunIterator, RunIterator
    from .base import TextLayout


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
    def __init__(
        self,
        layout: TextLayout,
        document: AbstractDocument,
        colors_iter: RunIterator,
        background_iter: AbstractRunIterator,
    ) -> None:
        self.layout = layout
        self.colors_iter = colors_iter
        self.stroke_iter = document.get_style_runs("stroke") if document.has_style_run("stroke") else None
        if self._uses_background_override() or any(
            document.has_style_run(attribute) for attribute in ("background_color", "underline", "strikethrough")
        ):
            self.decoration_iter = runlist.ZipRunIterator(
                (
                    background_iter,
                    document.get_style_runs("underline"),
                    document.get_style_runs("strikethrough"),
                ),
            )
        else:
            self.decoration_iter = None
        self.shadow_iter = document.get_style_runs("shadow") if document.has_style_run("shadow") else None
        self.baseline_iter = runlist.FilteredRunIterator(
            document.get_style_runs("baseline"), lambda value: value is not None, 0,
        )

    def _uses_background_override(self) -> bool:
        return False

    @abstractmethod
    def add_list(self, vertex_list: VertexList) -> None: ...

    @abstractmethod
    def add_box(self, box: _AbstractBox) -> None: ...


class _StaticLayoutContext(_LayoutContext):
    def __init__(
        self,
        layout: TextLayout,
        document: AbstractDocument,
        colors_iter: RunIterator,
        background_iter: AbstractRunIterator,
    ) -> None:
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
    def place(
        self,
        layout: TextLayout,
        i: int,
        x: float,
        y: float,
        z: float,
        line_x: float,
        line_y: float,
        rotation: float,
        visible: bool,
        anchor_x: float,
        anchor_y: float,
        context: _LayoutContext,
    ) -> None: ...

    @abstractmethod
    def update_translation(self, x: float, y: float, z: float) -> None: ...

    @abstractmethod
    def update_colors(self, colors: list[int], start: int, end: int) -> None: ...

    @abstractmethod
    def update_view_translation(self, translate_x: float, translate_y: float) -> None: ...

    @abstractmethod
    def update_rotation(self, rotation: float) -> None: ...

    @abstractmethod
    def update_visibility(self, visible: bool) -> None: ...

    @abstractmethod
    def update_anchor(self, anchor_x: float, anchor_y: float) -> None: ...

    @abstractmethod
    def delete(self, layout: TextLayout) -> None: ...

    @abstractmethod
    def get_position_in_box(self, x: float) -> int: ...

    @abstractmethod
    def get_point_in_box(self, position: int) -> float: ...


class _GlyphBox(_AbstractBox):
    owner: Texture
    font: Font
    glyphs: list[tuple[int, Glyph, GlyphPosition]]
    advance: int
    vertex_lists: list[_LayoutVertexList]
    _glyph_vertex_list: _LayoutVertexList | None

    def __init__(
        self,
        owner: Texture,
        font: Font,
        glyphs: list[tuple[int, Glyph, GlyphPosition]],
    ) -> None:
        """Create a run of glyphs sharing the same texture.

        Args:
            owner:
                Texture of all glyphs in this run.
            font:
                Font of all glyphs in this run.
            glyphs:
                Pairs of ``(kern, glyph)``, where ``kern`` gives horizontal
                displacement of the glyph in pixels (typically 0).
            offsets:
                A list of all position transformations done to each glyph.
        """
        advance = sum(self._glyph_advance(kern, glyph, glyph_pos) for kern, glyph, glyph_pos in glyphs)
        super().__init__(font.ascent, font.descent, advance, len(glyphs))
        assert owner
        self.owner = owner
        self.font = font
        self.glyphs = glyphs
        self.vertex_lists = []
        self._glyph_vertex_list = None

    @staticmethod
    def _glyph_advance(kern: float, glyph: Glyph, glyph_pos: GlyphPosition) -> int:
        """Return the pixel-rounded advance used to position glyph quads."""
        return round(kern) + round(glyph.advance + glyph_pos.x_advance)

    @staticmethod
    def _interpolate_gradient(
        gradient: LinearGradient,
        position: float,
        start: float,
        span: float,
    ) -> tuple[int, int, int, int]:
        t = 0.0 if span == 0 else min(max((position - start) / span, 0.0), 1.0)
        return tuple(round(a + (b - a) * t) for a, b in zip(gradient.start, gradient.end, strict=True))

    def _add_vertex_list(self, vertex_list: _LayoutVertexList | VertexList, context: _LayoutContext) -> None:
        self.vertex_lists.append(vertex_list)
        context.add_list(vertex_list)

    def _create_glyph_geometry(
        self,
        layout: TextLayout,
        start_index: int,
        line_x: float,
        line_y: float,
        context: _LayoutContext,
    ) -> tuple[list[float], list[float], int]:
        """Build the position and texture attributes for the fill glyphs."""
        vertices = []
        tex_coords = []
        baseline = 0
        x1 = round(line_x)
        for start, end, baseline_ in context.baseline_iter.ranges(start_index, start_index + self.length):
            baseline = layout._parse_distance(baseline_) or 0  # noqa: SLF001
            glyphs = self.glyphs[start - start_index : end - start_index]
            assert len(glyphs) == end - start
            y1 = round(line_y + baseline)
            for kern, glyph, glyph_pos in glyphs:
                x1 += round(kern)
                v0, v1, v2, v3 = glyph.vertices
                # Translate the whole glyph as a block. Rounding v0/v1/v2/v3 can distort vertices.
                gx = x1 + round(glyph_pos.x_offset)
                gy = y1 + round(glyph_pos.y_offset)
                vertices.extend(
                    [
                        v0 + gx,
                        v1 + gy,
                        0,
                        v2 + gx,
                        v1 + gy,
                        0,
                        v2 + gx,
                        v3 + gy,
                        0,
                        v0 + gx,
                        v3 + gy,
                        0,
                    ],
                )
                tex_coords.extend(glyph.tex_coords)
                x1 += round(glyph.advance + glyph_pos.x_advance)
        return vertices, tex_coords, baseline

    def _create_glyph_colors(
        self,
        start_index: int,
        vertices: list[float],
        context: _LayoutContext,
    ) -> list[int]:
        # Text color. The text shaders interpolate the color attribute, so a
        # gradient only needs different colors at each side of a glyph quad.
        colors = []
        for start, end, color in context.colors_iter.ranges(start_index, start_index + self.length):
            if color is None:
                color = (0, 0, 0, 255)  # noqa: PLW2901
            colors.extend(self._create_range_colors(color, start, end, start_index, vertices, "Color"))
        return colors

    def _create_range_colors(
        self,
        color: tuple[int, int, int, int] | LinearGradient,
        start: int,
        end: int,
        start_index: int,
        vertices: list[float],
        effect_name: str,
    ) -> list[int]:
        """Create quad colors for a solid or gradient style range."""
        character_count = end - start
        if isinstance(color, LinearGradient):
            start_glyph = start - start_index
            end_glyph = end - start_index
            left_edge = vertices[start_glyph * 12]
            right_edge = vertices[(end_glyph - 1) * 12 + 6]
            span = right_edge - left_edge
            colors = []
            for glyph_idx in range(start_glyph, end_glyph):
                left = vertices[glyph_idx * 12]
                right = vertices[glyph_idx * 12 + 6]
                left_color = self._interpolate_gradient(color, left, left_edge, span)
                right_color = self._interpolate_gradient(color, right, left_edge, span)
                colors.extend(left_color * 2 + right_color * 2)
            return colors
        if len(color) != 4:
            msg = f"{effect_name} color requires 4 values (R, G, B, A). Value received: {color}"
            raise ValueError(msg)
        return list(color * (character_count * 4))

    @staticmethod
    def _create_vertex_data(
        layout: TextLayout,
        vertices: Sequence[float],
        tex_coords: Sequence[float],
        colors: Sequence[int],
        translation: tuple[float, float, float],
        rotation: float,
        visible: bool,
        anchor_x: float,
        anchor_y: float,
        vertex_count: int,
    ) -> _VertexData:
        vertex_data: _VertexData = {
            "position": vertices,
            "translation": (*translation, layout.get_depth_offset(_GLYPH_DEPTH_LAYER)) * vertex_count,
            "colors": colors,
            "tex_coords": tex_coords,
            "rotation": (rotation,) * vertex_count,
            "visible": (visible,) * vertex_count,
            "anchor": (anchor_x, anchor_y) * vertex_count,
        }
        if "view_translation" in layout.program.attributes:
            vertex_data["view_translation"] = (0, 0, 0) * vertex_count
        return vertex_data

    @staticmethod
    def _set_depth_layer(
        layout: TextLayout,
        vertex_data: _VertexData,
        vertex_count: int,
        layer: int,
    ) -> _VertexData:
        translation = vertex_data["translation"]
        return vertex_data | {"translation": (*translation[:3], layout.get_depth_offset(layer)) * vertex_count}

    def _place_shadow(
        self,
        layout: TextLayout,
        start_index: int,
        vertices: list[float],
        indices: list[int],
        vertex_data: _VertexData,
        context: _LayoutContext,
    ) -> None:
        # A shadow needs no additional glyph rendering: it uses the same atlas
        # texture and geometry, at an offset below the fill layer.
        if context.shadow_iter is None:
            return
        shadow_colors = None
        shadow_vertices = None
        for start, end, shadow in context.shadow_iter.ranges(start_index, start_index + self.length):
            character_count = end - start
            if shadow is None:
                if shadow_colors is not None:
                    shadow_colors.extend((0, 0, 0, 0) * (character_count * 4))
                continue
            if len(shadow.offset) != 2:
                msg = f"Shadow offset requires 2 values (X, Y). Value received: {shadow.offset}"
                raise ValueError(msg)
            if shadow_colors is None:
                shadow_colors = list((0, 0, 0, 0) * ((start - start_index) * 4))
                shadow_vertices = list(vertices)
            shadow_colors.extend(
                self._create_range_colors(shadow.color, start, end, start_index, vertices, "Shadow"),
            )
            offset_start = (start - start_index) * 12
            offset_end = offset_start + character_count * 12
            for vertex_index in range(offset_start, offset_end, 3):
                shadow_vertices[vertex_index] += shadow.offset[0]
                shadow_vertices[vertex_index + 1] += shadow.offset[1]

        if shadow_colors is None:
            return

        assert shadow_vertices is not None
        shadow_data = self._set_depth_layer(
            layout,
            vertex_data | {"position": shadow_vertices, "colors": shadow_colors},
            self.length * 4,
            _SHADOW_DEPTH_LAYER,
        )
        shadow_list = layout.program.vertex_list_indexed(
            self.length * 4,
            GeometryMode.TRIANGLES,
            indices,
            layout.batch,
            layout.get_effect_group(self.owner, order=1 if layout.depth_sorting else 0),
            **shadow_data,
        )
        self._add_vertex_list(shadow_list, context)

    def _place_strokes(
        self,
        layout: TextLayout,
        start_index: int,
        line_x: float,
        line_y: float,
        baseline: int,
        vertices: list[float],
        translation: tuple[float, float, float],
        rotation: float,
        visible: bool,
        anchor_x: float,
        anchor_y: float,
        context: _LayoutContext,
    ) -> None:
        # Supported font backends may provide a second, stroked glyph mask. It is drawn
        # in a lower-order group so the regular fill glyph remains on top.
        if context.stroke_iter is None:
            return
        stroke_x = round(line_x)
        glyph_index = 0
        for start, end, stroke in context.stroke_iter.ranges(start_index, start_index + self.length):
            if stroke is None:
                continue

            range_start_glyph = start - start_index
            range_end_glyph = end - start_index
            while glyph_index < range_start_glyph:
                kern, glyph, glyph_pos = self.glyphs[glyph_index]
                stroke_x += round(kern)
                stroke_x += round(glyph.advance + glyph_pos.x_advance)
                glyph_index += 1

            gradient_span = None
            if isinstance(stroke.color, LinearGradient):
                gradient_left = vertices[range_start_glyph * 12]
                gradient_right = vertices[(range_end_glyph - 1) * 12 + 6]
                gradient_span = gradient_right - gradient_left

            for glyph_index in range(range_start_glyph, range_end_glyph):
                kern, glyph, glyph_pos = self.glyphs[glyph_index]
                stroke_x += round(kern)
                stroke_glyph = self.font.get_stroke_glyph(glyph, stroke.size, stroke.join)
                if stroke_glyph is not None:
                    if gradient_span is not None:
                        left = vertices[glyph_index * 12]
                        right = vertices[glyph_index * 12 + 6]
                        stroke_color = (
                            self._interpolate_gradient(stroke.color, left, gradient_left, gradient_span) * 2
                            + self._interpolate_gradient(stroke.color, right, gradient_left, gradient_span) * 2
                        )
                    else:
                        stroke_color = stroke.color * 4
                    v0, v1, v2, v3 = stroke_glyph.vertices
                    gx = stroke_x + round(glyph_pos.x_offset)
                    gy = round(line_y + baseline + glyph_pos.y_offset)
                    stroke_vertices = [
                        v0 + gx,
                        v1 + gy,
                        0,
                        v2 + gx,
                        v1 + gy,
                        0,
                        v2 + gx,
                        v3 + gy,
                        0,
                        v0 + gx,
                        v3 + gy,
                        0,
                    ]
                    stroke_data = self._create_vertex_data(
                        layout,
                        stroke_vertices,
                        stroke_glyph.tex_coords,
                        stroke_color,
                        translation,
                        rotation,
                        visible,
                        anchor_x,
                        anchor_y,
                        4,
                    )
                    stroke_data = self._set_depth_layer(
                        layout,
                        stroke_data,
                        4,
                        _STROKE_DEPTH_LAYER,
                    )
                    stroke_list = layout.program.vertex_list_indexed(
                        4,
                        GeometryMode.TRIANGLES,
                        (0, 1, 2, 0, 2, 3),
                        layout.batch,
                        layout.get_effect_group(stroke_glyph.owner, order=2 if layout.depth_sorting else 0),
                        **stroke_data,
                    )
                    self._add_vertex_list(stroke_list, context)
                stroke_x += round(glyph.advance + glyph_pos.x_advance)
            glyph_index = range_end_glyph

    def _create_decoration_geometry(
        self,
        start_index: int,
        line_x: float,
        line_y: float,
        baseline: int,
        decoration_iter: runlist.ZipRunIterator,
    ) -> _DecorationGeometry | None:
        # Decoration (background color, underline, and strikethrough)
        # Decorations are geometry only and without textures.
        # Should iterate over baseline too, but in practice any sensible
        # change in baseline will correspond with a change in font size,
        # and thus glyph run as well.  So we cheat and just use whatever
        # baseline was seen last.
        background_vertices = []
        background_colors = []
        underline_vertices = []
        underline_colors = []
        strikethrough_vertices = []
        strikethrough_colors = []
        y1 = line_y + self.descent + baseline
        y2 = line_y + self.ascent + baseline
        x1 = line_x
        glyph_index = 0
        has_decoration = False
        for start, end, (bg, underline, strikethrough) in decoration_iter.ranges(
            start_index, start_index + self.length,
        ):
            if bg is None and underline is None and strikethrough is None:
                continue

            has_decoration = True
            range_start_glyph = start - start_index
            range_end_glyph = end - start_index
            while glyph_index < range_start_glyph:
                kern, glyph, glyph_pos = self.glyphs[glyph_index]
                x1 += self._glyph_advance(kern, glyph, glyph_pos)
                glyph_index += 1

            x2 = x1
            background_x1 = x1
            background_y1 = y1
            background_x2 = x1
            background_y2 = y2
            for glyph_index in range(range_start_glyph, range_end_glyph):
                kern, glyph, glyph_pos = self.glyphs[glyph_index]
                x2 += round(kern)
                if bg is not None:
                    v0, v1, v2, v3 = glyph.vertices

                    # Glyphs can extend outside their advance, use bounds. (italic, emoji)
                    glyph_x = x2 + glyph_pos.x_offset
                    glyph_y = line_y + baseline + glyph_pos.y_offset
                    background_x1 = min(background_x1, glyph_x + v0)
                    background_y1 = min(background_y1, glyph_y + v1)
                    background_x2 = max(background_x2, glyph_x + v2)
                    background_y2 = max(background_y2, glyph_y + v3)

                x2 += round(glyph.advance + glyph_pos.x_advance)

            if bg is not None:
                if len(bg) != 4:
                    msg = f"Background color requires 4 values (R, G, B, A). Value received: {bg}"
                    raise ValueError(msg)

                background_vertices.extend(
                    [
                        background_x1,
                        background_y1,
                        0,
                        background_x2,
                        background_y1,
                        0,
                        background_x2,
                        background_y2,
                        0,
                        background_x1,
                        background_y2,
                        0,
                    ]
                )
                background_colors.extend(bg * 4)

            if underline is not None:
                if len(underline) != 4:
                    msg = f"Underline color requires 4 values (R, G, B, A). Value received: {underline}"
                    raise ValueError(msg)

                underline_vertices.extend([x1, line_y + baseline - 2, 0, x2, line_y + baseline - 2, 0])
                underline_colors.extend(underline * 2)

            if strikethrough is not None:
                if len(strikethrough) != 4:
                    msg = f"Strikethrough color requires 4 values (R, G, B, A). Value received: {strikethrough}"
                    raise ValueError(msg)

                strikethrough_y = line_y + baseline + self.ascent / 3
                strikethrough_vertices.extend([x1, strikethrough_y, 0, x2, strikethrough_y, 0])
                strikethrough_colors.extend(strikethrough * 2)

            x1 = x2
            glyph_index = range_end_glyph

        if not has_decoration:
            return None

        return _DecorationGeometry(
            _DecorationData(background_vertices, background_colors),
            _DecorationData(underline_vertices, underline_colors),
            _DecorationData(strikethrough_vertices, strikethrough_colors),
        )

    def _place_decorations(
        self,
        layout: TextLayout,
        start_index: int,
        line_x: float,
        line_y: float,
        baseline: int,
        translation: tuple[float, float, float],
        rotation: float,
        visible: bool,
        anchor_x: float,
        anchor_y: float,
        context: _LayoutContext,
    ) -> None:
        if context.decoration_iter is None:
            return

        geometry = self._create_decoration_geometry(
            start_index,
            line_x,
            line_y,
            baseline,
            context.decoration_iter,
        )
        if geometry is None:
            return

        if geometry.background.vertices:
            bg_layer = layout.get_depth_offset(_BACKGROUND_DEPTH_LAYER)
            bg_count = len(geometry.background.vertices) // 3
            # Needs this split for text highlighting in incremental layer.
            background_indices = [
                vertex + quad * 4
                for quad in range(bg_count // 4)
                for vertex in (0, 1, 2, 0, 2, 3)
            ]
            decoration_program = layout.decoration_shader
            background_list = decoration_program.vertex_list_indexed(
                bg_count,
                GeometryMode.TRIANGLES,
                background_indices,
                layout.batch,
                layout.background_decoration_group,
                position=geometry.background.vertices,
                translation=(*translation, bg_layer) * bg_count,
                view_translation=(0, 0, 0) * bg_count,
                colors=geometry.background.colors,
                rotation=(rotation,) * bg_count,
                visible=(visible,) * bg_count,
                anchor=(anchor_x, anchor_y) * bg_count,
            )
            self._add_vertex_list(background_list, context)

        fg_layer = layout.get_depth_offset(_FOREGROUND_DECORATION_DEPTH_LAYER)
        if geometry.underline.vertices:
            ul_count = len(geometry.underline.vertices) // 3
            decoration_program = layout.decoration_shader
            underline_list = decoration_program.vertex_list(
                ul_count,
                GeometryMode.LINES,
                layout.batch,
                layout.foreground_decoration_group,
                position=geometry.underline.vertices,
                translation=(*translation, fg_layer) * ul_count,
                view_translation=(0, 0, 0) * ul_count,
                colors=geometry.underline.colors,
                rotation=(rotation,) * ul_count,
                visible=(visible,) * ul_count,
                anchor=(anchor_x, anchor_y) * ul_count,
            )
            self._add_vertex_list(underline_list, context)

        if geometry.strikethrough.vertices:
            st_count = len(geometry.strikethrough.vertices) // 3
            decoration_program = layout.decoration_shader
            strikethrough_list = decoration_program.vertex_list(
                st_count,
                GeometryMode.LINES,
                layout.batch,
                layout.foreground_decoration_group,
                position=geometry.strikethrough.vertices,
                translation=(*translation, fg_layer) * st_count,
                view_translation=(0, 0, 0) * st_count,
                colors=geometry.strikethrough.colors,
                rotation=(rotation,) * st_count,
                visible=(visible,) * st_count,
                anchor=(anchor_x, anchor_y) * st_count,
            )
            self._add_vertex_list(strikethrough_list, context)

    def place(
        self,
        layout: TextLayout,
        i: int,
        x: float,
        y: float,
        z: float,
        line_x: float,
        line_y: float,
        rotation: float,
        visible: bool,
        anchor_x: float,
        anchor_y: float,
        context: _LayoutContext,
    ) -> None:
        """Create the initial attributes and vertex lists for this glyph run."""
        assert self.glyphs
        assert not self.vertex_lists

        try:
            group = layout.group_cache[self.owner]
        except KeyError:
            group = layout.group_class(self.owner, layout.program, order=3 if layout.depth_sorting else 1, parent=layout.group)
            layout._set_depth_test(group)  # noqa: SLF001
            layout.group_cache[self.owner] = group

        vertices, tex_coords, baseline = self._create_glyph_geometry(layout, i, line_x, line_y, context)
        colors = self._create_glyph_colors(i, vertices, context)
        indices = [element + glyph_index * 4 for glyph_index in range(self.length) for element in (0, 1, 2, 0, 2, 3)]
        translation = (x, y, z)
        vertex_data = self._create_vertex_data(
            layout,
            vertices,
            tex_coords,
            colors,
            translation,
            rotation,
            visible,
            anchor_x,
            anchor_y,
            self.length * 4,
        )

        self._place_shadow(layout, i, vertices, indices, vertex_data, context)

        vertex_list = layout.program.vertex_list_indexed(
            self.length * 4,
            GeometryMode.TRIANGLES,
            indices,
            layout.batch,
            group,
            **vertex_data,
        )
        self._glyph_vertex_list = vertex_list
        self._add_vertex_list(vertex_list, context)

        self._place_strokes(
            layout,
            i,
            line_x,
            line_y,
            baseline,
            vertices,
            translation,
            rotation,
            visible,
            anchor_x,
            anchor_y,
            context,
        )
        self._place_decorations(
            layout,
            i,
            line_x,
            line_y,
            baseline,
            translation,
            rotation,
            visible,
            anchor_x,
            anchor_y,
            context,
        )

    def update_translation(self, x: float, y: float, z: float) -> None:
        for _vertex_list in self.vertex_lists:
            depth_offset = _vertex_list.translation[3]
            _vertex_list.translation[:] = (x, y, z, depth_offset) * _vertex_list.count

    def update_colors(self, colors: list[int], start: int, end: int) -> None:
        """Update the glyph colors only when specified by a single color attribute in set_style.

        Update just the specific range of glyphs with the colors.
        """
        if self._glyph_vertex_list is not None:
            color_end_index = (end - start) * 4
            vertex_start_index = start * 16
            vertex_end_index = end * 16
            self._glyph_vertex_list.colors[vertex_start_index:vertex_end_index] = colors[:color_end_index] * 4

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
        for kern, glyph, offset in self.glyphs:
            if position == 0:
                break
            position -= 1
            x += self._glyph_advance(kern, glyph, offset)
        return x

    def get_position_in_box(self, x: float) -> int:
        position = 0
        last_glyph_x = 0
        for kern, glyph, offset in self.glyphs:
            last_glyph_x += round(kern)
            advance = round(glyph.advance + offset.x_advance)
            if last_glyph_x + advance / 2 > x:
                return position
            position += 1
            last_glyph_x += advance
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

    def place(
        self,
        layout: TextLayout,
        i: int,
        x: float,
        y: float,
        z: float,
        line_x: float,
        line_y: float,
        rotation: float,
        visible: bool,
        anchor_x: float,
        anchor_y: float,
        context: _LayoutContext,
    ) -> None:  # noqa: ARG002
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
