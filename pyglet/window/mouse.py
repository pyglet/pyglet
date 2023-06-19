"""Mouse constants and utilities for pyglet.window.
"""


class MouseStateHandler:
    """Simple handler that tracks the state of buttons from the mouse. If a
    button is pressed then this handler holds a True value for it.
    If the window loses focus, all buttons will be reset to False in order
    to avoid a "sticky" button state.

    For example::

        >>> win = window.Window()
        >>> mousebuttons = mouse.MouseStateHandler()
        >>> win.push_handlers(mousebuttons)

        # Hold down the "left" button...

        >>> mousebuttons[mouse.LEFT]
        True
        >>> mousebuttons[mouse.RIGHT]
        False

    """

    def __init__(self):
        self.data = {
            "x": 0,
            "y": 0,
        }

    def on_mouse_press(self, x, y, button, modifiers):
        self.data[button] = True

    def on_mouse_release(self, x, y, button, modifiers):
        self.data[button] = False

    def on_deactivate(self):
        self.data.clear()

    def on_mouse_motion(self, x, y, dx, dy):
        self.data["x"] = x
        self.data["y"] = y

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.data["x"] = x
        self.data["y"] = y

    def __getitem__(self, key):
        return self.data.get(key, False)


def buttons_string(buttons):
    """Return a string describing a set of active mouse buttons.

    Example::

        >>> buttons_string(LEFT | RIGHT)
        'LEFT|RIGHT'

    :Parameters:
        `buttons` : int
            Bitwise combination of mouse button constants.

    :rtype: str
    """
    button_names = []
    if buttons & LEFT:
        button_names.append("LEFT")
    if buttons & MIDDLE:
        button_names.append("MIDDLE")
    if buttons & RIGHT:
        button_names.append("RIGHT")
    if buttons & MOUSE4:
        button_names.append("MOUSE4")
    if buttons & MOUSE5:
        button_names.append("MOUSE5")
    return "|".join(button_names)


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
