"""Mouse constants and utilities for pyglet.window."""
from __future__ import annotations


class MouseStateHandler:
    """Simple handler that tracks the state of buttons and coordinates from the mouse.

    If a button is pressed then this handler holds a ``True`` value for it.
    If the window loses focus, all values will be reset to ``False`` in order
    to avoid a "sticky" state.

    For example::

        >>> win = window.Window()
        >>> mouse_state = mouse.MouseStateHandler()
        >>> win.push_handlers(mouse_state)

        # Hold down the "left" button...

        >>> mouse_state[mouse.LEFT]
        True
        >>> mouse_state[mouse.RIGHT]
        False


    Mouse coordinates can be retrieved by using the ``'x'`` and ``'y'`` strings.

    For example::

        >>> win = window.Window()
        >>> mouse_state = mouse.MouseStateHandler()
        >>> win.push_handlers(mouse_state)

        # Move the mouse around...

        >>> mouse_state['x']
        20
        >>> mouse_state['y']
        50
    """

    def __init__(self) -> None:  # noqa: D107
        self.data = {
            'x': 0,
            'y': 0,
        }

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:  # noqa: ARG002
        self.data[button] = True

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:  # noqa: ARG002
        self.data[button] = False

    def on_deactivate(self) -> None:
        self.data.clear()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:  # noqa: ARG002
        self.data['x'] = x
        self.data['y'] = y

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> None:  # noqa: ARG002
        self.data['x'] = x
        self.data['y'] = y

    def __getitem__(self, key: str) -> int | bool:
        return self.data.get(key, False)


def buttons_string(buttons: int) -> str:
    """Return a string describing a set of active mouse buttons.

    Example::

        >>> buttons_string(LEFT | RIGHT)
        'LEFT|RIGHT'

    Args:
        buttons:
            Bitwise combination of mouse button constants.
    """
    button_names = []
    if buttons & LEFT:
        button_names.append('LEFT')
    if buttons & MIDDLE:
        button_names.append('MIDDLE')
    if buttons & RIGHT:
        button_names.append('RIGHT')
    if buttons & MOUSE4:
        button_names.append('MOUSE4')
    if buttons & MOUSE5:
        button_names.append('MOUSE5')
    return '|'.join(button_names)


#: Constant for the left mouse button.
#:
#: :meta hide-value:
LEFT = 1 << 0
#: Constant for the middle mouse button.
#:
#: :meta hide-value:
MIDDLE = 1 << 1
#: Constant for the right mouse button.
#:
#: :meta hide-value:
RIGHT = 1 << 2
#: Constant for the mouse4 button.
#:
#: :meta hide-value:
MOUSE4 = 1 << 3
#: Constant for the mouse5 button.
#:
#: :meta hide-value:
MOUSE5 = 1 << 4
