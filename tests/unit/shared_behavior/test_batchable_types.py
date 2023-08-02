from typing import Callable, Tuple, Any

import pytest

from pyglet.graphics import Batch
from pyglet.shapes import *


# The shapes are tested individually since their RGBA handling is
# inlined for maximum speed instead of encapsulated in their baseclass.
# A typo might break color functionality in one but not the others.
@pytest.fixture(scope="module", params=[
    (Arc, (0, 0, 5)),
    (Circle, (0, 0, 5)),
    # Ellipse's a value below is nonsensical in normal use, but here it
    # makes sure the value is not confused with the RGBA alpha channel
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
def instance_factory_template(request) -> Tuple[Callable, Tuple[Any, ...]]:
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
