# Separate some structure types from the lib to prevent circular imports, as dwrite/d2d render targets use these too.
from __future__ import annotations

from ctypes import Structure
from ctypes.wintypes import FLOAT, LONG

from pyglet.libs.win32 import UINT32


class D2D1_SIZE_F(Structure):
    _fields_ = [
        ("width", FLOAT),
        ("height", FLOAT),
    ]


class D2D1_SIZE_U(Structure):
    _fields_ = [
        ("width", UINT32),
        ("height", UINT32),
    ]

class D2D1_POINT_2L(Structure):
    _fields_ = [
        ("x", LONG),
        ("y", LONG),
    ]

class D2D1_POINT_2F(Structure):
    _fields_ = [
        ("x", FLOAT),
        ("y", FLOAT),
    ]

class D2D1_COLOR_F(Structure):
    _fields_ = (
        ("r", FLOAT),
        ("g", FLOAT),
        ("b", FLOAT),
        ("a", FLOAT),
    )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(r={self.r}, g={self.g}, b={self.b}, a={self.a})"


class D2D_POINT_2F(Structure):
    _fields_ = (
        ("x", FLOAT),
        ("y", FLOAT),
    )


class D2D1_RECT_F(Structure):
    _fields_ = (
        ("left", FLOAT),
        ("top", FLOAT),
        ("right", FLOAT),
        ("bottom", FLOAT),
    )
