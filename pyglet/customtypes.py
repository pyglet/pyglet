"""Holds type aliases used throughout the codebase."""
from __future__ import annotations
import ctypes
import sys

from typing import Union, Literal, Type, Protocol, Tuple

from ctypes import _SimpleCData, _Pointer  # type: ignore  # noqa: PGH003

if sys.version_info >= (3, 12):
    from collections.abc import Buffer
else:
    # Best-effort placeholder for older Python versions
    Buffer = Union[bytes, bytearray, memoryview, ctypes.Array]

HorizontalAlign = Literal["left", "center", "right"]
AnchorX = Literal["left", "center", "right"]
AnchorY = Literal["top", "bottom", "center", "baseline"]
ContentVAlign = Literal["bottom", "center", "top"]

Number = Union[int, float]

RGBColor = Tuple[Number, Number, Number]
RGBAColor = Tuple[Number, Number, Number, Number]

DataTypes = Literal[
    'f',  # float
    'i',  # int
    'I',  # unsigned int
    'h',  # short
    'H',  # unsigned short
    'b',  # byte
    'B',  # unsigned byte
    'q',  # long long
    'Q',  # unsigned long long
    '?',  # bool
    'd',  # double
]

CType = Type[_SimpleCData]
CTypesPointer = _Pointer



class ScissorProtocol(Protocol):
    x: int
    y: int
    width: int
    height: int



__all__ = [
    "AnchorX",
    "AnchorY",
    "Buffer",
    "CType",
    "CTypesPointer",
    "ContentVAlign",
    "DataTypes",
    "HorizontalAlign",
    "RGBAColor",
    "RGBColor",
]
