
class Frame:
    """The base Frame object, implementing a 2D spatial hash.

    A `Frame` provides an efficient way to handle dispatching
    keyboard and mouse events to Widgets. This is done by
    implementing a 2D spatial hash. Only Widgets that are in the
    vicinity of the mouse pointer will be passed Window events,
    which can greatly improve efficiency when a large quantity
    of Widgets are in use.
    """

    def __init__(self, window, enable=True, cell_size=64, order=0):
        """Create an instance of a Frame.

        :Parameters:
            `window` : `~pyglet.window.Window`
                The SpatialHash will recieve events from this Window.
                Appropriate events will be passed on to all added Widgets.
            `enable`: bool
                Whether to enable frame.
            `cell_size` : int
                The cell ("bucket") size for each cell in the hash.
                Widgets may span multiple cells.
            `order` : int
                Widgets use internal OrderedGroups for draw sorting.
                This is the base value for these Groups.
        """
        self._window = window
        self._enable = enable
        self._cell_size = cell_size
        self._cells = {}
        self._active_widgets = set()
        self._order = order
        self._mouse_pos = 0, 0
        if self._enable:
            self._window.push_handlers(self)

    def _hash(self, x, y):
        """Normalize position to cell"""
        return int(x / self._cell_size), int(y / self._cell_size)

    def _on_reposition_handler(self, widget):
        self.remove_widget(widget)
        self.add_widget(widget)

    @property
    def enable(self):
        """Whether to enable frame.

        :type: bool
        """
        return self._enable

    @enable.setter
    def enable(self, value):
        self._enable = bool(value)
        if self._enable:
            self._window.push_handlers(self)
        else:
            self._window.remove_handlers(self)

    def add_widget(self, widget):
        """Add a Widget to the spatial hash."""
        min_vec, max_vec = self._hash(*widget.aabb[0:2]), self._hash(*widget.aabb[2:4])
        for i in range(min_vec[0], max_vec[0] + 1):
            for j in range(min_vec[1], max_vec[1] + 1):
                self._cells.setdefault((i, j), set()).add(widget)
        widget.update_groups(self._order)
        widget.set_handler("on_reposition", self._on_reposition_handler)

    def remove_widget(self, widget):
        """Remove a Widget."""
        for widgets in self._cells.values():
            if widget in widgets:
                widgets.remove(widget)

    def on_key_press(self, symbol, modifiers):
        """Pass the event to any widgets within range of the mouse"""
        for widget in self._cells.get(self._hash(*self._mouse_pos), set()):
            widget.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        """Pass the event to any widgets within range of the mouse"""
        for widget in self._cells.get(self._hash(*self._mouse_pos), set()):
            widget.on_key_release(symbol, modifiers)

    def on_mouse_press(self, x, y, buttons, modifiers):
        """Pass the event to any widgets within range of the mouse"""
        for widget in self._cells.get(self._hash(x, y), set()):
            widget.on_mouse_press(x, y, buttons, modifiers)
            self._active_widgets.add(widget)

    def on_mouse_release(self, x, y, buttons, modifiers):
        """Pass the event to any widgets that are currently active"""
        for widget in self._active_widgets:
            widget.on_mouse_release(x, y, buttons, modifiers)
        self._active_widgets.clear()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Pass the event to any widgets that are currently active"""
        for widget in self._active_widgets:
            widget.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
        self._mouse_pos = x, y

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Pass the event to any widgets within range of the mouse"""
        for widget in self._cells.get(self._hash(x, y), set()):
            widget.on_mouse_scroll(x, y, scroll_x, scroll_y)

    def on_mouse_motion(self, x, y, dx, dy):
        """Pass the event to any widgets within range of the mouse"""
        for cell in self._cells.values():
            for widget in cell:
                widget.on_mouse_motion(x, y, dx, dy)
        self._mouse_pos = x, y

    def on_text(self, text):
        """Pass the event to any widgets within range of the mouse"""
        for widget in self._cells.get(self._hash(*self._mouse_pos), set()):
            widget.on_text(text)

    def on_text_motion(self, motion):
        """Pass the event to any widgets within range of the mouse"""
        for widget in self._cells.get(self._hash(*self._mouse_pos), set()):
            widget.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        """Pass the event to any widgets within range of the mouse"""
        for widget in self._cells.get(self._hash(*self._mouse_pos), set()):
            widget.on_text_motion_select(motion)


class MovableFrame(Frame):
    """A Frame that allows Widget repositioning.

    When a specified modifier key is held down, Widgets can be
    repositioned by dragging them. Examples of modifier keys are
    Ctrl, Alt, Shift. These are defined in the `pyglet.window.key`
    module, and start witih `MOD_`. For example::

        from pyglet.window.key import MOD_CTRL

        frame = pyglet.gui.frame.MovableFrame(mywindow, modifier=MOD_CTRL)

    For more information, see the `pyglet.window.key` submodule
    API documentation.
    """

    def __init__(self, window, enable, order=0, modifier=0):
        super().__init__(window, enable=enable, order=order)
        self._modifier = modifier
        self._moving_widgets = set()

    def on_mouse_press(self, x, y, buttons, modifiers):
        if self._modifier & modifiers > 0:
            for widget in self._cells.get(self._hash(x, y), set()):
                if widget._check_hit(x, y):
                    self._moving_widgets.add(widget)
            for widget in self._moving_widgets:
                self.remove_widget(widget)
        else:
            super().on_mouse_press(x, y, buttons, modifiers)

    def on_mouse_release(self, x, y, buttons, modifiers):
        for widget in self._moving_widgets:
            self.add_widget(widget)
        self._moving_widgets.clear()
        super().on_mouse_release(x, y, buttons, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        for widget in self._moving_widgets:
            wx, wy = widget.position
            widget.position = wx + dx, wy + dy
        super().on_mouse_drag(x, y, dx, dy, buttons, modifiers)
