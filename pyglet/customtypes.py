"""Holds type aliases used throughout the codebase."""
import ctypes

from typing import Union, Tuple, TypeVar

# just Number
Number = Union[int, float]

# Colors
Channel = TypeVar('Channel', int, float)

# Backwards compatible placeholder for `collections.abc.Buffer` from Python 3.12
Buffer = Union[bytes, bytearray, memoryview, ctypes.Array]

# Points
Point2D = Tuple[Number, Number]
Point3D = Tuple[Number, Number, Number]


RGB = Tuple[Channel, Channel, Channel]
RGBA = Tuple[Channel, Channel, Channel, Channel]

# Can be used as Color[int] or Color[float]
Color = Union[RGB[Channel], RGBA[Channel]]

# predefined Colors
RGB255 = RGB[int]
RGBFloat = RGB[float]

RGBA255 = RGBA[int]
RGBAFloat = RGBA[float]

Color255 = Color[int]
ColorFloat = Color[float]

__all__ = [
    'Number',
    'Channel',
    'Buffer',
    
    'Point2D',
    'Point3D',
    
    'RGB',
    'RGBA',
    'Color',
    
    'RGB255', 'RGBFloat',
    'RGBA255', 'RGBAFloat',
    'Color255', 'ColorFloat',
]
