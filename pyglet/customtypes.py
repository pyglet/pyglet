"""Holds type aliases used throughout the codebase."""
import ctypes
import sys

from typing import Union, TYPE_CHECKING, Protocol, TypeVar

__all__ = [
    'R',
    "Buffer",
    'ByteString',
    'CallableArgsKwargs'
]


R = TypeVar('R')


# Backwards compatible placeholder for `collections.abc.Buffer` from Python 3.12
Buffer = Union[bytes, bytearray, memoryview, ctypes.Array]


# Handle deprecation of ByteString since 3.9
if TYPE_CHECKING or sys.version_info >= (3, 14):
    ByteString = Union[bytes, bytearray, memoryview]
else:
    from typing import ByteString


class CallableArgsKwargs(Protocol[R]):
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
        ...
