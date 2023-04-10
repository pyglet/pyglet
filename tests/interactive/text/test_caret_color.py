import pytest
from tests.base.interactive import InteractiveTestCase

from pyglet import app
from pyglet import gl
from pyglet import graphics
from pyglet import text
from pyglet.text import caret
from pyglet.text import layout
from pyglet import window
from pyglet.window import key, mouse


# old-style str.format for code brevity & lower line length
template = "Please observe whether the caret color matches {0}, then close the window."


class TestWindow(window.Window):
    def __init__(self, *args, caret_color=(0, 0, 0, 255), **kwargs):
        super(TestWindow, self).__init__(*args, **kwargs)

        self.batch = graphics.Batch()
        self.document = text.decode_text(
            template.format(caret_color)
        )

        self.margin = 2
        self.layout = layout.IncrementalTextLayout(self.document,
            self.width - self.margin * 2, self.height - self.margin * 2,
            multiline=True,
            batch=self.batch)
        self.caret = caret.Caret(self.layout, color=caret_color)
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


class _DRYHelperMixin:

    def build_window(self, color=(0, 0, 0, 255)):
        self.window = TestWindow(caret_color=color, resizable=False, visible=False)
        self.window.set_visible()

    def ask_color(self, color):
        self.user_verify(f"Was the caret color {color}?", take_screenshot=False)


@pytest.mark.requires_user_action
class CaretColorInitTestCase(InteractiveTestCase, _DRYHelperMixin):
    """Test if the text area Caret color was set correctly by init

    Examine & remember the color of the caret, and type Y + enter if the
    caret color matched the numbers in the label.

    Press ESC to exit the test.
    """

    def test_caret_color_init_rgb(self):
        color = (255, 0, 0)
        self.build_window(color)
        app.run()
        self.ask_color(color)

    def test_caret_color_init_rgba(self):
        # 80 seems to be an ok balance between visibility and
        # ease of telling apart from alpha == 255.
        color = (255, 0, 0, 80)
        self.build_window(color)
        app.run()
        self.ask_color(color)

