"""Holds type aliases used throughout the codebase."""
import ctypes
import sys

from typing import Union, Protocol, TypeVar, runtime_checkable

__all__ = [
    'R',
    'R_co',
    "Buffer",
    'CallableArgsKwargs'
]


R = TypeVar('R')
R_co = TypeVar('R_co', covariant=True)


if sys.version_info >= (3, 12):
    from collections.abc import Buffer
else:
    # Best-effort placeholder for older Python versions
    Buffer = Union[bytes, bytearray, memoryview, ctypes.Array]


@runtime_checkable
class CallableArgsKwargs(Protocol[R_co]):
    """3.8-friendly way of saying "a Callable taking *args & **kwargs."

    Use the R generic parameter to specify a return type::

        def report(
             *args,
             **kwargs,
             out_func: CallableArgsKwargs[None] = default
        ) -> None:
            out_func(*args, **kwargs)

    :py:class:`typing.Protocol` was added in Python 3.8, while
    :py:class:`typing.ParamSpec` was added in 3.10. We also can't
    use the ``typing_extensions`` backports due to the no hard
    dependencies rule.
    """

    def __call__(self, *args, **kwargs) -> R:
        raise NotImplementedError
