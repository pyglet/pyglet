import pytest
from pyglet.shapes import (
    Arc
)

# The shapes are tested individually since their RGBA handling is
# inlined for maximum speed instead of encapsulated into functions.
# A typo in one might break it but not the others.
@pytest.fixture(params=[
    (Arc, (0, 0, 5)),
])
def shape_instance(request):
    shape_type, required_args = request.param
    return shape_type(*required_args, color=(0, 255, 0, 37))


def test_opacity_set_from_rgba_color_init_argument(shape_instance):
    assert shape_instance.opacity == 37


def test_setting_opacity_does_not_change_rgb_channels(shape_instance):
    original_color = shape_instance.color[:3]
    shape_instance.opacity = 255
    assert shape_instance.color[:3] == original_color


def test_setting_rgba_color_changes_opacity(shape_instance):
    shape_instance.color = (0, 0, 0, 0)
    assert shape_instance.opacity == 0


def test_setting_rgb_color_sets_full_opacity(shape_instance):
    shape_instance.color = (0, 0, 255)
    assert shape_instance.opacity == 255
