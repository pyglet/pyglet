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
def x_update_value(request):
    return request.param


@pytest.fixture(params=_new_val_or_none(1))
def y_update_value(request):
    return request.param


@pytest.fixture(params=_new_val_or_none(2))
def z_update_value(request):
    return request.param


def test_update_sets_passed_positions(dummy_sprite, x_update_value, y_update_value, z_update_value):

    dummy_sprite.update(x=x_update_value, y=y_update_value, z=z_update_value)

    if x_update_value is not None:
        assert dummy_sprite.x == x_update_value

    if y_update_value is not None:
        assert dummy_sprite.y == y_update_value

    if z_update_value is not None:
        assert dummy_sprite.z == z_update_value


def test_update_leaves_unpassed_attributes_alone(dummy_sprite, x_update_value, y_update_value, z_update_value):
    dummy_sprite.update(x=x_update_value, y=y_update_value, z=z_update_value)

    if x_update_value is None:
        assert dummy_sprite.x == 0

    if y_update_value is None:
        assert dummy_sprite.y == 0

    if z_update_value is None:
        assert dummy_sprite.z == 0
