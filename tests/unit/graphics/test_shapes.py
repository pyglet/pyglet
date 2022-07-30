from functools import partial

import pytest

from pyglet.shapes import (
    Arc,
    Circle,
    Ellipse,
    Sector,
    Line,
    Rectangle,
    BorderedRectangle,
    Triangle,
    Star,
    Polygon
)

from . import (
    new_rgb_color,
    new_rgba_color,
    new_rgb_or_rgba_color
)


# The shapes are tested individually since their RGBA handling is
# inlined for maximum speed instead of encapsulated in their baseclass.
# A typo might break color functionality in one but not the others.
@pytest.fixture(params=[
    (Arc, (0, 0, 5)),
    (Circle, (0, 0, 5)),
    # Ellipse's a value below is nonsensical in normal use, but here it
    # makes sure the a value is not confused with the RGBA alpha channel
    # internally.
    (Ellipse, (0, 0, 0, 5)),
    (Sector, (0, 0, 3)),
    (Line, (0, 0, 7, 7)),
    (Rectangle, (0, 0, 20, 20)),
    (BorderedRectangle, (0, 0, 30, 10)),
    (Triangle, (0, 0, 2, 2, 5, 5)),
    (Star, (1, 1, 20, 11, 5)),
    (Polygon, ((0, 0), (1, 1), (2, 2)))
])
def shape_keywords_only(request):
    class_, positional_args = request.param
    return partial(class_, *positional_args)


@pytest.fixture
def rgba_shape(shape_keywords_only):
    return shape_keywords_only(color=(0, 255, 0, 37))


def test_init_sets_opacity_from_rgba_value_as_color_argument(rgba_shape):
    assert rgba_shape.opacity == 37


def test_init_sets_opacity_to_255_for_rgb_value_as_color_argument(shape_keywords_only):
    assert shape_keywords_only(color=(0, 0, 0)).opacity == 255


def test_setting_color_sets_color_rgb_channels(rgba_shape, new_rgb_or_rgba_color):
    rgba_shape.color = new_rgb_or_rgba_color
    assert rgba_shape.color[:3] == new_rgb_or_rgba_color[:3]


def test_setting_color_to_rgb_value_does_not_change_opacity(rgba_shape, new_rgb_color):
    original_opacity = rgba_shape.opacity
    rgba_shape.color = new_rgb_color
    assert rgba_shape.opacity == original_opacity


def test_setting_color_to_rgba_value_changes_opacity(rgba_shape, new_rgba_color):
    rgba_shape.color = new_rgba_color
    assert rgba_shape.opacity == new_rgba_color[3]
    assert rgba_shape.color[3] == new_rgba_color[3]


def test_setting_opacity_does_not_change_rgb_channels_on_color(rgba_shape):
    original_color = rgba_shape.color[:3]
    rgba_shape.opacity = 255
    assert rgba_shape.color[:3] == original_color
