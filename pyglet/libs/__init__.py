"""Platform-specific support components.

These consist of:

1. ctypes bindings for datastructures and functions
2. pyglet-specific wrapper functions around raw ctypes calls
3. vendored libraries in original or modified forms

When documenting these modules:

1. Use minimal formatting in any docstrings
2. Leave licenses at the tops of files in place

Simple docstrings with minimal formatting are best because:

1. No web doc is built for pyglet.libs
2. The docstrings will be used to debug complex platform issues
3. IDEs mangle formatting in any hover tooltips while debugging
"""

from typing import NoReturn
from collections.abc import Callable, Sequence


class MissingFunctionException(Exception):  # noqa: N818
    def __init__(self, name: str, requires: str | None = None,
                 suggestions: Sequence[str] | None = None) -> None:
        msg = f'{name} is not exported by the available OpenGL driver.'
        if requires:
            msg += f'  {requires} is required for this functionality.'
        if suggestions:
            msg += '  Consider alternative(s) {}.'.format(', '.join(suggestions))
        Exception.__init__(self, msg)


def missing_function(name: str, requires: str | None = None,
                     suggestions: Sequence[str] | None = None) -> Callable:
    def MissingFunction(*_args, **_kwargs) -> NoReturn:  # noqa: ANN002, ANN003, N802
        raise MissingFunctionException(name, requires, suggestions)

    return MissingFunction


__all__ = ['MissingFunctionException', 'missing_function']
