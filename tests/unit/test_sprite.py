from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import pyglet


@pytest.fixture(autouse=True)
def monkeypatch_default_sprite_shader(monkeypatch, get_dummy_shader_program):
    """Use a dummy shader when testing non-drawing functionality"""
    monkeypatch.setattr('pyglet.sprite.get_default_shader', get_dummy_shader_program)


@pytest.fixture()
def sprite():
    """A sprite with no image data.

    It is created at a non-zero position so that the update method can
    be verified as working when passed zero positions (Issue #673).
    Scale values do not need to be set to 0 in the fixture as they are
    all 1.0 by default.

    The lack of image data doesn't matter because these tests never touch
    a real GL context which would require it.
    """
    sprite = pyglet.sprite.Sprite(MagicMock(), x=1, y=2, z=3)
    sprite.rotation = 90

    return sprite


@pytest.fixture()
def batched_sprite():
    """A sprite with no image data, but is initially added to a batch.

    It is created at a non-zero position so that the update method can
    be verified as working when passed zero positions (Issue #673).
    Scale values do not need to be set to 0 in the fixture as they are
    all 1.0 by default.

    The lack of image data doesn't matter because these tests never touch
    a real GL context which would require it.
    """
    from pyglet.graphics import Batch
    sprite = pyglet.sprite.Sprite(MagicMock(), x=1, y=2, z=3, batch=Batch())
    sprite.rotation = 90

    return sprite


def _new_or_none(new_value: float = 0.0) -> tuple[float, None]:
    return new_value, None


@pytest.fixture(params=_new_or_none())
def x(request):
    return request.param


@pytest.fixture(params=_new_or_none())
def y(request):
    return request.param


@pytest.fixture(params=_new_or_none())
def z(request):
    return request.param


@pytest.fixture(params=_new_or_none())
def scale(request):
    return request.param


@pytest.fixture(params=_new_or_none())
def scale_x(request):
    return request.param


@pytest.fixture(params=_new_or_none())
def scale_y(request):
    return request.param


def test_color_initially_rgba_white(sprite):
    assert sprite.color == (255, 255, 255, 255)


def test_opacity_initially_255(sprite):
    assert sprite.opacity == 255

def test_color_changes_opacity_if_set_to_rgba(sprite, new_rgba_color):
    sprite.color = new_rgba_color
    assert sprite.opacity == new_rgba_color[3]


def test_color_leaves_opacity_unchanged_if_set_to_rgb(sprite, new_rgb_color):
    sprite.color = new_rgb_color
    assert sprite.opacity == 255


def test_color_changes_rgb_channels(sprite, new_rgb_or_rgba_color):
    sprite.color = new_rgb_or_rgba_color
    assert sprite.color[:3] == new_rgb_or_rgba_color[:3]


def test_opacity_setter_changes_opacity_channel_in_color(sprite, new_opacity_set_opacity_alone):
    sprite.opacity = new_opacity_set_opacity_alone
    assert sprite.color[3] == new_opacity_set_opacity_alone


def test_update_sets_passed_positions(sprite, x, y, z):
    sprite.update(x=x, y=y, z=z)

    if x is not None:
        assert sprite.x == x

    if y is not None:
        assert sprite.y == y

    if z is not None:
        assert sprite.z == z


def test_update_leaves_none_translations_alone(sprite, x, y, z):
    o_x, o_y, o_z = sprite.x, sprite.y, sprite.z

    sprite.update(x=x, y=y, z=z)

    if x is None:
        assert sprite.x == o_x

    if y is None:
        assert sprite.y == o_y

    if z is None:
        assert sprite.z == o_z


def test_update_sets_passed_scales(sprite, scale, scale_x, scale_y):
    sprite.update(scale=scale, scale_x=scale_x, scale_y=scale_y)

    if scale is not None:
        assert sprite.scale == scale

    if scale_x is not None:
        assert sprite.scale_x == scale_x

    if scale_y is not None:
        assert sprite.scale_y == scale_y


def test_update_leaves_none_scales_alone(sprite, scale, scale_x, scale_y):
    o_scale, o_scale_x, o_scale_y = sprite.scale, sprite.scale_x, sprite.scale_y

    sprite.update(scale=scale, scale_x=scale_x, scale_y=scale_y)

    if scale is None:
        assert sprite.scale == o_scale

    if scale_x is None:
        assert sprite.scale_x == o_scale_x

    if scale_y is None:
        assert sprite.scale_y == o_scale_y


def test_update_sets_rotation_when_passed(sprite):
    sprite.update(rotation=0.0)
    assert sprite.rotation == 0.0


def test_update_leaves_rotation_alone_when_none(sprite):
    sprite.update()
    assert sprite.rotation == 90


@pytest.mark.parametrize('fixture', ['sprite', 'batched_sprite'])
def test_group_setter(request, fixture):
    _sprite = request.getfixturevalue(fixture)
    from pyglet.graphics import Group
    new_group = Group()
    # Patch since magicmock returns functions for class variables...
    with patch.multiple(_sprite._vertex_list, indexed=True, instanced=False):  # noqa: SLF001
        _sprite.group = new_group

        assert _sprite.group is new_group


@pytest.mark.parametrize('fixture', ['sprite', 'batched_sprite'])
def test_batch_setter(request, fixture):
    _sprite = request.getfixturevalue(fixture)
    from pyglet.graphics import Batch
    new_batch = Batch()
    with patch.multiple(_sprite._vertex_list, indexed=True, instanced=False):  # noqa: SLF001
        _sprite.batch = new_batch
        assert _sprite.batch is new_batch


@pytest.mark.parametrize('fixture', ['sprite', 'batched_sprite'])
def test_program_setter(request, fixture):
    _sprite = request.getfixturevalue(fixture)

    program = MagicMock()
    with patch.multiple(_sprite._vertex_list, indexed=True, instanced=False):  # noqa: SLF001
        _sprite.program = program
        assert _sprite.program == program


@pytest.mark.parametrize('fixture', ['sprite', 'batched_sprite'])
def test_blend_setter(request, fixture):
    _sprite = request.getfixturevalue(fixture)

    blend_mode = (1, 1)
    with patch.multiple(_sprite._vertex_list, indexed=True, instanced=False):  # noqa: SLF001
        _sprite.blend_mode = blend_mode
        assert _sprite._group.blend_src == 1  # noqa: SLF001
        assert _sprite._group.blend_dest == 1  # noqa: SLF001
