"""Holds type aliases used throughout the codebase."""
import ctypes
from typing import Tuple, Union

number = Union[int, float]
Point2D = Tuple[number, number]
Point3D = Tuple[number, number, number]
Color = Union[Tuple[int, int, int], Tuple[int, int, int, int]]
# Backwards compatible placeholder for `collections.abc.Buffer` from Python 3.12
Buffer = Union[bytes, bytearray, memoryview, ctypes.Array]

__all__ = ("number", "Point2D", "Point3D", "Color", "Buffer")
