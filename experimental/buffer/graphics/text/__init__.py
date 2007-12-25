#!/usr/bin/python
# $Id:$

from graphics.text import layout, document

class Label(layout.TextLayout):
    def __init__(self, text='', font=None, color=(255, 255, 255, 255), 
                 x=0, y=0, halign='left', valign='top', batch=None,
                 state_order=0):
        if font is None:
            from pyglet import font as font_module
            font = font_module.load('', 10)
        doc = document.UnformattedDocument(text, font, color)
        super(Label, self).__init__(doc, batch, state_order)

        self._x = 0
        self._y = 0
        self._halign = 'left'
        self._valign = 'top'
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
