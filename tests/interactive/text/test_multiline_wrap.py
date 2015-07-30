import pytest
from tests.interactive.interactive_test_base import InteractiveTestCase

from pyglet import app
from pyglet import gl
from pyglet import graphics
from pyglet import text
from pyglet.text import caret
from pyglet.text import layout
from pyglet import window
from pyglet.window import key, mouse

nonewline_nowrap = """{font_size 24}Multiline=False\n
{font_size 12}This paragraph contains a lots of newlines however,\n
the parameter multiline=False makes pyglet {font_size 16}ignore{font_size 12} it.\n
For example this line should be not in a new line.\n
And because the parameter multiline=False (ignoring wrap_lines) the {font_size 16}long lines are not broken{font_size 12}, as you can see in this line."""

newline_nowrap = """{font_size 24}Multiline=True -- Wrap_line=False\n
{font_size 12}This paragraph contains a lots of newlines however,\n
the parameter multiline=True makes pyglet {font_size 16}accept{font_size 12} it.\n
For example this line should be in a new line.\n
And because the parameter wrap_lines=False the {font_size 16}long lines are not broken{font_size 12}, as you can see in this line."""

newline_wrap = """{font_size 24}Multiline=True -- Wrap_line=True\n
{font_size 12}This paragraph contains a lots of newlines however,\n
the parameter multiline=True makes pyglet {font_size 16}accept{font_size 12} it.\n
For example this line should be in a new line.\n
And because the parameter wrap_lines=True the {font_size 16}long lines are broken{font_size 12}, as you can see in this line."""


class TestWindow(window.Window):
    def __init__(self, multiline, wrap_lines, msg, *args, **kwargs):
        super(TestWindow, self).__init__(*args, **kwargs)

        self.batch = graphics.Batch()
        self.document = text.decode_attributed(msg)
        self.margin = 2
        self.layout = layout.IncrementalTextLayout(self.document,
            (self.width - self.margin * 2),
            self.height - self.margin * 2,
            multiline=multiline,
            wrap_lines=wrap_lines,
            batch=self.batch)
        self.caret = caret.Caret(self.layout)
        self.push_handlers(self.caret)

        self.wrap_lines = wrap_lines

        self.set_mouse_cursor(self.get_system_mouse_cursor('text'))

    def on_resize(self, width, height):
        super(TestWindow, self).on_resize(width, height)
        self.layout.begin_update()
        self.layout.x = self.margin
        self.layout.y = self.margin
        if self.wrap_lines:
           self.layout.width = width - self.margin * 2
        self.layout.height = height - self.margin * 2
        self.layout.end_update()

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


@pytest.mark.requires_user_action
class MultilineWrapTestCase(InteractiveTestCase):
    """Test that a paragraph is broken or not according the settings in an
    incremental layout.

    Three windows will be open (one per test) showing:
    - A paragraph in a single line, skipping newlines and no wrapping the line.
    - A paragraph in multiple lines, but the long lines will no be wrapped.
    - Last, a paragraph in multiple lines with wrapped lines.

    You can edit the text in each window and you must press ESC to close the window
    and continue with the next window until finish the test.

    Press ESC to exit the test.
    """

    def testMultilineFalse(self):
        self.window = TestWindow(
              multiline=False, wrap_lines=False,
              msg=nonewline_nowrap, resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Pass test?', take_screenshot=False)

    def testMultilineTrueNoLimited(self):
        self.window = TestWindow(
              multiline=True, wrap_lines=False,
              msg=newline_nowrap, resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Pass test?', take_screenshot=False)

    def testMultilineTrueLimited(self):
        self.window = TestWindow(
              multiline=True, wrap_lines=True,
              msg=newline_wrap, resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Pass test?', take_screenshot=False)

