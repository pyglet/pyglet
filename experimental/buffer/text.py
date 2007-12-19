#!/usr/bin/python
# $Id:$

import itertools
import re
import sys

import graphics

from pyglet.gl import *
from pyglet import event

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

class OverriddenStyleRunsRangeIterator(object):
    def __init__(self, base_iterator, start, end, style):
        self.iter = base_iterator
        self.override_start = start
        self.override_end = end
        self.override_style = style

    def iter_range(self, start, end):
        if end <= self.override_start or start >= self.override_end:
            # No overlap
            for r in self.iter.iter_range(start, end):
                yield r
        else:
            # Overlap: before, override, after
            if start < self.override_start < end:
                for r in self.iter.iter_range(start, self.override_start):
                    yield r
            yield (max(self.override_start, start),
                   min(self.override_end, end),
                   self.override_style)
            if start < self.override_end < end:
                for r in self.iter.iter_range(self.override_end, end):
                    yield r
        
    def get_style_at(self, index):
        if self.override_start <= index < self.override_end:
            return self.override_style
        else:
            return self.iter.get_style_at(index)

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

class TextViewOrderedState(graphics.AbstractState):
    def __init__(self, order, parent):
        super(TextViewOrderedState, self).__init__(parent)
        self.order = order

    def __cmp__(self, other):
        return cmp(self.order, other.order)

# TextViewState(OrderedState) order = user-defined
#   OrderedState; order = 0
#   TextViewForegroundState(OrderedState); order = 1
#     TextViewTextureState(AbstractState)  
#     ... [one for each font texture used] 
#     ...

class TextViewState(graphics.OrderedState):
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
        glScissor(self.scissor_x, self.scissor_y - self.scissor_height, 
                  self.scissor_width, self.scissor_height)
        glTranslatef(self.translate_x, self.translate_y, 0)

    def unset(self):
        glTranslatef(-self.translate_x, -self.translate_y, 0)
        glPopAttrib()

class TextViewForegroundState(graphics.OrderedState):
    def set(self):
        glEnable(GL_TEXTURE_2D)

    # unset not needed, as parent state will pop enable bit (background is
    # ordered before foreground)

class TextViewTextureState(graphics.AbstractState):
    def __init__(self, texture, parent):
        assert texture.target == GL_TEXTURE_2D
        super(TextViewTextureState, self).__init__(parent)

        self.texture = texture

    def set(self):
        glBindTexture(GL_TEXTURE_2D, self.texture.id)

    # unset not needed, as next state will either bind a new texture or pop
    # enable bit.

def _iter_paragraphs(text, start=0):
    try:
        while True:
            end = text.index('\n', start)
            yield start, end
            start = end + 1
    except ValueError:
        end = len(text)
        yield start, end

class AbstractDocument(event.EventDispatcher):
    def __init__(self, text):
        super(AbstractDocument, self).__init__()
        self._text = ''
        self.insert_text(0, text)

    def _get_text(self):
        return self._text

    def _set_text(self, text):
        self.remove_text(0, len(self._text))
        self.insert_text(0, text)
    
    text = property(_get_text, _set_text)

    def get_font_runs(self):
        '''
        :rtype: StyleRunsRangeIterator
        '''
        raise NotImplementedError('abstract')

    def get_font(self, position=None):
        raise NotImplementedError('abstract')

    def get_color_runs(self):
        raise NotImplementedError('abstract')
    
    def get_background_color_runs(self):
        raise NotImplementedError('abstract')

    def get_paragraph_runs(self):
        raise NotImplementedError('abstract')

    def insert_text(self, start, text):
        self._insert_text(start, text)
        self.dispatch_event('on_insert_text', start, text)

    def _insert_text(self, start, text):
        self._text = ''.join((self._text[:start], text, self._text[start:]))

    def remove_text(self, start, end):
        self._remove_text(start, end)
        self.dispatch_event('on_remove_text', start, end)

    def _remove_text(self, start, end):
        self._text = self._text[:start] + self._text[end:]

    def on_insert_text(self, start, text):
        '''
        :event:
        '''

    def on_remove_text(self, start, end):
        '''
        :event:
        '''

AbstractDocument.register_event_type('on_insert_text')
AbstractDocument.register_event_type('on_remove_text')

class UnformattedDocument(AbstractDocument):
    paragraph = Paragraph()
    
    def __init__(self, text, font, color):
        super(UnformattedDocument, self).__init__(text)
        self.font = font
        self.color = color

    def get_font_runs(self):
        return StyleRunsRangeIterator(((0, len(self.text), self.font),))

    def get_color_runs(self):
        return StyleRunsRangeIterator(((0, len(self.text), self.color),))

    def get_background_color_runs(self):
        return StyleRunsRangeIterator(((0, len(self.text), None),))

    def get_paragraph_runs(self):
        return StyleRunsRangeIterator(((0, len(self.text), self.paragraph),))

    def get_font(self, position=None):
        return self.font

class FormattedDocument(AbstractDocument):
    _paragraph_re = re.compile(r'\n', flags=re.DOTALL)

    def __init__(self, text, font, color):
        self._font_runs = StyleRuns(0, font)
        self._color_runs = StyleRuns(0, color)
        self._background_color_runs = StyleRuns(0, None)
        self._paragraph_runs = StyleRuns(0, Paragraph())
        super(FormattedDocument, self).__init__(text)

    def get_font_runs(self):
        return self._font_runs.get_range_iterator()

    def get_color_runs(self):
        return self._color_runs.get_range_iterator()
        
    def get_background_color_runs(self):
        return self._background_color_runs.get_range_iterator()

    def get_paragraph_runs(self):
        return self._paragraph_runs.get_range_iterator()

    def _insert_text(self, start, text):
        super(FormattedDocument, self)._insert_text(start, text)

        len_text = len(text)
        self._font_runs.insert(start, len_text)
        self._color_runs.insert(start, len_text)
        self._background_color_runs.insert(start, len_text)
        self._paragraph_runs.insert(start, len_text)

        # Insert paragraph breaks
        last_para_start = None
        for match in self._paragraph_re.finditer(text):
            prototype = self._paragraph_runs.get_style_at(start)
            para_start = start + match.start() + 1
            if last_para_start is not None:
                self._paragraph_runs.set_style(last_para_start, para_start, 
                    prototype.clone())
            last_para_start = para_start

        if last_para_start is not None:
            match = self._paragraph_re.search(self._text, last_para_start)
            if match:
                para_end = match.start()
            else:
                para_end = len_text
            self._paragraph_runs.set_style(last_para_start, para_end, 
                prototype.clone())

    def _remove_text(self, start, end):
        super(FormattedDocument, self)._remove_text(start, end)
        self._font_runs.delete(start, end)
        self._color_runs.delete(start, end)
        self._background_color_runs.delete(start, end)
        self._paragraph_runs.delete(start, end)

        # TODO merge paragraph styles


    def get_font(self, position=None):
        if position is None:
            raise NotImplementedError('TODO') # if only one font used, else
                # indeterminate
        return self._font_runs.get_style_at(position)

    ''' TODO
    def set_font(self, font, start=0, end=None):
        if end is None:
            end = len(self._text)
        self.font_runs.set_style(start, end, font)
        self.invalid_glyphs.invalidate(start, end)
        self._update()
    '''
    ''' TODO
    def set_background_color(self, color, start=0, end=None):
        if end is None:
            end = len(self._text)
        self.background_runs.set_style(start, end, color)
        self.invalid_style.invalidate(start, end)
        self._update()
    '''


class TextView(object):
    def __init__(self, document, width, height, batch=None, state_order=0):
        self._width = width
        self._height = height
        self.content_width = 10000 # TODO
        self.content_height = 0

        self.top_state = TextViewState(state_order)

        self.background_state = graphics.OrderedState(0, self.top_state)
        self.foreground_state = TextViewForegroundState(1, self.top_state)

        if batch is None:
            batch = graphics.Batch()
        self.batch = batch

        self.glyphs = []
        self.lines = []
        self.states = {}

        self.invalid_glyphs = InvalidRange()
        self.invalid_flow = InvalidRange()
        self.invalid_lines = InvalidRange()
        self.invalid_style = InvalidRange()
        self.invalid_vertex_lines = InvalidRange()
        self.visible_lines = InvalidRange()

        self.owner_runs = StyleRuns(0, None)

        self.document = document
        self.document.push_handlers(self)
        # HACK initial setup
        self.on_insert_text(0, self.document.text)

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

    def on_remove_text(self, start, end):
        self.glyphs[start:end] = []

        self.invalid_glyphs.delete(start, end)
        self.invalid_flow.delete(start, end)
        self.invalid_style.delete(start, end)

        self.owner_runs.delete(start, end)

        size = end - start
        for line in self.lines:
            if line.start > start:
                line.start -= size

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
        # TODO find last invalid line (use paragraph breaks); doesn't help
        # current case but will when paragraph style needs to use
        # different flow methods.
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

        #self._flow_glyphs_wrap(invalid_start, invalid_end, line_index)
        self._flow_glyphs_nowrap(invalid_start, invalid_end, line_index)

    def _flow_glyphs_wrap(self, invalid_start, invalid_end, line_index):
        # TODO owner_iterator range only to invalid_end, when invalid_end is
        # extended to end on paragraph boundary.
        owner_iterator = self.owner_runs.get_range_iterator().iter_range(
            invalid_start, len(self.document.text))
        font_iterator = self.document.get_font_runs()

        line = self.lines[line_index]
        x = 0

        run_accum = []
        for start, end, owner in owner_iterator:
            font = font_iterator.get_style_at(start)
            owner_accum = []
            owner_accum_commit = []
            index = start
            for (text, glyph) in zip(self.document.text[start:end],
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

    def _flow_glyphs_nowrap(self, invalid_start, invalid_end, line_index):
        owners = self.owner_runs.get_range_iterator()
        font_iterator = self.document.get_font_runs()

        x = 0

        # Needed in case of blank line at beginning
        font = font_iterator.get_style_at(invalid_start)

        for para_start, para_end in _iter_paragraphs(self.document.text, invalid_start):
            try:
                line = self.lines[line_index]
                if para_start >= invalid_end and line.start == para_start:
                    return

                line.clear(para_start)
                self.invalid_lines.invalidate(line_index, line_index + 1)
            except IndexError:
                line = Line(para_start)
                self.lines.append(line)
                self.invalid_lines.insert(line_index, 1)

            for start, end, owner in owners.iter_range(para_start, para_end):
                font = font_iterator.get_style_at(start)
                glyphs = self.glyphs[start:end]
                if glyphs:
                    line.add_glyph_run(GlyphRun(owner, font, glyphs))

            if not line.glyph_runs:
                line.ascent = font.ascent
                line.descent = font.descent
            
            line_index += 1

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
            y = 0
        else:
            last = self.lines[invalid_start - 1]
            y = last.y + last.descent
        
        line_index = invalid_start
        for line in self.lines[invalid_start:]:
            y -= line.ascent
            line.x = 0
            if line.y == y and line_index >= invalid_end: 
                break
            line.y = y
            y += line.descent

            line_index += 1

        # Update content height
        if line_index == len(self.lines):
            self.content_height = -y    

        # Invalidate lines that need new vertex lists.
        self.invalid_vertex_lines.invalidate(invalid_start, line_index)

    def _update_visible_lines(self):
        start = sys.maxint
        end = 0
        for i, line in enumerate(self.lines):
            if line.y + line.descent < self.view_y:
                start = min(start, i)
            if line.y + line.ascent > self.view_y - self.height:
                end = max(end, i) + 1

        # Delete newly invisible lines
        for i in range(self.visible_lines.start, start):
            self.lines[i].delete_vertex_lists()
        for i in range(end, self.visible_lines.end):
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

        colors_iter = self.document.get_color_runs()
        background_iter = self.document.get_background_color_runs()
        if self._selection_end - self._selection_start > 0:
            colors_iter = OverriddenStyleRunsRangeIterator(
                colors_iter,
                self._selection_start, 
                self._selection_end,
                self._selection_color)
            background_iter = OverriddenStyleRunsRangeIterator(
                background_iter,
                self._selection_start, 
                self._selection_end,
                self._selection_background_color)
        
        for line in self.lines[invalid_start:invalid_end]:
            i = line.start
            line.delete_vertex_lists()

            x0 = x1 = line.x
            y = line.y
            
            # Early out if not visible
            if y + line.descent > self.view_y:
                continue
            elif y + line.ascent < self.view_y - self.height:
                break

            for glyph_run in line.glyph_runs:
                assert glyph_run.glyphs
                try:
                    state = self.states[glyph_run.owner]
                except KeyError:
                    owner = glyph_run.owner
                    self.states[owner] = state = \
                        TextViewTextureState(owner, self.foreground_state)

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
                    background_list = self.batch.add(
                        background_vertex_count, GL_QUADS,
                        self.background_state,
                        ('v2f/dynamic', background_vertices),
                        ('c4B/dynamic', background_colors))
                    line.vertex_lists.append(background_list)


                i += n_glyphs

    # Viewport attributes

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
        self._width = width
        self.top_state.scissor_width = width
        self.invalid_flow.invalidate(0, len(self.document.text))
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
        view_x = max(0, min(self.content_width - self.width, view_x))
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
        self._update_visible_lines()
        self._update_vertex_lists()

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
        elif x >= self.view_x + self.width - 10:
            self.view_x = x - self.width + 10 

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


class Caret(object):
    _next_word_re = re.compile(r'(?<=\W)\w')
    _previous_word_re = re.compile(r'(?<=\W)\w+\W*$')
    
    def __init__(self, text_view, batch=None):
        self._text_view = text_view
        if batch is None:
            batch = text_view.batch
        self._list = batch.add(2, GL_LINES, text_view.background_state, 
            'v2f', 'c4B')

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
        self._update(line=self._ideal_line)
    
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
            self.position = min(len(self._text_view.document.text), self.position + 1) 
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
                self.position = len(self._text_view.document.text)
        elif motion == key.MOTION_BEGINNING_OF_FILE:
            self.position = 0
        elif motion == key.MOTION_END_OF_FILE:
            self.position = len(self._text_view.document.text)
        elif motion == key.MOTION_NEXT_WORD:
            pos = self._position + 1
            m = self._next_word_re.search(self._text_view.document.text, pos)
            if not m:
                self.position = len(self._text_view.document.text)
            else:
                self.position = m.start()
        elif motion == key.MOTION_PREVIOUS_WORD:
            pos = self._position
            m = self._previous_word_re.search(self._text_view.document.text, 0, pos)
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
        if line is None:
            line = self._text_view.get_line_from_position(self._position)
        else:
            self._ideal_line = line
        x, y = self._text_view.get_point_from_position(self._position, line)
        if update_ideal_x:
            self._ideal_x = x

        x -= self._text_view.top_state.translate_x
        y -= self._text_view.top_state.translate_y
        font = self._text_view.document.get_font(max(0, self._position - 1))
        self._list.vertices[:] = [x, y + font.descent, x, y + font.ascent]

        if self._mark is not None:
            self._text_view.set_selection(min(self._position, self._mark),
                                          max(self._position, self._mark))

        self._text_view.ensure_line_visible(line)
        self._text_view.ensure_x_visible(x)


def main():
    from pyglet import clock
    from pyglet import font
    from pyglet import window
    from pyglet.window import key

    w = window.Window(vsync=False, resizable=True)
    w.set_mouse_cursor(w.get_system_mouse_cursor('text'))

    @w.event
    def on_text(t):
        t = t.replace('\r', '\n')
        caret.mark = None
        text.document.insert_text(caret.position, t)
        caret.position += len(t)
        cursor_not_idle()

    @w.event
    def on_text_motion(motion):
        if motion == key.MOTION_BACKSPACE:
            if caret.position > 0:
                text.document.remove_text(caret.position - 1, caret.position)
                caret.position -= 1
        elif motion == key.MOTION_DELETE:
            if caret.position < len(text.text):
                text.document.remove_text(caret.position, caret.position + 1)
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

    @w.event
    def on_mouse_scroll(x, y, scroll_x, scroll_y):
        text.view_x -= scroll_x
        text.view_y += scroll_y * (12 * 96 / 72) # scroll 12pt @ 96dpi

    def on_resize(width, height):
        text.x = border
        text.y = height - border
        text.width = width - border * 2
        text.height = height - border * 2
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

    if len(sys.argv) > 1:
        content = open(sys.argv[1]).read()
    else:
        content = 'Specify a text file for input as argv[1].'

    # Draw to this border so we can test clipping.
    border = 50

    batch = graphics.Batch()
    ft = font.load('Times New Roman', 12, dpi=96)
    document = UnformattedDocument(content, ft, (0, 0, 0, 255))
    text = TextView(document,  
                    w.width-border*2, w.height-border*2, batch=batch) 
    caret = Caret(text)
    caret.color = (0, 0, 0)
    caret.visible = True
    caret.position = 0
    cursor_idle(0)

    fps = clock.ClockDisplay(font=font.load('', 10, dpi=96), 
        color=(0, 0, 0, 1), interval=1., format='FPS: %(fps)d')
    fps.label.x = 2
    fps.label.y = 15
    stats_text = font.Text(font.load('', 10, dpi=96), '', 
        x=2, y=2, color=(0, 0, 0, 1))
   
    def update_stats(dt):
        states = batch.state_map.values()
        usage = 0.
        blocks = 0
        domains = 0

        fragmentation = 0.
        free_space = 0.
        capacity = 0.

        for state in states:
            for domain in state.values():
                domains += 1
                free_space += domain.allocator.get_free_size()
                fragmentation += domain.allocator.get_fragmented_free_size()
                capacity += domain.allocator.capacity
                blocks += len(domain.allocator.starts)
        fragmentation /= free_space
        free_space /= capacity
        usage = 1. - free_space
        stats_text.text = \
            'States: %d  Domains: %d  Blocks: %d  Usage: %d%%  Fragmentation: %d%%' % \
            (len(states), domains, blocks, usage * 100, fragmentation * 100)
    clock.schedule_interval(update_stats, 1) 

    glClearColor(1, 1, 1, 1)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
    while not w.has_exit:
        clock.tick()
        w.dispatch_events()
        w.clear()
        batch.draw()
        fps.draw()
        stats_text.draw()

        glPushAttrib(GL_CURRENT_BIT)
        glColor3f(0, 0, 0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRectf(border - 2, border - 2, 
                w.width - border + 4, w.height - border + 4)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glPopAttrib()

        w.flip()

if __name__ == '__main__':
    main()
