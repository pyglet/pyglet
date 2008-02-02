#!/usr/bin/python
# $Id:$

import re

from pyglet import event
from pyglet.text import style

class Paragraph(object):
    def __init__(self):
        pass

    def clone(self):
        return Paragraph()

class AbstractDocument(event.EventDispatcher):
    def __init__(self, text):
        super(AbstractDocument, self).__init__()
        self._text = ''
        self.insert_text(0, text)

    def _get_text(self):
        return self._text

    def _set_text(self, text):
        self.delete_text(0, len(self._text))
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

    def delete_text(self, start, end):
        self._delete_text(start, end)
        self.dispatch_event('on_delete_text', start, end)

    def _delete_text(self, start, end):
        self._text = self._text[:start] + self._text[end:]

    def on_insert_text(self, start, text):
        '''
        :event:
        '''

    def on_delete_text(self, start, end):
        '''
        :event:
        '''

AbstractDocument.register_event_type('on_insert_text')
AbstractDocument.register_event_type('on_delete_text')

class UnformattedDocument(AbstractDocument):
    paragraph = Paragraph()
    
    def __init__(self, text, font, color):
        super(UnformattedDocument, self).__init__(text)
        self.font = font
        self.color = color

    def get_font_runs(self):
        return style.StyleRunsRangeIterator(((0, len(self.text), self.font),))

    def get_color_runs(self):
        return style.StyleRunsRangeIterator(((0, len(self.text), self.color),))

    def get_background_color_runs(self):
        return style.StyleRunsRangeIterator(((0, len(self.text), None),))

    def get_paragraph_runs(self):
        return style.StyleRunsRangeIterator(((0, len(self.text), self.paragraph),))

    def get_font(self, position=None):
        return self.font

class FormattedDocument(AbstractDocument):
    _paragraph_re = re.compile(r'\n', flags=re.DOTALL)

    def __init__(self, text, font, color):
        self._font_runs = style.StyleRuns(0, font)
        self._color_runs = style.StyleRuns(0, color)
        self._background_color_runs = style.StyleRuns(0, None)
        self._paragraph_runs = style.StyleRuns(0, Paragraph())
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

    def _delete_text(self, start, end):
        super(FormattedDocument, self)._delete_text(start, end)
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

