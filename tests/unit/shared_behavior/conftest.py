import importlib
import inspect
import re
from dataclasses import dataclass, field
from functools import lru_cache, partial
from types import ModuleType as Module
from typing import Callable, Optional, Iterable, Union, Tuple, List, Any

import pytest


# IMPORTANT: You must define an instance_factory_template fixture!
#
#
# This fixture needs to return a Tuple[Callable, Tuple[Any, ...]].
# You can use the helpers in this file to do so.
#
# The second value in it needs to contain the positional arguments
# for the callable.


# Identify module elements which are likely to return shaders.
SHADER_GETTER_PATTERN = re.compile(r"^get(_[a-zA-Z0-9]+)*_shader$")


def is_shader_getter(c: Callable) -> bool:
    """Returns true if an item appears to be a shader getter.


    """
    if not (hasattr(c, "__name__") and SHADER_GETTER_PATTERN.fullmatch(c.__name__)):
        return False

    if not callable(c):
        raise TypeError(f"{c} is not callable despite being named like a shader getter")

    return True


@dataclass(frozen=True)
class PatchTarget:
    """Specify targets for monkeypatching shader getters.

    When only the module prefix is defined, anything object located in a
    module starting with `module_prefix` will have members matching the
    regex above monkeypatched with the get_dummy_shader_program top-level
    fixture.

    If module_targets is defined, the target modules will have members
    matching the regex patched instead.
    """
    module_prefix: str = field()
    module_targets: Optional[Iterable[str]] = field(default=None)


# This is suboptimal, but it's fine for now since:
# 1. O(n) is meaningless when n < 10
# 2. We can cache results
SHADER_PATCH_TARGETS = [
    PatchTarget('pyglet.shapes'),
    PatchTarget('pyglet.text', module_targets=('pyglet.text.layout',)),
    PatchTarget('pyglet.sprite')
]


@lru_cache
def _module_and_name(src: Union[str, Module]) -> Tuple[Module, str]:
    """Return both a module and its name when given either of the two.

    Args:
        src: A module or the path/name of a module, ie 'pyglet.shapes'

    Returns:
        A tuple of a module and its name.
    """
    if isinstance(src, Module):
        return src, src.__name__
    elif isinstance(src, str):
        module = importlib.import_module(src)
        return module, src

    raise TypeError(f"Expected module or string, not {src!r}")


@lru_cache
def _get_patch_targets_for_module(module: Union[str, Module]) -> List[str]:
    """Get a list of strings consisting of the module path and shader getter.

    For example::

        >>> _get_patch_targets_for_module('pyglet.shapes')
        ['pyglet.shapes.get_default_shader']

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
    """Look up patch targets for a callable by its declaring module.

    Args:
        c: the target callable, preferably a type.

    Returns:
        A list of patch targets identified.
    """
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
            target_modules = entry.module_targets or [prefix]

            # Patch all requested target modules
            for target_module in target_modules:
                targets += _get_patch_targets_for_module(target_module)

    return targets



@pytest.fixture(autouse=True)
def monkeypatch_shaders(instance_factory_template, monkeypatch, get_dummy_shader_program):
    """Automatically monkeypatch based on the factory method in the template.

    Args:
        instance_factory_template: A Tuple of a callable + positional args
        monkeypatch: pytests' monkeypatch fixture
        get_dummy_shader_program: a top-level shader for replacing
    """
    targets = _get_targets_for_callable(instance_factory_template[0])

    for target in targets:
        monkeypatch.setattr(target, get_dummy_shader_program)


@pytest.fixture
def instance_factory(instance_factory_template):
    factory, positional_args = instance_factory_template
    return partial(factory, *positional_args)


@pytest.fixture
def rgb_or_rgba_instance(instance_factory, original_rgb_or_rgba_color):
    return instance_factory(color=original_rgb_or_rgba_color)


@pytest.fixture
def rgb_instance(instance_factory, original_rgb_color):
    return instance_factory(color=original_rgb_color)


@pytest.fixture
def rgba_instance(instance_factory, original_rgba_color):
    return instance_factory(color=original_rgba_color)
