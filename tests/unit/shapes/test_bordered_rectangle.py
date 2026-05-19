"""
Tests for behavior unique to BorderedRectangle.

Most color property behavior is tested with the other _ShapeBase
subclasses in test_shapes.py
"""
import pytest

from pyglet.shapes import BorderedRectangle


@pytest.fixture
def bordered_rectangle():
    return BorderedRectangle(0, 0, 10, 50, color=(0, 0, 0, 31), border_color=(1, 1, 1, 83))


def test_init_allows_independent_fill_and_border_alpha():
    rect = BorderedRectangle(0, 0, 10, 10, color=(1, 1, 1, 2), border_color=(255, 255, 255, 255))
    assert rect.color[3] == 2
    assert rect.border_color[3] == 255


@pytest.mark.parametrize(
    'color, border_color, expected_fill_alpha, expected_border_alpha', [
        ((0, 0, 0), (3, 3, 3), 255, 255),          # both RGB default to 255
        ((2, 2, 2, 5), (7, 7, 7), 5, 255),         # fill alpha from color
        ((17, 17, 17), (23, 23, 23, 0), 255, 0),   # border alpha from border_color
        ((1, 1, 1, 1), (2, 2, 2, 9), 1, 9)         # independent RGBA alphas
    ]
)
def test_init_sets_fill_and_border_opacity_independently(
        color,
        border_color,
        expected_fill_alpha,
        expected_border_alpha,
):
    rect = BorderedRectangle(0, 0, 10, 50, color=color, border_color=border_color)
    assert rect.opacity == expected_fill_alpha
    assert rect.color[3] == expected_fill_alpha
    assert rect.border_color[3] == expected_border_alpha


def test_setting_border_color_sets_border_color_rgb_channels(bordered_rectangle, new_rgb_or_rgba_color):
    bordered_rectangle.border_color = new_rgb_or_rgba_color
    assert bordered_rectangle.border_color[:3] == new_rgb_or_rgba_color[:3]


def test_setting_border_color_to_rgb_value_does_not_change_border_opacity(bordered_rectangle, new_rgb_color):
    original_fill_opacity = bordered_rectangle.color[3]
    original_border_opacity = bordered_rectangle.border_color[3]
    bordered_rectangle.border_color = new_rgb_color
    assert bordered_rectangle.color[3] == original_fill_opacity
    assert bordered_rectangle.border_color[3] == original_border_opacity


def test_setting_border_color_to_rgba_value_does_not_change_fill_color_rgb_channels(bordered_rectangle, new_rgba_color):
    original_rgb_color = bordered_rectangle.color[:3]
    bordered_rectangle.border_color = new_rgba_color
    assert bordered_rectangle.color[:3] == original_rgb_color


def test_setting_border_color_to_rgba_value_sets_only_border_opacity(bordered_rectangle, new_rgba_color):
    original_fill_opacity = bordered_rectangle.color[3]
    new_opacity = new_rgba_color[3]
    bordered_rectangle.border_color = new_rgba_color
    assert bordered_rectangle.color[3] == original_fill_opacity
    assert bordered_rectangle.border_color[3] == new_opacity


def test_setting_color_to_rgb_value_does_not_change_alpha_channel_on_border_color(bordered_rectangle, new_rgb_color):
    original_opacity = bordered_rectangle.border_color[3]
    bordered_rectangle.color = new_rgb_color
    assert bordered_rectangle.border_color[3] == original_opacity


def test_setting_color_to_rgba_value_does_not_change_rgb_channels_on_border_color(bordered_rectangle, new_rgba_color):
    original_border_rgb = bordered_rectangle.border_color[:3]
    bordered_rectangle.color = new_rgba_color
    assert bordered_rectangle.border_color[:3] == original_border_rgb


def test_setting_color_to_rgba_value_does_not_set_alpha_channel_on_border_color(bordered_rectangle, new_rgba_color):
    original_border_opacity = bordered_rectangle.border_color[3]
    new_opacity = new_rgba_color[3]
    bordered_rectangle.color = new_rgba_color
    assert bordered_rectangle.color[3] == new_opacity
    assert bordered_rectangle.border_color[3] == original_border_opacity


def test_setting_opacity_does_not_change_border_color_rgb_channels_or_alpha(bordered_rectangle):
    original_border_rgb = bordered_rectangle.border_color[:3]
    original_border_alpha = bordered_rectangle.border_color[3]
    bordered_rectangle.opacity = 47
    assert bordered_rectangle.border_color[:3] == original_border_rgb
    assert bordered_rectangle.border_color[3] == original_border_alpha
