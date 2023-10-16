"""Holds type aliases used throughout the codebase."""
import ctypes
import sys

from typing import Union, TYPE_CHECKING

__all__ = [
    "Buffer",
    'ByteString'
]

# Backwards compatible placeholder for `collections.abc.Buffer` from Python 3.12
Buffer = Union[bytes, bytearray, memoryview, ctypes.Array]

# Handle deprecation of ByteString since 3.9
if TYPE_CHECKING or sys.version_info >= (3, 14):
    ByteString = Union[bytes, bytearray, memoryview]
else:
    from typing import ByteString
