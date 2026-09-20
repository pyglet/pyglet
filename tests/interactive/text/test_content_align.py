from __future__ import annotations

import pytest

import pyglet
from pyglet import app, text, window
from pyglet.text import caret, layout
from pyglet.window import key
from tests.base.interactive import InteractiveTestCase

class TestWindow(window.Window):
    def __init__(self, content_valign='top', content_halign='left', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.batch = pyglet.graphics.Batch()
        self.document = text.decode_text(
            f"This text should be aligned to the {content_halign} and {content_valign}.\n"
            "Resize the window to verify it stays anchored,\n"
            "ythen close the window when done."
        )
        self.margin = 2
        self.layout = layout.IncrementalTextLayout(self.document,
                                                   width=self.width - self.margin * 2,
                                                   height=self.height - self.margin * 2,
                                                   multiline=True,
                                                   batch=self.batch)
        self.layout.content_valign = content_valign
        self.layout.content_halign = content_halign
        self.caret = caret.Caret(self.layout)
        self.push_handlers(self.caret)

        self.set_mouse_cursor(self.get_system_mouse_cursor('text'))

        self.context.set_clear_color(1, 1, 1, 1)

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.layout.begin_update()
        self.layout.x = self.margin
        self.layout.y = self.margin
        self.layout.width = width - self.margin * 2
        self.layout.height = height - self.margin * 2
        self.layout.end_update()

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.layout.view_x -= scroll_x
        self.layout.view_y += scroll_y * 16

    def on_draw(self):
        self.clear()
        self.batch.draw()

    def on_key_press(self, symbol, modifiers):
        super().on_key_press(symbol, modifiers)
        if symbol == key.TAB:
            self.caret.on_text('\t')

@pytest.mark.requires_user_action
class ContentAlignTestCase(InteractiveTestCase):
    def test_content_valign_top(self):
        """Test content_valign = 'top' property of IncrementalTextLayout.

        Examine and type over the text in the window that appears.  The window
        contents can be scrolled with the mouse wheel.  When the content height
        is less than the window height, the content should be aligned to the bottom
        of the window.

        Resize the window and verify the text stays anchored to the bottom.
        Close the window when you are done.
        """
        self.window = TestWindow(resizable=True, visible=False, content_valign='topy')
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

    def test_content_valign_bottom(self):
        """Test content_valign = 'bottom' property of IncrementalTextLayout.

        Examine and type over the text in the window that appears.  The window
        contents can be scrolled with the mouse wheel.  When the content height
        is less than the window height, the content should be aligned to the bottom
        of the window.

        Resize the window and verify the text stays anchored to the bottom.
        Close the window when you are done.
        """
        self.window = TestWindow(resizable=True, visible=False, content_valign='bottom')
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

    def test_content_valign_center(self):
        """Test content_valign = 'center' property of IncrementalTextLayout.

        Examine and type over the text in the window that appears.  The window
        contents can be scrolled with the mouse wheel.  When the content height
        is less than the window height, the content should be aligned to the center
        of the window.

        Resize the window and verify the text stays anchored to the center.
        Close the window when you are done.
        """
        self.window = TestWindow(resizable=True, visible=False, content_valign='center')
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

    def test_content_align_center_top(self):
        """Test content_halign = 'center' and content_valign = 'top'.

        Examine the text in the window that appears, then resize the window and
        verify it stays anchored to the center and top.  Close the window when
        you are done.

        """
        self.window = TestWindow(resizable=True, visible=False,
                                 content_halign='center', content_valign='top')
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

    def test_content_align_right_center(self):
        """Test content_halign = 'right' and content_valign = 'center'.

        Examine and type over the text in the window that appears.  The window
        contents can be scrolled with the mouse wheel.  The text says where it
        should be aligned.

        Resize the window and verify the text stays anchored to the right and
        center.
        Close the window when you are done.
        """
        self.window = TestWindow(resizable=True, visible=False,
                                 content_halign='right', content_valign='center')
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

    def test_content_align_right_bottom(self):
        """Test content_halign = 'right' and content_valign = 'bottom'.

        Examine and type over the text in the window that appears.  The window
        contents can be scrolled with the mouse wheel.  The text says where it
        should be aligned.

        Resize the window and verify the text stays anchored to the right and
        bottom.
        Close the window when you are done.
        """
        self.window = TestWindow(resizable=True, visible=False,
                                 content_halign='right', content_valign='bottom')
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

