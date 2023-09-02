"""Holds type aliases used throughout the codebase."""
import ctypes

from typing import Union, Tuple, TypeVar

# just Number
Number = Union[int, float]

# Backwards compatible placeholder for `collections.abc.Buffer` from Python 3.12
Buffer = Union[bytes, bytearray, memoryview, ctypes.Array]

# Points
Point2D = Tuple[Number, Number]
Point3D = Tuple[Number, Number, Number]

# Colors
RGB = Tuple[int, int, int]
RGBA = Tuple[int, int, int, int]
Color = Union[RGB, RGBA]

__all__ = [
    'Number',
    'Buffer',
    
    'Point2D',
    'Point3D',
    
    'RGB',
    'RGBA',
    'Color',
]
