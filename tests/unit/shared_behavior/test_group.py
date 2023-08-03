from typing import Tuple, Callable, Dict, Any

import pytest

from pyglet.graphics import Group


@pytest.fixture(scope="module")
def instance_factory_template(shape_templates) -> Tuple[Callable, Dict[str, Any]]:
    return shape_templates


def test_group_setter(rgb_or_rgba_instance):
    new_group = Group()
    rgb_or_rgba_instance.group = new_group
    assert rgb_or_rgba_instance.group is new_group
