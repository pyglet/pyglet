#!/usr/bin/python
# $Id:$

import sys

from pyglet.gl import *
from pyglet import graphics
from pyglet.text import style

class Line(object):
    align = 'left'

    def __init__(self, start):
        self.vertex_lists = []
        self.clear(start)

    def __repr__(self):
        return 'Line(%r)' % self.glyph_runs

    def add_glyph_run(self, glyph_run):
        self.glyph_runs.append(glyph_run)
        self.length += len(glyph_run.glyphs)
        self.ascent = max(self.ascent, glyph_run.font.ascent)
        self.descent = min(self.descent, glyph_run.font.descent)
        self.width += glyph_run.width

    def delete_vertex_lists(self):
        for list in self.vertex_lists:
            list.delete()

        self.vertex_lists = []

    def clear(self, start):
        # XXX clear() is redundant? lines get reconstructed anyway? 
        self.start = start
        self.length = 0
        
        self.glyph_runs = []
        self.ascent = 0
        self.descent = 0
        self.width = 0

        self.x = None
        self.y = None

        self.delete_vertex_lists()

class GlyphRun(object):
    def __init__(self, owner, font, glyphs, width):
        self.owner = owner
        self.font = font
        self.glyphs = glyphs
        self.width = width 

    def add_glyphs(self, glyphs):
        self.glyphs.extend(glyphs)

    def __repr__(self):
        return 'GlyphRun(%r)' % self.glyphs

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

class TextLayoutOrderedState(graphics.AbstractState):
    def __init__(self, order, parent):
        super(TextLayoutOrderedState, self).__init__(parent)
        self.order = order

    def __cmp__(self, other):
        return cmp(self.order, other.order)

# Text[Viewport]LayoutState(OrderedState) order = user-defined
#   OrderedState; order = 0
#   TextLayoutForegroundState(OrderedState); order = 1
#     TextLayoutTextureState(AbstractState)  
#     ... [one for each font texture used] 
#     ...

class TextLayoutState(graphics.OrderedState):
    def set(self):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset(self):
        glPopAttrib()
        
class TextViewportLayoutState(graphics.OrderedState):
    scissor_x = 0
    scissor_y = 0
    scissor_width = 0
    scissor_height = 0
    view_x = 0
    view_y = 0
    translate_x = 0 # x - view_x
    translate_y = 0 # y - view_y

    def set(self):
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

    def unset(self):
        glTranslatef(-self.translate_x, -self.translate_y, 0)
        glPopAttrib()

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

class TextLayoutForegroundState(graphics.OrderedState):
    def set(self):
        glEnable(GL_TEXTURE_2D)

    # unset not needed, as parent state will pop enable bit (background is
    # ordered before foreground)

class TextLayoutTextureState(graphics.AbstractState):
    def __init__(self, texture, parent):
        assert texture.target == GL_TEXTURE_2D
        super(TextLayoutTextureState, self).__init__(parent)

        self.texture = texture

    def set(self):
        glBindTexture(GL_TEXTURE_2D, self.texture.id)

    # unset not needed, as next state will either bind a new texture or pop
    # enable bit.

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

    top_state = TextLayoutState(0)
    background_state = TextLayoutForegroundState(0, top_state)
    foreground_state = TextLayoutForegroundState(1, top_state)

    def __init__(self, document, multiline=False, batch=None, state_order=0):
        self.content_width = 0
        self.content_height = 0

        self.states = {}
        self._init_states(state_order)

        if batch is None:
            batch = graphics.Batch()
        self.batch = batch

        self.multiline = multiline
        self.document = document       

    def delete(self):
        # TODO incremental
        for vertex_list in self._vertex_lists:
            vertex_list.delete()

    def draw(self):
        self.batch.draw_subset(self._vertex_lists)

    def _init_states(self, state_order):
        if state_order != 0:
            self.top_state = TextLayoutState(state_order)
            self.background_state = graphics.OrderedState(0, self.top_state)
            self.foreground_state = TextLayoutForegroundState(1, self.top_state)

    def _get_document(self):
        return self._document

    def _set_document(self, document):
        if self._document:
            # TODO
            assert False, 'Requires pyglet 1.1 feature'
            self._document.remove_handlers(self)
            self._uninit_document(self._document)
        document.push_handlers(self)
        self._document = document
        self._init_document()
    
    document = property(_get_document, _set_document)

    def _update(self):
        for _vertex_list in self._vertex_lists:
            _vertex_list.delete()
        self._vertex_lists = []
        
        if not self._document or not self._document.text:
            return

        len_text = len(self._document.text)
        glyphs = self._get_glyphs()
        owner_runs = style.StyleRuns(len_text, None)
        self._get_owner_runs(owner_runs, glyphs, 0, len_text)
        lines = [line for line in self._flow_glyphs(glyphs, 0, len_text)]
        self.content_width = 0
        self._flow_lines(lines, 0, 0, len(lines))

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
        
        for line in lines:
            self._vertex_lists.extend(self._create_vertex_lists(
                offset_x + line.x, offset_y + line.y, 
                line.glyph_runs, line.start,
                colors_iter, background_iter))

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
        runs = self._document.get_font_runs()
        text = self._document.text
        for start, end, font in runs.iter_range(0, len(text)):
            glyphs.extend(font.get_glyphs(text[start:end]))
        return glyphs

    def _get_owner_runs(self, owner_runs, glyphs, start, end):
        owner = glyphs[start].owner
        run_start = start
        # TODO avoid glyph slice on non-incremental
        for i, glyph in enumerate(glyphs[start:end]):
            if owner != glyph.owner:
                owner_runs.set_style(run_start, i + start, owner)
                owner = glyph.owner
                run_start = i + start
        owner_runs.set_style(run_start, end, owner)    

    def _flow_glyphs(self, glyphs, start, end):
        # TODO change flow generator on self, avoiding this conditional.
        if not self.multiline:
            for line in self._flow_glyphs_single_line(glyphs, start, end):
                yield line
        else:
            for line in self._flow_glyphs_wrap(glyphs, start, end):
                yield line

    def _flow_glyphs_wrap(self, glyphs, start, end):
        '''Word-wrap styled text into lines of fixed width.

        Fits `glyphs` in range `start` to `end` into `Line`s which are
        then yielded.
        '''
        owner_iterator = \
            self.owner_runs.get_range_iterator().iter_range(start, end)

        font_iterator = self._document.get_font_runs()

        para_align_iter = self._document.get_style_runs('align')
        def get_align(pos):
            align = para_align_iter.get_style_at(pos)
            if align not in ('left', 'right', 'center'):
                align = 'left'
            return align

        line = Line(start)
        line.align = get_align(start)

        # Current right-most x position in line being laid out.
        x = 0

        # GlyphRuns accumulated but not yet committed to a line.
        run_accum = []
        run_accum_width = 0

        # Iterate over glyph owners (texture states); these form GlyphRuns,
        # but broken into lines.
        font = None
        for start, end, owner in owner_iterator:
            font = font_iterator.get_style_at(start)

            # Glyphs accumulated in this owner but not yet committed to a
            # line.
            owner_accum = []
            owner_accum_width = 0

            # Glyphs accumulated in this owner AND also committed to the
            # current line (some whitespace has followed all of the committed
            # glyphs).
            owner_accum_commit = []
            owner_accum_commit_width = 0

            # Current glyph index
            index = start

            # Iterate over glyphs in this owner run.  `text` is the
            # corresponding character data for the glyph, and is used to find
            # whitespace and newlines.
            for (text, glyph) in zip(self.document.text[start:end],
                                     glyphs[start:end]):
                if text in u'\u0020\u200b':
                    # Whitespace: commit pending runs to thie line.
                    for run in run_accum:
                        line.add_glyph_run(run)
                    run_accum = []
                    run_accum_width = 0
                    owner_accum.append(glyph)
                    owner_accum_commit.extend(owner_accum)
                    owner_accum_commit_width += owner_accum_width

                    # Note that the width of the space glyph is added to the
                    # width of the new accumulation.  This is so whitespace at
                    # the end of a line does not contribute to its width.
                    owner_accum = []
                    owner_accum_width = glyph.advance

                    index += 1
                    x += glyph.advance
                    
                    # The index at which the next line will begin (the current
                    # index, because this is the current best breakpoint).
                    next_start = index
                else:
                    if (self._width is not None and
                        x + glyph.advance >= self._width) or text == '\n':

                        # Either the pending runs have overflowed the allowed
                        # line width or a newline was encountered.  Either
                        # way, the current line must be flushed.

                        if text == '\n':
                            # Forced newline.  Commit everything pending
                            # without exception.
                            for run in run_accum:
                                line.add_glyph_run(run)
                            run_accum = []
                            run_accum_width = 0
                            owner_accum_commit.extend(owner_accum)
                            owner_accum_commit_width += owner_accum_width
                            owner_accum = []
                            owner_accum_width = 0

                            line.length += 1
                            next_start = index + 1

                        # Create the GlyphRun for the committed glyphs in the
                        # current owner.
                        if owner_accum_commit:
                            line.add_glyph_run(
                                GlyphRun(owner, font, owner_accum_commit,
                                         owner_accum_commit_width))
                            owner_accum_commit = []
                            owner_accum_commit_width = 0

                        if text == '\n' and not line.glyph_runs:
                            # Empty line: give it the current font's default
                            # line-height.
                            line.ascent = font.ascent
                            line.descent = font.descent

                        # Flush the line, unless nothing got committed, in
                        # which case it's a really long string of glyphs
                        # without any breakpoints (in which case it will be
                        # flushed at the earliest breakpoint, not before
                        # something is committed).
                        if line.glyph_runs or text == '\n':
                            yield line
                            line = Line(next_start)
                            line.align = get_align(next_start)
                            x = run_accum_width + owner_accum_width

                    if text != '\n':
                        # If the glyph was any non-whitespace, non-newline
                        # character, add it to the pending run.
                        owner_accum.append(glyph)
                        owner_accum_width += glyph.advance
                        x += glyph.advance
                    index += 1

            # The owner run is finished; create GlyphRuns for the committed
            # and pending glyphs.
            if owner_accum_commit:
                line.add_glyph_run(GlyphRun(owner, font, owner_accum_commit,
                                            owner_accum_commit_width))
            if owner_accum:
                run_accum.append(GlyphRun(owner, font, owner_accum,
                                          owner_accum_width))
                run_accum_width += owner_accum_width

        # All glyphs have been processed: commit everything pending and flush
        # the final line.
        for run in run_accum:
            line.add_glyph_run(run)
    
        if not line.glyph_runs:
            # Empty line gets font's line-height
            if font is None:
                font = self._document.get_font(0)
            line.ascent = font.ascent
            line.descent = font.descent

        yield line

    '''
    # XXX merge me with _wrap (paragraph based).
    def _flow_glyphs_nowrap(self, owner_iterator, glyphs):
        font_iterator = self.document.get_font_runs()

        line = Line(start)
        x = 0
        font = font_iterator.get_style_at(0)

        for start, end, owner in owner_iterator:
            font = font_iterator.get_style_at(start)

            while '\n' in self.document.text[start:end]:
                para_end = self.document.text.index('\n', start)
                owner_glyphs = glyphs[start:para_end]
                if owner_glyphs:
                    line.add_glyph_run(GlyphRun(owner, font, owner_glyphs))

                if not line.glyph_runs:
                    line.ascent = font.ascent
                    line.descent = font.descent
                yield line
                start = para_end + 1
                line = Line(start)
                
            owner_glyphs = glyphs[start:end]
            if owner_glyphs:
                line.add_glyph_run(GlyphRun(owner, font, owner_glyphs))
    
        if not line.glyph_runs:
            line.ascent = font.ascent
            line.descent = font.descent
        
        yield line
    '''

    def _flow_glyphs_single_line(self, glyphs, start, end):
        owner_iterator = \
            self.owner_runs.get_range_iterator().iter_range(start, end)

        font_iterator = self.document.get_font_runs()

        line = Line(start)
        x = 0
        font = font_iterator.get_style_at(0)

        for start, end, owner in owner_iterator:
            font = font_iterator.get_style_at(start)
            owner_glyphs = glyphs[start:end]
            line.add_glyph_run(GlyphRun(owner, font, owner_glyphs))
    
        if not line.glyph_runs:
            line.ascent = font.ascent
            line.descent = font.descent

        yield line 

    def _flow_lines(self, lines, y, start, end):
        line_index = start
        for line in lines[start:]:
            y -= line.ascent

            if line.align == 'left' or line.width > self.width:
                line.x = 0
            elif line.align == 'center':
                line.x = self.width // 2 - line.width // 2
            elif line.align == 'right':
                line.x = self.width - line.width

            # TODO incremental needs to reduce content width (trigger rescan
            # if deleted line has content width -- yikes)
            self.content_width = max(self.content_width, line.width)
            if line.y == y and line_index >= end: 
                break
            line.y = y
            y += line.descent
            line_index += 1
        else:
            self.content_height = -y

        return line_index
        
    def _create_vertex_lists(self, x, y, glyph_runs, 
                             i, colors_iter, background_iter):
        x0 = x1 = x
        vertex_lists = []
        batch = self.batch

        for glyph_run in glyph_runs:
            assert glyph_run.glyphs
            try:
                state = self.states[glyph_run.owner]
            except KeyError:
                owner = glyph_run.owner
                self.states[owner] = state = \
                    TextLayoutTextureState(owner, self.foreground_state)

            n_glyphs = len(glyph_run.glyphs)
            vertices = []
            tex_coords = []
            for glyph in glyph_run.glyphs:
                v0, v1, v2, v3 = glyph.vertices
                v0 += x0
                v2 += x0
                v1 += y
                v3 += y
                vertices.extend([v0, v1, v2, v1, v2, v3, v0, v3])
                t = glyph.tex_coords
                tex_coords.extend(t)
                x0 += glyph.advance
            
            # Text color
            colors = []
            for start, end, color in colors_iter.iter_range(i, i+n_glyphs):
                if color is None:
                    color = (0, 0, 0, 255)
                colors.extend(color * ((end - start) * 4))

            list = batch.add(n_glyphs * 4, GL_QUADS, state, 
                ('v2f/dynamic', vertices),
                ('t3f/dynamic', tex_coords),
                ('c4B/dynamic', colors))
            vertex_lists.append(list)

            # Background color
            background_vertices = []
            background_colors = []
            background_vertex_count = 0
            for start, end, bg in background_iter.iter_range(i, i+n_glyphs):
                if bg is None:
                    for glyph in glyph_run.glyphs[start - i:end - i]:
                        x1 += glyph.advance
                    continue
                
                y1 = y + glyph_run.font.descent
                y2 = y + glyph_run.font.ascent
                x2 = x1
                for glyph in glyph_run.glyphs[start - i:end - i]:
                    x2 += glyph.advance
                    background_vertices.extend(
                        [x1, y1, x2, y1, x2, y2, x1, y2])
                    x1 += glyph.advance
                background_colors.extend(bg * ((end - start) * 4))
                background_vertex_count += (end - start) * 4

            if background_vertex_count:
                background_list = self.batch.add(
                    background_vertex_count, GL_QUADS,
                    self.background_state,
                    ('v2f/dynamic', background_vertices),
                    ('c4B/dynamic', background_colors))
                vertex_lists.append(background_list)

            i += n_glyphs

        return vertex_lists

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

class TextViewportLayout(TextLayout):
    def __init__(self, document, width, height, multiline=False,
                 batch=None, state_order=0):
        self._width = width
        self._height = height
        super(TextViewportLayout, self).__init__(
            document, multiline, batch, state_order)

    def _init_states(self, state_order):
        self.top_state = TextViewportLayoutState(state_order)
        self.background_state = graphics.OrderedState(0, self.top_state)
        self.foreground_state = TextLayoutForegroundState(1, self.top_state)

    def _set_x(self, x):
        self.top_state.scissor_x = x
        self.top_state.translate_x = x - self.top_state.view_x

    def _get_x(self):
        return self.top_state.scissor_x

    x = property(_get_x, _set_x)

    def _set_y(self, y):
        self.top_state.scissor_y = y
        self.top_state.translate_y = y - self.top_state.view_y

    def _get_y(self):
        return self.top_state.scissor_y

    y = property(_get_y, _set_y)

    def _set_width(self, width):
        if width is None:
            self.multiline = False
        self._width = width
        self.top_state.scissor_width = width
        self._update()

    def _get_width(self):
        return self._width

    width = property(_get_width, _set_width)

    def _set_height(self, height):
        self._height = height
        self.top_state.scissor_height = height

    def _get_height(self):
        return self._height

    height = property(_get_height, _set_height)

    # Offset of content within viewport

    def _set_view_x(self, view_x):
        view_x = max(0, min(self.content_width - self.width, view_x) + 1)
        self.top_state.view_x = view_x
        self.top_state.translate_x = self.top_state.scissor_x - view_x

    def _get_view_x(self):
        return self.top_state.view_x

    view_x = property(_get_view_x, _set_view_x)

    def _set_view_y(self, view_y):
        # view_y must be negative.
        view_y = min(0, max(self.height - self.content_height, view_y))
        self.top_state.view_y = view_y
        self.top_state.translate_y = self.top_state.scissor_y - view_y

    def _get_view_y(self):
        return self.top_state.view_y

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

class IncrementalTextLayout(TextViewportLayout):
    '''Displayed text suitable for interactive editing and/or scrolling
    large documents.'''
    def __init__(self, document, width, height, multiline=False, 
                 batch=None, state_order=0):
        self.glyphs = []
        self.lines = []

        self.invalid_glyphs = InvalidRange()
        self.invalid_flow = InvalidRange()
        self.invalid_lines = InvalidRange()
        self.invalid_style = InvalidRange()
        self.invalid_vertex_lines = InvalidRange()
        self.visible_lines = InvalidRange()

        self.owner_runs = style.StyleRuns(0, None)

        super(IncrementalTextLayout, self).__init__(
            document, width, height, multiline, batch, state_order)

    def _init_document(self):
        assert self._document, \
            'Cannot remove document from IncrementalTextLayout'
        self.on_insert_text(0, self._document.text)

    def _uninit_document(self):
        self.on_delete_text(0, len(self._document.text))

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
        # Special care if there is no text:
        if not self.glyphs:
            for line in self.lines:
                line.delete_vertex_lists()
            del self.lines[1:]
            if not self.lines:
                self.lines.append(Line(0))
            self.lines[0].clear(0)
            font = self.document.get_font(0)
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
        runs = self.document.get_font_runs()
        for start, end, font in runs.iter_range(invalid_start, invalid_end):
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
            line.clear(invalid_start)
            self.invalid_lines.invalidate(line_index, line_index + 1)
        except IndexError:
            line_index = 0
            invalid_start = 0
            line = Line(0)
            self.lines.append(line)
            self.invalid_lines.insert(0, 1)

        next_start = invalid_start

        for line in self._flow_glyphs(self.glyphs, 
                                      invalid_start, len(self._document.text)):
            try:
                self.lines[line_index].delete_vertex_lists()
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
                    line.delete_vertex_lists()
                del self.lines[line_index:]

    def _update_flow_lines(self):
        invalid_start, invalid_end = self.invalid_lines.validate()
        if invalid_end - invalid_start <= 0:
            return

        if invalid_start == 0:
            y = 0
        else:
            last = self.lines[invalid_start - 1]
            y = last.y + last.descent
        
        invalid_end = self._flow_lines(self.lines, y, 
            invalid_start, invalid_end)

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
            self.lines[i].delete_vertex_lists()
        for i in range(end, min(self.visible_lines.end, len(self.lines))):
            self.lines[i].delete_vertex_lists()
        
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
            colors_iter = style.OverriddenStyleRunsRangeIterator(
                colors_iter,
                self._selection_start, 
                self._selection_end,
                self._selection_color)
            background_iter = style.OverriddenStyleRunsRangeIterator(
                background_iter,
                self._selection_start, 
                self._selection_end,
                self._selection_background_color)

        for line in self.lines[invalid_start:invalid_end]:
            line.delete_vertex_lists()
            y = line.y

            # Early out if not visible
            if y + line.descent > self.view_y:
                continue
            elif y + line.ascent < self.view_y - self.height:
                break

            line.vertex_lists = self._create_vertex_lists(line.x, y, 
                line.glyph_runs, line.start, colors_iter, background_iter)

    # Invalidate everything when width changes

    def _set_width(self, width):
        self.invalid_flow.invalidate(0, len(self.document.text))
        super(IncrementalTextLayout, self)._set_width(width)

    def _get_width(self):
        return self._width

    width = property(_get_width, _set_width)

    # Invalidate invisible/visible lines when y scrolls

    def _set_view_y(self, view_y):
        # view_y must be negative.
        super(IncrementalTextLayout, self)._set_view_y(view_y)
        self._update_visible_lines()
        self._update_vertex_lists()

    def _get_view_y(self):
        return self.top_state.view_y

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
        
        position -= line.start
        for glyph_run in line.glyph_runs:
            for glyph in glyph_run.glyphs:
                if position == 0:
                    break
                position -= 1
                x += glyph.advance 
        return (x + self.top_state.translate_x, 
                line.y + self.top_state.translate_y)

    def get_line_from_point(self, x, y):
        x -= self.top_state.translate_x
        y -= self.top_state.translate_y

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
        return (line.x + self.top_state.translate_x, 
                line.y + self.top_state.translate_y)

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
        x -= self.top_state.translate_x

        position = line.start
        last_glyph_x = line.x
        for glyph_run in line.glyph_runs:
            for glyph in glyph_run.glyphs:
                if x < last_glyph_x + glyph.advance/2:
                    return position
                position += 1
                last_glyph_x += glyph.advance
        return position

    def get_line_count(self):
        return len(self.lines)

