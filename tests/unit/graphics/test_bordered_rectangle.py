"""
Border color related tests for the BorderedRectangle.

These should only cover behavior not tested by test_shapes.py
"""
import pytest

from pyglet.shapes import BorderedRectangle


@pytest.fixture
def rgba_bordered_rectangle():
    return BorderedRectangle(0, 0, 10, 50, border_color=(0, 0, 0, 31))


@pytest.mark.parametrize(
    'color, border_color, expected_alpha', [
        ((0, 0, 0, 1), (3, 3, 3, 0), 0),  # border_color's alpha used
        ((2, 2, 2, 5), (7, 7, 7, 11), 5),  # color's alpha used
        ((17, 17, 17, 0), (23, 23, 23, 23, 0), 0)  # use either
    ]
)
def test_init_sets_opacity_from_min_of_color_alpha_and_border_color_alpha(
        color, border_color, expected_alpha
):
    rect = BorderedRectangle(
        0, 0, 10, 50,
        color=color,
        border_color=border_color
    )
    assert rect.opacity == expected_alpha



def test_setting_rgba_border_color_changes_opacity_to_alpha_channel_value(rgba_bordered_rectangle):
    rgba_bordered_rectangle.border_color = (1, 2, 3, 53)
    assert rgba_bordered_rectangle.opacity == 53


def test_setting_rgba_border_color_does_not_change_fill_color_rgb_channels(rgba_bordered_rectangle):
    original_rgb_color = rgba_bordered_rectangle.color[:3]
    rgba_bordered_rectangle.border_color = (1, 1, 1, 29)
    assert rgba_bordered_rectangle.color[:3] == original_rgb_color


def test_setting_rgb_border_color_sets_opacity_to_255(rgba_bordered_rectangle):
    rgba_bordered_rectangle.border_color = (3, 4, 5)
    assert rgba_bordered_rectangle.opacity == 255
    assert rgba_bordered_rectangle.color[3] == 255
    assert rgba_bordered_rectangle.border_color[3] == 255


@pytest.mark.parametrize(
    'fill_color', (
            (1, 2, 3),
            (1, 2, 3, 59)
    )
)
def test_setting_border_color_sets_border_color_rgb_channels(rgba_bordered_rectangle, fill_color):
    rgba_bordered_rectangle.border_color = fill_color
    assert rgba_bordered_rectangle.border_color[:3] == fill_color[:3]


def test_setting_opacity_does_not_change_rgb_channels(rgba_bordered_rectangle):
    original_color_rgb = rgba_bordered_rectangle.color[:3]
    original_border_color_rgb = rgba_bordered_rectangle.border_color[:3]

    rgba_bordered_rectangle.opacity = 47
    assert rgba_bordered_rectangle.color[:3] == original_color_rgb
    assert rgba_bordered_rectangle.border_color[:3] == original_border_color_rgb


