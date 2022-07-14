import pytest
from pyglet.shapes import (
    Arc,
    Circle
)

# The shapes are tested individually since their RGBA handling is
# inlined for maximum speed instead of encapsulated into functions.
# A typo in one might break it but not the others.
@pytest.fixture(params=[
    (Arc, (0, 0, 5)),
    (Circle, (0, 0, 5)),
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


def test_setting_rgb_color_sets_full_opacity(rgba_shape):
    rgba_shape.color = (0, 0, 255)
    assert rgba_shape.opacity == 255
