from typing import Tuple
from unittest.mock import MagicMock
import pytest
import pyglet
from . import get_fake_shader_program


# We don't need a real GL context for unit tests
pyglet.sprite.get_default_shader = get_fake_shader_program


@pytest.fixture
def dummy_sprite():
    """A sprite at 0, 0 with no image data.

    The fact that there's no image data doesn't matter because these
    tests never touch a real GL context which would check for it.
    """
    return pyglet.sprite.Sprite(MagicMock())


def _new_val_or_none(dimension_index: int = 0) -> Tuple[float, None]:
    return float(dimension_index + 1), None


@pytest.fixture(params=_new_val_or_none())
def x(request):
    return request.param


@pytest.fixture(params=_new_val_or_none(1))
def y(request):
    return request.param


@pytest.fixture(params=_new_val_or_none(2))
def z(request):
    return request.param


@pytest.fixture(params=_new_val_or_none(3))
def scale(request):
    return request.param


@pytest.fixture(params=_new_val_or_none(4))
def scale_x(request):
    return request.param


@pytest.fixture(params=_new_val_or_none(5))
def scale_y(request):
    return request.param


def test_update_sets_passed_positions(dummy_sprite, x, y, z):

    dummy_sprite.update(x=x, y=y, z=z)

    if x is not None:
        assert dummy_sprite.x == x

    if y is not None:
        assert dummy_sprite.y == y

    if z is not None:
        assert dummy_sprite.z == z


def test_update_leaves_unpassed_translations_alone(dummy_sprite, x, y, z):
    dummy_sprite.update(x=x, y=y, z=z)

    if x is None:
        assert dummy_sprite.x == 0

    if y is None:
        assert dummy_sprite.y == 0

    if z is None:
        assert dummy_sprite.z == 0


def test_update_sets_passed_scales(dummy_sprite, scale, scale_x, scale_y):
    dummy_sprite.update(scale=scale, scale_x=scale_x, scale_y=scale_y)

    if scale is not None:
        assert dummy_sprite.scale == scale

    if scale_x is not None:
        assert dummy_sprite.scale_x == scale_x

    if scale_y is not None:
        assert dummy_sprite.scale_y == scale_y


def test_update_leaves_unpassed_scales_alone(dummy_sprite, x, y, z):
    dummy_sprite.update(x=x, y=y, z=z)

    if x is None:
        assert dummy_sprite.x == 0

    if y is None:
        assert dummy_sprite.y == 0

    if z is None:
        assert dummy_sprite.z == 0


def test_update_sets_rotation_when_passed(dummy_sprite):
    dummy_sprite.update(rotation=3.0)
    assert dummy_sprite.rotation == 3.0


def test_update_leaves_rotation_alone_when_none(dummy_sprite):
    dummy_sprite.update()
    assert dummy_sprite.rotation == 0
