from typing import Tuple, Callable, Dict, Any

import pytest


@pytest.fixture(scope="module")
def instance_factory_template(shape_templates) -> Tuple[Callable, Dict[str, Any]]:
    return shape_templates


def test_init_sets_opacity_from_rgba_value_as_color_argument(rgba_instance, original_rgba_color):
    assert rgba_instance.opacity == original_rgba_color[3]


def test_init_sets_opacity_to_255_for_rgb_value_as_color_argument(rgb_instance, original_rgb_color):
    assert rgb_instance.opacity == 255