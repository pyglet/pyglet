"""Holds type aliases used throughout the codebase."""
import ctypes
from typing import Tuple, TypeVar, Union

number = TypeVar("number", int, float)
Color = TypeVar("color", bound=Union[Tuple[int, int, int], Tuple[int, int, int, int]])
Point2D = TypeVar("Point2D", bound=Tuple[number, number])
Point3D = TypeVar("Point3D", bound=Tuple[number, number, number])
# Backwards compatible placeholder for `collections.abc.Buffer` from Python 3.12
Buffer = Union[bytes, bytearray, memoryview, ctypes.Array]

__all__ = ("number", "Color", "Point2D", "Point3D", "Buffer")
