#!/usr/bin/env python

'''Test that an empty document doesn't break.
'''

__docformat__ = 'restructuredtext'

__noninteractive = True

import unittest

from pyglet import gl
from pyglet import graphics
from pyglet.text import document
from pyglet.text import layout
from pyglet import window

class TestWindow(window.Window):
    def __init__(self, doctype, *args, **kwargs):
        super(TestWindow, self).__init__(*args, **kwargs)

        self.batch = graphics.Batch()
        self.document = doctype()
        self.layout = layout.IncrementalTextLayout(self.document,
            self.width, self.height, batch=self.batch)

    def on_draw(self):
        gl.glClearColor(1, 1, 1, 1)
        self.clear()
        self.batch.draw()

class TestCase(unittest.TestCase):
    def testUnformatted(self):
        self.window = TestWindow(document.UnformattedDocument)
        self.window.dispatch_events()
        self.window.close()

    def testFormatted(self):
        self.window = TestWindow(document.FormattedDocument)
        self.window.dispatch_events()
        self.window.close()

if __name__ == '__main__':
    unittest.main()
