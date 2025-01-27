"""Holds type aliases used throughout the codebase."""
import ctypes
import sys

from typing import Union, Literal, Type

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


__all__ = [
    "Buffer", "HorizontalAlign", "AnchorX", "AnchorY", "ContentVAlign", "DataTypes", "CType", "CTypesPointer",
]
