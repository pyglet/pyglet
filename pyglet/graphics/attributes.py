"""Vertex attribute descriptions and geometry-owned storage layouts."""
from __future__ import annotations

import ctypes
import re
from dataclasses import dataclass
from typing import Any

from pyglet.customtypes import CType, DataTypes

DataTypeTuple = ('?', 'f', 'i', 'I', 'h', 'H', 'b', 'B', 'q', 'Q')
_data_type_to_ctype = {
    '?': ctypes.c_bool, 'b': ctypes.c_byte, 'B': ctypes.c_ubyte,
    'h': ctypes.c_short, 'H': ctypes.c_ushort, 'i': ctypes.c_int,
    'I': ctypes.c_uint, 'f': ctypes.c_float, 'd': ctypes.c_double,
    'q': ctypes.c_longlong, 'Q': ctypes.c_ulonglong,
}


@dataclass(frozen=True)
class VertexLayout:
    """Complete geometry-owned vertex buffer formats, such as ``"4Bn"``."""
    formats: dict[str, str]

    def __init__(self, **formats: str) -> None:
        for name, fmt in formats.items():
            if not isinstance(fmt, str) or re.fullmatch(r"[1-4][?fihHbBIqdQ]n?", fmt) is None:
                msg = (f"Invalid vertex format {fmt!r} for attribute {name!r}.\n"
                       f"Expecting 1-4, followed by a format string and optional 'n' normalization flag.\n"
                       f"For example: '4Bn' would mean four values, as bytes (0-255), normalized.")
                raise ValueError(msg)
        object.__setattr__(self, 'formats', formats)


@dataclass(frozen=True)
class AttributeFormat:
    name: str
    components: int
    data_type: DataTypes
    normalized: bool
    divisor: int

    @property
    def is_instanced(self) -> bool:
        return self.divisor != 0


@dataclass(frozen=True)
class AttributeView:
    offset: int
    stride: int


class Attribute:
    fmt: AttributeFormat
    element_size: int
    c_type: CType
    location: int

    def __init__(self, name: str, location: int, components: int, data_type: DataTypes,
                 normalize: bool = False, divisor: int = 0) -> None:
        self.fmt = AttributeFormat(name, components, data_type, normalize, divisor)
        self.location = location
        self.c_type = _data_type_to_ctype[data_type]
        self.element_size = ctypes.sizeof(self.c_type)

    def set_data_type(self, data_type: DataTypes, normalize: bool) -> None:
        self.fmt = AttributeFormat(self.fmt.name, self.fmt.components, data_type, normalize, self.fmt.divisor)
        self.c_type = _data_type_to_ctype[data_type]
        self.element_size = ctypes.sizeof(self.c_type)

    def set_divisor(self, divisor: int) -> None:
        self.fmt = AttributeFormat(self.fmt.name, self.fmt.components, self.fmt.data_type, self.fmt.normalized, divisor)

    @property
    def key(self) -> tuple[str, int, int, DataTypes, bool, int]:
        return self.fmt.name, self.location, self.fmt.components, self.fmt.data_type, self.fmt.normalized, self.fmt.divisor


class GraphicsAttribute:
    def __init__(self, attribute: Attribute, view: AttributeView) -> None:
        self.attribute = attribute
        self.view = view

    def enable(self) -> None: raise NotImplementedError
    def disable(self) -> None: raise NotImplementedError
    def set_pointer(self) -> None: raise NotImplementedError
    def set_divisor(self) -> None: raise NotImplementedError


@dataclass(frozen=True)
class DomainAttributes:
    """Vertex attributes together with their stable domain lookup key."""
    attributes: dict[str, Any]
    key: str

    @classmethod
    def from_attributes(cls, attributes: dict[str, Any], key: str | None = None) -> DomainAttributes:
        if key is None:
            key = str(tuple(attribute.key for attribute in sorted(attributes.values(), key=lambda attribute: attribute.location)))
        return cls(attributes, key)
