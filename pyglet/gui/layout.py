"""Grid-based layout containers for GUI content.

The layout classes deliberately work with widgets, labels, sprites, and other
objects exposing ``position``, ``width``, and ``height``. Each layout is
constructed with its parent and derives its manager from that parent.
Interactive widgets remain direct children of a UI manager, frame, or
scrollable region.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar, cast, runtime_checkable

import pyglet
from pyglet.graphics import Batch, Group
from pyglet.gui.styles import Background, LayoutCellStyle, LayoutStyle, Padding

if TYPE_CHECKING:
    from pyglet.gui.manager import UIManager
    from pyglet.gui.widgets import ScrollableRegion, WidgetBase

StyleT = TypeVar("StyleT", bound=LayoutCellStyle)


class LayoutContent(Protocol):
    """Drawable content that can be positioned and sized by a layout cell."""

    @property
    def width(self) -> float:
        ...

    @width.setter
    def width(self, value: float) -> None:
        ...

    @property
    def height(self) -> float:
        ...

    @height.setter
    def height(self, value: float) -> None:
        ...

    @property
    def position(self) -> tuple[float, float]:
        ...

    @position.setter
    def position(self, value: tuple[float, float] | tuple[float, float, float]) -> None:
        ...


@runtime_checkable
class ParentOwnedContent(LayoutContent, Protocol):
    """Layout content that has a declared UI parent."""

    @property
    def parent(self) -> UIManager | Frame | ScrollableRegion | None:
        ...


@runtime_checkable
class ResizeAwareContent(Protocol):
    """Content that responds when its owning UI manager's window is resized."""

    def on_resize(self, width: int, height: int) -> None:
        ...


class LayoutCell(Generic[StyleT]):
    """A rectangular layout cell, optionally containing one drawable object."""

    def __init__(self, style: StyleT | None = None, batch: Batch | None = None, group: Group | None = None) -> None:
        """Create a layout cell.

        Args:
            style:
                The cell's visual and content-alignment style.
            batch:
                Optional batch for a generated background rectangle.
            group:
                Optional group for a generated background rectangle.
        """
        self._content: LayoutContent | None = None
        self._batch: Batch | None = batch
        self._group: Group | None = group
        self._background: Background | None = None
        self._rect: tuple[float, float, float, float] = (0, 0, 1, 1)
        self._style: StyleT = style if style is not None else cast("StyleT", LayoutCellStyle())
        self._span = (1, 1)
        self._layout: Layout | None = None
        self._update_background()

    @property
    def x(self) -> float:
        return self._rect[0]

    @property
    def y(self) -> float:
        return self._rect[1]

    @property
    def position(self) -> tuple[float, float]:
        return self.x, self.y

    @property
    def width(self) -> float:
        return self._rect[2]

    @property
    def height(self) -> float:
        return self._rect[3]

    @property
    def size(self) -> tuple[float, float]:
        return self.width, self.height

    @property
    def content(self) -> LayoutContent | None:
        return self._content

    @content.setter
    def content(self, value: LayoutContent | None) -> None:
        if value is self._content:
            raise ValueError("Layout cell already contains this object.")
        if value is not None:
            self._validate_content_parent(value)
        self._content = value
        self.realign()

    def _validate_content_parent(self, content: LayoutContent) -> None:
        """Require managed content to belong to this cell's layout tree."""
        if self._layout is None:
            return
        if isinstance(content, Layout):
            if content.parent is not self._layout:
                raise ValueError("A child layout must be constructed with this layout as its parent.")
            return

        if isinstance(content, ParentOwnedContent) and content.parent is not self._layout.input_parent:
            raise ValueError("A widget must be constructed with this layout's input parent.")

    @property
    def style(self) -> StyleT:
        """The typed style applied to this cell."""
        return self._style

    def set_style(self, style: StyleT) -> None:
        """Replace the cell style with a typed style object."""
        self._style = style
        self._update_background()
        self.realign()

    def on_resize(self, width: int, height: int) -> None:
        """Forward a window resize event to this cell's content, if supported."""
        if isinstance(self._content, ResizeAwareContent):
            self._content.on_resize(width, height)

    def _update_background(self) -> None:
        background = self._style.background
        if background is None:
            self._background = None
        elif isinstance(background, tuple):
            if not isinstance(self._background, pyglet.shapes.Rectangle):
                self._background = pyglet.shapes.Rectangle(
                    0, 0, 0, 0, color=background, batch=self._batch, group=self._group,
                )
            else:
                self._background.color = background
        else:
            self._background = background

    def realign(self, new_rect: tuple[float, float, float, float] | None = None) -> None:
        if new_rect is not None:
            self._rect = new_rect
            if self._background is not None:
                self._background.position = self.x, self.y
                self._background.width, self._background.height = self.width, self.height
        if self._content is None:
            return

        top, right, bottom, left = cast("Padding", self._style.padding)
        stretch_x, stretch_y = cast("tuple[bool, bool]", self._style.stretch_content)
        if self._layout is not None and isinstance(self._content, Layout):
            stretch_x, stretch_y = cast("tuple[bool, bool]", self._content.style.stretch_content)
        align_x, align_y = cast("tuple[str, str]", self._style.content_alignment)
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
            raise ValueError("Content alignment must use left/center/right and bottom/center/top.")
        try:
            self._content.position = x, y
        except (TypeError, ValueError):
            self._content.position = x, y, 0


class _SpanFiller:
    def __init__(self, cell: LayoutCell[LayoutCellStyle]) -> None:
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

    def parse_size(self, value: int | float | str | None) -> None:
        if value is None or value == "" or value == 0:
            self.size_type, self.size_data = None, 0
        elif isinstance(value, str) and value.endswith("%"):
            self.size_type, self.size_data = "percent", float(value[:-1].strip())
        elif isinstance(value, str) and value.endswith("px"):
            self.size_type, self.size_data = "pixels", float(value[:-2].strip())
        elif isinstance(value, (int, float, str)):
            self.size_type, self.size_data = "pixels", float(value)
        else:
            raise TypeError(f"Cannot parse layout size {value!r}.")


class _Grid:
    def __init__(self, rows: int, columns: int, style: LayoutStyle, batch: Batch | None, group: Group | None) -> None:
        self._style, self._batch, self._group = style, batch, group
        self.x: float = 0.0
        self.y: float = 0.0
        self.width: float = 0.0
        self.height: float = 0.0
        self._rows: list[_Sequence] = []
        self._columns: list[_Sequence] = []
        self._cells: list[list[LayoutCell[LayoutCellStyle] | _SpanFiller]] = []
        self.set_dimensions(rows, columns)

    @property
    def position(self) -> tuple[float, float]:
        """Position required by the ``LayoutContent`` protocol."""
        return self.x, self.y

    @position.setter
    def position(self, value: tuple[float, float] | tuple[float, float, float]) -> None:
        self.x, self.y = value[:2]
        self.realign()

    def _new_cell(self) -> LayoutCell[LayoutCellStyle]:
        return LayoutCell[LayoutCellStyle](
            LayoutCellStyle(
                background=self._style.cell_background,
                padding=self._style.cell_padding,
                content_alignment=self._style.cell_content_alignment,
                stretch_content=self._style.cell_stretch_content,
            ),
            self._batch,
            self._group,
        )

    def _new_sequence(self, key: str) -> _Sequence:
        margins = cast("tuple[float, float]", self._style.cell_margin)
        sequence = _Sequence(margins[0 if key == "column-size" else 1])
        sequence.parse_size(self._style.column_size if key == "column-size" else self._style.row_size)
        return sequence

    def set_dimensions(self, rows: int, columns: int) -> None:
        if rows <= 0 or columns <= 0:
            raise ValueError("Layouts require at least one row and one column.")
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
        fixed: float = 0
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

    def on_resize(self, width: int, height: int) -> None:
        """Forward a resize event through every cell in this grid."""
        for row in self._cells:
            for cell in row:
                if isinstance(cell, LayoutCell):
                    cell.on_resize(width, height)

    @property
    def calculated_width(self) -> float:
        return (
            sum(item.calculated_size + item.margin_after for item in self._columns[:-1])
            + self._columns[-1].calculated_size
        )

    @property
    def calculated_height(self) -> float:
        return (
            sum(item.calculated_size + item.margin_after for item in self._rows[:-1]) + self._rows[-1].calculated_size
        )


class Layout(LayoutCell[LayoutStyle]):
    """A grid layout with fixed, pixel, percentage, and flexible cell sizes.

    ``parent`` establishes the layout tree at construction time. Use a frame,
    UI manager, another layout, or a scrollable region as the parent.
    """
    grid: _Grid
    _cell_group: Group
    _parent: UIManager | Frame | Layout | ScrollableRegion | None

    def __init__(
        self,
        parent: UIManager | Frame | Layout | ScrollableRegion,
        x: float,
        y: float,
        width: float,
        height: float,
        rows: int,
        columns: int,
        style: LayoutStyle | None = None,
        batch: Batch | None = None,
        group: Group | None = None,
    ) -> None:
        layout_style = style or LayoutStyle()
        super().__init__(layout_style, batch, group)
        self._cell_group = pyglet.graphics.Group(order=1, parent=group)
        self._grid = _Grid(rows, columns, self._style, batch, self._cell_group)
        self._parent = None
        parent._add_layout(self)
        self._assign_cells_to_layout()
        self.realign((x, y, width, height))

    @property
    def rows(self) -> int:
        return len(self._grid._rows)

    @rows.setter
    def rows(self, value: int) -> None:
        self._grid.set_dimensions(value, self.columns)
        self._assign_cells_to_layout()

    @property
    def columns(self) -> int:
        return len(self._grid._columns)

    @columns.setter
    def columns(self, value: int) -> None:
        self._grid.set_dimensions(self.rows, value)
        self._assign_cells_to_layout()

    def cell(self, row: int, column: int = 0) -> LayoutCell[LayoutCellStyle] | None:
        if not 0 <= row < self.rows or not 0 <= column < self.columns:
            raise IndexError("layout cell index out of range")
        cell = self._grid._cells[row][column]
        return cell if isinstance(cell, LayoutCell) else None

    @property
    def style(self) -> LayoutStyle:
        """The typed style applied to this layout and its cells."""
        return self._style

    def set_style(self, style: LayoutStyle) -> None:
        """Replace the layout style and apply it to every existing cell."""
        self._style = style
        self._update_background()
        self._grid._style = style
        cell_style = LayoutCellStyle(
            background=style.cell_background,
            padding=style.cell_padding,
            stretch_content=style.cell_stretch_content,
            content_alignment=style.cell_content_alignment,
        )
        for cell in self._cells():
            cell.set_style(cell_style)
        for row in self._grid._rows:
            row.margin_after = cast("tuple[float, float]", style.cell_margin)[1]
            row.parse_size(style.row_size)
        for column in self._grid._columns:
            column.margin_after = cast("tuple[float, float]", style.cell_margin)[0]
            column.parse_size(style.column_size)
        self.realign()

    def _cells(self) -> Iterator[LayoutCell[LayoutCellStyle]]:
        return (cell for row in self._grid._cells for cell in row if isinstance(cell, LayoutCell))

    def _assign_cells_to_layout(self) -> None:
        for cell in self._cells():
            cell._layout = self

    @property
    def parent(self) -> UIManager | Frame | Layout | ScrollableRegion:
        """The layout container that owns this layout."""
        if self._parent is None:
            raise RuntimeError("Layout has no parent.")
        return self._parent

    @property
    def manager(self) -> UIManager | None:
        """The UI manager derived from this layout's parent."""
        return self.parent.manager

    @property
    def input_parent(self) -> UIManager | Frame | ScrollableRegion:
        """The object that owns input for widgets placed in this layout."""
        parent = self.parent
        return parent.input_parent if isinstance(parent, Layout) else parent

    def _add_layout(self, layout: Layout) -> None:
        layout._set_parent(self)

    def _set_parent(self, parent: UIManager | Frame | Layout | ScrollableRegion) -> None:
        if self._parent is not None:
            raise ValueError("Layout is already attached to a parent.")
        self._parent = parent

    def set_row_size(self, index: int, value: int | float | str | None) -> None:
        self._grid._rows[index].parse_size(value)
        self.realign()

    def set_column_size(self, index: int, value: int | float | str | None) -> None:
        self._grid._columns[index].parse_size(value)
        self.realign()

    def set_row_margin(self, index: int, value: float) -> None:
        self._grid._rows[index].margin_after = value
        self.realign()

    def set_column_margin(self, index: int, value: float) -> None:
        self._grid._columns[index].margin_after = value
        self.realign()

    def set_cell_span(self, row: int, column: int, rowspan: int | None = None, colspan: int | None = None) -> None:
        cell = self.cell(row, column)
        if cell is None:
            raise ValueError("A span must start at its top-left cell.")
        rowspan, colspan = rowspan or cell._span[0], colspan or cell._span[1]
        if rowspan < 1 or colspan < 1 or row + rowspan > self.rows or column + colspan > self.columns:
            raise ValueError("Cell span lies outside the layout.")
        for r in range(row, row + max(rowspan, cell._span[0])):
            for c in range(column, column + max(colspan, cell._span[1])):
                if (r, c) != (row, column):
                    self._grid._cells[r][c] = (
                        _SpanFiller(cell)
                        if r < row + rowspan and c < column + colspan
                        else LayoutCell[LayoutCellStyle](batch=self._batch, group=self._cell_group)
                    )
                    replacement = self._grid._cells[r][c]
                    if isinstance(replacement, LayoutCell):
                        replacement._layout = self
        cell._span = rowspan, colspan
        self.realign()

    def realign(self, new_rect: tuple[float, float, float, float] | None = None) -> None:
        super().realign(new_rect)
        self._grid.x, self._grid.y, self._grid.width, self._grid.height = (
            self.x,
            self.y,
            self.width,
            self.height,
        )
        self._grid.realign()

    def on_resize(self, width: int, height: int) -> None:
        """Forward a window resize event through this layout's grid."""
        self._grid.on_resize(width, height)

    @property
    def x(self) -> float:
        return self._rect[0]

    @x.setter
    def x(self, value: float) -> None:
        self.realign((value, self.y, self.width, self.height))

    @property
    def y(self) -> float:
        return self._rect[1]

    @y.setter
    def y(self, value: float) -> None:
        self.realign((self.x, value, self.width, self.height))

    @property
    def position(self) -> tuple[float, float]:
        return self.x, self.y

    @position.setter
    def position(self, value: tuple[float, float] | tuple[float, float, float]) -> None:
        self.realign((value[0], value[1], self.width, self.height))

    @property
    def width(self) -> float:
        return self._rect[2]

    @width.setter
    def width(self, value: float) -> None:
        self.realign((self.x, self.y, value, self.height))

    @property
    def height(self) -> float:
        return self._rect[3]

    @height.setter
    def height(self, value: float) -> None:
        self.realign((self.x, self.y, self.width, value))

    @property
    def size(self) -> tuple[float, float]:
        return self.width, self.height

    @size.setter
    def size(self, value: tuple[float, float]) -> None:
        self.realign((self.x, self.y, value[0], value[1]))

    def fit_to_content(self) -> None:
        self.size = self._grid.calculated_width, self._grid.calculated_height


class _SingleSequenceLayout(Layout, ABC):
    """Shared contract for one-dimensional layout containers."""

    @property
    @abstractmethod
    def count(self) -> int:
        """Number of content items in the sequence."""

    @abstractmethod
    def _grow(self) -> None:
        """Append one empty cell to the sequence."""

    @abstractmethod
    def _shrink(self, index: int) -> None:
        """Remove the cell at ``index`` from the sequence."""

    def append(self, content: LayoutContent) -> None:
        if self.is_empty:
            cell = self.cell(0)
            assert cell is not None
            cell.content = content
        else:
            self._grow()
            cell = self.cell(self.count - 1)
            assert cell is not None
            cell.content = content

    @property
    def is_empty(self) -> bool:
        cell = self.cell(0)
        assert cell is not None
        return cell.content is None

    def remove(self, content_or_index: LayoutContent | int) -> None:
        index = (
            content_or_index
            if isinstance(content_or_index, int)
            else next(
                (
                    i
                    for i in range(self.count)
                    if (cell := self.cell(i)) is not None and cell.content is content_or_index
                ),
                None,
            )
        )
        if index is None:
            raise ValueError("Content is not in this layout.")
        self._shrink(index)


class HBox(_SingleSequenceLayout):
    """Lay out content in a single horizontal row.

    Append content with :meth:`append`. Column widths, margins, padding, and
    content alignment are configured through :class:`LayoutStyle`.
    """

    def __init__(self, parent: UIManager | Frame | Layout | ScrollableRegion,
                 x: float, y: float, width: float, height: float, style: LayoutStyle | None = None,
                 batch: Batch | None = None, group: Group | None = None) -> None:
        """Create a horizontal layout.

        Args:
            parent: The layout's containing UI object.
            x: Left coordinate of the layout.
            y: Bottom coordinate of the layout.
            width: Layout width.
            height: Layout height.
            style: Optional layout style.
            batch: Optional batch for layout backgrounds.
            group: Optional group for layout backgrounds and content.
        """
        super().__init__(parent, x, y, width, height, 1, 1, style, batch, group)

    def cell(self, row: int, column: int = 0) -> LayoutCell[LayoutCellStyle] | None:
        return super().cell(0, row)

    @property
    def count(self) -> int:
        return 0 if self.is_empty else self.columns

    def _grow(self) -> None:
        self.columns += 1

    def _shrink(self, index: int) -> None:
        if self.columns == 1:
            cell = self.cell(0)
            assert cell is not None
            cell.content = None
        else:
            del self._grid._cells[0][index]
            del self._grid._columns[index]
            self.realign()


class VBox(_SingleSequenceLayout):
    """Lay out content in a single vertical column.

    Append content with :meth:`append`. Row heights, margins, padding, and
    content alignment are configured through :class:`LayoutStyle`.
    """

    def __init__(self, parent: UIManager | Frame | Layout | ScrollableRegion,
                 x: float, y: float, width: float, height: float, style: LayoutStyle | None = None,
                 batch: Batch | None = None, group: Group | None = None) -> None:
        """Create a vertical layout.

        Args:
            parent: The layout's containing UI object.
            x: Left coordinate of the layout.
            y: Bottom coordinate of the layout.
            width: Layout width.
            height: Layout height.
            style: Optional layout style.
            batch: Optional batch for layout backgrounds.
            group: Optional group for layout backgrounds and content.
        """
        super().__init__(parent, x, y, width, height, 1, 1, style, batch, group)

    def cell(self, row: int, column: int = 0) -> LayoutCell[LayoutCellStyle] | None:
        return super().cell(row, 0)

    @property
    def count(self) -> int:
        return 0 if self.is_empty else self.rows

    def _grow(self) -> None:
        self.rows += 1

    def _shrink(self, index: int) -> None:
        if self.rows == 1:
            cell = self.cell(0)
            assert cell is not None
            cell.content = None
        else:
            del self._grid._cells[index]
            del self._grid._rows[index]
            self.realign()


class Frame(Layout):
    """A visual layout container owned by one :class:`UIManager`."""

    def __init__(
        self, parent: UIManager, x: float, y: float, width: float, height: float, rows: int = 1, columns: int = 1,
        style: LayoutStyle | None = None, batch: Batch | None = None, group: Group | None = None,
    ) -> None:
        super().__init__(parent, x, y, width, height, rows, columns, style, batch, group)
        self._widgets: set[WidgetBase] = set()

    @property
    def manager(self) -> UIManager:
        """The UI manager that owns this frame's input routing."""
        return cast("UIManager", self.parent)

    @property
    def input_parent(self) -> Frame:
        """Frames own input for their direct and nested layout widgets."""
        return self

    def _add_layout(self, layout: Layout) -> None:
        super()._add_layout(layout)

    def _add_widget(self, widget: WidgetBase) -> None:
        """Register a widget constructed with this frame as its parent."""
        if widget.parent is not None:
            raise ValueError("Widget is already attached to a parent.")
        self._widgets.add(widget)
        widget.parent = self
        self.manager._register_widget(widget, self)

    def remove_widget(self, widget: WidgetBase) -> None:
        """Remove a child widget from this frame."""
        if widget not in self._widgets:
            raise ValueError("Widget is not a child of this frame.")
        self.manager._unregister_widget(widget)
        self._widgets.remove(widget)


class MovableFrame(Frame):
    """A frame container that the UI manager moves while a modifier is held."""

    def __init__(
        self, parent: UIManager, x: float, y: float, width: float, height: float, rows: int = 1, columns: int = 1,
        style: LayoutStyle | None = None, batch: Batch | None = None, group: Group | None = None,
        modifier: int = 0,
    ) -> None:
        super().__init__(parent, x, y, width, height, rows, columns, style, batch, group)
        self.modifier = modifier

    def _can_move(self, x: int, y: int, modifiers: int) -> bool:
        return (
            bool(self.modifier & modifiers)
            and self.x <= x <= self.x + self.width
            and self.y <= y <= self.y + self.height
        )

    def move(self, dx: float, dy: float) -> None:
        """Move this frame and its children by ``dx``, ``dy``."""
        self.position = self.x + dx, self.y + dy
        for widget in self._widgets:
            widget.position = widget.x + dx, widget.y + dy
