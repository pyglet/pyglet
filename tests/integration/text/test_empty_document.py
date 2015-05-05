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

    def set_bold(self):
        self.document.set_style(0, len(self.document.text), {"bold": True})


class EmptyDocumentTest(unittest.TestCase):
    """Test that an empty document doesn't break."""
    def test_unformatted(self):
        self.window = TestWindow(document.UnformattedDocument)
        self.window.dispatch_events()
        self.window.close()

    def test_formatted(self):
        self.window = TestWindow(document.FormattedDocument)
        self.window.dispatch_events()
        self.window.close()

    def test_bold_unformatted(self):
        self.window = TestWindow(document.UnformattedDocument)
        self.window.set_bold()
        self.window.dispatch_events()
        self.window.close()

    def test_bold_formatted(self):
        self.window = TestWindow(document.FormattedDocument)
        self.window.set_bold()
        self.window.dispatch_events()
        self.window.close()

