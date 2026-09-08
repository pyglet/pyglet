import pytest

import pyglet
from tests.base.interactive import InteractiveTestCase

from pyglet import app
from pyglet import gl
from pyglet import graphics
from pyglet import text
from pyglet.text import caret
from pyglet.text import layout
from pyglet import window
from pyglet.window import key, mouse



class TestWindow(window.Window):
    def __init__(self, layout_text, anchor_x, anchor_y, formatted = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout_text = layout_text
        self.formatted = formatted

        self.batch = graphics.Batch()
        self.line = pyglet.shapes.Line(x=self.width // 2, y=0,
                                       x2=self.width // 2, y2=self.height, color=(255, 0, 0, 255), batch=self.batch)
        self.line2 = pyglet.shapes.Line(x=0, y=self.height // 2,
                                        x2=self.width, y2=self.height // 2, color=(255, 0, 0, 255),  batch=self.batch)
        if formatted:
            self.document = pyglet.text.document.FormattedDocument(layout_text)
            self._set_doc_format()
        else:
            self.document = text.decode_text(layout_text)
        self.margin = 2
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.layout = layout.TextLayout(self.document,
                                        x=0,
                                        anchor_x=anchor_x,
                                        anchor_y=anchor_y,
                                       width=300,
                                       height=500,
                                       multiline=True,
                                       batch=self.batch)

    def _set_doc_format(self):
        self.document.set_style(0, 20, {'color': (255, 0, 0, 255), 'font_size': 15})
        self.document.set_style(0, 3, {'italic': True})

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            self.layout.anchor_x = self.anchor_x
            self.layout.anchor_y = self.anchor_y
            self.document.text = self.layout_text + " (Spacebar Pressed)"
            if self.formatted:
                self._set_doc_format()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.layout.begin_update()
        self.layout.x = (self.width // 2)
        #self.layout.y = self.height // 2
        self.layout.end_update()

        self.line.x = self.width // 2
        self.line.x2 = self.width // 2
        self.line.y2 = self.height

        self.line2.y = self.height // 2
        self.line2.x2 = self.width
        self.line2.y2 = self.height // 2

    def on_draw(self):
        gl.glClearColor(1, 1, 1, 1)
        self.clear()
        self.batch.draw()


@pytest.mark.requires_user_action
class AnchorTestCase(InteractiveTestCase):
    def test_content_anchor_left(self):
        """test_content_anchor_left = 'left' property of TextLayout.

        Ensure that the text is anchored the way the text describes.

        Press ESC to exit the test.
        """
        desc = """This should be aligned against the left side of the Y axis red line. (Top right quadrant)

Press Spacebar to verify the position remains the same."""
        self.window = TestWindow(desc, anchor_x="left", anchor_y="bottom", resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

    def test_content_anchor_center(self):
        """test_content_anchor_center = 'center' property of TextLayout.

        Ensure that the text is anchored the way the text describes.

        Press ESC to exit the test.
        """
        desc = """This should be aligned on the Y axis red line.

Press Spacebar to verify the position remains the same."""

        self.window = TestWindow(desc, anchor_x="center", anchor_y="bottom", resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

    def test_content_anchor_right(self):
        """test_content_anchor_right = 'right' property of TextLayout.

        Ensure that the text is anchored the way the text describes.

        Press ESC to exit the test.
        """
        desc = """This should be aligned against the right side of the Y axis red line. (Top left quadrant)

Press Spacebar to verify the position remains the same."""

        self.window = TestWindow(desc, anchor_x="right", anchor_y="bottom", resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

    def test_content_anchor_left_formatted(self):
        """test_content_anchor_left = 'left' property of TextLayout.

        Ensure that the text is anchored the way the text describes.

        Press ESC to exit the test.
        """
        desc = """This should be aligned against the left side of the Y axis red line. (Top right quadrant)

Press Spacebar to verify the position remains the same."""
        self.window = TestWindow(desc, anchor_x="left", anchor_y="bottom", formatted=True,resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

    def test_content_anchor_center_formatted(self):
        """test_content_anchor_center = 'center' property of TextLayout.

        Ensure that the text is anchored the way the text describes.

        Press ESC to exit the test.
        """
        desc = """This should be aligned on the Y axis red line.

Press Spacebar to verify the position remains the same."""

        self.window = TestWindow(desc, anchor_x="center", anchor_y="bottom", formatted=True, resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

    def test_content_anchor_right_formatted(self):
        """test_content_anchor_right = 'right' property of TextLayout.

        Ensure that the text is anchored the way the text describes.

        Press ESC to exit the test.
        """
        desc = """This should be aligned against the right side of the Y axis red line. (Top left quadrant)

Press Spacebar to verify the position remains the same."""

        self.window = TestWindow(desc, anchor_x="right", anchor_y="bottom", formatted=True, resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

