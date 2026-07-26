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


# Regression tests for #887: Arc.__contains__ raised NotImplementedError,
# and Arc's rotation was applied twice (see also the fix to
# Arc._get_vertices, which removed a leftover manual rotation term).
class TestArcContains:

    def test_point_on_the_ring_is_contained(self):
        arc = Arc(0, 0, radius=10, thickness=1.0, angle=360.0)
        assert (10, 0) in arc

    def test_point_in_the_hole_is_not_contained(self):
        arc = Arc(0, 0, radius=10, thickness=1.0, angle=360.0)
        assert (0, 0) not in arc

    def test_point_far_outside_is_not_contained(self):
        arc = Arc(0, 0, radius=10, thickness=1.0, angle=360.0)
        assert (100, 100) not in arc

    def test_point_within_half_thickness_of_the_ring_is_contained(self):
        arc = Arc(0, 0, radius=10, thickness=1.0, angle=360.0)
        assert (9.6, 0) in arc

    def test_point_beyond_half_thickness_of_the_ring_is_not_contained(self):
        arc = Arc(0, 0, radius=10, thickness=1.0, angle=360.0)
        assert (9.0, 0) not in arc

    def test_point_inside_the_swept_angle_is_contained(self):
        arc = Arc(0, 0, radius=10, thickness=1.0, angle=90.0, start_angle=0.0)
        assert (7.0710678, 7.0710678) in arc  # 45 degrees, within [0, 90]

    def test_point_outside_the_swept_angle_is_not_contained(self):
        arc = Arc(0, 0, radius=10, thickness=1.0, angle=90.0, start_angle=0.0)
        assert (-10, 0) not in arc  # 180 degrees, outside [0, 90]

    def test_contains_tracks_a_single_rotation_like_other_shapes(self):
        """Rotating an Arc by 90 degrees should move its swept wedge by
        exactly 90 degrees (matching Sector's convention), not by 180
        degrees in the opposite direction as it did before this fix.
        """
        arc = Arc(0, 0, radius=10, thickness=1.0, angle=90.0, start_angle=0.0)
        arc.rotation = 90
        # The [0, 90] wedge, rotated -90 degrees, now covers [-90, 0].
        assert (0, -10) in arc   # -90 degrees: new start of the wedge
        assert (10, 0) in arc    # 0 degrees: new end of the wedge
        assert (0, 10) not in arc  # 90 degrees: outside the rotated wedge

    def test_local_vertices_do_not_depend_on_rotation(self):
        """Arc._get_vertices() computes local-space geometry; rotation is
        applied entirely by the shared shader-based rotation (like every
        other shape). Before this fix, Arc uniquely also subtracted
        self._rotation while building local vertices, applying rotation
        twice: once here, and again in the shader.
        """
        arc = Arc(0, 0, radius=10, thickness=1.0, angle=90.0, start_angle=30.0)
        unrotated = arc._get_vertices()  # noqa: SLF001
        arc.rotation = 45
        rotated = arc._get_vertices()  # noqa: SLF001
        assert rotated == unrotated
