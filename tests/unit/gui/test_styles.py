import pytest

from pyglet.gui.styles import LayoutCellStyle, LayoutStyle, TextButtonStyle


def test_layout_cell_style_normalizes_shorthand_values():
    style = LayoutCellStyle(padding=3, stretch_content=True, content_alignment="center")

    assert style.padding == (3, 3, 3, 3)
    assert style.stretch_content == (True, True)
    assert style.content_alignment == ("center", "center")


def test_layout_cell_style_preserves_explicit_per_axis_values():
    style = LayoutCellStyle(
        padding=(1, 2, 3, 4), stretch_content=(True, False), content_alignment=("right", "top")
    )

    assert style.padding == (1, 2, 3, 4)
    assert style.stretch_content == (True, False)
    assert style.content_alignment == ("right", "top")


def test_layout_style_normalizes_cell_specific_values():
    style = LayoutStyle(cell_margin=4, cell_padding=2, cell_stretch_content=True)

    assert style.cell_margin == (4, 4)
    assert style.cell_padding == (2, 2, 2, 2)
    assert style.cell_stretch_content == (True, True)


def test_layout_style_keeps_size_specs_for_each_sequence():
    style = LayoutStyle(row_size="50%", column_size="24px")

    assert style.row_size == "50%"
    assert style.column_size == "24px"


def test_text_button_style_keeps_explicit_state_colors():
    style = TextButtonStyle(pressed_color=(1, 2, 3), hover_color=(4, 5, 6, 7))

    assert style.pressed_color == (1, 2, 3)
    assert style.unpressed_color == (255, 255, 255)
    assert style.hover_color == (4, 5, 6, 7)


@pytest.mark.parametrize("size", ["50%", "24px", 24, 0, None])
def test_layout_style_accepts_supported_size_forms(size):
    assert LayoutStyle(row_size=size).row_size == size
