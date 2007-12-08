#!/usr/bin/python
# $Id:$

import itertools
import re
import sys

import graphics

from pyglet.gl import *

TextState = graphics.TextureState

class StyleRun(object):
    def __init__(self, style, count):
        self.style = style
        self.count = count

    def __repr__(self):
        return 'StyleRun(%r, %d)' % (self.style, self.count)

class StyleRuns(object):
    def __init__(self, size, initial):
        self.runs = [StyleRun(initial, size)]


    def insert(self, pos, length):
        i = 0
        for run in self.runs:
            if i <= pos <= i + run.count:
                run.count += length
            i += run.count

    def delete(self, start, end):
        i = 0
        for run in self.runs:
            if end - start == 0:
                break
            if i <= start <= i + run.count:
                trim = min(end - start, i + run.count - start)
                run.count -= trim
                end -= trim
            i += run.count
        self.runs = [r for r in self.runs if r.count > 0]

        # Don't leave an empty list
        if not self.runs:
            self.runs = [StyleRun(run.style, 0)]

    def set_style(self, start, end, style):
        if end - start <= 0:
            return
        
        # Find runs that need to be split
        i = 0
        start_i = None
        start_trim = 0
        end_i = None
        end_trim = 0
        for run_i, run in enumerate(self.runs):
            count = run.count
            if i < start < i + count:
                start_i = run_i
                start_trim = start - i
            if i < end < i + count:
                end_i = run_i
                end_trim = end - i
            i += count
        
        # Split runs
        if start_i is not None:
            run = self.runs[start_i]
            self.runs.insert(start_i, StyleRun(run.style, start_trim))
            run.count -= start_trim
            if end_i is not None:
                if end_i == start_i:
                    end_trim -= start_trim
                end_i += 1
        if end_i is not None:
            run = self.runs[end_i]
            self.runs.insert(end_i, StyleRun(run.style, end_trim))
            run.count -= end_trim
                
        # Set new style on runs
        i = 0
        for run in self.runs:
            if start <= i and i + run.count <= end: 
                run.style = style
            i += run.count 

        # Merge adjacent runs
        last_run = self.runs[0]
        for run in self.runs[1:]:
            if run.style == last_run.style:
                run.count += last_run.count
                last_run.count = 0
            last_run = run

        # Delete collapsed runs
        self.runs = [r for r in self.runs if r.count > 0]

    def __iter__(self):
        i = 0
        for run in self.runs:
            yield i, i + run.count, run.style
            i += run.count

    def get_range_iterator(self):
        return StyleRunsRangeIterator(self)
    
    def get_style_at(self, index):
        i = 0
        for run in self.runs:
            if i <= index < i + run.count:
                return run.style
            i += run.count

        # If runs are empty, first position still returns default style
        if index == 0 and self.runs[0].count == 0:
            return self.runs[0].style

        assert False, 'Index not in range'

class OverridableStyleRuns(StyleRuns):
    def __init__(self, size, initial):
        super(OverridableStyleRuns, self).__init__(size, initial)
        self.override_start = -1 
        self.override_end = -1
        self.override_style = None

    def set_override(self, style, start, end):
        if start == end:
            start = end = -1
        self.override_style = style
        self.override_start = start
        self.override_end = end

    def __iter__(self):
        i = 0
        for run in self.runs:
            # Some overlap with override
            if i < self.override_start < i + run.count:
                yield i, self.override_start, run.style
            if i <= self.override_start < i + run.count:
                yield self.override_start, \
                      self.override_end, self.override_style
            if i <= self.override_end < i + run.count:
                yield self.override_end, i + run.count, run.style

            # No overlap with override
            if i + run.count < self.override_start or i >= self.override_end:
                yield i, i + run.count, run.style
            i += run.count

    def get_style_at(self, index):
        if self.override_start <= index < self.override_end:
            return self.override_style

        return super(OverridableStyleRuns, self).get_style_at(index)

    def __repr__(self):
        return '%s(%r, override_style=%r, override_start=%r, override_end=%r)'\
            % (self.__class__.__name__, self.runs,
               self.override_style, self.override_start, self.override_end)

class StyleRunsRangeIterator(object):
    '''Perform sequential range iterations over a StyleRuns.'''
    def __init__(self, style_runs):
        self.iter = iter(style_runs)
        self.curr_start, self.curr_end, self.curr_style = self.iter.next()
    
    def iter_range(self, start, end):
        '''Iterate over range [start:end].  The range must be sequential from
        the previous `iter_range` call.'''
        while start >= self.curr_end:
            self.curr_start, self.curr_end, self.curr_style = self.iter.next()
        yield start, min(self.curr_end, end), self.curr_style
        while end > self.curr_end:
            self.curr_start, self.curr_end, self.curr_style = self.iter.next()
            yield self.curr_start, min(self.curr_end, end), self.curr_style

    def get_style_at(self, index):
        while index >= self.curr_end:
            self.curr_start, self.curr_end, self.curr_style = self.iter.next()
        return self.curr_style

class Paragraph(object):
    def __init__(self):
        pass

    def clone(self):
        return Paragraph()

class Line(object):
    def __init__(self, start):
        self.vertex_lists = []
        self.clear(start)

    def __repr__(self):
        return 'Line(%r)' % self.glyph_runs

    def add_glyph_run(self, glyph_run):
        self.glyph_runs.append(glyph_run)
        self.ascent = max(self.ascent, glyph_run.font.ascent)
        self.descent = min(self.descent, glyph_run.font.descent)
        self.width += glyph_run.width

    def delete_vertex_lists(self):
        for list in self.vertex_lists:
            list.delete()

        self.vertex_lists = []

    def clear(self, start):
        self.start = start
        
        self.glyph_runs = []
        self.ascent = 0
        self.descent = 0
        self.width = 0

        self.x = None
        self.y = None

        self.delete_vertex_lists()

class GlyphRun(object):
    def __init__(self, owner, font, glyphs):
        self.owner = owner
        self.font = font
        self.glyphs = glyphs
        self.width = sum(g.advance for g in glyphs) # XXX

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

class TextView(object):
    _paragraph_re = re.compile(r'\n', flags=re.DOTALL)

    def __init__(self, font, text, color=(255, 255, 255, 255), width=400,
                 batch=None):
        self._width = width
        self.y = 480
        self.x = 0

        if batch is None:
            batch = graphics.Batch()
        self.batch = batch
        self.background_batch = graphics.Batch() # TODO XXX

        self._text = ''
        self.glyphs = []
        self.lines = []
        self.states = {}

        self.invalid_glyphs = InvalidRange()
        self.invalid_flow = InvalidRange()
        self.invalid_lines = InvalidRange()
        self.invalid_style = InvalidRange()
        self.invalid_vertex_lines = InvalidRange()

        self.font_runs = StyleRuns(0, font)
        self.owner_runs = StyleRuns(0, None)
        self.color_runs = OverridableStyleRuns(0, color)
        self.background_runs = OverridableStyleRuns(0, None)
        self.paragraph_runs = StyleRuns(0, Paragraph())

        self.insert_text(0, text)

    def insert_text(self, start, text):
        len_text = len(text)
        self._text = ''.join((self._text[:start], text, self._text[start:]))
        self.glyphs[start:start] = [None] * len_text

        self.invalid_glyphs.insert(start, len_text)
        self.invalid_flow.insert(start, len_text)
        self.invalid_style.insert(start, len_text)

        self.font_runs.insert(start, len_text)
        self.owner_runs.insert(start, len_text)
        self.color_runs.insert(start, len_text)
        self.background_runs.insert(start, len_text)
        self.paragraph_runs.insert(start, len_text)

        for line in self.lines:
            if line.start >= start:
                line.start += len_text

        # Insert paragraph breaks
        last_para_start = None
        for match in self._paragraph_re.finditer(text):
            prototype = self.paragraph_runs.get_style_at(start)
            para_start = start + match.start() + 1
            if last_para_start is not None:
                self.paragraph_runs.set_style(last_para_start, para_start, 
                    prototype.clone())
            last_para_start = para_start

        if last_para_start is not None:
            match = self._paragraph_re.search(self._text, last_para_start)
            if match:
                para_end = match.start()
            else:
                para_end = len_text
            self.paragraph_runs.set_style(last_para_start, para_end, 
                prototype.clone())
 
        self._update()

    def remove_text(self, start, end):
        self._text = self._text[:start] + self._text[end:]
        self.glyphs[start:end] = []

        self.invalid_glyphs.delete(start, end)
        self.invalid_flow.delete(start, end)
        self.invalid_style.delete(start, end)

        self.font_runs.delete(start, end)
        self.owner_runs.delete(start, end)
        self.color_runs.delete(start, end)
        self.background_runs.delete(start, end)
        self.paragraph_runs.delete(start, end)

        size = end - start
        for line in self.lines:
            if line.start > start:
                line.start -= size

        # TODO merge paragraph styles

        if start == 0:
            self.invalid_flow.invalidate(0, 1)
        else:
            self.invalid_flow.invalidate(start - 1, start)
        self._update()

    def _update(self):
        # Special care if there is no text:
        if not self.glyphs:
            for line in self.lines:
                line.delete_vertex_lists()
            del self.lines[1:]
            self.lines[0].clear(0)
            self.invalid_lines.invalidate(0, 1)
            self._flow_lines()
            self._update_vertex_lists()
            return

        self._update_glyphs()
        self._flow_glyphs()
        self._flow_lines()
        self._update_vertex_lists()

    def _update_glyphs(self):
        invalid_start, invalid_end = self.invalid_glyphs.validate()

        if invalid_end - invalid_start <= 0:
            return

        # Update glyphs
        font_range_iter = self.font_runs.get_range_iterator()
        for start, end, font in \
                font_range_iter.iter_range(invalid_start, invalid_end):
            text = self._text[start:end]
            self.glyphs[start:end] = font.get_glyphs(text)

        # Update owner runs
        owner = self.glyphs[start].owner
        run_start = start
        for i, glyph in enumerate(self.glyphs[invalid_start:invalid_end]):
            if owner != glyph.owner:
                self.owner_runs.set_style(
                    run_start, i + invalid_start, owner)
                owner = glyph.owner
                run_start = i + start
        self.owner_runs.set_style(run_start, invalid_end, owner)            

        # Updated glyphs need flowing
        self.invalid_flow.invalidate(invalid_start, invalid_end)

    def _flow_glyphs(self):
        invalid_start, invalid_end = self.invalid_flow.validate()

        if invalid_end - invalid_start <= 0:
            return
        
        # Find first invalid line
        line_index = 0
        for i, line in enumerate(self.lines):
            if line.start > invalid_start:
                break
            line_index = i

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

        owner_iterator = self.owner_runs.get_range_iterator().iter_range(
            invalid_start, len(self._text))
        font_iterator = self.font_runs.get_range_iterator()
        x = 0

        run_accum = []
        for start, end, owner in owner_iterator:
            font = font_iterator.get_style_at(start)
            owner_accum = []
            owner_accum_commit = []
            index = start
            for (text, glyph) in zip(self._text[start:end],
                                        self.glyphs[start:end]):
                if text in u'\u0020\u200b':
                    for run in run_accum:
                        line.add_glyph_run(run)
                    run_accum = []
                    owner_accum.append(glyph)
                    owner_accum_commit.extend(owner_accum)
                    owner_accum = []

                    line.width = x # Do not include trailing space in line width
                    x += glyph.advance
                    index += 1
                    
                    next_start = index
                else:
                    if x + glyph.advance >= self._width or text == '\n':
                        if text == '\n':
                            for run in run_accum:
                                line.add_glyph_run(run)
                            run_accum = []
                            owner_accum_commit.extend(owner_accum)
                            owner_accum = []

                            line.width = x 
                            next_start = index + 1

                        if owner_accum_commit:
                            line.add_glyph_run(
                                GlyphRun(owner, font, owner_accum_commit))
                            owner_accum_commit = []

                        if text == '\n' and not line.glyph_runs:
                            line.ascent = font.ascent
                            line.descent = font.descent

                        if line.glyph_runs or text == '\n':
                            line_index += 1
                            try:
                                line = self.lines[line_index]
                                if (next_start == line.start and
                                    next_start > invalid_end):
                                    # No more lines need to be modified, early
                                    # exit.
                                    return
                                line.clear(next_start) # XXX early exit
                                self.invalid_lines.invalidate(
                                    line_index, line_index + 1)
                            except IndexError:
                                line = Line(next_start)
                                self.lines.append(line)
                                self.invalid_lines.insert(line_index, 1)
                            x = sum(r.width for r in run_accum) # XXX
                            x += sum(g.advance for g in owner_accum) # XXX
                    if text != '\n':
                        owner_accum.append(glyph)
                        x += glyph.advance
                    index += 1

            if owner_accum_commit:
                line.add_glyph_run(GlyphRun(owner, font, owner_accum_commit))
            if owner_accum:
                run_accum.append(GlyphRun(owner, font, owner_accum))

        for run in run_accum:
            line.add_glyph_run(run)

        # The last line is at line_index, if there are any more lines after
        # that they are stale and need to be deleted.
        for line in self.lines[line_index + 1:]:
            line.delete_vertex_lists()
        del self.lines[line_index + 1:]

    def _flow_lines(self):
        invalid_start, invalid_end = self.invalid_lines.validate()
        if invalid_end - invalid_start <= 0:
            return

        if invalid_start == 0:
            y = self.y
        else:
            last = self.lines[invalid_start - 1]
            y = last.y + last.descent
        
        line_index = invalid_start
        for line in self.lines[invalid_start:]:
            y -= line.ascent
            line.x = self.x
            if line.y == y and line_index >= invalid_end: 
                break
            line.y = y
            y += line.descent

            line_index += 1

        # Invalidate lines that need new vertex lists.
        self.invalid_vertex_lines.invalidate(invalid_start, line_index)

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

        colors_iter = self.color_runs.get_range_iterator()
        background_iter = self.background_runs.get_range_iterator()
        
        for line in self.lines[invalid_start:invalid_end]:
            i = line.start
            line.delete_vertex_lists()

            x0 = x1 = line.x
            y = line.y
            for glyph_run in line.glyph_runs:
                assert glyph_run.glyphs
                try:
                    state = self.states[glyph_run.owner]
                except KeyError:
                    owner = glyph_run.owner
                    self.states[owner] = state = TextState(owner)

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
                    colors.extend(color * ((end - start) * 4))

                list = batch.add(n_glyphs * 4, GL_QUADS, state, 
                    ('v2f/dynamic', vertices),
                    ('t3f/dynamic', tex_coords),
                    ('c4B/dynamic', colors))
                line.vertex_lists.append(list)

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
                    background_list = self.background_batch.add(
                        background_vertex_count, GL_QUADS, None,
                        ('v2f/dynamic', background_vertices),
                        ('c4B/dynamic', background_colors))
                    line.vertex_lists.append(background_list)


                i += n_glyphs

    # Viewport attributes

    def _set_width(self, width):
        self._width = width
        self.invalid_flow.invalidate(0, len(self.text))
        self._update()

    def _get_width(self):
        return self._width

    width = property(_get_width, _set_width)

    # Visible selection

    _selection_start = 0
    _selection_end = 0

    def set_selection(self, start, end):
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

        self.color_runs.set_override(self._selection_color, start, end)
        self.background_runs.set_override(self._selection_background_color, 
            start, end)

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
        return x, line.y

    def get_line_from_point(self, x, y):
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
        return line.x, line.y

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

    # Styled text access

    def _get_text(self):
        return self._text

    text = property(_get_text)

    def set_font(self, font, start=0, end=None):
        if end is None:
            end = len(self._text)
        self.font_runs.set_style(start, end, font)
        self.invalid_glyphs.invalidate(start, end)
        self._update()

    def get_font(self, position=None):
        if position is None:
            raise NotImplementedError('TODO') # if only one font used, else
                # indeterminate
        return self.font_runs.get_style_at(position)

    def set_background_color(self, color, start=0, end=None):
        if end is None:
            end = len(self._text)
        self.background_runs.set_style(start, end, color)
        self.invalid_style.invalidate(start, end)
        self._update()

class Caret(object):
    _next_word_re = re.compile(r'(?<=\W)\w')
    _previous_word_re = re.compile(r'(?<=\W)\w+\W*$')
    
    def __init__(self, text_view, batch=None):
        self._text_view = text_view
        if batch is None:
            batch = text_view.batch
        self._list = batch.add(2, GL_LINES, None, 'v2f', 'c4B')

        self._ideal_x = None
        self._ideal_line = None
    
    def _set_color(self, color):
        self._list.colors[:3] = color
        self._list.colors[4:7] = color

    def _get_color(self):
        return self._list.colors[:3]

    color = property(_get_color, _set_color)

    def _set_visible(self, visible=True):
        alpha = visible and 255 or 0
        self._list.colors[3] = alpha
        self._list.colors[7] = alpha

    def _get_visible(self):
        return self._list.colors[3] == 255

    visible = property(_get_visible, _set_visible)

    _position = 0
    def _set_position(self, index):
        self._position = index
        self._update()

    def _get_position(self):
        return self._position

    position = property(_get_position, _set_position)

    _mark = None
    def _set_mark(self, mark):
        self._mark = mark
        self._update()
    
    def _get_mark(self):
        return self._mark

    mark = property(_get_mark, _set_mark)

    def _set_line(self, line):
        if self._ideal_x is None:
            self._ideal_x, _ = \
                self._text_view.get_point_from_position(self._position)
        self._position = self._mark = \
            self._text_view.get_position_on_line(line, self._ideal_x)
        self._update(line=line, update_ideal_x=False)

    def _get_line(self):
        if self._ideal_line:
            return self._ideal_line
        else:
            return self._text_view.get_line_from_position(self._position)

    line = property(_get_line, _set_line)

    def move(self, motion):
        from pyglet.window import key

        if self._mark:
            self._mark = None
            self._text_view.set_selection(0, 0)

        if motion == key.MOTION_LEFT:
            self.position = max(0, self.position - 1)
        elif motion == key.MOTION_RIGHT:
            self.position = min(len(self._text_view._text), self.position + 1) 
        elif motion == key.MOTION_UP:
            self.line = max(0, self.line - 1)
        elif motion == key.MOTION_DOWN:
            line = self.line
            if line < self._text_view.get_line_count() - 1:
                self.line = line + 1
        elif motion == key.MOTION_BEGINNING_OF_LINE:
            self.position = self._text_view.get_position_on_line(self.line, 0)
        elif motion == key.MOTION_END_OF_LINE:
            line = self.line
            if line < self._text_view.get_line_count() - 1:
                self.position = \
                    self._text_view.get_position_on_line(line + 1, 0) - 1
            else:
                self.position = len(self._text_view.text)
        elif motion == key.MOTION_BEGINNING_OF_FILE:
            self.position = 0
        elif motion == key.MOTION_END_OF_FILE:
            self.position = len(self._text_view.text)
        elif motion == key.MOTION_NEXT_WORD:
            pos = self._position + 1
            m = self._next_word_re.search(self._text_view.text, pos)
            if not m:
                self.position = len(self._text_view.text)
            else:
                self.position = m.start()
        elif motion == key.MOTION_PREVIOUS_WORD:
            pos = self._position
            m = self._previous_word_re.search(self._text_view.text, 0, pos)
            if not m:
                self.position = 0
            else:
                self.position = m.start()

    def move_to_point(self, x, y):
        line = self._text_view.get_line_from_point(x, y)
        self._mark = None
        self._position = self._text_view.get_position_on_line(line, x)
        self._update(line=line)

    def select_to_point(self, x, y):
        line = self._text_view.get_line_from_point(x, y)
        self._position = self._text_view.get_position_on_line(line, x)
        self._update(line=line)
        
    def _update(self, line=None, update_ideal_x=True):
        x, y = self._text_view.get_point_from_position(self._position, line)
        if update_ideal_x:
            self._ideal_x = x
        self._ideal_line = line

        font = self._text_view.get_font(max(0, self._position - 1))
        self._list.vertices[:] = [x, y + font.descent, x, y + font.ascent]

        if self._mark is not None:
            self._text_view.set_selection(min(self._position, self._mark),
                                          max(self._position, self._mark))

def test_text1(batch, width):
    from pyglet import font
    ft = font.load('Times New Roman', 36)
    ft2 = font.load('Times New Roman', 48, italic=True)
    ft3 = font.load('Times New Roman', 72, italic=True)
    text = TextView(ft, 'Hello, world!', batch=batch, width=width, 
        color=(0, 0, 0, 255)) 
    text.color_runs.set_style(7, 12, (100, 255, 255, 255))
    text.color_runs.set_style(0, 5, (255, 100, 100, 255))
    text.font_runs.set_style(8, 11, ft2)
    text.font_runs.set_style(9, 10, ft3)
    return text

def test_text2(batch, width):
    from pyglet import font
    ft = font.load('Times New Roman', 12)
    ft2 = font.load('Times New Roman', 16)
    text = TextView(ft, frog_prince, batch=batch,
        width=width, color=(0, 0, 0, 255)) 
    text.set_font(ft2, 101, 134)
    text.set_background_color([255, 255, 100, 255], 100, 150)
    return text

def test_text3(batch, width):
    from pyglet import font
    ft = font.load('Georgia', 128)
    text = TextView(ft, 'ab cdefhijklm nop qrs tuv wxyz', 
        color=(0, 0, 0, 255), batch=batch, width=width)
    return text

def main():
    from pyglet import clock
    from pyglet import window
    from pyglet.window import key

    w = window.Window(vsync=False, resizable=True)
    w.set_mouse_cursor(w.get_system_mouse_cursor('text'))

    @w.event
    def on_text(t):
        t = t.replace('\r', '\n')
        caret.mark = None
        text.insert_text(caret.position, t)
        caret.position += len(t)
        cursor_not_idle()

    @w.event
    def on_text_motion(motion):
        if motion == key.MOTION_BACKSPACE:
            if caret.position > 0:
                text.remove_text(caret.position - 1, caret.position)
                caret.position -= 1
        elif motion == key.MOTION_DELETE:
            if caret.position < len(text.text):
                text.remove_text(caret.position, caret.position + 1)
                caret._update()
        else:
            caret.move(motion)
        cursor_not_idle()

    @w.event
    def on_mouse_press(x, y, button, modifiers):
        caret.move_to_point(x, y)
        caret.mark = caret.position
        cursor_not_idle()

    @w.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        caret.select_to_point(x, y)
        cursor_not_idle()

    def on_resize(width, height):
        text.y = height
        text.width = width
        caret._update()
    w.push_handlers(on_resize)

    def blink_cursor(dt):
        caret.visible = not caret.visible

    def cursor_idle(dt):
        clock.schedule_interval(blink_cursor, 0.5)

    def cursor_not_idle():
        clock.unschedule(blink_cursor)
        clock.unschedule(cursor_idle)
        clock.schedule_once(cursor_idle, 0.1)
        caret.visible = True

    batch = graphics.Batch()
    text = test_text2(batch, w.width)
    caret = Caret(text)
    caret.color = (0, 0, 0)
    caret.visible = True
    caret.position = 0

    fps = clock.ClockDisplay()
    
    cursor_idle(0)

    glClearColor(1, 1, 1, 1)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
    while not w.has_exit:
        clock.tick()
        w.dispatch_events()
        w.clear()
        text.background_batch.draw()
        batch.draw()
        fps.draw()
        w.flip()

frog_prince = '''In olden times when wishing still helped one, there lived a king whose daughters were all beautiful, but the youngest was so beautiful that the sun itself, which has seen so much, was astonished whenever it shone in her face.  Close by the king's castle lay a great dark forest, and under an old lime-tree in the forest was a well, and when the day was very warm, the king's child went out into the forest and sat down by the side of the cool fountain, and when she was bored she took a golden ball, and threw it up on high and caught it, and this ball was her favorite plaything.
This is the next pararaph.
And here's another one.'''

if __name__ == '__main__':
    main()
