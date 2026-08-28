"""Grid-based layout containers for GUI content.

The layout classes deliberately work with widgets, labels, sprites, and other
objects exposing ``position``, ``width``, and ``height``.  They do not own the
objects placed in their cells.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pyglet


class LayoutCell:
    """A rectangular layout cell, optionally containing one drawable object."""

    def __init__(self, style: Mapping[str, Any] | None = None, batch=None, group=None) -> None:
        self._content = None
        self._batch = batch
        self._group = group
        self._background = None
        self._rect = (0, 0, 1, 1)
        self._style: dict[str, Any] = {}
        self._span = (1, 1)
        self.set_style(style or {})
        self._set_style_if_none("stretch-content", False)
        self._set_style_if_none("content-alignment", "center")
        self._set_style_if_none("padding", 0)

    @property
    def x(self):
        return self._rect[0]

    @property
    def y(self):
        return self._rect[1]

    @property
    def position(self):
        return self.x, self.y

    @property
    def width(self):
        return self._rect[2]

    @property
    def height(self):
        return self._rect[3]

    @property
    def size(self):
        return self.width, self.height

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value) -> None:
        self._content = value
        self.realign()

    def set_style(self, data: Mapping[str, Any] | str, value: Any = None) -> None:
        """Set one style value or a mapping of style values."""
        if not isinstance(data, str):
            for key, item in data.items():
                self.set_style(key, item)
            return

        key = data
        if key == "background":
            self._style[key] = value
            self._update_background()
        elif key == "padding":
            if isinstance(value, (int, float)):
                value = (value,) * 4
            if len(value) != 4:
                raise ValueError("padding must be a number or (top, right, bottom, left)")
            for side, item in zip(("top", "right", "bottom", "left"), value):
                self._style[f"padding-{side}"] = item
            self._style[key] = tuple(value)
        elif key.startswith("padding-"):
            self._style[key] = value
            self._style["padding"] = tuple(
                self._style.get(f"padding-{side}", 0) for side in ("top", "right", "bottom", "left")
            )
        elif key == "stretch-content":
            if isinstance(value, bool):
                value = (value, value)
            self._style["stretch-content-x"], self._style["stretch-content-y"] = value
            self._style[key] = tuple(value)
        elif key.startswith("stretch-content-"):
            self._style[key] = value
            self._style["stretch-content"] = (
                self._style.get("stretch-content-x", False),
                self._style.get("stretch-content-y", False),
            )
        elif key == "content-alignment":
            if isinstance(value, str):
                value = (value, value)
            self._style["content-alignment-x"], self._style["content-alignment-y"] = value
            self._style[key] = tuple(value)
        elif key.startswith("content-alignment-"):
            self._style[key] = value
            self._style["content-alignment"] = (
                self._style.get("content-alignment-x", "center"),
                self._style.get("content-alignment-y", "center"),
            )
        else:
            self._style[key] = value
        self.realign()

    def get_style(self, key: str):
        return self._style.get(key)

    def _set_style_if_none(self, key: str, value: Any) -> None:
        if self.get_style(key) is None:
            self.set_style(key, value)

    def _update_background(self) -> None:
        background = self.get_style("background")
        if background is None:
            if self._background is not None and hasattr(self._background, "delete"):
                self._background.delete()
            self._background = None
        elif isinstance(background, tuple):
            if not isinstance(self._background, pyglet.shapes.Rectangle):
                if self._background is not None and hasattr(self._background, "delete"):
                    self._background.delete()
                self._background = pyglet.shapes.Rectangle(
                    0, 0, 0, 0, color=background, batch=self._batch, group=self._group
                )
            else:
                self._background.color = background
        else:
            self._background = background

    def realign(self, new_rect=None) -> None:
        if new_rect is not None:
            self._rect = tuple(new_rect)
            if self._background is not None:
                self._background.position = self.x, self.y
                self._background.width, self._background.height = self.width, self.height
        if self._content is None:
            return

        top, right, bottom, left = self.get_style("padding")
        stretch_x, stretch_y = self.get_style("stretch-content")
        align_x, align_y = self.get_style("content-alignment")
        if stretch_x:
            self._content.width = max(0, self.width - left - right)
        if stretch_y:
            self._content.height = max(0, self.height - top - bottom)
        content_width = self._content.width or 0
        content_height = self._content.height or 0
        x = {
            "left": self.x + left,
            "center": self.x + (self.width - content_width) / 2,
            "right": self.x + self.width - right - content_width,
        }.get(align_x)
        y = {
            "bottom": self.y + bottom,
            "center": self.y + (self.height - content_height) / 2,
            "top": self.y + self.height - top - content_height,
        }.get(align_y)
        if x is None or y is None:
            raise ValueError("content alignment must use left/center/right and bottom/center/top")
        try:
            self._content.position = x, y
        except (TypeError, ValueError):
            self._content.position = x, y, 0


class _SpanFiller:
    def __init__(self, cell: LayoutCell) -> None:
        self.cell = cell


class _Sequence:
    def __init__(self, margin: float = 0) -> None:
        self.margin_after = margin
        self.size_type: str | None = None
        self.size_data: float = 0
        self.calculated_size: float = 0

    @property
    def size_specified(self) -> bool:
        return self.size_type is not None

    def parse_size(self, value) -> None:
        if value is None or value == "" or value == 0:
            self.size_type, self.size_data = None, 0
        elif isinstance(value, str) and value.endswith("%"):
            self.size_type, self.size_data = "percent", float(value[:-1].strip())
        elif isinstance(value, str) and value.endswith("px"):
            self.size_type, self.size_data = "pixels", float(value[:-2].strip())
        elif isinstance(value, (int, float)) or isinstance(value, str):
            self.size_type, self.size_data = "pixels", float(value)
        else:
            raise TypeError(f"Cannot parse layout size {value!r}")


class _Grid:
    def __init__(self, rows: int, columns: int, style: dict[str, Any], batch, group) -> None:
        self._style, self._batch, self._group = style, batch, group
        self.x = self.y = self.width = self.height = 0
        self._rows: list[_Sequence] = []
        self._columns: list[_Sequence] = []
        self._cells: list[list[LayoutCell | _SpanFiller]] = []
        self.set_dimensions(rows, columns)

    def _new_cell(self) -> LayoutCell:
        return LayoutCell(
            {
                "background": self._style["cell-background"],
                "padding": self._style["cell-padding"],
                "content-alignment": self._style["cell-content-alignment"],
                "stretch-content": self._style["cell-stretch-content"],
            },
            self._batch,
            self._group,
        )

    def _new_sequence(self, key: str) -> _Sequence:
        sequence = _Sequence(self._style["cell-margin"])
        if key in self._style:
            sequence.parse_size(self._style[key])
        return sequence

    def set_dimensions(self, rows: int, columns: int) -> None:
        if rows <= 0 or columns <= 0:
            raise ValueError("layouts require at least one row and one column")
        old_cells = self._cells
        self._cells = [[self._new_cell() for _ in range(columns)] for _ in range(rows)]
        for row in range(min(rows, len(old_cells))):
            for column in range(min(columns, len(old_cells[row]))):
                cell = old_cells[row][column]
                self._cells[row][column] = cell
                if isinstance(cell, LayoutCell):
                    cell._span = min(cell._span[0], rows - row), min(cell._span[1], columns - column)
        self._rows = (self._rows + [self._new_sequence("row-size") for _ in range(rows)])[:rows]
        self._columns = (self._columns + [self._new_sequence("column-size") for _ in range(columns)])[:columns]
        self.realign()

    def _update_sizes(self, sequences: list[_Sequence], extent: float) -> None:
        margins = sum(item.margin_after for item in sequences[:-1])
        fixed = 0
        flexible: list[_Sequence] = []
        for item in sequences:
            if item.size_type == "pixels":
                item.calculated_size = item.size_data
            elif item.size_type == "percent":
                item.calculated_size = extent * item.size_data / 100
            else:
                flexible.append(item)
                continue
            fixed += item.calculated_size
        if flexible:
            size = max(0, extent - margins - fixed) / len(flexible)
            for item in flexible:
                item.calculated_size = size

    def _cell_rect(self, row: int, column: int) -> tuple[float, float, float, float]:
        cell = self._cells[row][column]
        assert isinstance(cell, LayoutCell)
        x = self.x + sum(item.calculated_size + item.margin_after for item in self._columns[:column])
        y_offset = sum(item.calculated_size + item.margin_after for item in self._rows[:row])
        width = sum(self._columns[column + i].calculated_size for i in range(cell._span[1]))
        width += sum(self._columns[column + i].margin_after for i in range(cell._span[1] - 1))
        height = sum(self._rows[row + i].calculated_size for i in range(cell._span[0]))
        height += sum(self._rows[row + i].margin_after for i in range(cell._span[0] - 1))
        return x, self.y + self.height - y_offset - height, width, height

    def realign(self) -> None:
        self._update_sizes(self._columns, self.width)
        self._update_sizes(self._rows, self.height)
        for row, cells in enumerate(self._cells):
            for column, cell in enumerate(cells):
                if isinstance(cell, LayoutCell):
                    cell.realign(self._cell_rect(row, column))

    @property
    def calculated_width(self):
        return (
            sum(item.calculated_size + item.margin_after for item in self._columns[:-1])
            + self._columns[-1].calculated_size
        )

    @property
    def calculated_height(self):
        return (
            sum(item.calculated_size + item.margin_after for item in self._rows[:-1]) + self._rows[-1].calculated_size
        )


class Layout(LayoutCell):
    """A grid layout with fixed, pixel, percentage, and flexible cell sizes."""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        rows: int,
        columns: int,
        style: Mapping[str, Any] | None = None,
        batch=None,
        group=None,
    ) -> None:
        super().__init__(style, batch, group)
        for key, value in (
            ("cell-margin", 1),
            ("cell-background", None),
            ("cell-stretch-content", False),
            ("cell-content-alignment", "center"),
            ("cell-padding", 0),
        ):
            self._set_style_if_none(key, value)
        self.set_style("stretch-content", True)
        self._cell_group = pyglet.graphics.Group(order=1, parent=group)
        self._content = _Grid(rows, columns, self._style, batch, self._cell_group)
        self.realign((x, y, width, height))

    @property
    def rows(self):
        return len(self._content._rows)

    @rows.setter
    def rows(self, value):
        self._content.set_dimensions(value, self.columns)

    @property
    def columns(self):
        return len(self._content._columns)

    @columns.setter
    def columns(self, value):
        self._content.set_dimensions(self.rows, value)

    def cell(self, row: int, column: int = 0) -> LayoutCell | None:
        if not 0 <= row < self.rows or not 0 <= column < self.columns:
            raise IndexError("layout cell index out of range")
        cell = self._content._cells[row][column]
        return cell if isinstance(cell, LayoutCell) else None

    def set_style(self, data, value=None) -> None:
        super().set_style(data, value)
        # LayoutCell creates ``_content`` as None before Layout has built its
        # grid.  Initial styles therefore need to be recorded only; they are
        # applied to the grid when it is constructed below.
        if not isinstance(data, str) or not isinstance(self._content, _Grid):
            return
        if data == "cell-background":
            for cell in self._cells():
                cell.set_style("background", value)
        elif (
            data.startswith("cell-padding")
            or data.startswith("cell-stretch-content")
            or data.startswith("cell-content-alignment")
        ):
            for cell in self._cells():
                cell.set_style(data[5:], value)
        elif data in {"cell-margin", "cell-margin-x", "cell-margin-y", "row-size", "column-size"}:
            if data.startswith("cell-margin"):
                margin = (
                    value if data != "cell-margin" else ((value, value) if isinstance(value, (int, float)) else value)
                )
                if data != "cell-margin-y":
                    for item in self._content._columns:
                        item.margin_after = margin[0] if isinstance(margin, tuple) else margin
                if data != "cell-margin-x":
                    for item in self._content._rows:
                        item.margin_after = margin[1] if isinstance(margin, tuple) else margin
            else:
                for item in self._content._rows if data == "row-size" else self._content._columns:
                    item.parse_size(value)
        self.realign()

    def _cells(self):
        return (cell for row in self._content._cells for cell in row if isinstance(cell, LayoutCell))

    def set_row_size(self, index: int, value) -> None:
        self._content._rows[index].parse_size(value)
        self.realign()

    def set_column_size(self, index: int, value) -> None:
        self._content._columns[index].parse_size(value)
        self.realign()

    def set_row_margin(self, index: int, value) -> None:
        self._content._rows[index].margin_after = value
        self.realign()

    def set_column_margin(self, index: int, value) -> None:
        self._content._columns[index].margin_after = value
        self.realign()

    def set_cell_span(self, row: int, column: int, rowspan: int | None = None, colspan: int | None = None) -> None:
        cell = self.cell(row, column)
        if cell is None:
            raise ValueError("a span must start at its top-left cell")
        rowspan, colspan = rowspan or cell._span[0], colspan or cell._span[1]
        if rowspan < 1 or colspan < 1 or row + rowspan > self.rows or column + colspan > self.columns:
            raise ValueError("cell span lies outside the layout")
        for r in range(row, row + max(rowspan, cell._span[0])):
            for c in range(column, column + max(colspan, cell._span[1])):
                if (r, c) != (row, column):
                    self._content._cells[r][c] = (
                        _SpanFiller(cell)
                        if r < row + rowspan and c < column + colspan
                        else LayoutCell(batch=self._batch, group=self._cell_group)
                    )
        cell._span = rowspan, colspan
        self.realign()

    def realign(self, new_rect=None) -> None:
        super().realign(new_rect)
        if hasattr(self, "_content") and isinstance(self._content, _Grid):
            self._content.x, self._content.y, self._content.width, self._content.height = (
                self.x,
                self.y,
                self.width,
                self.height,
            )
            self._content.realign()

    x = property(LayoutCell.x.fget, lambda self, value: self.realign((value, self.y, self.width, self.height)))
    y = property(LayoutCell.y.fget, lambda self, value: self.realign((self.x, value, self.width, self.height)))
    position = property(LayoutCell.position.fget, lambda self, value: self.realign((*value, self.width, self.height)))
    width = property(LayoutCell.width.fget, lambda self, value: self.realign((self.x, self.y, value, self.height)))
    height = property(LayoutCell.height.fget, lambda self, value: self.realign((self.x, self.y, self.width, value)))
    size = property(LayoutCell.size.fget, lambda self, value: self.realign((self.x, self.y, *value)))

    def fit_to_content(self) -> None:
        self.size = self._content.calculated_width, self._content.calculated_height


class _SingleSequenceLayout(Layout):
    def append(self, content) -> None:
        if self.is_empty:
            self.cell(0).content = content
        else:
            self._grow()
            self.cell(self.count - 1).content = content

    @property
    def is_empty(self) -> bool:
        return self.cell(0).content is None

    def remove(self, content_or_index) -> None:
        index = (
            content_or_index
            if isinstance(content_or_index, int)
            else next((i for i in range(self.count) if self.cell(i).content is content_or_index), None)
        )
        if index is None:
            return
        self._shrink(index)


class HBox(_SingleSequenceLayout):
    def __init__(self, x, y, width, height, style=None, batch=None, group=None) -> None:
        super().__init__(x, y, width, height, 1, 1, style, batch, group)

    def cell(self, column, _=0):
        return super().cell(0, column)

    @property
    def count(self):
        return 0 if self.is_empty else self.columns

    def _grow(self):
        self.columns += 1

    def _shrink(self, index):
        if self.columns == 1:
            self.cell(0).content = None
        else:
            del self._content._cells[0][index]
            del self._content._columns[index]
            self.realign()


class VBox(_SingleSequenceLayout):
    def __init__(self, x, y, width, height, style=None, batch=None, group=None) -> None:
        super().__init__(x, y, width, height, 1, 1, style, batch, group)

    def cell(self, row, _=0):
        return super().cell(row, 0)

    @property
    def count(self):
        return 0 if self.is_empty else self.rows

    def _grow(self):
        self.rows += 1

    def _shrink(self, index):
        if self.rows == 1:
            self.cell(0).content = None
        else:
            del self._content._cells[index]
            del self._content._rows[index]
            self.realign()
