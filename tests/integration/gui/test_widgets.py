import gc

import pyglet
import pytest

from pyglet.gui.widgets import PushButton, Slider, TextButton, TextEntry, ToggleButton


def image(width=20, height=10):
    return pyglet.image.ImageData(width, height, "RGBA", bytes((255, 255, 255, 255)) * width * height)


@pytest.fixture
def batch():
    return pyglet.graphics.Batch()


def test_push_button_renders_state_images_and_dispatches_events(test_window, manager, batch):
    pressed, unpressed, hover = image(), image(), image()
    button = PushButton(manager, 0, 0, pressed, unpressed, hover, batch=batch)
    events = []
    button.push_handlers(on_press=lambda widget: events.append("press"))
    button.push_handlers(on_release=lambda widget: events.append("release"))

    button.on_mouse_press(5, 5, 1, 0)
    button.on_mouse_release(5, 5, 1, 0)

    assert button.value is False
    assert button._sprite.image is hover.get_texture()
    assert events == ["press", "release"]


def test_widget_without_a_batch_can_be_removed_and_recreated(test_window, manager):
    pressed, unpressed = image(), image()
    button = ToggleButton(manager, 0, 0, pressed, unpressed)

    manager.remove_widget(button)
    del button
    gc.collect()

    replacement = ToggleButton(manager, 0, 0, pressed, unpressed)

    assert replacement.parent is manager


def test_toggle_button_renders_and_dispatches_its_value(test_window, manager, batch):
    pressed, unpressed = image(), image()
    button = ToggleButton(manager, 0, 0, pressed, unpressed, batch=batch)
    values = []
    button.push_handlers(on_toggle=lambda widget, value: values.append(value))

    button.on_mouse_press(5, 5, 1, 0)
    button.on_mouse_press(5, 5, 1, 0)

    assert button.value is False
    assert values == [True, False]


def test_toggle_button_keeps_its_pressed_image_after_mouse_leave(test_window, manager, batch):
    pressed, unpressed = image(), image()
    button = ToggleButton(manager, 0, 0, pressed, unpressed, batch=batch)

    button.on_mouse_press(5, 5, 1, 0)
    button.on_mouse_leave_widget(25, 5)

    assert button.value is True
    assert button._sprite.image is pressed.get_texture()


def test_slider_renders_and_clamps_its_knob(test_window, manager, batch):
    slider = Slider(manager, 0, 0, image(100, 20), image(20, 20), edge=10, batch=batch)
    values = []
    slider.push_handlers(on_change=lambda widget, value: values.append(value))

    slider.on_mouse_press(20, 10, 1, 0)
    slider.on_mouse_drag(90, 10, 70, 0, 1, 0)
    slider.on_mouse_release(90, 10, 1, 0)

    assert values == [0.0, 100.0]
    assert slider.value == 100.0
    assert slider._knob_spr.x == slider._max_knob_x


def test_text_button_repositions_real_label_after_resize(test_window, manager, batch):
    button = TextButton(manager, 10, 20, "Centered", batch=batch)

    button.width = 100
    button.height = 40
    button.on_mouse_press(60, 40, 1, 0)
    button.on_mouse_release(60, 40, 1, 0)

    assert button._label.position == (60, 40, 0)
    assert button._label.color == (*button._hover_color, 255)


def test_text_entry_uses_real_layout_caret_and_outline_when_resized(test_window, manager, batch):
    entry = TextEntry(manager, "start", 10, 20, 40, batch=batch)
    commits = []
    entry.push_handlers(on_commit=lambda widget, value: commits.append(value))

    entry.width = 100
    entry.height = 30
    entry.on_mouse_press(15, 25, 1, 0)
    entry._caret.position = len(entry.value)
    entry.on_text("x")
    entry.on_text("\r")

    assert entry._outline.width == 104
    assert entry._outline.height == 34
    assert manager.focused_widget is None
    assert commits == ["startx"]


@pytest.mark.parametrize("value", [1, None, "yes"])
def test_push_button_value_requires_boolean(test_window, manager, batch, value):
    button = PushButton(manager, 0, 0, image(), image(), batch=batch)

    with pytest.raises(AssertionError):
        button.value = value
