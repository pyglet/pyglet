"""Holds type aliases used throughout the codebase."""
import ctypes
import sys

from typing import Union, Literal


if sys.version_info >= (3, 12):
    from collections.abc import Buffer
else:
    # Best-effort placeholder for older Python versions
    Buffer = Union[bytes, bytearray, memoryview, ctypes.Array]

HorizontalAlign = Literal["left", "center", "right"]
AnchorX = Literal["left", "center", "right"]
AnchorY = Literal["top", "bottom", "center", "baseline"]
ContentVAlign = Literal["bottom", "center", "top"]



__all__ = [
    "Buffer", "HorizontalAlign", "AnchorX", "AnchorY", "ContentVAlign"
]
