import pytest

from pyglet.gui.frame import Frame
from pyglet.gui.layout import VBox
from pyglet.gui.widgets import ScrollableRegion, WidgetBase


class RecordingWidget(WidgetBase):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.events = []

    def _update_position(self):
        pass

    def on_mouse_press(self, x, y, buttons, modifiers):
        self.events.append(("press", x, y))

    def on_mouse_release(self, x, y, buttons, modifiers):
        self.events.append(("release", x, y))

    def on_text(self, text):
        self.events.append(("text", text))


def test_scrollable_region_registers_with_real_frame_and_child_camera(test_window, frame):
    region = ScrollableRegion(10, 20, 100, 80, frame=frame, camera=test_window.camera)

    assert region.parent is frame
    assert region.view is not test_window.camera.view
    assert region in frame._widgets


def test_scrollable_region_clamps_real_camera_view_offset(test_window):
    region = ScrollableRegion(0, 0, 100, 80, camera=test_window.camera, horizontal=False)
    region.content = VBox(0, 0, 100, 200)

    region.set_scroll(y=500)

    assert region.scroll_y == 120
    assert region.view.position == (0, -120)


def test_scrollable_region_routes_input_to_scrolled_child(test_window):
    region = ScrollableRegion(0, 0, 100, 80, camera=test_window.camera, horizontal=False)
    region.content = VBox(0, 0, 100, 200)
    widget = RecordingWidget(10, -110, 20, 20)
    region.add_widget(widget)
    region.set_scroll(y=120)

    region.on_mouse_press(15, 15, 1, 0)
    region.on_mouse_release(15, 15, 1, 0)

    assert widget.events == [("press", 15, -105), ("release", 15, -105)]


def test_scrollable_region_is_usable_without_a_frame(test_window):
    region = ScrollableRegion(0, 0, 100, 80, camera=test_window.camera)

    assert region.parent is None
    assert region._window is None


def test_scrollable_region_rejects_ambiguous_view_sources(test_window):
    with pytest.raises(ValueError, match="either a camera or a view"):
        ScrollableRegion(0, 0, 10, 10, camera=test_window.camera, view=test_window.camera.view)
