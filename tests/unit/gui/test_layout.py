from dataclasses import dataclass

import pytest

from pyglet.gui.layout import HBox, Layout, LayoutCell, VBox
from pyglet.gui.manager import UIDirtyFlag, UIManager
from pyglet.gui.styles import LayoutCellStyle, LayoutStyle


class Window:
    def push_handlers(self, *handlers: object) -> None:
        pass


parent = UIManager(Window(), enable=False)


@dataclass
class Content:
    width: float
    height: float
    position: tuple[float, float] = (0, 0)


class ResizeAwareContent(Content):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.resize_events = []

    def on_resize(self, width, height):
        self.resize_events.append((width, height))


def test_layout_cell_aligns_content_with_padding():
    cell = LayoutCell(LayoutCellStyle(padding=(2, 3, 5, 7), content_alignment=("right", "top")))
    content = Content(10, 8)
    cell.content = content

    cell.realign((10, 20, 40, 30))

    assert content.position == (37, 40)


def test_layout_cell_stretches_content_to_its_inner_size():
    cell = LayoutCell(LayoutCellStyle(padding=4, stretch_content=True))
    content = Content(1, 1)
    cell.content = content

    cell.realign((0, 0, 30, 20))

    assert (content.width, content.height) == (22, 12)
    assert content.position == (4, 4)


def test_layout_cell_stretches_content_per_axis():
    cell = LayoutCell(LayoutCellStyle(stretch_content=(True, False)))
    content = Content(10, 8)
    cell.content = content

    cell.realign((0, 0, 30, 20))

    assert (content.width, content.height) == (30, 8)


def test_layout_cell_positions_nested_layout_content_with_padding():
    cell = LayoutCell(LayoutCellStyle(padding=(2, 3, 5, 7), content_alignment=("left", "bottom")))
    content = Layout(parent, 0, 0, 100, 40, 1, 1, LayoutStyle(column_size=30, row_size=20, padding=(2, 4, 3, 5)))
    cell.content = content

    cell.realign((0, 0, 100, 40))

    assert content.position == (7, 5)
    assert content.size == (100, 40)


def test_layout_distributes_flexible_cells_and_margins():
    layout = Layout(parent, 10, 20, 100, 60, 2, 2, LayoutStyle(cell_margin=(4, 6)))

    assert layout.cell(0, 0).size == (48, 27)
    assert layout.cell(0, 0).position == (10, 53)
    assert layout.cell(1, 1).position == (62, 20)


def test_layout_cell_span_covers_intervening_margin():
    layout = Layout(parent, 0, 0, 100, 40, 1, 2, LayoutStyle(cell_margin=(4, 0)))
    layout.set_cell_span(0, 0, colspan=2)
    layout.realign()

    assert layout.cell(0, 0).size == (100, 40)
    assert layout.cell(0, 1) is None


def test_layout_resize_event_propagates_through_nested_layouts():
    outer = Layout(parent, 0, 0, 100, 100, 1, 1)
    inner = Layout(outer, 0, 0, 100, 100, 1, 1)
    content = ResizeAwareContent(10, 10)
    inner.cell(0, 0).content = content
    outer.cell(0, 0).content = inner

    outer.on_resize(800, 600)

    assert content.resize_events == [(800, 600)]


def test_nested_layout_uses_its_stretch_content_style():
    outer = Layout(parent, 0, 0, 100, 100, 1, 1)
    inner = Layout(outer, 0, 0, 10, 20, 1, 1, LayoutStyle(stretch_content=(True, False)))

    outer.cell(0, 0).content = inner
    outer.realign()

    assert inner.size == (100, 20)


def test_nested_layout_can_disable_stretching_in_its_style():
    outer = Layout(parent, 0, 0, 100, 100, 1, 1)
    inner = Layout(outer, 0, 0, 10, 20, 1, 1, LayoutStyle(stretch_content=False))

    outer.cell(0, 0).content = inner
    outer.realign()

    assert inner.size == (10, 20)


def test_layout_set_style_reconfigures_existing_cells_and_sequences():
    layout = Layout(parent, 0, 0, 100, 60, 2, 2)
    style = LayoutStyle(cell_margin=(10, 5), row_size=20, cell_padding=3)

    layout.set_style(style)
    layout.realign()

    assert layout.style is style
    assert layout.cell(0, 0).style.padding == (3, 3, 3, 3)
    assert layout.cell(0, 0).size == (45, 20)
    assert layout.cell(1, 0).position == (0, 15)


def test_layout_resizes_sequences_with_pixel_percent_and_flexible_sizes():
    layout = Layout(parent, 0, 0, 200, 100, 1, 3)
    layout.set_column_size(0, 20)
    layout.set_column_size(1, "25%")
    layout.realign()

    assert layout.cell(0, 0).size == (20, 100)
    assert layout.cell(0, 1).size == (50, 100)
    assert layout.cell(0, 2).size == (128, 100)
    assert layout.cell(0, 2).position == (72, 0)


def test_layout_dimension_changes_preserve_existing_content():
    layout = Layout(parent, 0, 0, 100, 100, 1, 1)
    content = Content(10, 10)
    layout.cell(0, 0).content = content

    layout.columns = 2
    layout.rows = 2

    assert layout.rows == 2
    assert layout.columns == 2
    assert layout.cell(0, 0).content is content


def test_layout_span_can_be_reduced_and_restores_covered_cells():
    layout = Layout(parent, 0, 0, 100, 40, 1, 2)
    layout.set_cell_span(0, 0, colspan=2)
    layout.realign()
    layout.set_cell_span(0, 0, colspan=1)
    layout.realign()

    assert layout.cell(0, 0).size == (49.5, 40)
    assert layout.cell(0, 1) is not None
    assert layout.cell(0, 1).size == (49.5, 40)


def test_layout_fit_to_content_uses_calculated_cell_sizes_and_margins():
    layout = Layout(parent, 0, 0, 1, 1, 2, 2, LayoutStyle(row_size=10, column_size=20, cell_margin=(3, 5)))

    layout.fit_to_content()

    assert layout.size == (43, 25)


def test_layout_rejects_invalid_dimensions_and_cell_indexes():
    with pytest.raises(ValueError, match="at least one row"):
        Layout(parent, 0, 0, 100, 100, 0, 1)

    layout = Layout(parent, 0, 0, 100, 100, 1, 1)
    with pytest.raises(IndexError, match="index"):
        layout.cell(1, 0)
    with pytest.raises(ValueError, match="outside"):
        layout.set_cell_span(0, 0, colspan=2)


@pytest.mark.parametrize("layout_type", [HBox, VBox])
def test_single_sequence_layout_append_and_remove(layout_type):
    layout = layout_type(parent, 0, 0, 100, 100)
    first, second = Content(10, 10), Content(10, 10)

    layout.append(first)
    layout.append(second)
    layout.remove(first)

    assert layout.count == 1
    assert layout.cell(0).content is second


@pytest.mark.parametrize("layout_type", [HBox, VBox])
def test_single_sequence_layout_can_remove_by_index_and_become_empty(layout_type):
    layout = layout_type(parent, 0, 0, 100, 100)
    content = Content(10, 10)
    layout.append(content)

    layout.remove(0)

    assert layout.count == 0
    assert layout.is_empty


def test_manager_batches_layout_calculation_until_its_next_update():
    manager = UIManager(Window(), enable=False)
    layout = VBox(manager, 0, 0, 100, 100)
    calls = 0
    realign = layout._grid.realign

    def track_realign():
        nonlocal calls
        calls += 1
        realign()

    layout._grid.realign = track_realign
    layout.append(Content(10, 10))
    layout.append(Content(10, 10))

    assert calls == 0
    assert manager._dirty_flags == UIDirtyFlag.LAYOUT

    manager._process_dirty()

    assert calls == 1
    assert manager._dirty_flags == UIDirtyFlag.NONE


def test_manual_realign_calculates_and_clears_a_pending_layout_update():
    manager = UIManager(Window(), enable=False)
    layout = VBox(manager, 0, 0, 100, 100)
    layout.append(Content(10, 10))

    assert layout in manager._dirty_layouts

    layout.realign()

    assert layout not in manager._dirty_layouts
    assert manager._dirty_flags == UIDirtyFlag.NONE
