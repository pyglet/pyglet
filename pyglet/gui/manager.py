"""WIP."""
from __future__ import annotations

from enum import Flag, auto
from typing import TYPE_CHECKING

import pyglet

from pyglet.gui.layout import Frame, Layout, MovableFrame
from pyglet.gui.widgets import WidgetBase

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pyglet.window import BaseWindow, MouseCursor


class UIDirtyFlag(Flag):
    """Dirty flag to defer UI changes managed by :class:`UIManager`."""

    NONE = 0
    LAYOUT = auto()


class UIManager:
    """Own a window's GUI input, focus, and widget registration.

    A UI manager is the single event handler for a window's GUI.  It uses a
    spatial hash to dispatch pointer events efficiently, and owns keyboard
    focus and mouse capture. Construct widgets, frames, and layouts with this
    manager as their parent to register them automatically.
    """

    def __init__(self, window: BaseWindow, enable: bool = True, cell_size: int = 64, order: int = 0,
                 cursor: str | MouseCursor | None = None) -> None:
        """Create a UI manager for ``window``.

        Args:
            window:
                The SpatialHash will receive events from this Window.
                Appropriate events will be passed on to all added Widgets.
            enable:
                Whether to enable this manager.
            cell_size:
                The cell ("bucket") size for each cell in the hash.
                Widgets may span multiple cells.
            order:
                Widgets use internal ordered Groups for draw sorting.
                This is the base value for these Groups.
            cursor:
                System cursor name or custom mouse cursor to show when no widget
                supplies one.
        """
        self._window = window
        self._enable = enable
        self._cell_size = cell_size
        self._cells: dict[tuple[int, int], set[WidgetBase]] = {}
        self._widgets: set[WidgetBase] = set()
        self._frames: set[Frame] = set()
        self._widget_cells: dict[WidgetBase, set[tuple[int, int]]] = {}
        self._active_widgets: set[WidgetBase] = set()
        self._moving_frames: set[MovableFrame] = set()
        self._focused_widget: WidgetBase | None = None
        self._order = order
        self.cursor = cursor
        self._mouse_pos = 0, 0
        self._resizing = False
        self._dirty_flags = UIDirtyFlag.NONE
        self._dirty_layouts: set[Layout] = set()
        self._dirty_scheduled = False
        self._dirty_callback = self._process_dirty
        if self._enable:
            self._window.push_handlers(self)
            self._schedule_dirty_processing()

    def _schedule_dirty_processing(self) -> None:
        if self._enable and not self._dirty_scheduled:
            pyglet.clock.schedule_interval(self._dirty_callback, 1 / 60)
            self._dirty_scheduled = True

    def _stop_dirty_processing(self) -> None:
        if self._dirty_scheduled:
            pyglet.clock.unschedule(self._dirty_callback)
            self._dirty_scheduled = False

    def _invalidate_layout(self, layout: Layout) -> None:
        """Mark a layout for calculation on the next UI update."""
        self._dirty_flags |= UIDirtyFlag.LAYOUT
        self._dirty_layouts.add(layout)

    def _clear_dirty_layout(self, layout: Layout) -> None:
        """Remove a layout that was calculated explicitly."""
        self._dirty_layouts.discard(layout)
        if not self._dirty_layouts:
            self._dirty_flags &= ~UIDirtyFlag.LAYOUT

    def _process_dirty(self, dt: float = 0.0) -> None:
        """Calculate queued layouts once after a batch of UI changes."""
        while self._dirty_layouts:
            layouts = tuple(self._dirty_layouts)
            self._dirty_layouts.clear()
            for layout in layouts:
                layout._realign()
        self._dirty_flags &= ~UIDirtyFlag.LAYOUT

    def _hash(self, x: float, y: float) -> tuple[int, int]:
        """Normalize position to cell."""
        return int(x / self._cell_size), int(y / self._cell_size)

    def _on_reposition_handler(self, widget: WidgetBase) -> None:
        # Do not update hash until after resize.
        if not self._resizing:
            self._remove_from_cells(widget)
            self._add_to_cells(widget)

    def _add_to_cells(self, widget: WidgetBase) -> None:
        """Add a widget to the cells covered by its current bounds."""
        min_vec, max_vec = self._hash(*widget.aabb[0:2]), self._hash(*widget.aabb[2:4])
        cells = set()
        for i in range(min_vec[0], max_vec[0] + 1):
            for j in range(min_vec[1], max_vec[1] + 1):
                cell = i, j
                self._cells.setdefault(cell, set()).add(widget)
                cells.add(cell)
        self._widget_cells[widget] = cells

    def _remove_from_cells(self, widget: WidgetBase) -> None:
        """Remove a widget from the cells it occupied before its last update."""
        for cell in self._widget_cells.pop(widget, set()):
            widgets = self._cells[cell]
            widgets.remove(widget)
            if not widgets:
                del self._cells[cell]

    def _rebuild_cells(self) -> None:
        """Rebuild the spatial hash from the current widget bounds."""
        self._cells.clear()
        self._widget_cells.clear()
        for widget in self._widgets:
            self._add_to_cells(widget)

    def _widgets_at(self, x: float, y: float) -> Iterable[WidgetBase]:
        """Return the unique widgets in the spatial-hash cell at a point."""
        return self._cells.get(self._hash(x, y), ())

    def _all_widgets(self) -> Iterable[WidgetBase]:
        """Return every registered widget once, regardless of its cell coverage."""
        return self._widgets

    def _set_mouse_cursor(self, cursor: str | MouseCursor | None = None) -> None:
        cursor = self.cursor if cursor is None else cursor
        if isinstance(cursor, str):
            cursor = self._window.get_system_mouse_cursor(cursor)
        self._window.set_mouse_cursor(cursor)

    @property
    def focused_widget(self) -> WidgetBase | None:
        """The widget currently receiving keyboard and text input."""
        return self._focused_widget

    def set_focus(self, widget: WidgetBase | None) -> None:
        """Set the widget that receives keyboard and text input."""
        if widget is not None and widget.manager is not self:
            raise ValueError("Focus target is not attached to this UI manager.")
        if widget is self._focused_widget:
            return
        previous_widget = self._focused_widget
        self._focused_widget = widget
        if previous_widget is not None:
            previous_widget.dispatch_event("on_focus_lost")
        if widget is not None:
            widget.dispatch_event("on_focus_gain")

    @property
    def manager(self) -> UIManager:
        """Return this manager so widgets can derive it from their parent."""
        return self

    @property
    def enable(self) -> bool:
        """Whether to enable this UI manager.

        :type: bool
        """
        return self._enable

    @enable.setter
    def enable(self, value: bool) -> None:
        self._enable = bool(value)
        if self._enable:
            self._window.push_handlers(self)
            self._schedule_dirty_processing()
        else:
            self._window.remove_handlers(self)
            self._stop_dirty_processing()

    def _register_widget(self, widget: WidgetBase, parent: UIManager | Frame) -> None:
        if widget.manager is not None:
            raise ValueError("Widget is already attached to a UI manager.")
        if widget.parent is not None and widget.parent is not parent:
            raise ValueError("Widget already belongs to another parent.")
        widget.parent = parent
        widget._set_ui_manager(self)
        self._widgets.add(widget)
        widget.update_groups(self._order)
        # Preserve handlers already registered for this event.
        widget.push_handlers(on_reposition=self._on_reposition_handler)
        if not self._resizing:
            self._add_to_cells(widget)

    def _unregister_widget(self, widget: WidgetBase) -> None:
        if widget.manager is not self:
            raise ValueError("Widget is not attached to this UI manager.")
        if widget is self._focused_widget:
            self.set_focus(None)
        self._widgets.remove(widget)
        self._active_widgets.discard(widget)
        widget.remove_handlers(on_reposition=self._on_reposition_handler)
        if not self._resizing:
            self._remove_from_cells(widget)
        widget._set_ui_manager(None)
        widget.parent = None

    def _add_widget(self, widget: WidgetBase) -> None:
        """Register a widget constructed with this manager as its parent."""
        self._register_widget(widget, self)

    def remove_widget(self, widget: WidgetBase) -> None:
        """Remove a Widget from the spatial hash."""
        if widget.parent is not self:
            raise ValueError("Only widgets parented directly by this manager can be removed here.")
        self._unregister_widget(widget)

    def _add_layout(self, layout: Layout) -> None:
        """Register a layout constructed with this manager as its parent."""
        layout._set_parent(self)
        if isinstance(layout, Frame):
            self._frames.add(layout)

    # Handlers

    def on_resize(self, width: int, height: int) -> None:
        """Notify widgets of a frame resize, then rebuild the spatial hash."""
        # Widgets can update their position/size in response to this event.
        # Defer the hash rebuild until after processing, to prevent hash issues.
        self._resizing = True
        try:
            for widget in self._all_widgets():
                widget.dispatch_event("on_resize", width, height)
        finally:
            self._resizing = False
            self._rebuild_cells()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """Pass the event to the focused widget, or widgets under the mouse."""
        if self._focused_widget is not None:
            self._focused_widget.on_key_press(symbol, modifiers)
        else:
            for widget in self._widgets_at(*self._mouse_pos):
                widget.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        """Pass the event to the focused widget, or widgets under the mouse."""
        if self._focused_widget is not None:
            self._focused_widget.on_key_release(symbol, modifiers)
        else:
            for widget in self._widgets_at(*self._mouse_pos):
                widget.on_key_release(symbol, modifiers)

    def on_mouse_press(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        """Pass the event to any widgets within range of the mouse."""
        self._moving_frames = {
            frame
            for frame in self._frames
            if isinstance(frame, MovableFrame) and frame._can_move(x, y, modifiers)
        }
        if self._moving_frames:
            self.set_focus(None)
            return
        self.set_focus(None)
        for widget in self._widgets_at(x, y):
            widget.on_mouse_press(x, y, buttons, modifiers)
            self._active_widgets.add(widget)

    def on_mouse_release(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        """Pass the event to any widgets that are currently active."""
        if self._moving_frames:
            self._moving_frames.clear()
            return
        for widget in self._active_widgets:
            widget.on_mouse_release(x, y, buttons, modifiers)
        self._active_widgets.clear()

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> None:
        """Pass drag events to active widgets and update hover state."""
        if self._moving_frames:
            for frame in self._moving_frames:
                frame.move(dx, dy)
            return
        for widget in self._active_widgets:
            widget.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
        self.on_mouse_motion(x, y, dx, dy)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float) -> None:
        """Pass the event to any widgets within range of the mouse."""
        for widget in self._widgets_at(x, y):
            widget.on_mouse_scroll(x, y, scroll_x, scroll_y)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        """Dispatch widget enter/leave transitions and motion within the spatial hash."""
        current_widgets = {widget for widget in self._widgets_at(x, y) if widget._check_hit(x, y)}
        previous_widgets = {
            widget
            for widget in self._widgets_at(*self._mouse_pos)
            if widget._check_hit(*self._mouse_pos)
        }
        for widget in previous_widgets - current_widgets:
            widget.dispatch_event("on_mouse_leave_widget", x, y)
        for widget in current_widgets - previous_widgets:
            widget.dispatch_event("on_mouse_enter_widget", x, y)
        for widget in current_widgets:
            widget.on_mouse_motion(x, y, dx, dy)
        self._mouse_pos = x, y

    def on_text(self, text: str) -> None:
        """Pass the event to the focused widget, or widgets under the mouse."""
        if self._focused_widget is not None:
            self._focused_widget.on_text(text)
        else:
            for widget in self._widgets_at(*self._mouse_pos):
                widget.on_text(text)

    def on_text_motion(self, motion: int) -> None:
        """Pass the event to the focused widget, or widgets under the mouse."""
        if self._focused_widget is not None:
            self._focused_widget.on_text_motion(motion)
        else:
            for widget in self._widgets_at(*self._mouse_pos):
                widget.on_text_motion(motion)

    def on_text_motion_select(self, motion: int) -> None:
        """Pass the event to the focused widget, or widgets under the mouse."""
        if self._focused_widget is not None:
            self._focused_widget.on_text_motion_select(motion)
        else:
            for widget in self._widgets_at(*self._mouse_pos):
                widget.on_text_motion_select(motion)


