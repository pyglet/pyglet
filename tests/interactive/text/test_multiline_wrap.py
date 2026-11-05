from __future__ import annotations

import pytest

import pyglet
from pyglet import app, text, window
from pyglet.text import caret, layout
from pyglet.window import key
from tests.base.interactive import InteractiveTestCase

nonewline_nowrap = """{font_size 24}Multiline=False\n
{font_size 12}This paragraph contains a lots of newlines, however\n
the parameter multiline=False makes pyglet {font_size 16}ignore{font_size 12} it.\n
For example this line should not be in a new line.\n
And because the parameter multiline=False (ignoring wrap_lines) the {font_size 16}long lines are not broken{font_size 12}, as you can see in this line."""

newline_nowrap = """{font_size 24}Multiline=True -- Wrap_line=False\n
{font_size 12}This paragraph contains a lots of newlines, which\n
pyglet {font_size 16}accepts{font_size 12} due to the parameter multiline=True.\n
For example this line should be in a new line.\n
And, because the parameter wrap_lines=False, the {font_size 16}long lines are not broken{font_size 12}, as you can see in this line."""

newline_wrap = """{font_size 24}Multiline=True -- Wrap_line=True\n
{font_size 12}This paragraph contains a lots of newlines, which\n
pyglet {font_size 16}accepts{font_size 12} due to the parameter multiline=True.\n
For example this line should be in a new line.\n
And, because the parameter wrap_lines=True the {font_size 16}long lines are broken{font_size 12}, as you can see in this line."""


cjk_wrap = """{font_name ['Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC', 'Noto Sans CJK JP', 'Malgun Gothic']}{font_size 14}
Click between characters, move with arrow keys, and use Shift or mouse dragging to select.
Type, delete, and press Enter to check editing. Resize the window to change the wrapping.
Check the caret and selection at the end of each wrapped line. Scroll to see all samples.
Press ESC to finish.

{font_size 20}这是一个很长的中文句子它没有空格所以应该自动换行到下一行这是另一个没有空格的中文句子。

中文标点：「开头的括号应该跟着文字，结尾的标点应该留在前一行。」测试（括号）和句号。再检查逗号、问号？感叹号！

これは空白のない長い日本語の文章です。「括弧と句読点の位置」を確認しながらカーソルを動かしてください。ウィンドウの幅を変えて折り返しを確認してください。

한국어문장이공백없이계속이어져도줄바꿈이되어야합니다.커서를움직이고글자를입력하거나삭제하면서줄끝의위치를확인하세요.

pyglet是一个用于Python的跨平台窗口和多媒体库，可以用来开发游戏和其他视觉丰富的应用程序。Latin words should stay together with default wrapping.
"""


class BaseTestWindow(window.Window):
    def __init__(self, multiline, wrap_lines, msg, *args, **kwargs):
        super().__init__(*args, width=640, height=480, **kwargs)

        self.batch = pyglet.graphics.Batch()
        self.document = text.decode_attributed(msg)
        self.margin = 2
        self.layout = layout.IncrementalTextLayout(self.document,
                                                   width=(self.width - self.margin * 2),
                                                   height=self.height - self.margin * 2,
                                                   multiline=multiline,
                                                   wrap_lines=wrap_lines,
                                                   batch=self.batch)
        self.caret = caret.Caret(self.layout)
        self.push_handlers(self.caret)

        self.wrap_lines = wrap_lines

        self.set_mouse_cursor(self.get_system_mouse_cursor('text'))

        self.context.set_clear_color(1, 1, 1, 1)

    def on_resize(self, width, height):
        super().on_resize(width, height)
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
        self.clear()
        self.batch.draw()

    def on_key_press(self, symbol, modifiers):
        super().on_key_press(symbol, modifiers)
        if symbol == key.TAB:
            self.caret.on_text('\t')


@pytest.mark.requires_user_action
class MultilineWrapTestCase(InteractiveTestCase):
    """Test that a paragraph is broken or not according the settings in an
    incremental layout.

    Three windows will be open (one per test) showing:
    - A paragraph in a single line, ignoring newlines and not wrapping the line.
    - A paragraph in multiple lines, but the long lines will not be wrapped.
    - Last, a paragraph in multiple lines with wrapped lines.

    You can edit the text in each window, and you must press ESC to close the window
    and continue with the next window until finish the test.

    Press ESC to exit the test.
    """

    def testMultilineFalse(self):
        self.window = BaseTestWindow(
              multiline=False, wrap_lines=False,
              msg=nonewline_nowrap, resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Pass test?', take_screenshot=False)

    def testMultilineTrueNoLimited(self):
        self.window = BaseTestWindow(
              multiline=True, wrap_lines=False,
              msg=newline_nowrap, resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Pass test?', take_screenshot=False)

    def testMultilineTrueLimited(self):
        self.window = BaseTestWindow(
              multiline=True, wrap_lines=True,
              msg=newline_wrap, resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Pass test?', take_screenshot=False)

    def _test_cjk_wrap(self, wrap):
        self.window = BaseTestWindow(
            multiline=True, wrap_lines=True,
            msg=f"{{wrap {wrap!r}}}" + cjk_wrap, resizable=True, visible=False)
        self.window.set_caption(f"CJK wrapping and caret placement: wrap={wrap!r}")
        self.window.set_visible()
        app.run()
        self.user_verify('Did wrapping, caret placement, selection, and editing work correctly?', take_screenshot=False)

    def test_cjk_word_wrap(self):
        """Check CJK word wrapping and caret placement while editing and resizing.

        Closing punctuation should stay with the preceding text, and opening
        brackets should stay with the following text. Narrow Latin words should
        remain intact. Verify clicks, arrows, selection, typing, and deletion
        across wrapped line boundaries. Press ESC to finish.
        """
        self._test_cjk_wrap(True)

    def test_cjk_char_wrap(self):
        """Check CJK character wrapping and caret placement while editing and resizing.

        Characters may wrap individually, including Latin words and punctuation.
        Verify clicks, arrows, selection, typing, and deletion across wrapped
        line boundaries. Press ESC to finish.
        """
        self._test_cjk_wrap("char")

