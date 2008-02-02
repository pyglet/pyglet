#!/usr/bin/python
# $Id:$

'''Formatted and unformatted document interfaces used by text layout.

TODO overview

Style attributes
================

The following style attribute names are recognised by pyglet:

``font_name``
    Font family name, as given to `pyglet.font.load`.
``font_size``
    Font size, in points.
``bold``
    Boolean.
``italic``
    Boolean.
``color``
    4-tuple of ints in range (0, 255) giving RGBA text color
``background_color``
    4-tuple of ints in range (0, 255) giving RGBA text background color; or
    ``None`` for no background fill.

Other attributes can be used to store additional style information within the
document; it will be ignored by the built-in text classes.

All style attributes (including those not present in a document) default to
``None`` (including the so-called "boolean" styles listed above).  The meaning
of a ``None`` style is style- and application-dependent. 

:since: pyglet 1.1
'''

import re
import sys

from pyglet import event
from pyglet.text import style

_is_epydoc = hasattr(sys, 'is_epydoc') and sys.is_epydoc

class Paragraph(object):
    '''Paragraph style.
    
    '''
    def __init__(self):
        pass

    def clone(self):
        return Paragraph()

class AbstractDocument(event.EventDispatcher):
    '''Abstract document interface used by all `pyglet.text` classes.

    This class can be overridden to interface pyglet with a third-party
    document format.  It may be easier to implement the document format in
    terms of one of the supplied concrete classes `FormattedDocument` or
    `UnformattedDocument`. 
    '''
    def __init__(self, text=''):
        super(AbstractDocument, self).__init__()
        self._text = ''
        if text:
            self.insert_text(0, text)

    def _get_text(self):
        return self._text

    def _set_text(self, text):
        self.delete_text(0, len(self._text))
        self.insert_text(0, text)
    
    text = property(_get_text, _set_text, 
                    doc='''Document text.
                   
        For efficient incremental updates, use the `insert_text` and
        `delete_text` methods instead of replacing this property.
        
        :type: str
        ''')

    def get_paragraph_runs(self):
        '''Get a style iterator over the `Paragraph` instances of the
        document.

        :rtype: `StyleRunsRangeIterator`
        '''
        raise NotImplementedError('abstract')

    def get_paragraph(self, position):
        '''Get the paragraph style at the given position.

        :Parameters:
            `position` : int
                Character position of document to query.
            
        :rtype: `Paragraph`
        '''
        raise NotImplementedError('abstract')

    def get_style_runs(self, attribute):
        '''Get a style iterator over the given style attribute.

        :Parameters:
            `attribute` : str
                Name of style attribute to query.

        :rtype: `StyleRunsRangeIterator`
        '''
        raise NotImplementedError('abstract')

    def get_style(self, attribute, position):
        '''Get an attribute style at the given position.

        :Parameters:
            `attribute` : str
                Name of style attribute to query.
            `position` : int
                Character position of document to query.

        :return: The style set for the attribute at the given position.
        '''
        raise NotImplementedError('abstract')

    def get_style_range(self, attribute, start, end):
        '''Get an attribute style over the given range.

        If the style varies over the range, `style.INDETERMINATE` is returned.

        :Parameters:
            `attribute` : str
                Name of style attribute to query.
            `start` : int
                Starting character position.
            `end` : int
                Ending character position (exclusive).

        :return: The style set for the attribute over the given range, or
            `style.INDETERMINATE` if more than one value is set.
        '''
        iter = self.get_style_runs(attribute)
        _, value_end, value = iter.iter_range(start, end).next()
        if value_end < end:
            return style.INDETERMINATE
        else:
            return value

    def get_font_runs(self, dpi=None):
        '''Get a style iterator over the `pyglet.font.Font` instances used in
        the document.

        The font instances are created on-demand by inspection of the
        ``font_name``, ``font_size``, ``bold`` and ``italic`` style
        attributes.

        :Parameters:
            `dpi` : float
                Optional resolution to construct fonts at.  See
                `pyglet.font.load`.

        :rtype: `StyleRunsRangeIterator`
        '''
        raise NotImplementedError('abstract')

    def get_font(self, position, dpi=None):
        '''Get the font instance used at the given position.

        :see: `get_font_runs`

        :Parameters:
            `position` : int
                Character position of document to query.
            `dpi` : float
                Optional resolution to construct fonts at.  See
                `pyglet.font.load`.

        :rtype: `pyglet.font.Font`
        '''
        raise NotImplementedError('abstract')
    
    def insert_text(self, start, text, attributes=None):
        '''Insert text into the document.

        :Parameters:
            `start` : int
                Character insertion point within document.
            `text` : str
                Text to insert.
            `attributes` : dict
                Optional dictionary giving named style attributes of the
                inserted text.

        '''
        self._insert_text(start, text, attributes)
        self.dispatch_event('on_insert_text', start, text)

    def _insert_text(self, start, text, attributes):
        self._text = ''.join((self._text[:start], text, self._text[start:]))

    def delete_text(self, start, end):
        '''Delete text from the document.

        :Parameters:
            `start` : int
                Starting character position to delete from.
            `end` : int
                Ending character position to delete to (exclusive).

        '''
        self._delete_text(start, end)
        self.dispatch_event('on_delete_text', start, end)

    def _delete_text(self, start, end):
        self._text = self._text[:start] + self._text[end:]

    def set_style(self, start, end, attributes):
        '''Set text style of some or all of the document.

        :Parameters:
            `start` : int
                Starting character position.
            `end` : int
                Ending character position (exclusive).
            `attributes` : dict
                Dictionary giving named style attributes of the text.

        '''
        self._set_style(start, end, attributes)
        self.dispatch_event('on_style_text', start, end, attributes)

    def _set_style(self, start, end, attributes):
        raise NotImplementedError('abstract')

    if _is_epydoc:
        def on_insert_text(start, text):
            '''Text was inserted into the document.

            :Parameters:
                `start` : int
                    Character insertion point within document.
                `text` : str
                    The text that was inserted.

            :event:
            '''

        def on_delete_text(start, end):
            '''Text was deleted from the document.

            :Parameters:
                `start` : int
                    Starting character position of deleted text.
                `end` : int
                    Ending character position of deleted text (exclusive).

            :event:
            '''

        def on_style_text(start, end, attributes):
            '''Text style was modified.

            :Parameters:
                `start` : int
                    Starting character position of modified text.
                `end` : int
                    Ending character position of modified text (exclusive).
                `attributes` : dict
                    Dictionary giving updated named style attributes of the
                    text.

            '''

AbstractDocument.register_event_type('on_insert_text')
AbstractDocument.register_event_type('on_delete_text')
AbstractDocument.register_event_type('on_style_text')

class UnformattedDocument(AbstractDocument):
    '''A document having uniform character and paragraph style over all text.

    Changes to the style of any paragraph or text within the document affects
    the entire document.  For convenience, the `position` parameters of the
    style methods may therefore be omitted.
    '''

    def __init__(self, text=''):
        super(UnformattedDocument, self).__init__(text)
        self.paragraph = Paragraph()
        self.styles = {}

    def get_paragraph_runs(self):
        return style.StyleRunsRangeIterator(
            ((0, len(self.text), self.paragraph),))

    def get_paragraph(self, position=None):
        return self.paragraph

    def get_style_runs(self, attribute):
        value = self.styles.get(attribute)
        return style.StyleRunsRangeIterator(((0, len(self.text), value),))

    def get_style(self, attribute, position=None):
        return self.styles.get(attribute)

    def set_style(self, start, end, attributes):
        return super(UnformattedDocument, self).set_style(
            0, len(self.text), attributes)

    def _set_style(self, start, end, attributes):
        for attribute, value in attributes.items():
            self.styles[attribute] = value

    def get_font_runs(self, dpi=None):
        ft = self.get_font(dpi=dpi)
        return style.StyleRunsRangeIterator(((0, len(self.text), ft),))

    def get_font(self, position=None, dpi=None):
        from pyglet import font
        font_name = self.styles.get('font_name')
        font_size = self.styles.get('font_size')
        bold = self.styles.get('bold', False)
        italic = self.styles.get('italic', False)
        return font.load(font_name, font_size, 
                         bold=bold, italic=italic, dpi=dpi) 

class FormattedDocument(AbstractDocument):
    '''Simple implementation of a document that maintains text formatting.

    Changes to text and paragraph style are applied according to the
    description in `AbstractDocument`.  All styles default to ``None``.
    '''

    _paragraph_re = re.compile(r'\n', flags=re.DOTALL)

    def __init__(self, text=''):
        self._paragraph_runs = style.StyleRuns(0, Paragraph())
        self._style_runs = {}
        self._font_runs = style.StyleRuns(0, None)
        super(FormattedDocument, self).__init__(text)

    def get_paragraph_runs(self):
        return self._paragraph_runs.get_range_iterator()

    def get_paragraph(self, position):
        return self._paragraph_runs.get_style_at(position)

    def get_style_runs(self, attribute):
        try:
            return self._style_runs[attribute].get_range_iterator()
        except KeyError:
            return _no_style_range_iterator

    def get_style(self, attribute, position):
        try:
            return self._style_runs[attribute].get_style_at(position)
        except KeyError:
            return None

    def _set_style(self, start, end, attributes):
        for attribute, value in attributes.items():
            try:
                runs = self._style_runs[attribute]
            except KeyError:
                runs = self._style_runs[attribute] = style.StyleRuns(0, None)
                runs.insert(0, len(self._text))
            runs.set_style(start, end, value)

    def get_font_runs(self, dpi=None):
        return _FontStyleRunsRangeIterator(self.get_style_runs('font_name'),
                                           self.get_style_runs('font_size'),
                                           self.get_style_runs('bold'),
                                           self.get_style_runs('italic'),
                                           dpi)

    def get_font(self, position, dpi=None):
        iter = self.get_font_runs(dpi)
        return iter.get_style_at(position)

    def _insert_text(self, start, text, attributes):
        super(FormattedDocument, self)._insert_text(start, text, attributes)

        len_text = len(text)
        self._paragraph_runs.insert(start, len_text)
        for runs in self._style_runs.values():
            runs.insert(start, len_text)

        if attributes is not None:
            for attribute, value in attributes.items():
                try:
                    runs = self._style_runs[attribute]
                except KeyError:
                    runs = self._style_runs[attribute] = \
                        style.StyleRuns(0, None)
                runs.set_style(start, start + len_text, value)

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
        self._paragraph_runs.delete(start, end)
        for runs in self._style_runs.values():
            runs.delete(start, end)

class _FontStyleRunsRangeIterator(object):
    def __init__(self, font_names, font_sizes, bolds, italics, dpi):
        self.zip_iter = style.ZipStyleRunsRangeIterator(
            (font_names, font_sizes, bolds, italics))
        self.dpi = dpi

    def iter_range(self, start, end):
        from pyglet import font
        for start, end, styles in self.zip_iter.iter_range(start, end):
            font_name, font_size, bold, italic = styles
            ft = font.load(font_name, font_size, 
                           bold=bold, italic=italic, dpi=self.dpi)
            yield start, end, ft

    def get_style_at(self, index):
        from pyglet import font
        font_name, font_size, bold, italic = self.zip_iter.get_style_at(index)
        return font.load(font_name, font_size,
                         bold=bold, italic=italic, dpi=self.dpi)

class _NoStyleRangeIterator(object):
    def iter_range(self, start, end):
        yield start, end, None

    def get_style_at(self, index):
        return None
_no_style_range_iterator = _NoStyleRangeIterator()
