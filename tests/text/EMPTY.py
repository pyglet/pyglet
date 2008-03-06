#!/usr/bin/env python

'''Test an unformatted document is editable.

Examine and type over the text in the window that appears.  The window
contents can be scrolled with the mouse wheel.

Press ESC to exit the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: STYLE.py 1754 2008-02-10 13:26:52Z Alex.Holkner $'

import unittest

from pyglet import app
from pyglet import gl
from pyglet import graphics
from pyglet.text import caret
from pyglet.text import document
from pyglet.text import layout
from pyglet import window
from pyglet.window import key, mouse

class TestWindow(window.Window):
    def __init__(self, doctype, *args, **kwargs):
        super(TestWindow, self).__init__(*args, **kwargs)

        self.batch = graphics.Batch()
        self.document = doctype()
        self.margin = 2
        self.layout = layout.IncrementalTextLayout(self.document,
            10, 10, # on_resize resolves this before layout happens
            multiline=True,
            batch=self.batch)
        self.caret = caret.Caret(self.layout)
        self.push_handlers(self.caret)

        self.set_mouse_cursor(self.get_system_mouse_cursor('text'))

    def on_resize(self, width, height):
        super(TestWindow, self).on_resize(width, height)
        self.layout.begin_update()
        self.layout.x = self.margin
        self.layout.y = self.margin
        self.layout.width = width - self.margin * 2
        self.layout.height = height - self.margin * 2
        self.layout.end_update()
        self.caret._update() # XXX

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.layout.view_x -= scroll_x
        self.layout.view_y += scroll_y * 16

    def on_draw(self):
        gl.glClearColor(1, 1, 1, 1)
        self.clear()
        self.batch.draw()

    def on_key_press(self, symbol, modifiers):
        super(TestWindow, self).on_key_press(symbol, modifiers)
        if symbol == key.TAB:
            self.caret.on_text('\t')

class TestCase(unittest.TestCase):
    def testUnformatted(self):
        self.window = TestWindow(document.UnformattedDocument,
            resizable=True, visible=False)
        self.window.set_visible()
        app.run()

    def testFormatted(self):
        self.window = TestWindow(document.FormattedDocument,
            resizable=True, visible=False)
        self.window.set_visible()
        app.run()

if __name__ == '__main__':
    unittest.main()
