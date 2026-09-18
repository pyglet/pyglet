from pyglet.gui.layout import MovableFrame
from pyglet.gui.manager import UIManager
from pyglet.gui.widgets import TextEntry, WidgetBase


class TrackingWidget(WidgetBase):
    def __init__(self, parent, x=0, y=0, width=10, height=10):
        super().__init__(parent, x, y, width, height)
        self.group_orders = []
        self.events = []
        self.resize_events = []
        self._register_with_parent()

    def _update_position(self):
        pass

    def update_groups(self, order):
        self.group_orders.append(order)

    def on_resize(self, width, height):
        self.resize_events.append((width, height))

    def on_mouse_press(self, x, y, buttons, modifiers):
        self.events.append(("press", x, y))

    def on_mouse_release(self, x, y, buttons, modifiers):
        self.events.append(("release", x, y))

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.events.append(("drag", x, y))

    def on_key_press(self, symbol, modifiers):
        self.events.append(("key_press", symbol, modifiers))

    def on_text(self, text):
        self.events.append(("text", text))

    def on_focus_gain(self):
        self.events.append(("focus_gain",))

    def on_focus_lost(self):
        self.events.append(("focus_lost",))


def test_manager_registers_widget_with_a_real_window_and_orders_its_groups(manager):
    widget = TrackingWidget(manager)

    assert widget.parent is manager
    assert widget.group_orders == [0]
    assert widget in manager._widgets


def test_manager_resize_rebuilds_hash_and_propagates_to_widget(manager):
    widget = TrackingWidget(manager)
    widget.position = 30, 30
    manager.on_resize(640, 480)

    assert widget.resize_events == [(640, 480)]
    assert widget in manager._cells[(0, 0)]


def test_manager_remove_unregisters_reposition_handler(manager):
    widget = TrackingWidget(manager)
    manager.remove_widget(widget)
    widget.position = 100, 100

    assert widget.parent is None
    assert manager._cells == {}


def test_manager_dispatches_input_to_widgets_in_the_current_mouse_cell(manager):
    target = TrackingWidget(manager)
    other = TrackingWidget(manager, 100, 100)
    manager.on_mouse_motion(5, 5, 0, 0)
    manager.on_key_press(1, 2)
    manager.on_text("x")

    assert target.events == [("key_press", 1, 2), ("text", "x")]
    assert other.events == []


def test_manager_dispatches_text_to_the_focused_entry_after_the_mouse_moves(manager):
    entry = TextEntry(manager, '', 0, 0, 40)
    other_entry = TextEntry(manager, '', 100, 100, 40)
    manager.on_mouse_press(5, 5, 1, 0)
    manager.on_mouse_motion(105, 105, 100, 100)
    manager.on_text('x')

    assert entry.value == 'x'
    assert other_entry.value == ''


def test_manager_owns_focus_and_dispatches_focus_transition_events(manager):
    first = TrackingWidget(manager)
    second = TrackingWidget(manager, 100, 100)

    manager.set_focus(first)
    manager.set_focus(second)
    manager.set_focus(None)

    assert manager.focused_widget is None
    assert first.events == [("focus_gain",), ("focus_lost",)]
    assert second.events == [("focus_gain",), ("focus_lost",)]


def test_manager_keeps_widget_active_through_a_drag_and_release(manager):
    widget = TrackingWidget(manager)
    manager.on_mouse_press(5, 5, 1, 0)
    manager.on_mouse_drag(25, 5, 20, 0, 1, 0)
    manager.on_mouse_release(25, 5, 1, 0)

    assert widget.events == [("press", 5, 5), ("drag", 25, 5), ("release", 25, 5)]


def test_movable_frame_moves_its_child_widgets(test_window):
    manager = UIManager(test_window)
    container = MovableFrame(manager, 0, 0, 100, 100, modifier=1)
    widget = TrackingWidget(container)

    manager.on_mouse_press(5, 5, 1, 1)
    manager.on_mouse_drag(105, 105, 100, 100, 1, 1)
    manager.on_mouse_release(105, 105, 1, 1)

    assert widget.position == (100, 100)
    assert widget.parent is container
    assert widget in manager._cells[(1, 1)]
    manager.enable = False
