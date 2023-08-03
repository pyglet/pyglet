from typing import Tuple, Callable, Dict, Any

import pytest


@pytest.fixture(scope="module")
def instance_factory_template(shape_templates) -> Tuple[Callable, Dict[str, Any]]:
    return shape_templates


def test_setting_opacity_does_not_change_rgb_channels(rgb_or_rgba_instance, original_rgb_or_rgba_color):
    rgb_or_rgba_instance.opacity = 255
    assert rgb_or_rgba_instance.color[:3] == original_rgb_or_rgba_color[:3]


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

