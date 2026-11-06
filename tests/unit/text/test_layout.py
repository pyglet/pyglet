import pyglet
import pyglet.text.layout


def test_incrementallayout_get_position_on_line_before_start_of_text():
    single_line_text = "This is a single line of text."
    document = pyglet.text.document.UnformattedDocument(single_line_text)
    font = document.get_font()
    layout = pyglet.text.layout.IncrementalTextLayout(document,
                                                                  height = font.ascent - font.descent,
                                                                  width = 200,
                                                                  multiline=False)
    layout.x = 100
    layout.y = 100

    assert layout.get_position_on_line(0, 100) == 0
    assert layout.get_position_on_line(0, 90) == 0
    assert layout.get_position_on_line(0, 80) == 0
    assert layout.get_position_on_line(0, 70) == 0
    assert layout.get_position_on_line(0, 60) == 0
    assert layout.get_position_on_line(0, 50) == 0


def test_update_block_defers_updates_and_returns_layout():
    document = pyglet.text.document.UnformattedDocument("Hello world")
    layout = pyglet.text.layout.TextLayout(document, width=100, height=100)

    # Updates are enabled by default.
    assert layout._update_enabled is True

    with layout.update_block() as block:
        # The context manager yields the layout itself...
        assert block is layout
        # ...and defers updates for the duration of the block.
        assert layout._update_enabled is False
        # Changes made inside the block do not trigger a relayout yet.
        layout.width = 200

    # After the block exits, updates are re-enabled and the pending
    # relayout is performed exactly once.
    assert layout._update_enabled is True


def test_update_block_restores_update_enabled_on_exception():
    document = pyglet.text.document.UnformattedDocument("Hello world")
    layout = pyglet.text.layout.TextLayout(document, width=100, height=100)
    assert layout._update_enabled is True

    try:
        with layout.update_block():
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    # The layout must not be left in a disabled state when the block raises.
    assert layout._update_enabled is True


def test_update_block_available_on_incremental_layout():
    # update_block is inherited by subclasses such as IncrementalTextLayout.
    document = pyglet.text.document.UnformattedDocument("Hello world")
    layout = pyglet.text.layout.IncrementalTextLayout(document, width=100, height=100)
    with layout.update_block():
        assert layout._update_enabled is False
    assert layout._update_enabled is True
