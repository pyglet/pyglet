from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

from pyglet.customtypes import RGBColor, RGBAColor

HorizontalAlignment: TypeAlias = Literal["left", "center", "right"]
VerticalAlignment: TypeAlias = Literal["bottom", "center", "top"]
ContentAlignment: TypeAlias = tuple[HorizontalAlignment, VerticalAlignment]
AxisFlags: TypeAlias = tuple[bool, bool]
Padding: TypeAlias = tuple[float, float, float, float]
CellMargin: TypeAlias = tuple[float, float]
LayoutSize: TypeAlias = int | float | str | None
Color: TypeAlias = RGBColor | RGBAColor


def _padding(value: float | Padding) -> Padding:
    return (value,) * 4 if isinstance(value, (int, float)) else value


def _axis_flags(value: bool | AxisFlags) -> AxisFlags:
    return (value, value) if isinstance(value, bool) else value


def _alignment(value: str | ContentAlignment) -> ContentAlignment:
    return (value, value) if isinstance(value, str) else value  # type: ignore[return-value]


def _margin(value: float | CellMargin) -> CellMargin:
    return (value, value) if isinstance(value, (int, float)) else value


@dataclass
class WidgetStyle:
    """Common visual style fields shared by GUI components."""

    background: Color | Any | None = None


@dataclass
class LayoutCellStyle(WidgetStyle):
    """Style for one layout cell and its contained object."""

    padding: int | float | Padding = 0
    stretch_content: bool | AxisFlags = False
    content_alignment: str | ContentAlignment = "center"

    def __post_init__(self) -> None:
        self.padding = _padding(self.padding)
        self.stretch_content = _axis_flags(self.stretch_content)
        self.content_alignment = _alignment(self.content_alignment)


@dataclass
class LayoutStyle(LayoutCellStyle):
    """Style for a layout and the cells it creates."""

    cell_margin: int | float | CellMargin = 1
    cell_background: Color | Any | None = None
    cell_padding: int | float | Padding = 0
    cell_stretch_content: bool | AxisFlags = False
    cell_content_alignment: str | ContentAlignment = "center"
    row_size: LayoutSize = None
    column_size: LayoutSize = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.cell_margin = _margin(self.cell_margin)
        self.cell_padding = _padding(self.cell_padding)
        self.cell_stretch_content = _axis_flags(self.cell_stretch_content)
        self.cell_content_alignment = _alignment(self.cell_content_alignment)


@dataclass
class ButtonStyle(WidgetStyle):
    """Base style for button widgets, reserved for shared button properties."""


@dataclass
class TextButtonStyle(ButtonStyle):
    """Colors used by :class:`~pyglet.gui.TextButton` interaction states."""

    pressed_color: Color = (255, 0, 0)
    unpressed_color: Color = (255, 255, 255)
    hover_color: Color = (0, 255, 0)
