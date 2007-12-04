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
        assert False, 'Index not in range'

class StyleRunOld(object):
    def __init__(self, start, style):
        self.start = start
        self.style = style

    def __repr__(self):
        return 'StyleRun(%d, %r)' % (self.start, self.style)


class StyleRunsOld(object):
    def __init__(self, size, initial):
        self.size = size
        self.runs = [StyleRun(0, initial)]

    def insert(self, pos, length):
        assert 0 <= pos <= self.size, 'Index not in range'
    
        # Push along all runs after the insertion point, ends up using the
        # usual style for interactive insertion.
        for run in self.runs:
            if run.start >= pos and run.start != 0:
                run.start += length        
        self.size += length

    def delete(self, start, end):
        assert 0 <= start < end <= self.size, 'Slice not in range'

        # Delete everything?
        if start == 0 and end == self.size:
            self.size = 0
            del self.runs[1:]
            return

        # Find indices of style runs that hold start and end slice.
        start_index = None
        end_index = None
        for i, run in enumerate(self.runs):
            if run.start >= start and start_index is None:
                start_index = i
            if run.start == end:
                end_index = i
                break
            elif run.start > end:
                end_index = i - 1
                break
        if end_index is None:
            end_index = len(self.runs) - 1
        if start_index is None:
            start_index = end_index

        # Remove old styles (may be nothing)
        del self.runs[start_index:end_index]

        # Pull back all runs after end point (now the start point after
        # deletion)
        if end_index == 0:
            self.runs[0].start = 0
        elif start_index < len(self.runs):
            if end_index < start_index:
                import pdb; pdb.set_trace()
            elif start_index != end_index:
                self.runs[start_index].start = start
        d = end - start
        for run in self.runs[start_index + 1:]:
            run.start -= d
        self.size -= d
 
    def set_style(self, start, end, style):
        assert 0 <= start < end <= self.size, 'Slice not in range'

        # Find indices of style runs before and after new style range
        start_index = None
        end_index = None
        end_style = None
        for i, run in enumerate(self.runs):
            if run.start >= start and start_index is None:
                start_index = i
            if run.start >= end:
                end_index = i
                break
            end_style = run.style
        if end_index is None:
            end_index = len(self.runs)
        if start_index is None:
            start_index = end_index
            
        # Remove old styles (may be nothing)
        del self.runs[start_index:end_index]
        
        # Insert new style unless unnecessary
        if len(self.runs) <= start_index or \
           self.runs[start_index].style != style:
            self.runs.insert(start_index, StyleRun(start, style))

        if end == self.size:
            return

        # Insert following style unless unnecessary
        if end_style != style and (
            len(self.runs) <= start_index + 1 or
            self.runs[start_index + 1].style != end_style):
            self.runs.insert(start_index + 1, StyleRun(end, end_style))
    
    def __iter__(self):
        last_run = None
        for run in self.runs:
            if last_run:
                yield last_run.start, run.start, last_run.style
            last_run = run
        yield last_run.start, self.size, last_run.style

    def get_range_iterator(self):
        return StyleRunsRangeIterator(self)

    def get_style_at(self, index):
        assert 0 <= index <= self.size, 'Index not in range'
        last_run = None
        for run in self.runs:
            if run.start > index:
                return last_run.style
            last_run = run
        return last_run.style

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

class Line(object):
    def __init__(self, start):
        self.clear(start, delete_lists=False)

    def __repr__(self):
        return 'Line(%r)' % self.glyph_runs

    def add_glyph_run(self, glyph_run):
        self.glyph_runs.append(glyph_run)
        self.ascent = max(self.ascent, glyph_run.font.ascent)
        self.descent = min(self.descent, glyph_run.font.descent)
        self.width += glyph_run.width

    def clear(self, start, delete_lists=True):
        if delete_lists:
            for list in self.vertex_lists:
                list.delete()

        self.start = start
        
        self.glyph_runs = []
        self.ascent = 0
        self.descent = 0
        self.width = 0

        self.x = None
        self.y = None

        self.vertex_lists = []

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
        self.start = min(self.start, start)
        self.end = max(self.end, end)

    def validate(self):
        start, end = self.start, self.end
        self.start = sys.maxint
        self.end = 0
        return start, end

class TextView(object):
    def __init__(self, font, text, color=(255, 255, 255, 255), width=400,
                 batch=None):
        self.width = width
        self.y = 480
        self.x = 0

        if batch is None:
            batch = graphics.Batch()
        self.batch = batch

        self._text = ''
        self.glyphs = []
        self.lines = []
        self.states = {}

        self.invalid_glyphs = InvalidRange()
        self.invalid_lines = InvalidRange()
        self.invalid_vertex_lines = InvalidRange()

        self.font_runs = StyleRuns(0, font)
        self.owner_runs = StyleRuns(0, None)
        self.color_runs = StyleRuns(0, color)

        self.insert_text(0, text)

    def insert_text(self, start, text):
        len_text = len(text)
        self._text = ''.join((self._text[:start], text, self._text[start:]))
        self.glyphs[start:start] = [None] * len_text

        self.invalid_glyphs.insert(start, len_text)
        self.font_runs.insert(start, len_text)
        self.owner_runs.insert(start, len_text)
        self.color_runs.insert(start, len_text)
        
        for line in self.lines:
            if line.start >= start:
                line.start += len_text

        self._update()

    def remove_text(self, start, end):
        self._text = self._text[:start] + self._text[end:]
        self.glyphs[start:end] = []

        self.invalid_glyphs.delete(start, end)
        self.font_runs.delete(start, end)
        self.owner_runs.delete(start, end)
        self.color_runs.delete(start, end)

        size = end - start
        for line in self.lines:
            if line.start > start:
                line.start -= size

        self.invalid_glyphs.invalidate(start, start + 1)
        self._update()

    def _update(self):
        invalid_start, invalid_end = self.invalid_glyphs.validate()

        if invalid_end - invalid_start > 0:
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

            # Reflow
            self._flow_glyphs(invalid_start, invalid_end)

        self._flow_lines()
        self._update_vertex_lists()

    def _flow_glyphs(self, invalid_start, invalid_end):
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
                    if x + glyph.advance >= self.width:
                        if owner_accum_commit:
                            line.add_glyph_run(
                                GlyphRun(owner, font, owner_accum_commit))
                            owner_accum_commit = []
                        if line.glyph_runs:
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
                    owner_accum.append(glyph)
                    x += glyph.advance
                    index += 1

            if owner_accum_commit:
                line.add_glyph_run(GlyphRun(owner, font, owner_accum_commit))
            if owner_accum:
                run_accum.append(GlyphRun(owner, font, owner_accum))

        for run in run_accum:
            line.add_glyph_run(run)

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
        invalid_start, invalid_end = self.invalid_vertex_lines.validate()
        if invalid_end - invalid_start <= 0:
            return

        batch = self.batch

        colors_iter = self.color_runs.get_range_iterator()
        i = 0
        
        for line in self.lines[invalid_start:invalid_end]:
            assert not line.vertex_lists
            x = line.x
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
                    v0 += x
                    v2 += x
                    v1 += y
                    v3 += y
                    vertices.extend([v0, v1, v2, v1, v2, v3, v0, v3])
                    t = glyph.tex_coords
                    tex_coords.extend(t[0] + t[1] + t[2] + t[3])
                    x += glyph.advance
                
                colors = []
                for start, end, color in colors_iter.iter_range(i, i+n_glyphs):
                    colors.extend(color * ((end - start) * 4))

                list = batch.add(n_glyphs * 4, GL_QUADS, state, 
                    ('v2f/dynamic', vertices),
                    ('t3f/dynamic', tex_coords),
                    ('c4B/dynamic', colors))
                line.vertex_lists.append(list)

                i += n_glyphs

    # Coordinate translation

    def get_position_from_point(self, x, y):
        line = self.get_line_from_point(x, y)
        return self.get_position_on_line(line, x)
    
    def get_point_from_position(self, position):
        line = self.lines[0]
        for next_line in self.lines:
            if next_line.start > position:
                break
            line = next_line

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
        return line_index

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

    def get_point_from_line(self, line):
        line = self.lines[line]
        return line.x, line.y

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

class Caret(object):
    _next_word_re = re.compile(r'(?<=\W)\w')
    _previous_word_re = re.compile(r'(?<=\W)\w+\W*$')
    
    def __init__(self, text_view, batch=None):
        self._text_view = text_view
        if batch is None:
            batch = text_view.batch
        self._list = batch.add(2, GL_LINES, None, 'v2f', 'c4B')

        self._ideal_x = None
    
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

    def move(self, motion):
        from pyglet.window import key
        if motion == key.MOTION_LEFT:
            self.position = max(0, self.position - 1)
        elif motion == key.MOTION_RIGHT:
            self.position = min(len(self._text_view._text), self.position + 1) 
        elif motion == key.MOTION_UP:
            line = self._text_view.get_line_from_position(self._position)
            self.move_to_line(max(0, line - 1))
        elif motion == key.MOTION_DOWN:
            line = self._text_view.get_line_from_position(self._position)
            if line < self._text_view.get_line_count() - 1:
                self.move_to_line(line + 1)
        elif motion == key.MOTION_BEGINNING_OF_LINE:
            line = self._text_view.get_line_from_position(self._position)
            self.position = self._text_view.get_position_on_line(line, 0)
        elif motion == key.MOTION_END_OF_LINE:
            line = self._text_view.get_line_from_position(self._position)
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

    def move_to_line(self, line):
        if self._ideal_x is None:
            self._ideal_x, _ = \
                self._text_view.get_point_from_position(self._position)
        self._position = \
            self._text_view.get_position_on_line(line, self._ideal_x)
        self._update(update_ideal_x=False)
        
    def _update(self, update_ideal_x=True):
        x, y = self._text_view.get_point_from_position(self._position)
        if update_ideal_x:
            self._ideal_x = x
        font = self._text_view.get_font(max(0, self._position - 1))
        self._list.vertices[:] = [x, y + font.descent, x, y + font.ascent]
                

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
    ft = font.load('Times New Roman', 16)
    ft2 = font.load('Times New Roman', 48)
    text = TextView(ft, frog_prince.replace('\n', ' '), batch=batch,
        width=width, color=(0, 0, 0, 255)) 
    text.set_font(ft2, 101, 134)
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

    w = window.Window(vsync=False)
    w.set_mouse_cursor(w.get_system_mouse_cursor('text'))

    @w.event
    def on_text(t):
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
            if caret.position < len(text.text) - 1:
                text.remove_text(caret.position, caret.position + 1)
                caret._update()
        else:
            caret.move(motion)
        cursor_not_idle()

    @w.event
    def on_mouse_press(x, y, button, modifiers):
        caret.position = text.get_position_from_point(x, y)
        cursor_not_idle()

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
        batch.draw()
        fps.draw()
        w.flip()

frog_prince = '''In olden times when wishing still
helped one, there lived a king whose daughters were all beautiful, but the
youngest was so beautiful that the sun itself, which has seen so much, was
astonished whenever it shone in her face.  Close by
the king's castle lay a great dark forest, and under an old lime-tree in the
forest was a well, and when the day was very warm, the king's child went out
into the forest and sat down by the side of the cool fountain, and when she
was bored she took a golden ball, and threw it up on high and caught it, and
this ball was her favorite plaything.'''

if __name__ == '__main__':
    main()
