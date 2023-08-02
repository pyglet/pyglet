from typing import Callable, Tuple, Any, Dict

import pytest

from pyglet.graphics import Batch
from pyglet.shapes import *


# todo: expand this to a general defaults fixture + a filtration tool?
# The shapes are tested individually since their RGBA handling is
# inlined for maximum speed instead of encapsulated in their baseclass.
# A typo might break color functionality in one but not the others.
@pytest.fixture(scope="module", params=[
    (Arc, dict(x=0, y=0, radius=5)),
    (Circle, dict(x=0, y=0, radius=5)),
    # Ellipse's a value below is nonsensical in normal use, but here it
    # makes sure the value is not confused with the RGBA alpha channel
    # internally.
    (Ellipse, dict(x=0, y=0, a=0, b=5)),
    (Sector, dict(x=0, y=0, radius=3)),
    (Line, dict(x=0, y=0, x2=7, y2=7)),
    (Rectangle, dict(x=0, y=0, width=20, height=20)),
    (BorderedRectangle, dict(x=0, y=0, width=30, height=10)),
    (Triangle, dict(x=0, y=0, x2=2, y2=2, x3=5, y3=5)),
    (Star, dict(x=0, y=0, inner_radius=20, outer_radius=11, num_spikes=5)),
    (Polygon, {
        "*coordinates": (
                (0, 0),
                (1, 1),
                (2, 2)
        )
    })
])
def instance_factory_template(request) -> Tuple[Callable, Dict[str, Any]]:
    return request.param


def test_init_sets_opacity_from_rgba_value_as_color_argument(rgba_instance, original_rgba_color):
    assert rgba_instance.opacity == original_rgba_color[3]


def test_init_sets_opacity_to_255_for_rgb_value_as_color_argument(rgb_instance, original_rgb_color):
    assert rgb_instance.opacity == 255


def test_setting_color_sets_rgb_channels(
        rgb_or_rgba_instance,
        new_rgb_or_rgba_color,
):
    rgb_or_rgba_instance.color = new_rgb_or_rgba_color
    assert rgb_or_rgba_instance.color[:3] == new_rgb_or_rgba_color[:3]


def test_setting_color_to_rgb_value_does_not_change_opacity(
        rgb_or_rgba_instance,
        new_rgb_color,
        original_rgb_or_rgba_expected_alpha
):
    rgb_or_rgba_instance.color = new_rgb_color
    assert rgb_or_rgba_instance.opacity == original_rgb_or_rgba_expected_alpha


def test_setting_color_to_rgba_value_changes_opacity(rgb_or_rgba_instance, new_rgba_color):
    rgb_or_rgba_instance.color = new_rgba_color
    assert rgb_or_rgba_instance.opacity == new_rgba_color[3]


def test_setting_opacity_does_not_change_rgb_channels(rgb_or_rgba_instance, original_rgb_or_rgba_color):
    rgb_or_rgba_instance.opacity = 255
    assert rgb_or_rgba_instance.color[:3] == original_rgb_or_rgba_color[:3]


def test_batch_setter(rgb_or_rgba_instance):
    new_batch = Batch()
    rgb_or_rgba_instance.batch = new_batch
    assert rgb_or_rgba_instance.batch is new_batch
