"""Holds type aliases used throughout the codebase."""
import ctypes

from typing import Union


__all__ = [
    "Buffer"
]

# Backwards compatible placeholder for `collections.abc.Buffer` from Python 3.12
Buffer = Union[bytes, bytearray, memoryview, ctypes.Array]
