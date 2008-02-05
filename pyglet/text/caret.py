#!/usr/bin/python
# $Id:$

'''Provides keyboard and mouse editing procedures for text layout.

Example usage::

    from pyglet import window
    from pyglet.text import layout, caret

    my_window = window.Window(...)
    my_layout = layout.IncrementalTextLayout(...)
    my_caret = caret.Caret(my_layout)
    my_window.push_handlers(my_caret)

:since: pyglet 1.1
'''

import re
import time

from pyglet import clock
from pyglet.window import key

class Caret(object):
    '''Visible text insertion marker for 
    `pyglet.text.layout.IncrementalTextLayout`.

    The caret is drawn as a single vertical bar at the document `position` 
    on a text layout object.  If `mark` is not None, it gives the unmoving
    end of the current text selection.  The visible text selection on the
    layout is updated along with `mark` and `position`.
    
    By default the layout's graphics batch is used, so the caret does not need
    to be drawn explicitly.  Even if a different graphics batch is supplied,
    the caret will be correctly positioned and clipped within the layout.

    Updates to the document (and so the layout) are automatically propogated
    to the caret.  

    The caret object can be pushed onto a window event handler stack with
    `Window.push_handlers`.  The caret will respond correctly to keyboard,
    text, mouse and activation events, including double- and triple-clicks.
    If the text layout is being used alongside other graphical widgets, a
    GUI toolkit will be needed to delegate keyboard and mouse events to the
    appropriate widget.  pyglet does not provide such a toolkit at this stage.
    '''

    _next_word_re = re.compile(r'(?<=\W)\w')
    _previous_word_re = re.compile(r'(?<=\W)\w+\W*$')
    _next_para_re = re.compile(r'\n', flags=re.DOTALL)
    _previous_para_re = re.compile(r'\n', flags=re.DOTALL)

    _position = 0

    _active = True
    _visible = True
    _blink_visible = True
    _click_count = 0
    _click_time = 0

    #: Blink period, in seconds.
    PERIOD = 0.5
    
    def __init__(self, text_view, batch=None):
        from pyglet import gl
        self._text_view = text_view
        if batch is None:
            batch = text_view.batch
        self._list = batch.add(2, gl.GL_LINES, text_view.background_state, 
            'v2f', ('c4B', [0, 0, 0, 255] * 2))

        self._ideal_x = None
        self._ideal_line = None
        self._next_attributes = {}

        self.visible = True

    def _blink(self, dt):
        self._blink_visible = not self._blink_visible
        if self._visible and self._active and self._blink_visible:
            alpha = 255
        else:
            alpha = 0
        self._list.colors[3] = alpha
        self._list.colors[7] = alpha

    def _nudge(self):
        self.visible = True

    def _set_visible(self, visible):
        self._visible = visible
        clock.unschedule(self._blink)
        if visible and self._active and self.PERIOD:
            clock.schedule_interval(self._blink, self.PERIOD)
            self._blink_visible = False # flipped immediately by next blink
        self._blink(0)

    def _get_visible(self):
        return self._visible

    visible = property(_get_visible, _set_visible)
    
    def _set_color(self, color):
        self._list.colors[:3] = color
        self._list.colors[4:7] = color

    def _get_color(self):
        return self._list.colors[:3]

    color = property(_get_color, _set_color)

    def _set_position(self, index):
        self._position = index
        self._next_attributes.clear()
        self._update()

    def _get_position(self):
        return self._position

    position = property(_get_position, _set_position)

    _mark = None
    def _set_mark(self, mark):
        self._mark = mark
        self._update(line=self._ideal_line)
        if mark is None:
            self._text_view.set_selection(0, 0)
    
    def _get_mark(self):
        return self._mark

    mark = property(_get_mark, _set_mark)

    def _set_line(self, line):
        if self._ideal_x is None:
            self._ideal_x, _ = \
                self._text_view.get_point_from_position(self._position)
        self._position = \
            self._text_view.get_position_on_line(line, self._ideal_x)
        self._update(line=line, update_ideal_x=False)

    def _get_line(self):
        if self._ideal_line is not None:
            return self._ideal_line
        else:
            return self._text_view.get_line_from_position(self._position)

    line = property(_get_line, _set_line)

    def get_style(self, attribute):
        if self._mark is None or self._mark == self._position:
            try:
                return self._next_attributes[attribute]
            except KeyError:
                return self._text_view.document.get_style(attribute, 
                                                          self._position)

        start = min(self._position, self._mark)
        end = max(self._position, self._mark)
        return self._text_view.document.get_style_range(attribute, start, end)

    def set_style(self, attributes):
        if self._mark is None or self._mark == self._position:
            self._next_attributes.update(attributes)
            return

        start = min(self._position, self._mark)
        end = max(self._position, self._mark)
        self._text_view.document.set_style(start, end, attributes)

    def _delete_selection(self):
        self._text_view.document.delete_text(min(self._mark, self._position),
                                             max(self._mark, self._position))
        self._position = min(self.position, self.mark)
        self._mark = None
        self._text_view.set_selection(0, 0)

    def move_to_point(self, x, y):
        line = self._text_view.get_line_from_point(x, y)
        self._mark = None
        self._text_view.set_selection(0, 0)
        self._position = self._text_view.get_position_on_line(line, x)
        self._update(line=line)
        self._next_attributes.clear()

    def select_to_point(self, x, y):
        line = self._text_view.get_line_from_point(x, y)
        self._position = self._text_view.get_position_on_line(line, x)
        self._update(line=line)
        self._next_attributes.clear()

    def select_word(self, x, y):
        line = self._text_view.get_line_from_point(x, y)
        p = self._text_view.get_position_on_line(line, x)
        m1 = self._previous_word_re.search(self._text_view.document.text, 
                                           0, p+1)
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
        self._next_attributes.clear()

    def select_paragraph(self, x, y):
        line = self._text_view.get_line_from_point(x, y)
        p = self._text_view.get_position_on_line(line, x)
        self.mark = self._text_view.document.get_paragraph_start(p)
        self._position = self._text_view.document.get_paragraph_end(p)
        self._update(line=line) 
        self._next_attributes.clear()

    def _update(self, line=None, update_ideal_x=True):
        if line is None:
            line = self._text_view.get_line_from_position(self._position)
            self._ideal_line = None
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

    def on_text(self, text):
        if self._mark is not None:
            self._delete_selection()

        text = text.replace('\r', '\n')
        self._text_view.document.insert_text(self.position, text,
                                            self._next_attributes)
        self._position += len(text)
        self._nudge()
        self._update()

    def on_text_motion(self, motion, select=False):
        if motion == key.MOTION_BACKSPACE:
            if self.mark is not None:
                self._delete_selection()
                self._update()
            elif self.position > 0:
                self._text_view.document.delete_text(
                    self.position - 1, self.position)
                self.position -= 1
        elif motion == key.MOTION_DELETE:
            if self.mark is not None:
                self._delete_selection()
                self._update()
            elif self.position < len(self._text_view.document.text):
                self._text_view.document.delete_text(
                    self.position, self.position + 1)
                self._update()
        elif self._mark is not None and not select:
            self._mark = None
            self._text_view.set_selection(0, 0)

        if motion == key.MOTION_LEFT:
            self.position = max(0, self.position - 1)
        elif motion == key.MOTION_RIGHT:
            self.position = min(len(self._text_view.document.text), 
                                self.position + 1) 
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
                self._position = \
                    self._text_view.get_position_on_line(line + 1, 0) - 1
                self._update(line)
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
            m = self._previous_word_re.search(self._text_view.document.text, 
                                              0, pos)
            if not m:
                self.position = 0
            else:
                self.position = m.start()

        self._next_attributes.clear()
        self._nudge()

    def on_text_motion_select(self, motion):
        if self.mark is None:
            self.mark = self.position
        self.on_text_motion(motion, True)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        # scroll 12pt @ 96dpi
        self._text_view.view_x -= scroll_x * (12 * 96 / 72)
        self._text_view.view_y += scroll_y * (12 * 96 / 72) 

    def on_mouse_press(self, x, y, button, modifiers):
        t = time.time()
        if t - self._click_time < 0.25:
            self._click_count += 1
        else:
            self._click_count = 1
        self._click_time = time.time()

        if self._click_count == 1:
            self.move_to_point(x, y)
        elif self._click_count == 2:
            self.select_word(x, y)
        elif self._click_count == 3:
            self.select_paragraph(x, y)
            self._click_count = 0

        self._nudge()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.mark is None:
            self.mark = self.position
        self.select_to_point(x, y)
        self._nudge()

    def on_activate(self):
        self._active = True
        self.visible = self.visible

    def on_deactivate(self):
        self._active = False
        self.visible = self.visible
