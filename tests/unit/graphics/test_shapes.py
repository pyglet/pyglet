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

# The shapes are tested individually since their RGBA handling is
# inlined for maximum speed instead of encapsulated into functions.
# A typo in one might break color functionality in one but not the
# others.
@pytest.fixture(params=[
    (Arc, (0, 0, 5)),
    (Circle, (0, 0, 5)),
    # Ellipse's a value below is impossible in normal use, but here it
    # makes sure the a value is not confused with the RGBA alpha channel
    # internally.
    (Ellipse, (0, 0, 0, 5)),
    (Sector, (0, 0, 3)),
    (Line, (0, 0, 7, 7)),
    (Rectangle, (0, 0, 20, 20)),
    (BorderedRectangle, (0, 0, 30, 10)),
    (Triangle, (0, 0, 2, 2, 5, 5)),
    (Star, (1, 1, 20, 11, 5)),
    (Polygon, ((0, 0), (1, 1), (2, 2)), )
])
def rgba_shape(request):
    shape_type, required_args = request.param
    return shape_type(*required_args, color=(0, 255, 0, 37))


def test_opacity_set_from_rgba_color_init_argument(rgba_shape):
    assert rgba_shape.opacity == 37


def test_setting_opacity_does_not_change_rgb_channels(rgba_shape):
    original_color = rgba_shape.color[:3]
    rgba_shape.opacity = 255
    assert rgba_shape.color[:3] == original_color


def test_setting_rgba_color_changes_opacity(rgba_shape):
    rgba_shape.color = (0, 0, 0, 0)
    assert rgba_shape.opacity == 0


def test_setting_rgb_color_does_not_change_opacity(rgba_shape):
    original_opacity = rgba_shape.opacity
    rgba_shape.color = (128, 128, 128)
    assert rgba_shape.opacity == original_opacity
