from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

from pyglet.customtypes import RGBColor, RGBAColor

HorizontalAlignment: TypeAlias = Literal["left", "center", "right"]
VerticalAlignment: TypeAlias = Literal["bottom", "center", "top"]
ContentAlignment: TypeAlias = tuple[HorizontalAlignment, VerticalAlignment]
AxisFlags: TypeAlias = tuple[bool, bool]
Padding: TypeAlias = tuple[int, int, int, int]
CellMargin: TypeAlias = tuple[float, float]
LayoutSize: TypeAlias = int | float | str | None
Color: TypeAlias = RGBColor | RGBAColor


def _padding(value: int | Padding) -> Padding:
    return (value,) * 4 if isinstance(value, int) else value


def _axis_flags(value: bool | AxisFlags) -> AxisFlags:
    return (value, value) if isinstance(value, bool) else value


def _alignment(value: str | ContentAlignment) -> ContentAlignment:
    return (value, value) if isinstance(value, str) else value  # type: ignore[return-value]


def _margin(value: float | CellMargin) -> CellMargin:
    return (value, value) if isinstance(value, (int, float)) else value


@dataclass
class WidgetStyle:
    """Common visual style fields shared by GUI components."""

    #: RGB/RGBA background color, a drawable background object, or ``None``.
    background: Color | Any | None = None


@dataclass
class LayoutCellStyle(WidgetStyle):
    """Style for one layout cell and its contained object."""

    #: Interior spacing as one integer or ``(top, right, bottom, left)``.
    padding: int | Padding = 0
    #: One boolean or ``(horizontal, vertical)`` flags for content stretching.
    stretch_content: bool | AxisFlags = False
    #: A horizontal value or ``(horizontal, vertical)`` content alignment tuple.
    content_alignment: str | ContentAlignment = "center"

    def __post_init__(self) -> None:
        self.padding = _padding(self.padding)
        self.stretch_content = _axis_flags(self.stretch_content)
        self.content_alignment = _alignment(self.content_alignment)


@dataclass
class LayoutStyle(LayoutCellStyle):
    """Style for a layout and the cells it creates."""

    #: Spacing between cells as one number or ``(horizontal, vertical)``.
    cell_margin: int | float | CellMargin = 1
    #: RGB/RGBA color, drawable object, or ``None`` for each cell background.
    cell_background: Color | Any | None = None
    #: Default cell padding as one integer or ``(top, right, bottom, left)``.
    cell_padding: int | Padding = 0
    #: Default cell content stretching flags.
    cell_stretch_content: bool | AxisFlags = False
    #: Default cell content alignment.
    cell_content_alignment: str | ContentAlignment = "center"
    #: Number, ``"Npx"``, ``"N%"``, or ``None`` for flexible row sizing.
    row_size: LayoutSize = None
    #: Number, ``"Npx"``, ``"N%"``, or ``None`` for flexible column sizing.
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

    #: RGB/RGBA text color while the button is pressed.
    pressed_color: Color = (255, 0, 0)
    #: RGB/RGBA text color while the button is idle.
    unpressed_color: Color = (255, 255, 255)
    #: RGB/RGBA text color while the button is hovered.
    hover_color: Color = (0, 255, 0)
