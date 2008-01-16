#!/usr/bin/python
# $Id:$

import re

from pyglet.gl import *

class Caret(object):
    _next_word_re = re.compile(r'(?<=\W)\w')
    _previous_word_re = re.compile(r'(?<=\W)\w+\W*$')
    _next_para_re = re.compile(r'\n', flags=re.DOTALL)
    _previous_para_re = re.compile(r'\n', flags=re.DOTALL)
    
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

    def _delete_selection(self):
        self._text_view.document.remove_text(min(self._mark, self._position),
                                             max(self._mark, self._position))
        self._position = min(self.position, self.mark)
        self._mark = None
        self._text_view.set_selection(0, 0)

    def on_text(self, text):
        if self._mark is not None:
            self._delete_selection()

        text = text.replace('\r', '\n')
        self._text_view.document.insert_text(self.position, text)
        self.position += len(text)

    def on_text_motion(self, motion, select=False):
        from pyglet.window import key

        if motion == key.MOTION_BACKSPACE:
            if self.mark is not None:
                self._delete_selection()
                self._update()
            elif self.position > 0:
                self._text_view.document.remove_text(
                    self.position - 1, self.position)
                self.position -= 1
        elif motion == key.MOTION_DELETE:
            if self.mark is not None:
                self._delete_selection()
                self._update()
            elif self.position < len(self._text_view.document.text):
                self._text_view.document.remove_text(
                    self.position, self.position + 1)
                self._update()
        elif self._mark is not None and not select:
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
            self.position = self._text_view.get_position_from_line(self.line)
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


    def on_text_motion_select(self, motion):
        if self.mark is None:
            self.mark = self.position
        self.on_text_motion(motion, True)

    def move_to_point(self, x, y):
        line = self._text_view.get_line_from_point(x, y)
        self._mark = None
        self._position = self._text_view.get_position_on_line(line, x)
        self._update(line=line)

    def select_to_point(self, x, y):
        line = self._text_view.get_line_from_point(x, y)
        self._position = self._text_view.get_position_on_line(line, x)
        self._update(line=line)

    def select_word(self, x, y):
        line = self._text_view.get_line_from_point(x, y)
        p = self._text_view.get_position_on_line(line, x)
        m1 = self._previous_word_re.search(self._text_view.document.text, 0, p)
        if not m1:
            m1 = 0
        else:
            m1 = m1.start()
        self.mark = m1

        m2 = self._next_word_re.search(self._text_view.document.text, p)
        if not m2:
            m2 = len(self._text_view.document.text)
        else:
            m2 = m2.start()
        self._position = m2
        self._update(line=line)

    def select_paragraph(self, x, y):
        line = self._text_view.get_line_from_point(x, y)
        p = self._text_view.get_position_on_line(line, x)
        m1 = self._previous_para_re.search(self._text_view.document.text, 0, p)
        if not m1:
            m1 = 0
        else:
            m1 = m1.start()
        self.mark = m1

        m2 = self._next_para_re.search(self._text_view.document.text, p)
        if not m2:
            m2 = len(self._text_view.document.text)
        else:
            m2 = m2.start()
        self._position = m2
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


