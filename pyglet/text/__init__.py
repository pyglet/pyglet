#!/usr/bin/python
# $Id:$

import os.path

from pyglet.text import layout, document, caret

class DocumentDecodeException(Exception):
    '''An error occured decoding document text.'''
    pass

class DocumentDecoder(object):
    '''Abstract document decoder.
    '''

    def decode(self, text, path=None):
        '''Decode document text.
        
        :Parameters:
            `text` : str
                Text to decode
            `path` : str
                File system path to use as base path for additional resources
                referenced within the document (for example, HTML images).

        :rtype: `AbstractDocument`
        '''
        raise NotImplementedError('abstract')

def get_decoder(filename, mimetype=None):
    '''Get a document decoder for the given filename and MIME type.

    If `mimetype` is omitted it is guessed from the filename extension.

    The following MIME types are supported:

    ``text/plain``
        Plain text
    ``text/html``
        HTML 4 Transitional
    ``text/vnd.pyglet-attributed``
        Attributed text; see `pyglet.text.formats.attributed`

    `DocumendDecodeException` is raised if another MIME type is given.

    :Parameters:
        `filename` : str
            Filename to guess the MIME type from.  If a MIME type is given,
            the filename is ignored.
        `mimetype` : str
            MIME type to lookup, or ``None`` to guess the type from the
            filename.

    :rtype: `DocumentDecoder`
    '''
    if mimetype is None:
        _, ext = os.path.splitext(filename)
        if ext.lower() in ('.htm', '.html', '.xhtml'):
            mimetype = 'text/html'
        else:
            mimetype = 'text/plain'

    if mimetype == 'text/plain':
        from pyglet.text.formats import plaintext
        return plaintext.PlainTextDecoder()
    elif mimetype == 'text/html':
        from pyglet.text.formats import html
        return html.HTMLDecoder()
    elif mimetype == 'text/vnd.pyglet-attributed':
        from pyglet.text.formats import attributed
        return attributed.AttributedTextDecoder()
    else:
        raise DocumentDecodeException('Unknown format "%s"' % mimetype)
    
def load(filename, file=None, mimetype=None):
    '''Load a document from a file.

    :Parameters:
        `filename` : str
            Filename of document to load.
        `file` : file-like object
            File object containing encoded data.  If omitted, `filename` is
            loaded from disk.
        `mimetype` : str
            MIME type of the document.  If omitted, the filename extension is
            used to guess a MIME type.  See `get_decoder` for a list of
            supported MIME types.

    :rtype: `AbstractDocument`
    '''
    decoder = get_decoder(filename, mimetype)
    if file is None:
        file = open(filename)
    path = os.path.dirname(filename)
    return decoder.decode(file.read(), path)

def decode_html(text, path=None):
    '''Create a document directly from some HTML formatted text.

    :Parameters:
        `text` : str
            HTML data to decode.
        `path` : str
            Filename path giving the base path for additional resources
            referenced from the document (e.g., images).

    :rtype: `FormattedDocument`
    '''
    decoder = get_decoder(None, 'text/html')
    return decoder.decode(text, path)

def decode_attributed(text):
    '''Create a document directly from some attributed text.

    See `pyglet.text.formats.attributed` for a description of attributed text.

    :Parameters:
        `text` : str
            Attributed text to decode.

    :rtype: `FormattedDocument`
    '''
    decoder = get_decoder(None, 'text/vnd.pyglet-attributed')
    return decoder.decode(text)

def decode_text(text):
    '''Create a document directly from some plain text.

    :Parameters:
        `text` : str
            Plain text to initialise the document with.

    :rtype: `UnformattedDocument`
    '''
    decoder = get_decoder(None, 'text/plain')
    return decoder.decode(text)

class Label(layout.TextLayout):
    def __init__(self, text='', font=None, color=(255, 255, 255, 255), 
                 x=0, y=0, halign='left', valign='top', batch=None,
                 group=None):
        doc = document.UnformattedDocument(text)
        doc.set_style(0, 1, {'color': color})
        super(Label, self).__init__(doc, multiline=False, 
                                    batch=batch, group=group)

        self._x = x
        self._y = y
        self._halign = halign
        self._valign = valign
        self._update()

    def _get_text(self):
        return self.document.text

    def _set_text(self, text):
        self.document.text = text

    text = property(_get_text, _set_text)

    def _get_color(self):
        return self.document.get_style('color')

    def _set_color(self, color):
        # XXX passing in dummy start, end - didn't want to change the API
        self.document.set_style(0, 0, dict(color=color))
        self._update() # XXX

    color = property(_get_color, _set_color)

    def _get_font(self):
        return self.document.font

    def _set_font(self, font):
        self.document.font = font
        self._update() # XXX

    font = property(_get_font, _set_font)
