"""Holds type aliases used throughout the codebase."""
import ctypes
import sys

from typing import Union

__all__ = [
    "Buffer",
]


if sys.version_info >= (3, 12):
    from collections.abc import Buffer
else:
    # Best-effort placeholder for older Python versions
    Buffer = Union[bytes, bytearray, memoryview, ctypes.Array]
