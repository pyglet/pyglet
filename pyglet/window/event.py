"""Events for :py:mod:`pyglet.window`.

See :py:class:`~pyglet.window.Window` for a description of the window event types.
"""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from pyglet.window import key, mouse

if TYPE_CHECKING:
    from io import StringIO


class WindowEventLogger:
    """Print all events to a file.

    When this event handler is added to a window it prints out all events
    and their parameters; useful for debugging or discovering which events
    you need to handle.

    Example::

        win = window.Window()
        event_logger = WindowEventLogger()
        win.push_handlers(event_logger)

    """

    def __init__(self, logfile: StringIO | None = None) -> None:
        """Create an event logger which writes to ``logfile``.

        Args:
            logfile:
                The file to write to.  If unspecified, stdout will be used.
        """
        if logfile is None:
            logfile = sys.stdout
        self.file = logfile

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        print(f'on_key_press(symbol={key.symbol_string(symbol)}, modifiers={key.modifiers_string(modifiers)})',
              file=self.file)

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        print(f'on_key_release(symbol={key.symbol_string(symbol)}, modifiers={key.modifiers_string(modifiers)})',
              file=self.file)

    def on_text(self, text: str) -> None:
        print(f'on_text(text={text!r})', file=self.file)

    def on_text_motion(self, motion: int) -> None:
        print(f'on_text_motion(motion={key.motion_string(motion)})', file=self.file)

    def on_text_motion_select(self, motion: int) -> None:
        print(f'on_text_motion_select(motion={key.motion_string(motion)})', file=self.file)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        print(f'on_mouse_motion(x={x}, y={y}, dx={dx}, dy={dy})', file=self.file)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> None:
        print(
            f'on_mouse_drag(x={x}, y={y}, dx={dx}, dy={dy}, buttons={mouse.buttons_string(buttons)}, modifiers='
            f'{key.modifiers_string(modifiers)})',
            file=self.file)

    def on_mouse_press(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        print(
            f'on_mouse_press(x={x}, y={y}, button={mouse.buttons_string(buttons)!r}, modifiers='
            f'{key.modifiers_string(modifiers)})',
            file=self.file)

    def on_mouse_release(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        print(
            f'on_mouse_release(x={x}, y={y}, button={mouse.buttons_string(buttons)!r}, modifiers='
            f'{key.modifiers_string(modifiers)})',
            file=self.file)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float) -> None:
        print(f'on_mouse_scroll(x={x}, y={y}, scroll_x={scroll_x}, scroll_y={scroll_y})', file=self.file)

    def on_close(self) -> None:
        print('on_close()', file=self.file)

    def on_mouse_enter(self, x: int, y: int) -> None:
        print('on_mouse_enter(x=%d, y=%d)' % (x, y), file=self.file)

    def on_mouse_leave(self, x: int, y: int) -> None:
        print('on_mouse_leave(x=%d, y=%d)' % (x, y), file=self.file)

    def on_expose(self) -> None:
        print('on_expose()', file=self.file)

    def on_resize(self, width: int, height: int) -> None:
        print(f'on_resize(width={width}, height={height})', file=self.file)

    def on_move(self, x: int, y: int) -> None:
        print(f'on_move(x={x}, y={y})', file=self.file)

    def on_activate(self) -> None:
        print('on_activate()', file=self.file)

    def on_deactivate(self) -> None:
        print('on_deactivate()', file=self.file)

    def on_show(self) -> None:
        print('on_show()', file=self.file)

    def on_hide(self) -> None:
        print('on_hide()', file=self.file)

    def on_context_lost(self) -> None:
        print('on_context_lost()', file=self.file)

    def on_context_state_lost(self) -> None:
        print('on_context_state_lost()', file=self.file)

    def on_draw(self) -> None:
        print('on_draw()', file=self.file)
