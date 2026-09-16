import pytest

from pyglet.gui.layout import VBox
from pyglet.gui.widgets import ScrollableRegion, WidgetBase


class RecordingWidget(WidgetBase):
    def __init__(self, parent, x, y, width, height):
        super().__init__(parent, x, y, width, height)
        self.events = []
        self._register_with_parent()

    def _update_position(self):
        pass

    def on_mouse_press(self, x, y, buttons, modifiers):
        self.events.append(("press", x, y))

    def on_mouse_release(self, x, y, buttons, modifiers):
        self.events.append(("release", x, y))

    def on_text(self, text):
        self.events.append(("text", text))


def test_scrollable_region_registers_with_manager_and_child_camera(test_window, manager):
    region = ScrollableRegion(manager, 10, 20, 100, 80, camera=test_window.camera)

    assert region.parent is manager
    assert region.view is not test_window.camera.view
    assert region in manager._widgets


def test_scrollable_region_uses_parent_manager(test_window, manager):
    region = ScrollableRegion(manager, 10, 20, 100, 80, camera=test_window.camera)

    assert region.manager is manager


def test_scrollable_child_shares_manager_without_top_level_registration(test_window, manager):
    region = ScrollableRegion(manager, 10, 20, 100, 80, camera=test_window.camera)
    widget = RecordingWidget(region, 10, 10, 20, 20)

    assert widget.manager is manager
    assert widget.parent is region
    manager.on_mouse_press(15, 15, 1, 0)
    assert widget.events == []


def test_scrollable_region_clamps_real_camera_view_offset(test_window):
    region = ScrollableRegion(None, 0, 0, 100, 80, camera=test_window.camera, horizontal=False)
    region.content = VBox(region, 0, 0, 100, 200)

    region.set_scroll(y=500)

    assert region.scroll_y == 120
    assert region.view.position == (0, -120)


def test_scrollable_region_routes_input_to_scrolled_child(test_window):
    region = ScrollableRegion(None, 0, 0, 100, 80, camera=test_window.camera, horizontal=False)
    region.content = VBox(region, 0, 0, 100, 200)
    widget = RecordingWidget(region, 10, -110, 20, 20)
    region.set_scroll(y=120)

    region.on_mouse_press(15, 15, 1, 0)
    region.on_mouse_release(15, 15, 1, 0)

    assert widget.events == [("press", 15, -105), ("release", 15, -105)]


def test_scrollable_region_is_usable_without_a_manager(test_window):
    region = ScrollableRegion(None, 0, 0, 100, 80, camera=test_window.camera)

    assert region.parent is None
    assert region._window is None


def test_scrollable_region_rejects_ambiguous_view_sources(test_window):
    with pytest.raises(ValueError, match="either a camera or a view"):
        ScrollableRegion(None, 0, 0, 10, 10, camera=test_window.camera, view=test_window.camera.view)
