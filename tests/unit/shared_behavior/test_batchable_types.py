import importlib
import inspect
import re
from dataclasses import dataclass, field
from functools import partial, lru_cache
from typing import Optional, Iterable, Callable, Tuple, Any, List, Union
from types import ModuleType as Module

import pytest

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
    (Polygon, ((0, 0), (1, 1), (2, 2)))
])
def tested_instance_factory_args(request) -> Tuple[Callable, Tuple[Any, ...]]:
    return request.param


SHADER_GETTER_PATTERN = re.compile(r"^get(_[a-zA-Z0-9]+)*_shader$")


def is_shader_getter(c: Callable) -> bool:

    if not hasattr(c, "__name__"):
        return False

    name = c.__name__
    if SHADER_GETTER_PATTERN.fullmatch(name):
        if not callable(c):
            raise TypeError("{c} is not callable despite being named like a shader getter")
        return True

    return False


@dataclass(frozen=True)
class PatchTarget:
    """
    Specify targets for monkeypatching shader getters.

    When only the module prefix is defined, anything object located in a
    module starting with `module_prefix` will have members matching the
    regex above monkeypatched with the get_dummy_shader_program top-level
    fixture.

    If module_targets is defined, the target modules will have members
    matching the regex patched instead.

    If function_targets is defined, only the named functions will be
    monkeypatched during the test.
    """
    module_prefix: str = field()
    module_targets: Optional[Iterable[str]] = field(default=None)


# A more general usecase would use a trie, but this is fine for n = 3 since we cache per type
SHADER_PATCH_TARGETS = [
    PatchTarget('pyglet.shapes'),
    PatchTarget('pyglet.text', module_targets=('pyglet.text.layout',)),
    PatchTarget('pyglet.sprite')
]


@lru_cache
def _module_and_name(src: Union[str, Module]) -> Tuple[Module, str]:

    if isinstance(src, Module):
        return src, src.__name__
    elif isinstance(src, str):
        module = importlib.import_module(src)
        return module, src

    raise TypeError(f"Expected module or string, not {src!r}")


@lru_cache
def patch_targets_for_module(module: Union[str, Module]) -> List[str]:
    """
    Return a list of shader getters targets for a module, including the module.

    Args:
        module: The module to search as either a string or a bare module.

    Returns:
        A list of full monkeypatch targets.
    """
    module, module_name = _module_and_name(module)

    full_monkeypatch_targets = []

    for member_name, value in inspect.getmembers(module, is_shader_getter):
       full_monkeypatch_targets.append(f"{module_name}.{member_name}")

    return full_monkeypatch_targets


@lru_cache
def _get_targets_for_callable(c: Callable) -> List[str]:

    # Preflight check
    if not callable(c):
        raise TypeError(f"First arg must be callable and preferably a type, not {c}")

    if not (parent_module := inspect.getmodule(c)):
        raise ValueError(f"Couldn't get module object for {c!r}")

    # Acceptable performance implementation for the moment
    parent_module_name = parent_module.__name__

    targets = []

    for entry in SHADER_PATCH_TARGETS:
        prefix = entry.module_prefix

        if parent_module_name.startswith(prefix):
            # Use the prefix module if no module targets were defined
            target_modules = entry.module_targets if entry.module_targets else [prefix]
            for target_module in target_modules:
                targets += patch_targets_for_module(target_module)

    return targets

def get_patch_targets(object: Any) -> List[str]:
    return _get_targets_for_callable(object if isinstance(object, type) else object.__class__)


@pytest.fixture(autouse=True)
def monkeypatch_shaders(tested_instance_factory_args, monkeypatch, get_dummy_shader_program):
    first_arg = tested_instance_factory_args[0]

    targets = get_patch_targets(first_arg)

    for target in targets:
        monkeypatch.setattr(target, get_dummy_shader_program)


@pytest.fixture
def instance_factory(tested_instance_factory_args):
    factory, positional_args = tested_instance_factory_args
    return partial(factory, *positional_args)


@pytest.fixture()
def rgb_or_rgba_shape(instance_factory, original_rgb_or_rgba_color):
    return instance_factory(color=original_rgb_or_rgba_color)


@pytest.fixture
def rgba_shape(instance_factory):
    return instance_factory(color=(0, 255, 0, 37))


def test_init_sets_opacity_from_rgba_value_as_color_argument(rgba_shape):
    assert rgba_shape.opacity == 37


def test_init_sets_opacity_to_255_for_rgb_value_as_color_argument(instance_factory):
    assert instance_factory(color=(0, 0, 0)).opacity == 255


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
