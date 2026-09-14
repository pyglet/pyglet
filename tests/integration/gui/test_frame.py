from pyglet.gui.frame import MovableFrame
from pyglet.gui.widgets import WidgetBase


class TrackingWidget(WidgetBase):
    def __init__(self, x=0, y=0, width=10, height=10):
        super().__init__(x, y, width, height)
        self.group_orders = []
        self.events = []
        self.resize_events = []

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


def test_frame_registers_widget_with_a_real_window_and_orders_its_groups(frame):
    widget = TrackingWidget()

    frame.add_widget(widget)

    assert widget.parent is frame
    assert widget.group_orders == [0]
    assert widget in frame._widgets


def test_frame_resize_rebuilds_hash_and_propagates_to_widget(frame):
    widget = TrackingWidget()
    frame.add_widget(widget)

    widget.position = 30, 30
    frame.on_resize(640, 480)

    assert widget.resize_events == [(640, 480)]
    assert widget in frame._cells[(0, 0)]


def test_frame_remove_unregisters_reposition_handler(frame):
    widget = TrackingWidget()
    frame.add_widget(widget)
    frame.remove_widget(widget)

    widget.position = 100, 100

    assert widget.parent is None
    assert frame._cells == {}


def test_frame_dispatches_input_to_widgets_in_the_current_mouse_cell(frame):
    target = TrackingWidget()
    other = TrackingWidget(100, 100)
    frame.add_widget(target)
    frame.add_widget(other)

    frame.on_mouse_motion(5, 5, 0, 0)
    frame.on_key_press(1, 2)
    frame.on_text("x")

    assert target.events == [("key_press", 1, 2), ("text", "x")]
    assert other.events == []


def test_frame_keeps_widget_active_through_a_drag_and_release(frame):
    widget = TrackingWidget()
    frame.add_widget(widget)

    frame.on_mouse_press(5, 5, 1, 0)
    frame.on_mouse_drag(25, 5, 20, 0, 1, 0)
    frame.on_mouse_release(25, 5, 1, 0)

    assert widget.events == [("press", 5, 5), ("drag", 25, 5), ("release", 25, 5)]


def test_movable_frame_rehashes_widget_after_modifier_drag(test_window):
    frame = MovableFrame(test_window, modifier=1)
    widget = TrackingWidget()
    frame.add_widget(widget)

    frame.on_mouse_press(5, 5, 1, 1)
    frame.on_mouse_drag(105, 105, 100, 100, 1, 1)
    frame.on_mouse_release(105, 105, 1, 1)

    assert widget.position == (100, 100)
    assert widget.parent is frame
    assert widget in frame._cells[(1, 1)]
    frame.enable = False
