"""Vertex attribute descriptions and geometry-owned storage layouts."""
from __future__ import annotations

import ctypes
import re
from dataclasses import dataclass
from typing import Any

from pyglet.customtypes import CType, DataTypes

DataTypeTuple = ('?', 'f', 'd', 'i', 'I', 'h', 'H', 'b', 'B', 'q', 'Q')
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
    """Geometry-owned vertex attribute format."""

    name: str
    components: int
    data_type: DataTypes
    normalized: bool = False
    divisor: int = 0

    @property
    def is_instanced(self) -> bool:
        return self.divisor != 0

    @property
    def c_type(self) -> CType:
        return _data_type_to_ctype[self.data_type]

    @property
    def element_size(self) -> int:
        return ctypes.sizeof(self.c_type)

    @property
    def key(self) -> tuple[str, int, DataTypes, bool, int]:
        return self.name, self.components, self.data_type, self.normalized, self.divisor

    def with_data_type(self, data_type: DataTypes, normalized: bool) -> AttributeFormat:
        return AttributeFormat(self.name, self.components, data_type, normalized, self.divisor)

    def with_divisor(self, divisor: int) -> AttributeFormat:
        return AttributeFormat(self.name, self.components, self.data_type, self.normalized, divisor)


@dataclass(frozen=True)
class AttributeView:
    offset: int
    stride: int


@dataclass(frozen=True)
class ShaderAttribute:
    """Shader-introspected vertex input metadata."""

    name: str
    location: int
    components: int
    data_type: DataTypes
    shader_type: Any = None

    @property
    def is_integer(self) -> bool:
        return self.data_type in ('?', 'b', 'B', 'h', 'H', 'i', 'I', 'q', 'Q')

    @property
    def is_unsigned_integer(self) -> bool:
        return self.data_type in ('B', 'H', 'I', 'Q')

    @property
    def is_signed_integer(self) -> bool:
        return self.data_type in ('b', 'h', 'i', 'q')


# Kept as a compatibility alias for code that imports the old name.
Attribute = ShaderAttribute


class GraphicsAttribute:
    """API-specific geometry layout for an attribute buffer."""

    def __init__(self, attribute_format: AttributeFormat, view: AttributeView) -> None:
        self.fmt = attribute_format
        self.view = view


@dataclass(frozen=True)
class DomainAttributes:
    """Vertex attributes together with their stable domain lookup key."""
    attributes: dict[str, AttributeFormat]
    key: str

    @classmethod
    def from_attributes(cls, attributes: dict[str, AttributeFormat], key: str | None = None) -> DomainAttributes:
        if key is None:
            ordered = sorted(attributes.values(), key=lambda attribute: attribute.name)
            key = str(tuple(attribute.key for attribute in ordered))
        return cls(attributes, key)
