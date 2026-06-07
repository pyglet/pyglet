"""Holds type aliases used throughout the codebase."""
from __future__ import annotations
import ctypes
import sys

from typing import Union, Literal, Type, Protocol, Tuple, runtime_checkable

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

MediaTypes = Literal["audio", "video", "image"]

Number = Union[int, float]

RGBColor = Tuple[int, int, int]
RGBAColor = Tuple[int, int, int, int]

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



@runtime_checkable
class ScissorProtocol(Protocol):
    """Protocol for an object that holds information for scissor states."""

    @property
    def area(self) -> tuple[int, int, int, int]:
        """Return the region of the scissor area.

        Requires the x, y, width, and height in screen space coordinates.
        """



__all__ = [
    "AnchorX",
    "AnchorY",
    "Buffer",
    "CType",
    "CTypesPointer",
    "ContentVAlign",
    "DataTypes",
    "HorizontalAlign",
    "MediaTypes",
    "RGBAColor",
    "RGBColor",
    "ScissorProtocol",
]
