#!/usr/bin/python
# $Id:$

'''

Layout distinguishes between paragraph breaks (\n or U+2029) and line breaks
(U+2028).  Margin space is inserted between paragraph breaks, not between line
breaks.  Follows UTR #13 http://unicode.org/reports/tr13/tr13-5.html.
'''

import math
import sys

from pyglet.gl import *
from pyglet import graphics
from pyglet.text import document
from pyglet.text import runlist

class Line(object):
    align = 'left'

    margin_left = 0
    margin_right = 0

    length = 0
        
    ascent = 0
    descent = 0
    width = 0
    paragraph_begin = False
    paragraph_end = False

    x = None
    y = None

    def __init__(self, start):
        self.vertex_lists = []
        self.start = start
        self.boxes = []

    def __repr__(self):
        return 'Line(%r)' % self.boxes

    def add_box(self, box):
        self.boxes.append(box)
        self.length += box.length
        self.ascent = max(self.ascent, box.ascent)
        self.descent = min(self.descent, box.descent)
        self.width += box.advance

    def delete(self, layout):
        for list in self.vertex_lists:
            list.delete()
        self.vertex_lists = []

        for box in self.boxes:
            box.delete(layout)

class LayoutContext(object):
    def __init__(self, layout, document, colors_iter, background_iter):
        self.colors_iter = colors_iter
        underline_iter = document.get_style_runs('underline')
        self.decoration_iter = runlist.ZipRunIterator(
            (background_iter, 
             underline_iter))
        self.baseline_iter = runlist.FilteredRunIterator(
            document.get_style_runs('baseline'),
            lambda value: value is not None, 0)

class StaticLayoutContext(LayoutContext):
    def __init__(self, layout, document, colors_iter, background_iter):
        super(StaticLayoutContext, self).__init__(layout, document,
                                                  colors_iter, background_iter)
        self.vertex_lists = []

    def add_list(self, list):
        self.vertex_lists.append(list)

class IncrementalLayoutContext(LayoutContext):
    line = None

    def add_list(self, list):
        self.line.vertex_lists.append(list)

class AbstractBox(object):
    owner = None

    def __init__(self, ascent, descent, advance, length):
        self.ascent = ascent
        self.descent = descent
        self.advance = advance
        self.length = length

    def place(self, layout, i, x, y):
        raise NotImplementedError('abstract')

    def delete(self, layout):
        raise NotImplementedError('abstract')

    def get_position_in_box(self, x):
        raise NotImplementedError('abstract')

    def get_point_in_box(self, position):
        raise NotImplementedError('abstract')

class GlyphBox(AbstractBox):
    def __init__(self, owner, font, glyphs, advance):
        '''Create a run of glyphs sharing the same texture.

        :Parameters:
            `owner` : `pyglet.image.Texture`
                Texture of all glyphs in this run.
            `font` : `pyglet.font.base.Font`
                Font of all glyphs in this run.
            `glyphs` : list of (int, `pyglet.font.base.Glyph`)
                Pairs of ``(kern, glyph)``, where ``kern`` gives horizontal
                displacement of the glyph in pixels (typically 0).
            `advance` : int
                Width of glyph run; must correspond to the sum of advances
                and kerns in the glyph list.

        '''
        super(GlyphBox, self).__init__(
            font.ascent, font.descent, advance, len(glyphs))
        self.owner = owner
        self.font = font
        self.glyphs = glyphs
        self.advance = advance 

    def place(self, layout, i, x, y, context):
        assert self.glyphs
        try:
            group = layout.groups[self.owner]
        except KeyError:
            group = layout.groups[self.owner] = \
                TextLayoutTextureGroup(self.owner, layout.foreground_group)

        n_glyphs = self.length
        vertices = []
        tex_coords = []
        x1 = x
        for start, end, baseline in context.baseline_iter.ranges(i, i+n_glyphs):
            baseline = layout._points_to_pixels(baseline)
            assert len(self.glyphs[start - i:end - i]) == end - start
            for kern, glyph in self.glyphs[start - i:end - i]:
                x1 += kern
                v0, v1, v2, v3 = glyph.vertices
                v0 += x1
                v2 += x1
                v1 += y + baseline
                v3 += y + baseline
                vertices.extend([v0, v1, v2, v1, v2, v3, v0, v3])
                t = glyph.tex_coords
                tex_coords.extend(t)
                x1 += glyph.advance
        
        # Text color
        colors = []
        for start, end, color in context.colors_iter.ranges(i, i+n_glyphs):
            if color is None:
                color = (0, 0, 0, 255)
            colors.extend(color * ((end - start) * 4))

        list = layout.batch.add(n_glyphs * 4, GL_QUADS, group, 
            ('v2f/dynamic', vertices),
            ('t3f/dynamic', tex_coords),
            ('c4B/dynamic', colors))
        context.add_list(list)

        # Decoration (background color and underline)
        #
        # Should iterate over baseline too, but in practice any sensible
        # change in baseline will correspond with a change in font size,
        # and thus glyph run as well.  So we cheat and just use whatever
        # baseline was seen last.
        background_vertices = []
        background_colors = []
        underline_vertices = []
        underline_colors = []
        y1 = y + self.descent + baseline
        y2 = y + self.ascent + baseline
        x1 = x
        for start, end, decoration in \
                context.decoration_iter.ranges(i, i+n_glyphs):
            bg, underline = decoration
            x2 = x1
            for kern, glyph in self.glyphs[start - i:end - i]:
                x2 += glyph.advance + kern

            if bg is not None:
                background_vertices.extend(
                    [x1, y1, x2, y1, x2, y2, x1, y2])
                background_colors.extend(bg * 4)

            if underline is not None:
                underline_vertices.extend(
                    [x1, y + baseline - 2, x2, y + baseline - 2])
                underline_colors.extend(underline * 2)

            x1 = x2
            
        if background_vertices:
            background_list = layout.batch.add(
                len(background_vertices) // 2, GL_QUADS,
                layout.background_group,
                ('v2f/dynamic', background_vertices),
                ('c4B/dynamic', background_colors))
            context.add_list(background_list)

        if underline_vertices:
            underline_list = layout.batch.add(
                len(underline_vertices) // 2, GL_LINES,
                layout.foreground_decoration_group,
                ('v2f/dynamic', underline_vertices),
                ('c4B/dynamic', underline_colors))
            context.add_list(underline_list)

    def delete(self, layout):
        pass

    def get_point_in_box(self, position):
        x = 0
        for (kern, glyph) in self.glyphs:
            if position == 0:
                break
            position -= 1
            x += glyph.advance + kern
        return x

    def get_position_in_box(self, x):
        position = 0
        last_glyph_x = 0
        for kern, glyph in self.glyphs:
            last_glyph_x += kern
            if last_glyph_x + glyph.advance / 2 > x:
                return position
            position += 1
            last_glyph_x += glyph.advance
        return position

    def __repr__(self):
        return 'GlyphBox(%r)' % self.glyphs

class InlineElementBox(AbstractBox):
    def __init__(self, element):
        '''Create a glyph run holding a single element.
        '''        
        super(InlineElementBox, self).__init__(
            element.ascent, element.descent, element.advance, 1)
        self.element = element
        self.placed = False

    def place(self, layout, i, x, y, context):
        self.element.place(layout, x, y)
        self.placed = True

    def delete(self, layout):
        # font == element
        if self.placed:
            self.element.remove(layout)
            self.placed = False

    def get_point_in_box(self, position):
        if position == 0:
            return 0
        else:
            return self.advance

    def get_position_in_box(self, x):
        if x < self.advance / 2:
            return 0
        else:
            return 1
    
    def __repr__(self):
        return 'InlineElementBox(%r)' % self.element

class InvalidRange(object):
    def __init__(self):
        self.start = sys.maxint
        self.end = 0

    def insert(self, start, length):
        if self.start >= start:
            self.start += length
        if self.end >= start:
            self.end += length
        self.invalidate(start, start + length)

    def delete(self, start, end):
        if self.start > end:
            self.start -= end - start
        elif self.start > start:
            self.start = start
        if self.end > end:
            self.end -= end - start
        elif self.end > start:
            self.end = start

    def invalidate(self, start, end):
        if end <= start:
            return
        self.start = min(self.start, start)
        self.end = max(self.end, end)

    def validate(self):
        start, end = self.start, self.end
        self.start = sys.maxint
        self.end = 0
        return start, end

# Text group hierarchy
#
# top_group                     [Scrollable]TextLayoutGroup(AbstractGroup)
#   background_group            OrderedGroup(0)
#   foreground_group            TextLayoutForegroundGroup(OrderedGroup(1))
#     [font textures]           TextLayoutTextureGroup(AbstractGroup)  
#     [...]                     TextLayoutTextureGroup(AbstractGroup)  
#   foreground_decoration_group 
#                       TextLayoutForegroundDecorationGroup(OrderedGroup(2))

class TextLayoutGroup(graphics.AbstractGroup):
    def set_state(self):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        glPopAttrib()
        
class ScrollableTextLayoutGroup(graphics.AbstractGroup):
    scissor_x = 0
    scissor_y = 0
    scissor_width = 0
    scissor_height = 0
    view_x = 0
    view_y = 0
    translate_x = 0 # x - view_x
    translate_y = 0 # y - view_y

    def set_state(self):
        glPushAttrib(GL_ENABLE_BIT | GL_SCISSOR_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # Disable scissor to check culling.
        glEnable(GL_SCISSOR_TEST)
        glScissor(self.scissor_x - 1, 
                  self.scissor_y - self.scissor_height, 
                  self.scissor_width + 1, 
                  self.scissor_height)
        glTranslatef(self.translate_x, self.translate_y, 0)

    def unset_state(self):
        glTranslatef(-self.translate_x, -self.translate_y, 0)
        glPopAttrib()

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

class TextLayoutForegroundGroup(graphics.OrderedGroup):
    def set_state(self):
        glEnable(GL_TEXTURE_2D)

    # unset_state not needed, as parent group will pop enable bit 

class TextLayoutForegroundDecorationGroup(graphics.OrderedGroup):
    def set_state(self):
        glDisable(GL_TEXTURE_2D)

    # unset_state not needed, as parent group will pop enable bit 

class TextLayoutTextureGroup(graphics.AbstractGroup):
    def __init__(self, texture, parent):
        assert texture.target == GL_TEXTURE_2D
        super(TextLayoutTextureGroup, self).__init__(parent)

        self.texture = texture

    def set_state(self):
        glBindTexture(GL_TEXTURE_2D, self.texture.id)

    # unset_state not needed, as next group will either bind a new texture or
    # pop enable bit.

    def __hash__(self):
        return hash((self.texture.id, self.parent))

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and 
                self.texture.id == other.texture.id and
                self.parent is other.parent)

    def __repr__(self):
        return '%s(%d, %r)' % (self.__class__.__name__, 
                               self.texture.id,
                               self.parent)

class TextLayout(object):
    _document = None
    _vertex_lists = ()

    top_group = TextLayoutGroup()
    background_group = graphics.OrderedGroup(0, top_group)
    foreground_group = TextLayoutForegroundGroup(1, top_group)
    foreground_decoration_group = \
        TextLayoutForegroundDecorationGroup(2, top_group)

    _update_enabled = True

    def __init__(self, document, multiline=False, dpi=None, 
                 batch=None, group=None):
        self.content_width = 0
        self.content_height = 0

        self.groups = {}
        self._init_groups(group)

        if batch is None:
            batch = graphics.Batch()
        self.batch = batch

        self.multiline = multiline
        if dpi is None:
            if sys.platform == 'darwin':
                dpi = 72
            else:
                dpi = 96
        self._dpi = dpi
        self.document = document       

    def _points_to_pixels(self, points):
        if points is None:
            return None
        return int(self._dpi * points / 72)

    def begin_update(self):
        '''Indicate that a number of changes to the layout or document
        are about to occur.

        Changes to the layout or document between calls to `begin_update` and
        `end_update` do not trigger any costly relayout of text.  Relayout of
        all changes is performed when `end_update` is called.

        Note that between the `begin_update` and `end_update` calls, values
        such as `content_width` are undefined (i.e., they may or may not
        be updated to reflect the latest changes).
        '''
        self._update_enabled = False

    def end_update(self):
        '''Perform pending layout changes since `begin_update`.

        See `begin_update`.
        '''
        self._update_enabled = True
        self._update()

    dpi = property(lambda self: self._dpi, 
                   doc='''Get DPI used by this layout.

    Read-only.

    :type: float
    ''')

    def delete(self):
        for vertex_list in self._vertex_lists:
            vertex_list.delete()

    def draw(self):
        self.batch.draw_subset(self._vertex_lists)

    def _init_groups(self, group):
        if group:
            self.top_group = TextLayoutGroup(group)
            self.background_group = graphics.OrderedGroup(0, self.top_group)
            self.foreground_group = TextLayoutForegroundGroup(1, self.top_group)
            self.foreground_decoration_group = \
                TextLayoutForegroundDecorationGroup(2, self.top_group)
        # Otherwise class groups are (re)used.

    def _get_document(self):
        return self._document

    def _set_document(self, document):
        if self._document:
            self._document.remove_handlers(self)
            self._uninit_document(self._document)
        document.push_handlers(self)
        self._document = document
        self._init_document()
    
    document = property(_get_document, _set_document)

    def _update(self):
        if not self._update_enabled:
            return

        for _vertex_list in self._vertex_lists:
            _vertex_list.delete()
        self._vertex_lists = []
        
        if not self._document or not self._document.text:
            return

        len_text = len(self._document.text)
        glyphs = self._get_glyphs()
        owner_runs = runlist.RunList(len_text, None)
        self._get_owner_runs(owner_runs, glyphs, 0, len_text)
        lines = [line for line in self._flow_glyphs(glyphs, owner_runs, 
                                                    0, len_text)]
        self.content_width = 0
        self._flow_lines(lines, 0, len(lines))

        colors_iter = self._document.get_style_runs('color')
        background_iter = self._document.get_style_runs('background_color')

        if self._halign == 'left':
            offset_x = self._x
        elif self._halign == 'center':
            if self._width is None:
                offset_x = self._x - self.content_width // 2
            else:
                offset_x = self._x + (self._width - self.content_width) // 2
        elif self._halign == 'right':
            if self._width is None:
                offset_x = self._x - self.content_width
            else:
                offset_x = self._x + self._width - self.content_width
        else:
            assert False, 'Invalid halign'
        
        if self._valign == 'top':
            offset_y = self._y
        elif self._valign == 'baseline':
            offset_y = self._y + lines[0].ascent
        elif self._valign == 'bottom':
            if self._height is None:
                offset_y = self._y + self.content_height
            else:
                offset_y = self._y - self._height + self.content_height
        elif self._valign == 'center':
            if self._height is None:
                if len(lines) == 1:
                    offset_y = \
                        self._y + lines[0].ascent // 2 - lines[0].descent // 4
                else:
                    offset_y = self._y + self.content_height // 2
            else:
                offset_y = self._y + (self._height + self.content_height) // 2
        else:
            assert False, 'Invalid valign'
        
        context = StaticLayoutContext(self, self._document, 
                                      colors_iter, background_iter)
        for line in lines:
            self._create_vertex_lists(offset_x + line.x, offset_y + line.y, 
                                      line.start, line.boxes, context)
        self._vertex_lists.extend(context.vertex_lists)

    def _init_document(self):
        self._update()

    def _uninit_document(self):
        pass

    def on_insert_text(self, start, text):
        self._init_document()

    def on_delete_text(self, start, end):
        self._init_document()

    def on_style_text(self, start, end, attributes):
        self._init_document()

    def _get_glyphs(self):
        glyphs = []
        runs = runlist.ZipRunIterator((
            self._document.get_font_runs(dpi=self._dpi),
            self._document.get_element_runs()))
        text = self._document.text
        for start, end, (font, element) in runs.ranges(0, len(text)):
            if element:
                glyphs.append(InlineElementBox(element))
            else:
                glyphs.extend(font.get_glyphs(text[start:end]))
        return glyphs

    def _get_owner_runs(self, owner_runs, glyphs, start, end):
        owner = glyphs[start].owner
        run_start = start
        # TODO avoid glyph slice on non-incremental
        for i, glyph in enumerate(glyphs[start:end]):
            if owner != glyph.owner:
                owner_runs.set_run(run_start, i + start, owner)
                owner = glyph.owner
                run_start = i + start
        owner_runs.set_run(run_start, end, owner)    

    def _flow_glyphs(self, glyphs, owner_runs, start, end):
        # TODO change flow generator on self, avoiding this conditional.
        if not self.multiline:
            for line in self._flow_glyphs_single_line(glyphs, owner_runs, 
                                                      start, end):
                yield line
        else:
            for line in self._flow_glyphs_wrap(glyphs, owner_runs, start, end):
                yield line

    def _flow_glyphs_wrap(self, glyphs, owner_runs, start, end):
        '''Word-wrap styled text into lines of fixed width.

        Fits `glyphs` in range `start` to `end` into `Line`s which are
        then yielded.
        '''
        owner_iterator = owner_runs.get_run_iterator().ranges(start, end)

        font_iterator = self._document.get_font_runs(dpi=self._dpi)

        align_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs('align'),
            lambda value: value in ('left', 'right', 'center'), 
            'left')
        wrap_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs('wrap'),
            lambda value: value in (True, False),
            True)
        margin_left_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs('margin_left'), 
            lambda value: value is not None, 0)
        margin_right_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs('margin_right'),
            lambda value: value is not None, 0)
        indent_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs('indent'),
            lambda value: value is not None, 0)
        kerning_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs('kerning'),
            lambda value: value is not None, 0)
        tab_stops_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs('tab_stops'),
            lambda value: value is not None, [])
        
        line = Line(start)
        line.align = align_iterator[start]
        line.margin_left = margin_left_iterator[start]
        line.margin_right = margin_right_iterator[start]
        if start == 0 or self.document.text[start - 1] in u'\n\u2029':
            line.paragraph_begin = True
            line.margin_left += self._points_to_pixels(indent_iterator[start])
        wrap = wrap_iterator[start]
        width = self._width - line.margin_left - line.margin_right

        # Current right-most x position in line being laid out.
        x = 0

        # Boxes accumulated but not yet committed to a line.
        run_accum = []
        run_accum_width = 0

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
            for (text, glyph) in zip(self.document.text[start:end],
                                     glyphs[start:end]):
                if nokern:
                    kern = 0
                    nokern = False
                else:
                    kern = self._points_to_pixels(kerning_iterator[index])

                if text in u'\u0020\u200b\t':
                    # Whitespace: commit pending runs to this line.
                    for run in run_accum:
                        line.add_box(run)
                    run_accum = []
                    run_accum_width = 0

                    if text == '\t':
                        # Fix up kern for this glyph to align to the next tab
                        # stop
                        for tab_stop in tab_stops_iterator[index]:
                            if tab_stop > x + line.margin_left:
                                break
                        else:
                            # No more tab stops, tab to 100 pixels
                            tab = 50.
                            tab_stop = \
                              (((x + line.margin_left) // tab) + 1) * tab
                        kern = int(tab_stop - x - line.margin_left - 
                                   glyph.advance)

                    owner_accum.append((kern, glyph))
                    owner_accum_commit.extend(owner_accum)
                    owner_accum_commit_width += owner_accum_width + \
                        glyph.advance

                    # Note that the width of the space glyph is added to
                    # the width of the new accumulation.  This is so
                    # whitespace at the end of a line does not contribute
                    # to its width.
                    owner_accum = []
                    owner_accum_width = 0
                    #owner_accum_width = glyph.advance
                    x += glyph.advance + kern

                    index += 1
                        
                    # The index at which the next line will begin (the
                    # current index, because this is the current best
                    # breakpoint).
                    next_start = index
                else:
                    new_paragraph = text in u'\n\u2029'
                    new_line = (text == u'\u2028') or new_paragraph
                    if (wrap and self._width is not None and
                        x + kern + glyph.advance >= width) or new_line:

                        # Either the pending runs have overflowed the allowed
                        # line width or a newline was encountered.  Either
                        # way, the current line must be flushed.

                        if new_line:
                            # Forced newline.  Commit everything pending
                            # without exception.
                            for run in run_accum:
                                line.add_box(run)
                            run_accum = []
                            run_accum_width = 0
                            owner_accum_commit.extend(owner_accum)
                            owner_accum_commit_width += owner_accum_width
                            owner_accum = []
                            owner_accum_width = 0

                            line.length += 1
                            next_start = index + 1

                        # Create the GlyphBox for the committed glyphs in the
                        # current owner.
                        if owner_accum_commit:
                            line.add_box(
                                GlyphBox(owner, font, owner_accum_commit,
                                         owner_accum_commit_width))
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
                            if new_paragraph:
                                line.paragraph_end = True
                            yield line
                            line = Line(next_start)
                            line.align = align_iterator[next_start]
                            line.margin_left = margin_left_iterator[next_start]
                            line.margin_right = \
                                margin_right_iterator[next_start]
                            if new_paragraph:
                                line.paragraph_begin = True

                            # Remove kern from first glyph of line
                            if run_accum:
                                k, g = run_accum[0].glyphs[0]
                                run_accum[0].glyphs[0] = (0, g)
                                run_accum_width -= k
                            elif owner_accum:
                                k, g = owner_accum[0]
                                owner_accum[0] = (0, g)
                                owner_accum_width -= k
                            else:
                                nokern = True

                            x = run_accum_width + owner_accum_width

                    if isinstance(glyph, AbstractBox):
                        # Glyph is already in a box. XXX Ignore kern?
                        run_accum.append(glyph)
                        run_accum_width += glyph.advance
                        x += glyph.advance
                    elif new_paragraph:
                        # New paragraph started, update wrap style
                        wrap = wrap_iterator[next_start]
                        line.margin_left += \
                            self._points_to_pixels(indent_iterator[next_start])
                        width = (self._width - 
                                 line.margin_left - line.margin_right)
                    elif not new_line:
                        # If the glyph was any non-whitespace, non-newline
                        # character, add it to the pending run.
                        owner_accum.append((kern, glyph))
                        owner_accum_width += glyph.advance + kern
                        x += glyph.advance + kern
                    index += 1

            # The owner run is finished; create GlyphBoxes for the committed
            # and pending glyphs.
            if owner_accum_commit:
                line.add_box(GlyphBox(owner, font, owner_accum_commit,
                                            owner_accum_commit_width))
            if owner_accum:
                run_accum.append(GlyphBox(owner, font, owner_accum,
                                          owner_accum_width))
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

    def _flow_glyphs_single_line(self, glyphs, owner_runs, start, end):
        owner_iterator = owner_runs.get_run_iterator.ranges(start, end)
        font_iterator = self.document.get_font_runs(dpi=self._dpi)
        kern_iterator = runlist.FilteredRunIterator(
            self.document.get_style_runs('kerning'),
            lambda value: value is not None, 0)

        line = Line(start)
        x = 0
        font = font_iterator[0]

        for start, end, owner in owner_iterator:
            font = font_iterator[start]
            width = 0
            owner_glyphs = []
            for kern_start, kern_end, kern in kern_iterator.ranges(start, end): 
                gs = glyphs[kern_start:kern_end]
                width += sum([g.advance for g in gs])
                width += kern * (kern_end - kern_start)
                owner_glyphs.extend(zip([kern] * (kern_end - kern_start), gs))
            line.add_box(GlyphBox(owner, font, owner_glyphs, width))
    
        if not line.boxes:
            line.ascent = font.ascent
            line.descent = font.descent

        line.paragraph_begin = line.paragraph_end = True

        yield line 

    def _flow_lines(self, lines, start, end):
        margin_top_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs('margin_top'),
            lambda value: value is not None, 0)
        margin_bottom_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs('margin_bottom'),
            lambda value: value is not None, 0)
        line_spacing_iterator = self._document.get_style_runs('line_spacing')
        leading_iterator = runlist.FilteredRunIterator(
            self._document.get_style_runs('leading'),
            lambda value: value is not None, 0)

        if start == 0:
            y =  0
        else:
            line = lines[start - 1]
            line_spacing = \
                self._points_to_pixels(line_spacing_iterator[line.start])
            leading = \
                self._points_to_pixels(leading_iterator[line.start])

            y = line.y
            if line_spacing is None:
                y += line.descent
            if line.paragraph_end:
                y -= margin_bottom_iterator[line.start]


        line_index = start
        for line in lines[start:]:
            if line.paragraph_begin:
                y -= margin_top_iterator[line.start]
                line_spacing = \
                    self._points_to_pixels(line_spacing_iterator[line.start])
                leading = self._points_to_pixels(leading_iterator[line.start])
            else:
                y -= leading
            
            if line_spacing is None:
                y -= line.ascent
            else:
                y -= line_spacing
            if line.align == 'left' or line.width > self.width:
                line.x = line.margin_left
            elif line.align == 'center':
                line.x = (self.width - line.margin_left - line.margin_right
                          - line.width) // 2 + line.margin_left
            elif line.align == 'right':
                line.x = self.width - line.margin_right - line.width

            # TODO incremental needs to reduce content width (trigger rescan
            # if deleted line has content width -- yikes)
            self.content_width = max(self.content_width, 
                                     line.width + line.margin_left)

            if line.y == y and line_index >= end: 
                # Early exit: all invalidated lines have been reflowed and the
                # next line has no change (therefore subsequent lines do not
                # need to be changed).
                break
            line.y = y

            if line_spacing is None:
                y += line.descent
            if line.paragraph_end:
                y -= margin_bottom_iterator[line.start]

            line_index += 1
        else:
            self.content_height = -y

        return line_index
        
    def _create_vertex_lists(self, x, y, i, boxes, context):
        for box in boxes:
            box.place(self, i, x, y, context)
            x += box.advance
            i += box.length

    _x = 0
    def _set_x(self, x):
        dx = x - self._x
        l_dx = lambda x: x + dx
        for vertex_list in self._vertex_lists:
            vertices = vertex_list.vertices[:]
            vertices[::2] = map(l_dx, vertices[::2])
            vertex_list.vertices[:] = vertices
        self._x = x

    def _get_x(self):
        return self._x

    x = property(_get_x, _set_x)

    _y = 0
    def _set_y(self, y):
        dy = y - self._y
        l_dy = lambda y: y + dy
        for vertex_list in self._vertex_lists:
            vertices = vertex_list.vertices[:]
            vertices[1::2] = map(l_dy, vertices[1::2])
            vertex_list.vertices[:] = vertices
        self._y = y

    def _get_y(self):
        return self._y

    y = property(_get_y, _set_y)

    _width = None
    def _set_width(self, width):
        if width is None:
            self.multiline = False
        self._width = width
        self._update()

    def _get_width(self):
        return self._width

    width = property(_get_width, _set_width)

    _height = None
    def _set_height(self, height):
        self._height = height
        self._update()

    def _get_height(self):
        return self._height

    height = property(_get_height, _set_height)


    # XXX not valid for incremental.
    
    _halign = 'left'
    def _set_halign(self, halign):
        self._halign = halign
        self._update()

    def _get_halign(self):
        return self._halign

    halign = property(_get_halign, _set_halign)

    _valign = 'top'
    def _set_valign(self, valign):
        self._valign = valign
        self._update()

    def _get_valign(self):
        return self._valign

    valign = property(_get_valign, _set_valign)

class ScrollableTextLayout(TextLayout):
    def __init__(self, document, width, height, multiline=False, dpi=None,
                 batch=None, group=None):
        self._width = width
        self._height = height
        super(ScrollableTextLayout, self).__init__(
            document, multiline, dpi, batch, group)

    def _init_groups(self, group):
        # Scrollable layout never shares group becauase of translation.   
        self.top_group = ScrollableTextLayoutGroup(group)
        self.background_group = graphics.OrderedGroup(0, self.top_group)
        self.foreground_group = TextLayoutForegroundGroup(1, self.top_group)
        self.foreground_decoration_group = \
            TextLayoutForegroundDecorationGroup(2, self.top_group)

    def _set_x(self, x):
        self.top_group.scissor_x = x
        self.top_group.translate_x = x - self.top_group.view_x

    def _get_x(self):
        return self.top_group.scissor_x

    x = property(_get_x, _set_x)

    def _set_y(self, y):
        self.top_group.scissor_y = y
        self.top_group.translate_y = y - self.top_group.view_y

    def _get_y(self):
        return self.top_group.scissor_y

    y = property(_get_y, _set_y)

    def _set_width(self, width):
        if width is None:
            self.multiline = False
        self._width = width
        self.top_group.scissor_width = width
        self._update()

    def _get_width(self):
        return self._width

    width = property(_get_width, _set_width)

    def _set_height(self, height):
        self._height = height
        self.top_group.scissor_height = height

    def _get_height(self):
        return self._height

    height = property(_get_height, _set_height)

    # Offset of content within viewport

    def _set_view_x(self, view_x):
        view_x = max(0, min(self.content_width - self.width, view_x))
        self.top_group.view_x = view_x
        self.top_group.translate_x = self.top_group.scissor_x - view_x

    def _get_view_x(self):
        return self.top_group.view_x

    view_x = property(_get_view_x, _set_view_x)

    def _set_view_y(self, view_y):
        # view_y must be negative.
        view_y = min(0, max(self.height - self.content_height, view_y))
        self.top_group.view_y = view_y
        self.top_group.translate_y = self.top_group.scissor_y - view_y

    def _get_view_y(self):
        return self.top_group.view_y

    view_y = property(_get_view_y, _set_view_y)

    def ensure_line_visible(self, line):
        line = self.lines[line]
        y1 = line.y + line.ascent
        y2 = line.y + line.descent
        if y1 > self.view_y:
            self.view_y = y1
        elif y2 < self.view_y - self.height:
            self.view_y = y2  + self.height

    def ensure_x_visible(self, x):
        if x <= self.view_x + 10:
            self.view_x = x - 10
        elif x >= self.view_x + self.width:
            self.view_x = x - self.width + 10 
        elif (x >= self.view_x + self.width - 10 and 
              self.content_width > self.width):
            self.view_x = x - self.width + 10 

class IncrementalTextLayout(ScrollableTextLayout):
    '''Displayed text suitable for interactive editing and/or scrolling
    large documents.'''
    def __init__(self, document, width, height, multiline=False, dpi=None,
                 batch=None, group=None):
        self.glyphs = []
        self.lines = []

        self.invalid_glyphs = InvalidRange()
        self.invalid_flow = InvalidRange()
        self.invalid_lines = InvalidRange()
        self.invalid_style = InvalidRange()
        self.invalid_vertex_lines = InvalidRange()
        self.visible_lines = InvalidRange()

        self.owner_runs = runlist.RunList(0, None)

        super(IncrementalTextLayout, self).__init__(
            document, width, height, multiline, dpi, batch, group)

    def _init_document(self):
        assert self._document, \
            'Cannot remove document from IncrementalTextLayout'
        self.on_insert_text(0, self._document.text)

    def _uninit_document(self):
        self.on_delete_text(0, len(self._document.text))

    def delete(self):
        for line in self.lines:
            line.delete(self)

    def on_insert_text(self, start, text):
        len_text = len(text)
        self.glyphs[start:start] = [None] * len_text

        self.invalid_glyphs.insert(start, len_text)
        self.invalid_flow.insert(start, len_text)
        self.invalid_style.insert(start, len_text)

        self.owner_runs.insert(start, len_text)

        for line in self.lines:
            if line.start >= start:
                line.start += len_text

        self._update()

    def on_delete_text(self, start, end):
        self.glyphs[start:end] = []

        self.invalid_glyphs.delete(start, end)
        self.invalid_flow.delete(start, end)
        self.invalid_style.delete(start, end)

        self.owner_runs.delete(start, end)

        size = end - start
        for line in self.lines:
            if line.start > start:
                line.start = max(line.start - size, start)

        if start == 0:
            self.invalid_flow.invalidate(0, 1)
        else:
            self.invalid_flow.invalidate(start - 1, start)

        self._update()

    def on_style_text(self, start, end, attributes):
        if ('font_name' in attributes or
            'font_size' in attributes or
            'bold' in attributes or
            'italic' in attributes):
            self.invalid_glyphs.invalidate(start, end)
        elif False: # Attributes that change flow
            self.invalid_flow.invalidate(start, end)
        elif ('color' in attributes or
              'background_color' in attributes):
            self.invalid_style.invalidate(start, end)

        self._update()

    def _update(self):
        if not self._update_enabled:
            return

        # Special care if there is no text:
        if not self.glyphs:
            for line in self.lines:
                line.delete(self)
            del self.lines[:]
            self.lines.append(Line(0))
            font = self.document.get_font(0, dpi=self._dpi)
            self.lines[0].ascent = font.ascent
            self.lines[0].descent = font.descent
            self.invalid_lines.invalidate(0, 1)

        self._update_glyphs()
        self._update_flow_glyphs()
        self._update_flow_lines()
        self._update_visible_lines()
        self._update_vertex_lists()

    def _update_glyphs(self):
        invalid_start, invalid_end = self.invalid_glyphs.validate()

        if invalid_end - invalid_start <= 0:
            return

        # Update glyphs
        runs = runlist.ZipRunIterator((
            self._document.get_font_runs(dpi=self._dpi),
            self._document.get_element_runs()))
        for start, end, (font, element) in \
                runs.ranges(invalid_start, invalid_end):
            if element:
                self.glyphs[start] = InlineElementBox(element)
            else:
                text = self.document.text[start:end]
                self.glyphs[start:end] = font.get_glyphs(text)

        # Update owner runs
        self._get_owner_runs(
            self.owner_runs, self.glyphs, invalid_start, invalid_end)

        # Updated glyphs need flowing
        self.invalid_flow.invalidate(invalid_start, invalid_end)

    def _update_flow_glyphs(self):
        invalid_start, invalid_end = self.invalid_flow.validate()

        if invalid_end - invalid_start <= 0:
            return
        
        # Find first invalid line
        line_index = 0
        for i, line in enumerate(self.lines):
            if line.start >= invalid_start:
                break
            line_index = i

        # (No need to find last invalid line; the update loop below stops
        # calling the flow generator when no more changes are necessary.)

        try:
            line = self.lines[line_index]
            invalid_start = min(invalid_start, line.start)
            line.delete(self)
            line = self.lines[line_index] = Line(invalid_start)
            self.invalid_lines.invalidate(line_index, line_index + 1)
        except IndexError:
            line_index = 0
            invalid_start = 0
            line = Line(0)
            self.lines.append(line)
            self.invalid_lines.insert(0, 1)

        next_start = invalid_start

        for line in self._flow_glyphs(self.glyphs, self.owner_runs,
                                      invalid_start, len(self._document.text)):
            try:
                self.lines[line_index].delete(self)
                self.lines[line_index] = line
                self.invalid_lines.invalidate(line_index, line_index + 1)
            except IndexError:
                self.lines.append(line)
                self.invalid_lines.insert(line_index, 1)
                
            next_start = line.start + line.length
            line_index += 1
                
            try:
                next_line = self.lines[line_index]
                if next_start == next_line.start and next_start > invalid_end:
                    # No more lines need to be modified, early exit.
                    break
            except IndexError:
                pass
        else:
            # The last line is at line_index - 1, if there are any more lines
            # after that they are stale and need to be deleted.
            if next_start == len(self._document.text) and line_index > 0:
                for line in self.lines[line_index:]:
                    line.delete(self)
                del self.lines[line_index:]

    def _update_flow_lines(self):
        invalid_start, invalid_end = self.invalid_lines.validate()
        if invalid_end - invalid_start <= 0:
            return

        invalid_end = self._flow_lines(self.lines, invalid_start, invalid_end)

        # Invalidate lines that need new vertex lists.
        self.invalid_vertex_lines.invalidate(invalid_start, invalid_end)

    def _update_visible_lines(self):
        start = sys.maxint
        end = 0
        for i, line in enumerate(self.lines):
            if line.y + line.descent < self.view_y:
                start = min(start, i)
            if line.y + line.ascent > self.view_y - self.height:
                end = max(end, i) + 1

        # Delete newly invisible lines
        for i in range(self.visible_lines.start, min(start, len(self.lines))):
            self.lines[i].delete(self)
        for i in range(end, min(self.visible_lines.end, len(self.lines))):
            self.lines[i].delete(self)
        
        # Invalidate newly visible lines
        self.invalid_vertex_lines.invalidate(start, self.visible_lines.start)
        self.invalid_vertex_lines.invalidate(self.visible_lines.end, end)

        self.visible_lines.start = start
        self.visible_lines.end = end

    def _update_vertex_lists(self):
        # Find lines that have been affected by style changes
        style_invalid_start, style_invalid_end = self.invalid_style.validate()
        self.invalid_vertex_lines.invalidate(
            self.get_line_from_position(style_invalid_start),
            self.get_line_from_position(style_invalid_end) + 1)
        
        invalid_start, invalid_end = self.invalid_vertex_lines.validate()
        if invalid_end - invalid_start <= 0:
            return

        batch = self.batch

        colors_iter = self.document.get_style_runs('color')
        background_iter = self.document.get_style_runs('background_color')
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

        context = IncrementalLayoutContext(self, self._document, 
                                           colors_iter, background_iter)

        for line in self.lines[invalid_start:invalid_end]:
            line.delete(self)
            context.line = line
            y = line.y

            # Early out if not visible
            if y + line.descent > self.view_y:
                continue
            elif y + line.ascent < self.view_y - self.height:
                break

            self._create_vertex_lists(line.x, y, line.start,
                                      line.boxes, context)

    # Invalidate everything when width changes

    def _set_width(self, width):
        if width == self._width:
            # Quick optimisation for speeding up vertical resize.
            return

        self.invalid_flow.invalidate(0, len(self.document.text))
        super(IncrementalTextLayout, self)._set_width(width)

    def _get_width(self):
        return self._width

    width = property(_get_width, _set_width)

    # Recalculate visible lines when height changes
    def _set_height(self, height):
        super(IncrementalTextLayout, self)._set_height(height)
        if self._update_enabled:
            self._update_visible_lines()
            self._update_vertex_lists()

    def _get_height(self):
        return self._height

    height = property(_get_height, _set_height)

    # Invalidate invisible/visible lines when y scrolls

    def _set_view_y(self, view_y):
        # view_y must be negative.
        super(IncrementalTextLayout, self)._set_view_y(view_y)
        self._update_visible_lines()
        self._update_vertex_lists()

    def _get_view_y(self):
        return self.top_group.view_y

    view_y = property(_get_view_y, _set_view_y)

    # Visible selection

    _selection_start = 0
    _selection_end = 0

    def set_selection(self, start, end):
        start = max(0, start)
        end = min(end, len(self.document.text))
        if start == self._selection_start and end == self._selection_end:
            return

        if end > self._selection_start and start < self._selection_end:
            # Overlapping, only invalidate difference
            self.invalid_style.invalidate(min(start, self._selection_start),
                                          max(start, self._selection_start))
            self.invalid_style.invalidate(min(end, self._selection_end),
                                          max(end, self._selection_end))
        else:
            # Non-overlapping, invalidate both ranges
            self.invalid_style.invalidate(self._selection_start, 
                                          self._selection_end)
            self.invalid_style.invalidate(start, end)

        self._selection_start = start
        self._selection_end = end

        self._update()

    _selection_color = [255, 255, 255, 255]
    _selection_background_color = [46, 106, 197, 255]

    # Coordinate translation

    def get_position_from_point(self, x, y):
        line = self.get_line_from_point(x, y)
        return self.get_position_on_line(line, x)
    
    def get_point_from_position(self, position, line=None):
        if line is None:
            line = self.lines[0]
            for next_line in self.lines:
                if next_line.start > position:
                    break
                line = next_line
        else:
            line = self.lines[line]
            
        x = line.x

        baseline = self._document.get_style('baseline', max(0, position - 1))
        if baseline is None:
            baseline = 0
        else:
            baseline = self._points_to_pixels(baseline) 

        position -= line.start
        for box in line.boxes:
            if position - box.length <= 0:
                x += box.get_point_in_box(position)
                break
            position -= box.length
            x += box.advance
       
        return (x + self.top_group.translate_x, 
                line.y + self.top_group.translate_y + baseline)

    def get_line_from_point(self, x, y):
        x -= self.top_group.translate_x
        y -= self.top_group.translate_y

        line_index = 0
        for line in self.lines:
            if y > line.y + line.descent:
                break
            line_index += 1
        if line_index >= len(self.lines):
            line_index = len(self.lines) - 1
        return line_index

    def get_point_from_line(self, line):
        line = self.lines[line]
        return (line.x + self.top_group.translate_x, 
                line.y + self.top_group.translate_y)

    def get_line_from_position(self, position):
        line = -1
        for next_line in self.lines:
            if next_line.start > position:
                break
            line += 1
        return line

    def get_position_from_line(self, line):
        return self.lines[line].start

    def get_position_on_line(self, line, x):
        line = self.lines[line]
        x -= self.top_group.translate_x

        position = line.start
        last_glyph_x = line.x
        for box in line.boxes:
            if 0 <= x - last_glyph_x < box.advance:
                position += box.get_position_in_box(x - last_glyph_x)
                break
            last_glyph_x += box.advance
            position += box.length

        return position

    def get_line_count(self):
        return len(self.lines)

