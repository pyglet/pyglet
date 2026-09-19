"""Vertex attribute descriptions and geometry-owned storage layouts."""


from __future__ import annotations

import ctypes
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyglet.customtypes import CType, DataTypes

DataTypeTuple = ('?', 'f', 'd', 'i', 'I', 'h', 'H', 'b', 'B', 'q', 'Q')
_vertex_format_pattern = re.compile(r"(?P<components>[1-4])(?P<data_type>[?fihHbBIqdQ])"
                                   r"(?P<normalized>n?)(?:/(?P<divisor>[0-9]+))?")
_data_type_to_ctype = {
    '?': ctypes.c_bool, 'b': ctypes.c_byte, 'B': ctypes.c_ubyte,
    'h': ctypes.c_short, 'H': ctypes.c_ushort, 'i': ctypes.c_int,
    'I': ctypes.c_uint, 'f': ctypes.c_float, 'd': ctypes.c_double,
    'q': ctypes.c_longlong, 'Q': ctypes.c_ulonglong,
}


class VertexLayout:
    """Describe the storage format and input rate of vertex attributes.

    Attributes can be specified using compact format strings or explicit
    :class:`AttributeFormat` instances.

    Format strings consist of a component count, data type, optional
    normalization flag, and optional instance divisor::

        "<components><type>[n][/<divisor>]"

    For example::

        VertexLayout(
            position="2f",
            colors="4Bn",
            translation="3f/1",
            variant="1I/4",
        )

    The component count specifies how many values make up the attribute.
    The data type specifies the storage type of each component. A trailing
    ``n`` marks integer data as normalized.

    The optional divisor controls the attribute input rate. A divisor of
    ``0`` (the default) advances once per vertex. A divisor of ``1`` advances
    once per instance, and values greater than ``1`` advance once every that
    many instances.
    """

    __slots__ = ("_attribute_formats", "_has_divisors", "_key")

    def __init__(self, **formats: str | AttributeFormat) -> None:
        attributes: dict[str, AttributeFormat] = {}

        divisors = False
        for name, value in formats.items():
            if isinstance(value, AttributeFormat):
                if value.name != name:
                    value = AttributeFormat(
                        name,
                        value.components,
                        value.data_type,
                        value.normalized,
                        value.divisor,
                    )

                attributes[name] = value
                continue

            if not isinstance(value, str):
                msg = (
                    f"Vertex format for attribute '{name!r}' must be a "
                    f"str or AttributeFormat, got {type(value).__name__}."
                )
                raise TypeError(msg)

            match = _vertex_format_pattern.fullmatch(value)
            if match is None:
                msg = (
                    f"Invalid vertex format '{value!r}' for attribute '{name!r}'. "
                    "Expected 1-4 components followed by a data type string, "
                    "optional 'n' normalization flag, and optional '/divisor'. "
                    "For example: '4Bn' or '3f/1'."
                )
                raise ValueError(msg)

            divisor = int(match["divisor"] or 0)
            attributes[name] = AttributeFormat(
                name,
                int(match["components"]),
                match["data_type"],  # type: ignore[arg-type]
                bool(match["normalized"]),
                divisor,
            )
            if divisor:
                divisors = True

        self._attribute_formats = MappingProxyType(attributes)
        self._has_divisors = divisors

        self._key = tuple(
            attribute.key
            for attribute in sorted(
                attributes.values(),
                key=lambda attribute: attribute.name,
            )
        )

    @property
    def has_divisors(self) -> bool:
        """Geometry contains divisors for instancing."""
        return self._has_divisors

    @property
    def attribute_formats(self) -> Mapping[str, AttributeFormat]:
        """Geometry attribute formats in this layout."""
        return self._attribute_formats

    @property
    def key(self) -> tuple:
        """Stable geometry-only identity used for domain lookup."""
        return self._key

    def with_divisors(self, **divisors: int) -> VertexLayout:
        """Return a copy with the specified attribute divisors."""
        attributes = dict(self._attribute_formats)

        for name, divisor in divisors.items():
            if divisor < 0:
                msg = f"Instance divisor for '{name!r}' must not be negative."
                raise ValueError(msg)

            try:
                attributes[name] = attributes[name].with_divisor(divisor)
            except KeyError:
                msg = f"Attribute '{name!r}' is not part of this VertexLayout."
                raise ValueError(msg) from None

        return type(self)(**attributes)


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
