import pytest

from pyglet import gl
from pyglet import graphics
from pyglet.text import document
from pyglet.text import layout
from pyglet import window


@pytest.fixture(params=[document.UnformattedDocument, document.FormattedDocument])
def text_window(request):

    class _TestWindow(window.Window):
        def __init__(self, doctype, *args, **kwargs):
            super(_TestWindow, self).__init__(*args, **kwargs)

            self.batch = graphics.Batch()
            self.document = doctype()
            self.layout = layout.IncrementalTextLayout(
                self.document, 0, 0, 0, self.width, self.height, batch=self.batch)

        def on_draw(self):
            gl.glClearColor(1, 1, 1, 1)
            self.clear()
            self.batch.draw()

        def set_bold(self):
            self.document.set_style(0, len(self.document.text), {"bold": True})

    return _TestWindow(request.param)


def test_empty_document(text_window):
    """Empty text document can be rendered."""
    text_window.dispatch_events()
    text_window.close()


def test_empty_document_bold(text_window):
    """Empty text document can be rendered and attributes can be set."""
    text_window.set_bold()
    text_window.dispatch_events()
    text_window.close()
