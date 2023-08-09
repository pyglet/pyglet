from typing import Callable, Tuple, Any, Dict

import pytest

from pyglet.graphics import Batch


@pytest.fixture(scope="module")
def instance_factory_template(shape_templates) -> Tuple[Callable, Dict[str, Any]]:
    return shape_templates


def test_batch_setter(rgb_or_rgba_instance):
    new_batch = Batch()
    rgb_or_rgba_instance.batch = new_batch
    assert rgb_or_rgba_instance.batch is new_batch
