"""
Tests for behavior unique to BorderedRectangle.

Most color property behavior is tested with the other _ShapeBase
subclasses in test_shapes.py
"""
import pytest

from pyglet.shapes import BorderedRectangle


@pytest.fixture
def bordered_rectangle():
    return BorderedRectangle(0, 0, 10, 50, color=(0, 0, 0, 31), border_color=(1, 1, 1))


def test_init_raises_value_error_on_conflicting_rgba_alphas():
    with pytest.raises(ValueError):
        _ = BorderedRectangle(0, 0, 10, 10, color=(1, 1, 1, 2), border_color=(255, 255, 255, 255))


@pytest.mark.parametrize(
    'color, border_color, expected_alpha', [
        ((0, 0, 0), (3, 3, 3), 255),         # 255 alpha when both colors RGB
        ((2, 2, 2, 5), (7, 7, 7), 5),        # color is RGBA, its alpha used
        ((17, 17, 17), (23, 23, 23, 0), 0),  # border_color's alpha used
        ((1, 1, 1, 1), (2, 2, 2, 1), 1)      # identical alphas are accepted
    ]
)
def test_init_sets_opacity_for_valid_color_and_border_color_alphas(color, border_color, expected_alpha):
    rect = BorderedRectangle(0, 0, 10, 50, color=color, border_color=border_color)
    assert rect.opacity == expected_alpha


def test_setting_border_color_sets_border_color_rgb_channels(bordered_rectangle, new_rgb_or_rgba_color):
    bordered_rectangle.border_color = new_rgb_or_rgba_color
    assert bordered_rectangle.border_color[:3] == new_rgb_or_rgba_color[:3]


def test_setting_border_color_to_rgb_value_does_not_change_opacity(bordered_rectangle, new_rgb_color):
    original_opacity = bordered_rectangle.opacity
    bordered_rectangle.border_color = new_rgb_color
    assert bordered_rectangle.opacity == original_opacity
    assert bordered_rectangle.color[3] == original_opacity
    assert bordered_rectangle.border_color[3] == original_opacity


def test_setting_border_color_to_rgba_value_does_not_change_fill_color_rgb_channels(bordered_rectangle, new_rgba_color):
    original_rgb_color = bordered_rectangle.color[:3]
    bordered_rectangle.border_color = new_rgba_color
    assert bordered_rectangle.color[:3] == original_rgb_color


def test_setting_border_color_to_rgba_value_sets_opacity(bordered_rectangle, new_rgba_color):
    new_opacity = new_rgba_color[3]
    bordered_rectangle.border_color = new_rgba_color
    assert bordered_rectangle.opacity == new_opacity
    assert bordered_rectangle.color[3] == new_opacity
    assert bordered_rectangle.border_color[3] == new_opacity


def test_setting_color_to_rgb_value_does_not_change_alpha_channel_on_border_color(bordered_rectangle, new_rgb_color):
    original_opacity = bordered_rectangle.opacity
    bordered_rectangle.color = new_rgb_color
    assert bordered_rectangle.border_color[3] == original_opacity


def test_setting_color_to_rgba_value_does_not_change_rgb_channels_on_border_color(bordered_rectangle, new_rgba_color):
    original_border_rgb = bordered_rectangle.border_color[:3]
    bordered_rectangle.color = new_rgba_color
    assert bordered_rectangle.border_color[:3] == original_border_rgb


def test_setting_color_to_rgba_value_sets_alpha_channel_on_border_color(bordered_rectangle, new_rgba_color):
    new_opacity = new_rgba_color[3]
    bordered_rectangle.color = new_rgba_color
    assert bordered_rectangle.border_color[3] == new_opacity


def test_setting_opacity_does_not_change_border_color_rgb_channels(bordered_rectangle):
    original_border_rgb = bordered_rectangle.border_color[:3]
    bordered_rectangle.opacity = 47
    assert bordered_rectangle.border_color[:3] == original_border_rgb
