#!/usr/bin/python
# $Id:$

from pyglet.text import layout, document

def attributed(text):
    from pyglet.text.formats import attributed
    return attributed.AttributedTextDecoder().decode(text)

def load_attributed(filename, file=None):
    if file is None:
        file = open(filename)
    return attributed(file.read())

class Label(layout.TextLayout):
    def __init__(self, text='', font=None, color=(255, 255, 255, 255), 
                 x=0, y=0, halign='left', valign='top', batch=None,
                 state_order=0):
        doc = document.UnformattedDocument(text)
        doc.set_style(0, 1, {'color': color})
        super(Label, self).__init__(doc, multiline=False, batch=batch,
                                    state_order=state_order)

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
        return self.document.color

    def _set_color(self, color):
        self.document.color = color
        self._update() # XXX

    color = property(_get_color, _set_color)

    def _get_font(self):
        return self.document.font

    def _set_font(self, font):
        self.document.font = font
        self._update() # XXX

    font = property(_get_font, _set_font)
