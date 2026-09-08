from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TYPE_CHECKING


if TYPE_CHECKING:
    from pyglet.customtypes import RGBAColor


@dataclass(slots=True)
class DropShadow:
    """Style data for a text drop shadow.

    Args:
        offset: Pixel offset relative to the text.
        color: RGBA color or :class:`LinearGradient` of the shadow.
    """

    offset: tuple[int, int] = (1, -1)
    color: RGBAColor | LinearGradient = (0, 0, 0, 255)


@dataclass(slots=True)
class Stroke:
    """Style data for a text stroke.

    Args:
        size: Width of the stroke outside the glyph, in pixels.
        color: RGBA color or :class:`LinearGradient` of the stroke.
        join: Shape used where two straight contour segments meet.
    """

    size: float = 1.0
    color: RGBAColor | LinearGradient = (0, 0, 0, 255)
    join: Literal["miter", "round", "bevel"] = "round"

    def __post_init__(self) -> None:
        if self.join not in {"miter", "round", "bevel"}:
            msg = f"Unsupported stroke join: {self.join!r}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class LinearGradient:
    """A horizontal gradient used as a text ``color`` style.

    The gradient runs from the left to the right edge of each visual styled
    range. Wrapped ranges restart the gradient on each line.

    Args:
        start: RGBA color at the left edge.
        end: RGBA color at the right edge.
    """

    start: RGBAColor
    end: RGBAColor

    def __post_init__(self) -> None:
        if len(self.start) != 4 or len(self.end) != 4:
            msg = "LinearGradient colors require 4 values (R, G, B, A)."
            raise ValueError(msg)
