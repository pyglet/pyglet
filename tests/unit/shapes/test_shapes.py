from __future__ import annotations

from functools import partial
from unittest.mock import MagicMock

import pytest

from pyglet.graphics import Batch, Group
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
    (Polygon, ((0, 0), (1, 1), (2, 2))),
    (MultiLine, ((0, 0), (1, 1), (2, 2))),
])
def shape_and_positionals(request):
    return request.param


# Enable type-specific behavior; just Line + rotation at the moment
@pytest.fixture()
def shape_type(shape_and_positionals):
    return shape_and_positionals[0]


@pytest.fixture()
def shape_keywords_only(shape_and_positionals):
    class_, positional_args = shape_and_positionals
    return partial(class_, *positional_args)


@pytest.fixture()
def rgb_or_rgba_shape(shape_keywords_only, original_rgb_or_rgba_color):
    return shape_keywords_only(color=original_rgb_or_rgba_color)


@pytest.fixture()
def rgba_shape(shape_keywords_only):
    return shape_keywords_only(color=(0, 255, 0, 37))


def test_init_sets_opacity_from_rgba_value_as_color_argument(rgba_shape):
    assert rgba_shape.opacity == 37


def test_init_sets_opacity_to_255_for_rgb_value_as_color_argument(shape_keywords_only):
    assert shape_keywords_only(color=(0, 0, 0)).opacity == 255


def test_init_sets_rotation_to_zero(rgb_or_rgba_shape, shape_type):
    if shape_type is Line:
        pytest.xfail("Rotation test not yet valid for line due to design ambiguity")
    assert rgb_or_rgba_shape.rotation == 0


def test_rotation_prop_sets_rotation(rgb_or_rgba_shape, new_nonzero_rotation):
    rgb_or_rgba_shape.rotation = new_nonzero_rotation
    assert rgb_or_rgba_shape.rotation == new_nonzero_rotation


def test_setting_color_sets_color_rgb_channels(rgb_or_rgba_shape, new_rgb_or_rgba_color):
    rgb_or_rgba_shape.color = new_rgb_or_rgba_color
    assert rgb_or_rgba_shape.color[:3] == new_rgb_or_rgba_color[:3]


def test_setting_color_to_rgb_value_does_not_change_opacity(rgb_or_rgba_shape, new_rgb_color):
    original_opacity = rgb_or_rgba_shape.opacity
    rgb_or_rgba_shape.color = new_rgb_color
    assert rgb_or_rgba_shape.opacity == original_opacity


def test_setting_color_to_rgba_value_changes_opacity(rgb_or_rgba_shape, new_rgba_color):
    rgb_or_rgba_shape.color = new_rgba_color
    assert rgb_or_rgba_shape.opacity == new_rgba_color[3]
    assert rgb_or_rgba_shape.color[3] == new_rgba_color[3]


def test_setting_opacity_does_not_change_rgb_channels_on_color(rgb_or_rgba_shape):
    original_color = rgb_or_rgba_shape.color[:3]
    rgb_or_rgba_shape.opacity = 255
    assert rgb_or_rgba_shape.color[:3] == original_color


def test_group_setter(shape_keywords_only):
    shape = shape_keywords_only()

    new_group = Group()
    shape.group = new_group
    assert shape.group is new_group


def test_batch_setter(shape_keywords_only):
    shape = shape_keywords_only()

    new_batch = Batch()
    shape.batch = new_batch
    assert shape.batch is new_batch


def test_program_setter(shape_keywords_only):
    shape = shape_keywords_only()

    program = MagicMock()
    shape.program = program
    assert shape.program == program


def test_blend_setter(shape_keywords_only):
    shape = shape_keywords_only()

    blend_mode = (1, 1)
    shape.blend_mode = blend_mode
    assert shape._group.blend_src == 1  # noqa: SLF001
    assert shape._group.blend_dest == 1  # noqa: SLF001
