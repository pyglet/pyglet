from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, ClassVar

from pyglet.event import EventDispatcher
from pyglet.font.base import grapheme_break
from pyglet.text import runlist
from pyglet.text.layout.base import (
    TextLayout,
    _AbstractBox,
    _InlineElementBox,
    _InvalidRange,
    _is_pyglet_doc_run,
    _LayoutContext,
    _Line,
)
from pyglet.text.layout.scrolling import ScrollableTextDecorationGroup, ScrollableTextLayoutGroup

if TYPE_CHECKING:
    from pyglet.customtypes import AnchorX, AnchorY
    from pyglet.graphics import Batch, Group
    from pyglet.graphics.shader import ShaderProgram
    from pyglet.graphics.vertexdomain import VertexList
    from pyglet.text.document import AbstractDocument


class _IncrementalLayoutContext(_LayoutContext):
    # This Context is modified to instead store vertex lists in the Lines themselves. This is due to the fact that
    # IncrementalLayout only handles lines that are visible. When lines change, the vertex lists are destroyed, but
    # boxes are kept alive. This also allows the Layout to determine word wraps and line lengths without a vertex list.

    line = None

    def add_list(self, vertex_list: VertexList) -> None:
        self.line.vertex_lists.append(vertex_list)

    def add_box(self, box: _AbstractBox) -> None:
        pass


class IncrementalTextLayoutGroup(ScrollableTextLayoutGroup):  # noqa: D101
    # Subclass so that the scissor_area isn't shared with the
    # ScrollableTextLayout. We use a class variable here so
    # that it can be set before the document glyphs are created.
    scissor_area: ClassVar[tuple[int, int, int, int]] = 0, 0, 0, 0


class IncrementalTextDecorationGroup(ScrollableTextDecorationGroup):  # noqa: D101
    # Subclass so that the scissor_area isn't shared with the
    # ScrollableTextDecorationGroup. We use a class variable here so
    # that it can be set before the document glyphs are created.
    scissor_area: ClassVar[tuple[int, int, int, int]] = 0, 0, 0, 0


class IncrementalTextLayout(TextLayout, EventDispatcher):
    """Displayed text suitable for interactive editing and/or scrolling large documents.

    Unlike :py:func:`~pyglet.text.layout.TextLayout` and
    :py:class:`~pyglet.text.layout.ScrollableTextLayout`, this class generates
    vertex lists only for lines of text that are visible.  As the document is
    scrolled, vertex lists are deleted and created as appropriate to keep
    video memory usage to a minimum and improve rendering speed.

    Changes to the document are quickly reflected in this layout, as only the
    affected line(s) are reflowed.  Use :py:meth:`~pyglet.text.layout.TextLayout.begin_update` and
    :py:meth:`~pyglet.text.layout.TextLayout.end_update` to
    further reduce the amount of processing required.

    The layout can also display a text selection (text with a different
    background color).  The :py:class:`~pyglet.text.caret.Caret` class implements
    a visible text cursor and provides event handlers for scrolling, selecting and
    editing text in an incremental text layout.

    Attributes:
        group_class: Default group used to set the state for all glyphs.
        decoration_class: Default group used to set the state for all decorations including background colors and
            underlines.
    """

    glyphs: list[Any]
    lines: list[_Line]

    _selection_start: int = 0
    _selection_end: int = 0
    _selection_color: tuple[int, int, int, int] = (255, 255, 255, 255)
    _selection_background_color: tuple[int, int, int, int] = (46, 106, 197, 255)

    group_class: ClassVar[type[IncrementalTextLayoutGroup]] = IncrementalTextLayoutGroup
    decoration_class: ClassVar[type[IncrementalTextDecorationGroup]] = IncrementalTextDecorationGroup

    _translate_x: int = 0
    _translate_y: int = 0

    _invalid_glyphs: _InvalidRange
    _invalid_flow: _InvalidRange
    _invalid_lines: _InvalidRange
    _invalid_style: _InvalidRange
    _invalid_vertex_lines: _InvalidRange
    _visible_lines: _InvalidRange

    _owner_runs: runlist.RunList

    _width: int
    _height: int

    def __init__(self, document: AbstractDocument,
                 x: float = 0, y: float = 0, z: float = 0,
                 width: int = None, height: int = None,
                 anchor_x: AnchorX = 'left', anchor_y: AnchorY = 'bottom', rotation: float = 0, multiline: bool = False,
                 dpi: float | None = None, batch: Batch | None = None, group: Group | None = None,
                 program: ShaderProgram | None = None, wrap_lines: bool = True) -> None:

        if width is None or height is None:
            msg = "Invalid size. IncrementalTextLayout width or height cannot be None."
            raise Exception(msg)

        #: :meta private:
        self.glyphs = []

        #: :meta private:
        # All lines in the document, including those hidden from view.
        self.lines = []

        self._invalid_glyphs = _InvalidRange()
        self._invalid_flow = _InvalidRange()
        self._invalid_lines = _InvalidRange()
        self._invalid_style = _InvalidRange()
        self._invalid_vertex_lines = _InvalidRange()
        self._visible_lines = _InvalidRange()

        self._owner_runs = runlist.RunList(0, None)

        super().__init__(document, x, y, z, width, height, anchor_x, anchor_y, rotation, multiline, dpi, batch, group,
                         program, wrap_lines)

    def _update_scissor_area(self) -> None:
        area = (self.left, self.bottom, self._width, self._height)

        for group in self.group_cache.values():
            group.scissor_area = area
        self.background_decoration_group.scissor_area = area
        self.foreground_decoration_group.scissor_area = area

    def _init_document(self) -> None:
        assert self._document, "Cannot remove document from IncrementalTextLayout"
        self.on_insert_text(0, self._document.text)

    def _uninit_document(self) -> None:
        self.on_delete_text(0, len(self._document.text))

    def _get_lines(self) -> list[_Line]:
        return self.lines

    def delete(self) -> None:
        for line in self.lines:
            line.delete(self)
        self._batch = None
        if self._document:
            self._document.remove_handlers(self)
        self._document = None

    def on_insert_text(self, start: int, text: str) -> None:
        len_text = len(text)
        self.glyphs[start:start] = [None] * len_text

        self._invalid_glyphs.insert(start, len_text)

        # When inserting text normally with content_valign top, the text only affects the line its on and after it.
        # With other alignments, such as bottom, by adding text you may be pushing the lines above upwards.
        # To account for this, we need to invalidate the text above as well.
        if self._multiline and self._content_valign != "top":
            visible_line = self.lines[self._visible_lines.start]
            self._invalid_flow.invalidate(visible_line.start, start + len_text)

        self._invalid_flow.insert(start, len_text)
        self._invalid_style.insert(start, len_text)

        self._owner_runs.insert(start, len_text)

        for line in self.lines:
            if line.start >= start:
                line.start += len_text

        self._update()

    def on_delete_text(self, start: int, end: int) -> None:
        self.glyphs[start:end] = []

        # Same requirement as on_insert_text
        if self._multiline and self._content_valign != "top":
            visible_line = self.lines[self._visible_lines.start]
            self._invalid_flow.invalidate(visible_line.start, end)

        self._invalid_glyphs.delete(start, end)
        self._invalid_flow.delete(start, end)
        self._invalid_style.delete(start, end)

        self._owner_runs.delete(start, end)

        size = end - start
        for line in self.lines:
            if line.start > start:
                line.start = max(line.start - size, start)

        if start == 0:
            self._invalid_flow.invalidate(0, 1)
        else:
            self._invalid_flow.invalidate(start - 1, start)

        self._update()

    def on_style_text(self, start: int, end: int, attributes: dict[str, Any]) -> None:
        if "font_name" in attributes or "font_size" in attributes or "weight" in attributes or "italic" in attributes:
            self._invalid_glyphs.invalidate(start, end)
        elif "color" in attributes or "background_color" in attributes:
            self._invalid_style.invalidate(start, end)
        else:  # Attributes that change flow
            self._invalid_flow.invalidate(start, end)

        self._update()

    def _update(self) -> None:
        if not self._update_enabled:
            return

        trigger_update_event = (self._invalid_glyphs.is_invalid() or
                                self._invalid_flow.is_invalid() or
                                self._invalid_lines.is_invalid())

        len_groups = len(self.group_cache)
        # Special care if there is no text:
        if not self.glyphs:
            for line in self.lines:
                line.delete(self)
            del self.lines[:]
            self.lines.append(_Line(0))
            font = self.document.get_font(0, dpi=self._dpi)
            self.lines[0].ascent = font.ascent
            self.lines[0].descent = font.descent
            self.lines[0].paragraph_begin = self.lines[0].paragraph_end = True
            self._invalid_lines.invalidate(0, 1)

        self._update_glyphs()
        self._update_flow_glyphs()
        self._update_flow_lines()
        self._update_visible_lines()
        self._update_vertex_lists()

        self._line_count = len(self.lines)
        self._ascent = self.lines[0].ascent
        self._descent = self.lines[0].descent

        # Update group cache areas if the count has changed. Usually if it starts with no text.
        # Group cache is only cleared in a regular TextLayout. May need revisiting if that changes.
        if len_groups != len(self.group_cache):
            self._update_scissor_area()

        if trigger_update_event:
            self.dispatch_event("on_layout_update")

    def _update_glyphs(self) -> None:
        invalid_start, invalid_end = self._invalid_glyphs.validate()

        if invalid_end - invalid_start <= 0:
            return

        # Find grapheme breaks and extend glyph range to encompass.
        text = self.document.text
        while invalid_start > 0:
            if grapheme_break(text[invalid_start - 1], text[invalid_start]):
                break
            invalid_start -= 1

        len_text = len(text)
        while invalid_end < len_text:
            if grapheme_break(text[invalid_end - 1], text[invalid_end]):
                break
            invalid_end += 1

        # Update glyphs
        runs = runlist.ZipRunIterator((
            self._document.get_font_runs(dpi=self._dpi),
            self._document.get_element_runs()))
        for start, end, (font, element) in runs.ranges(invalid_start, invalid_end):
            if element:
                self.glyphs[start] = _InlineElementBox(element)
            else:
                text = self.document.text[start:end]
                self.glyphs[start:end] = font.get_glyphs(text)

        # Update owner runs
        owner_runs = self._get_owner_runs(self.glyphs[invalid_start:invalid_end])
        self._owner_runs.set_runs(invalid_start, invalid_end, owner_runs)

        # Updated glyphs need flowing
        self._invalid_flow.invalidate(invalid_start, invalid_end)

    def _update_flow_glyphs(self) -> None:
        invalid_start, invalid_end = self._invalid_flow.validate()

        if invalid_end - invalid_start <= 0:
            return

        # Find first invalid line
        line_index = 0
        for i, line in enumerate(self.lines):
            if line.start >= invalid_start:
                break
            line_index = i

        # Flow from previous line; fixes issue with adding a space into
        # overlong line (glyphs before space would then flow back onto
        # previous line).
        # TODO:  Could optimise this by keeping track of where the overlong lines are.
        line_index = max(0, line_index - 1)

        # (No need to find last invalid line; the update loop below stops
        # calling the flow generator when no more changes are necessary.)

        try:
            line = self.lines[line_index]
            invalid_start = min(invalid_start, line.start)
            line.delete(self)
            self.lines[line_index] = _Line(invalid_start)
            self._invalid_lines.invalidate(line_index, line_index + 1)
        except IndexError:
            line_index = 0
            invalid_start = 0
            line = _Line(0)
            self.lines.append(line)
            self._invalid_lines.insert(0, 1)

        content_width_invalid = False
        next_start = invalid_start

        for line in self._flow_glyphs(self.glyphs, self._owner_runs, invalid_start, len(self._document.text)):
            try:
                old_line = self.lines[line_index]
                old_line.delete(self)
                old_line_width = old_line.width + old_line.margin_left
                new_line_width = line.width + line.margin_left
                if old_line_width == self._content_width and new_line_width < old_line_width:
                    content_width_invalid = True
                self.lines[line_index] = line
                self._invalid_lines.invalidate(line_index, line_index + 1)
            except IndexError:
                self.lines.append(line)
                self._invalid_lines.insert(line_index, 1)

            next_start = line.start + line.length
            line_index += 1

            try:
                next_line = self.lines[line_index]
                if next_start == next_line.start and next_start > invalid_end:
                    # No more lines need to be modified, early exit.
                    break
            except IndexError:
                pass

        # The last line is at line_index - 1, if there are any more lines
        # after that they are stale and need to be deleted.
        if next_start == len(self._document.text) and line_index > 0:
            for line in self.lines[line_index:]:
                old_line_width = old_line.width + old_line.margin_left
                if old_line_width == self._content_width:
                    content_width_invalid = True
                line.delete(self)
            del self.lines[line_index:]

        if content_width_invalid or len(self.lines) == 1:
            # Rescan all lines to look for the new maximum content width
            content_width = 0
            for line in self.lines:
                content_width = max(line.width + line.margin_left, content_width)
            self._content_width = content_width

    def _update_flow_lines(self) -> None:
        invalid_start, invalid_end = self._invalid_lines.validate()
        if invalid_end - invalid_start <= 0:
            return

        invalid_end = self._flow_lines(self.lines, invalid_start, invalid_end)

        # Invalidate lines that need new vertex lists.
        self._invalid_vertex_lines.invalidate(invalid_start, invalid_end)

    def _update_visible_lines(self) -> None:
        start = sys.maxsize
        end = 0

        for i, line in enumerate(self.lines):
            if line.y + line.descent < self._translate_y:
                start = min(start, i)
            if line.y + line.ascent > self._translate_y - self.height:
                end = max(end, i) + 1

        # Delete newly invisible lines
        for i in range(self._visible_lines.start, min(start, len(self.lines))):
            self.lines[i].delete(self)
        for i in range(end, min(self._visible_lines.end, len(self.lines))):
            self.lines[i].delete(self)

        # Invalidate newly visible lines
        self._invalid_vertex_lines.invalidate(start, self._visible_lines.start)
        self._invalid_vertex_lines.invalidate(self._visible_lines.end, end)

        self._visible_lines.start = start
        self._visible_lines.end = end

    def _update_vertex_lists(self, update_view_translation:bool =True) -> None:
        # Find lines that have been affected by style changes
        style_invalid_start, style_invalid_end = self._invalid_style.validate()
        self._invalid_vertex_lines.invalidate(
            self.get_line_from_position(style_invalid_start),
            self.get_line_from_position(style_invalid_end) + 1)

        invalid_start, invalid_end = self._invalid_vertex_lines.validate()
        if invalid_end - invalid_start <= 0:
            return

        colors_iter = self.document.get_style_runs("color")
        background_iter = self.document.get_style_runs("background_color")
        if self._selection_end - self._selection_start > 0:
            colors_iter = runlist.OverriddenRunIterator(
                colors_iter,
                self._selection_start,
                self._selection_end,
                self._selection_color)
            background_iter = runlist.OverriddenRunIterator(
                background_iter,
                self._selection_start,
                self._selection_end,
                self._selection_background_color)

        context = _IncrementalLayoutContext(self, self._document, colors_iter, background_iter)

        lines = self.lines[invalid_start:invalid_end]
        self._line_count = len(self.lines)
        self._ascent = lines[0].ascent
        self._descent = lines[0].descent

        self._anchor_left = self._get_left_anchor()
        self._anchor_bottom = self._get_bottom_anchor()
        top_anchor = self._get_top_anchor()

        for line in lines:
            line.delete(self)
            context.line = line
            y = line.y

            # Early out if not visible
            if y + line.descent > self._translate_y:
                continue
            if y + line.ascent < self._translate_y - self.height:
                break

            self._create_vertex_lists(line.x, y, self._anchor_left, top_anchor, line.start, line.boxes, context)

        # Update translation as new and old lines aren't guaranteed to update the translation after.
        if update_view_translation:
            self._update_view_translation()

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, x: float) -> None:
        super()._set_x(x)
        self._update_scissor_area()

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, y: float) -> None:
        super()._set_y(y)
        self._update_scissor_area()

    @property
    def z(self) -> float:
        return self._z

    @z.setter
    def z(self, z: float) -> None:
        super()._set_z(z)
        self._update_scissor_area()

    @property
    def position(self) -> tuple[float, float, float]:
        return self._x, self._y, self._z

    @position.setter
    def position(self, position: tuple[float, float, float]) -> None:
        super()._set_position(position)
        self._update_view_translation()
        self._update_scissor_area()

    @property
    def anchor_x(self) -> AnchorX:
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, anchor_x: AnchorX) -> None:
        self._anchor_x = anchor_x
        self._update_anchor()
        self._update_scissor_area()
        self._update_view_translation()

    @property
    def anchor_y(self) -> AnchorY:
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, anchor_y: AnchorY) -> None:
        self._anchor_y = anchor_y
        self._update_anchor()
        self._update_scissor_area()
        self._update_view_translation()

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, width: int) -> None:
        # Invalidate everything when width changes
        if width == self._width:
            return
        self._width = width
        self._invalid_flow.invalidate(0, len(self.document.text))
        self._update()

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, height: int) -> None:
        # Recalculate visible lines when height changes
        if height == self._height:
            return
        self._height = height
        if self._update_enabled:
            self._update_visible_lines()
            self._update_vertex_lists()

    @property
    def multiline(self) -> bool:
        return self._multiline

    @multiline.setter
    def multiline(self, multiline: bool) -> None:
        self._invalid_flow.invalidate(0, len(self.document.text))
        self._multiline = multiline
        self._wrap_lines_invariant()
        self._update()

    def _update_view_translation(self) -> None:
        # Offset of content within viewport
        for line in self.lines[self._visible_lines.start:self._visible_lines.end]:
            for box in line.boxes:
                box.update_view_translation(self._translate_x, self._translate_y)

        self.dispatch_event("on_translation_update")

    def _update_translation(self) -> None:
        # Vertex lists are stored in the lines.
        for line in self.lines[self._visible_lines.start:self._visible_lines.end]:
            for box in line.boxes:
                box.update_translation(self._x, self._y, self._z)

    def _update_anchor(self) -> None:
        self._anchor_left = self._get_left_anchor()
        self._anchor_bottom = self._get_bottom_anchor()

        anchor_left, anchor_top = (self._anchor_left, self._get_top_anchor())

        # A line can also have more than 1 box. For example, if the text "This is a test" does not fill
        # the whole line, it will be split to 2 boxes: ("This is a ", "test")
        # This is to allow the second GlyphBox to be pushed onto the next line should it wrap in multiline.
        # "This is a test " will be created as one GlyphBox.
        for line in self.lines[self._visible_lines.start:self._visible_lines.end]:
            # A line can have no vertex list if it's out of view OR is an empty row.

            # Accumulate the X accounting for multiple GlyphBoxes.
            anchor_x = anchor_left
            for box in line.boxes:
                box.update_anchor(anchor_x, anchor_top)
                anchor_x += box.advance

    def _get_bottom_anchor(self) -> float:
        """Returns the anchor for the Y axis from the bottom."""
        height = self._height
        if self._content_valign == "top":
            offset = min(0, self._height)
        elif self._content_valign == "bottom":
            offset = 0
        elif self._content_valign == "center":
            offset = min(0, self._height) // 2
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

    @property
    def rotation(self) -> float:
        """Rotation will always be 0 as incremental layouts cannot be rotated.

        Raises:
            NotImplementedError: Rotating IncrementalTextLayout's is not supported.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, angle: float) -> None:  # noqa: ARG002
        msg = "Rotating IncrementalTextLayout's is not supported."
        raise NotImplementedError(msg)

    @property
    def view_x(self) -> int:
        """Horizontal scroll offset.

        The initial value is 0, and the left edge of the text will touch the left
        side of the layout bounds.  A positive value causes the text to "scroll"
        to the right.  Values are automatically clipped into the range
        ``[0, content_width - width]``
        """
        return self._translate_x

    @view_x.setter
    def view_x(self, view_x: int) -> None:
        translation = max(0, min(self._content_width - self._width, view_x))
        if translation != self._translate_x:
            self._translate_x = translation
            self._update_view_translation()

    @property
    def view_y(self) -> int:
        """Vertical scroll offset.

        The initial value is 0, and the top of the text will touch the top of the
        layout bounds (unless the content height is less than the layout height,
        in which case `content_valign` is used).

        A negative value causes the text to "scroll" upwards.  Values outside of
        the range ``[height - content_height, 0]`` are automatically clipped in
        range.
        """
        return self._translate_y

    @view_y.setter
    def view_y(self, view_y: int) -> None:
        # Invalidate invisible/visible lines when y scrolls
        # view_y must be negative.
        translation = min(0, max(self.height - self._content_height, view_y))
        if translation != self._translate_y:
            self._translate_y = translation
            self._update_visible_lines()
            self._update_vertex_lists(update_view_translation=False)
            self._update_view_translation()

    # Visible selection

    def set_selection(self, start: int, end: int) -> None:
        """Set the text selection range.

        If ``start`` equals ``end`` no selection will be visible.

        Args:
            start: Starting character position of selection.
            end: End of selection, exclusive.
        """
        start = max(0, start)
        end = min(end, len(self.document.text))
        if start == self._selection_start and end == self._selection_end:
            return

        if end > self._selection_start and start < self._selection_end:
            # Overlapping, only invalidate difference
            self._invalid_style.invalidate(min(start, self._selection_start), max(start, self._selection_start))
            self._invalid_style.invalidate(min(end, self._selection_end), max(end, self._selection_end))
        else:
            # Non-overlapping, invalidate both ranges
            self._invalid_style.invalidate(self._selection_start, self._selection_end)
            self._invalid_style.invalidate(start, end)

        self._selection_start = start
        self._selection_end = end

        self._update()

    @property
    def selection_start(self) -> int:
        """Starting position of the active selection.

        :see: py:meth:`~pyglet.text.layout.IncrementalTextLayout.set_selection`
        """
        return self._selection_start

    @selection_start.setter
    def selection_start(self, start: int) -> None:
        self.set_selection(start, self._selection_end)

    @property
    def selection_end(self) -> int:
        """End position of the active selection (exclusive).

        :see: py:meth:`~pyglet.text.layout.IncrementalTextLayout.set_selection`
        """
        return self._selection_end

    @selection_end.setter
    def selection_end(self, end: int) -> None:
        self.set_selection(self._selection_start, end)

    @property
    def selection_color(self) -> tuple[int, int, int, int]:
        """Text color of active selection.

        The color is an RGBA tuple with components in range [0, 255].
        """
        return self._selection_color

    @selection_color.setter
    def selection_color(self, color: tuple[int, int, int, int]) -> None:
        self._selection_color = color
        self._invalid_style.invalidate(self._selection_start, self._selection_end)

    @property
    def selection_background_color(self) -> tuple[int, int, int, int]:
        """Background color of active selection.

        The color is an RGBA tuple with components in range [0, 255].
        """
        return self._selection_background_color

    @selection_background_color.setter
    def selection_background_color(self, background_color: tuple[int, int, int, int]) -> None:
        self._selection_background_color = background_color
        self._invalid_style.invalidate(self._selection_start, self._selection_end)

    # Coordinate translation

    def get_position_from_point(self, x: float, y: float) -> int:
        """Get the closest document position to a point."""
        line = self.get_line_from_point(x, y)
        return self.get_position_on_line(line, x)

    def get_point_from_position(self, position: int, line_idx: int | None=None) -> tuple[float, float]:
        """Get the X, Y coordinates of a character position in the document.

        The position that ends a line has an ambiguous point: it can be either
        the end of the line, or the beginning of the next line.  You may
        optionally specify a line index to disambiguate the case.

        The resulting Y coordinate gives the baseline of the line.
        """
        if line_idx is None:
            line = self.lines[0]
            for next_line in self.lines:
                if next_line.start > position:
                    break
                line = next_line
        else:
            line = self.lines[line_idx]

        x = line.x

        baseline = self._document.get_style("baseline", max(0, position - 1))
        if baseline is None:
            baseline = 0
        else:
            baseline = self._parse_distance(baseline)

        position -= line.start
        for box in line.boxes:
            if position - box.length <= 0:
                x += box.get_point_in_box(position)
                break
            position -= box.length
            x += box.advance

        return x, line.y + baseline

    def get_line_from_point(self, x: float, y: float) -> int:
        """Get the closest line index to a point."""
        x -= self._translate_x
        y -= self._get_content_height() + self.bottom - self._translate_y

        line_index = 0
        for line in self.lines:
            if y > line.y + line.descent:
                break
            line_index += 1
        if line_index >= len(self.lines):
            line_index = len(self.lines) - 1
        return line_index

    def get_point_from_line(self, line_idx: int) -> tuple[float, float]:
        """Get the X, Y coordinates of a line index."""
        line = self.lines[line_idx]
        return line.x + self._translate_x, line.y + self._translate_y

    def get_line_from_position(self, position: int) -> int:
        """Get the line index of a character position in the document."""
        line = -1
        for next_line in self.lines:
            if next_line.start > position:
                break
            line += 1
        return line

    def get_position_from_line(self, line_idx: int) -> int:
        """Get the first document character position of a given line index."""
        return int(self.lines[line_idx].start + self._x)

    def get_position_on_line(self, line_idx: int, x: float) -> int:
        """Get the closest document position for a given line index and X coordinate."""
        line = self.lines[line_idx]

        x += self._translate_x
        x -= self.left

        if x < line.x:
            return line.start

        position = line.start
        last_glyph_x = line.x
        for box in line.boxes:
            if 0 <= x - last_glyph_x < box.advance:
                position += box.get_position_in_box(x - last_glyph_x)
                break
            last_glyph_x += box.advance
            position += box.length

        return position

    def _get_content_height(self) -> int:
        """Returns the height of the layout content factoring in the vertical alignment."""
        if self._height is None:
            height = self.content_height
            offset = 0
        else:
            height = self._height
            if self._content_valign == "top":
                offset = 0
            elif self._content_valign == "bottom":
                offset = max(0, self._height - self.content_height)
            elif self._content_valign == "center":
                offset = max(0, self._height - self.content_height) // 2
            else:
                msg = '`content_valign` must be either "top", "bottom", or "center".'
                raise Exception(msg)

        return height - offset

    def _get_left_anchor(self) -> float:
        """Returns the anchor for the X axis from the left."""
        width = self.width

        if self._anchor_x == "left":
            return 0
        if self._anchor_x == "center":
            return -(width // 2)
        if self._anchor_x == "right":
            return -width

        msg = '`anchor_x` must be either "left", "center", or "right".'
        raise Exception(msg)

    def ensure_line_visible(self, line_idx: int) -> None:
        """Adjust `view_y` so that the line with the given index is visible."""
        line = self.lines[line_idx]
        y1 = line.y + line.ascent
        y2 = line.y + line.descent
        if y1 > self.view_y:
            self.view_y = y1
        elif y2 < self.view_y - self.height:
            self.view_y = y2 + self.height
        elif abs(self.view_y) > self.content_height - self.height:
            self.view_y = -self.content_height

    def ensure_x_visible(self, x: float) -> None:
        """Adjust ``view_x`` so that the given X coordinate is visible.

        The X coordinate is given relative to the current ``view_x``.
        """
        x -= self.left

        if x <= self.view_x:
            self.view_x = x

        elif x >= self.view_x + self.width or (x >= self.view_x + self.width) and (self._content_width > self.width):
            self.view_x = x - self.width

        elif self.view_x + self.width > self._content_width:
            self.view_x = self._content_width

    if _is_pyglet_doc_run:
        def on_layout_update(self) -> None:
            """Some or all of the layout text was reflowed.

            Text reflow is caused by document edits or changes to the layout's
            size.  Changes to the layout's position or active selection, and
            certain document edits such as text color, do not cause a reflow.

            Handle this event to update the position of a graphical element
            that depends on the laid out position of a glyph or line.

            :event:
            """


IncrementalTextLayout.register_event_type("on_layout_update")
IncrementalTextLayout.register_event_type("on_translation_update")
