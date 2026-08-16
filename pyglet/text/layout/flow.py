"""Glyph collection, line wrapping, and flow algorithms for text layouts."""

from __future__ import annotations

from typing import Callable, Iterator

from pyglet.text import runlist
from pyglet.text.document import AbstractDocument, UnformattedDocument
from pyglet.text.layout.boxes import _AbstractBox, _GlyphBox, _InlineElementBox, _Line
from pyglet.font.base import Glyph, GlyphPosition

# Just have one object for empty positions in layout. It won't be modified.
_empty_pos = GlyphPosition(0, 0, 0, 0)


class _FlowLayoutBase:
    """Shared glyph and line-flow implementation for text layouts."""

    _document: AbstractDocument
    _dpi: float
    _shaping: bool
    _width: int | None
    _multiline: bool
    _wrap_lines: bool
    _content_width: int
    _content_height: int
    _line_count: int

    document: AbstractDocument
    width: int | None

    def _parse_distance(self, distance: str | int | float | None) -> int | None:
        raise NotImplementedError

    @property
    def _flow_glyphs(
        self,
    ) -> Callable[
        [list[_InlineElementBox | Glyph], list[GlyphPosition], runlist.RunList, int, int],
        Iterator[_Line],
    ]:
        if self._multiline:
            return self._flow_glyphs_wrap
        return self._flow_glyphs_single_line

    def _get_lines(self) -> list[_Line]:
        if not self._multiline and type(self._document) is UnformattedDocument:
            return self._get_unformatted_single_line()

        return self._get_lines_generic()

    def _get_lines_generic(self) -> list[_Line]:
        len_text = len(self._document.text)
        glyphs, offsets = self._get_glyphs()
        owner_runs = runlist.RunList(len_text, None)
        self._get_owner_runs(owner_runs, glyphs, 0, len_text)
        lines = list(self._flow_glyphs(glyphs, offsets, owner_runs, 0, len_text))
        self._content_width = 0
        self._line_count = len(lines)
        self._flow_lines(lines, 0, self._line_count)
        return lines

    def _get_unformatted_single_line(self) -> list[_Line]:
        """Lay out a uniform, single-line document without generic run iterators."""
        document = self._document
        text = document.text
        font = document.get_font(dpi=self._dpi)
        glyphs, offsets = font.get_glyphs(text, self._shaping)

        line = _Line(0)
        if self._width:
            align = document.get_style("align")
            if align in ("left", "right", "center"):
                line.align = align

        kerning = document.get_style("kerning")
        if kerning is None:
            kerning = 0

        owner = glyphs[0].owner
        owner_glyphs = []
        for glyph, offset in zip(glyphs, offsets):
            if glyph.owner != owner:
                line.add_box(_GlyphBox(owner, font, owner_glyphs))
                owner = glyph.owner
                owner_glyphs = []

            owner_glyphs.append((kerning, glyph, offset))

        line.add_box(_GlyphBox(owner, font, owner_glyphs))
        line.paragraph_begin = line.paragraph_end = True

        self._content_width = line.width
        self._line_count = 1
        self._flow_unformatted_single_line(line)
        return [line]

    def _flow_unformatted_single_line(self, line: _Line) -> None:
        """Position a uniform single line without paragraph run processing."""
        document = self._document
        margin_top = document.get_style("margin_top")
        margin_bottom = document.get_style("margin_bottom")
        line_spacing = document.get_style("line_spacing")

        margin_top = self._parse_distance(margin_top) if margin_top is not None else 0
        margin_bottom = self._parse_distance(margin_bottom) if margin_bottom is not None else 0
        line_spacing = self._parse_distance(line_spacing) if line_spacing is not None else None

        if line.align == "center" and line.width <= self.width:
            line.x = (self.width - line.width) // 2
        elif line.align == "right" and line.width <= self.width:
            line.x = self.width - line.width

        y = -margin_top
        y -= line.ascent if line_spacing is None else line_spacing
        line.y = y
        if line_spacing is None:
            y += line.descent
        y -= margin_bottom
        self._content_height = -y

    def _get_glyphs(self) -> tuple[list[_InlineElementBox | Glyph], list[tuple[int, int]]]:
        glyphs = []
        offsets = []
        runs = runlist.ZipRunIterator((self._document.get_font_runs(dpi=self._dpi), self._document.get_element_runs()))
        text = self._document.text
        for start, end, (font, element) in runs.ranges(0, len(text)):
            if element:
                glyphs.append(_InlineElementBox(element))
                offsets.append(_empty_pos)
            else:
                char_glyphs, char_offsets = font.get_glyphs(text[start:end], self._shaping)
                glyphs.extend(char_glyphs)
                offsets.extend(char_offsets)

        return glyphs, offsets

    def _get_owner_runs(
        self, owner_runs: runlist.RunList, glyphs: list[_InlineElementBox | Glyph], start: int, end: int
    ) -> None:
        owner = glyphs[start].owner
        run_start = start

        for index in range(start, end):
            glyph = glyphs[index]
            if owner != glyph.owner:
                owner_runs.set_run(run_start, index, owner)
                owner = glyph.owner
                run_start = index
        owner_runs.set_run(run_start, end, owner)

    def _flow_glyphs_wrap(
        self,
        glyphs: list[_InlineElementBox | Glyph],
        offsets: list[GlyphPosition],
        owner_runs: runlist.RunList,
        start: int,
        end: int,
    ) -> Iterator[_Line]:
        # Word-wrap styled text into lines of fixed width.
        # Fits glyphs in range start to end into Lines which are then yielded.
        owner_iterator = owner_runs.get_run_iterator().ranges(start, end)

        font_iterator = self._document.get_font_runs(dpi=self._dpi)

        align_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs("align"), lambda value: value in ("left", "right", "center"), "left"
        )
        if self._width is None:
            wrap_iterator = runlist.ConstRunIterator(len(self.document.text), False)
        else:
            wrap_iterator = runlist.FilteredRunIterator(
                self._document.get_style_runs("wrap"), lambda value: value in (True, False, "char", "word"), True
            )
        margin_left_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs("margin_left"), lambda value: value is not None, 0
        )
        margin_right_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs("margin_right"), lambda value: value is not None, 0
        )
        indent_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs("indent"), lambda value: value is not None, 0
        )
        kerning_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs("kerning"), lambda value: value is not None, 0
        )
        tab_stops_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs("tab_stops"), lambda value: value is not None, []
        )
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
            for text, glyph, offset in zip(self.document.text[start:end], glyphs[start:end], offsets[start:end]):
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
                            tab = 50.0
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
                            line.add_box(_GlyphBox(owner, font, owner_accum_commit))
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
                line.add_box(_GlyphBox(owner, font, owner_accum_commit))
            if owner_accum:
                run_accum.append(_GlyphBox(owner, font, owner_accum))
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

    def _flow_glyphs_single_line(
        self,
        glyphs: list[_InlineElementBox | Glyph],
        offsets: list[GlyphPosition],
        owner_runs: runlist.RunList,
        start: int,
        end: int,
    ) -> Iterator[_Line]:
        owner_iterator = owner_runs.get_run_iterator().ranges(start, end)
        font_iterator = self.document.get_font_runs(dpi=self._dpi)
        kern_iterator = runlist.FilteredRunIterator(
            self.document.get_style_runs("kerning"), lambda value: value is not None, 0
        )

        line = _Line(start)
        font = font_iterator[0]

        if self._width:
            align_iterator = runlist.FilteredRunIterator(
                self._document.get_style_runs("align"), lambda value: value in ("left", "right", "center"), "left"
            )
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
                line.add_box(_GlyphBox(owner, font, owner_glyphs))

        if not line.boxes:
            line.ascent = font.ascent
            line.descent = font.descent

        line.paragraph_begin = line.paragraph_end = True

        yield line

    def _flow_lines(self, lines: list[_Line], start: int, end: int) -> int:
        margin_top_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs("margin_top"), lambda value: value is not None, 0
        )
        margin_bottom_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs("margin_bottom"), lambda value: value is not None, 0
        )
        line_spacing_iterator = self._document.get_style_runs("line_spacing")
        leading_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs("leading"), lambda value: value is not None, 0
        )

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
