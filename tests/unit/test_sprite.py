from typing import Tuple
from unittest.mock import MagicMock
import pytest
import pyglet
from . import get_fake_shader_program


# We don't need a real GL context for unit tests
pyglet.sprite.get_default_shader = get_fake_shader_program


@pytest.fixture
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


def _new_or_none(new_value: float = 0.0) -> Tuple[float, None]:
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

    sprite.update(x=x, y=y, z=z)

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
