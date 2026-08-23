import pyglet

from pyglet.shapes import Circle
from pyglet.graphics import Group, Batch
from tests.annotations import Platform, skip_platform


def test_batch_migration(test_window):
    batch = Batch()
    group = Group(order=10)
    shape = Circle(100, 100, 50, batch=batch, group=group)
    assert shape.batch == batch
    assert shape.group == group

    new_batch = Batch()
    shape.batch = new_batch
    assert shape.batch == new_batch


def test_group_migration(test_window):
    batch = Batch()
    group = Group(order=10)
    shape = Circle(100, 100, 50, batch=batch, group=group)
    assert shape.batch == batch
    assert shape.group == group

    new_group = Group()
    shape.group = new_group
    assert shape.group == new_group

# Doesn't really support a hidden window/multiple "windows".
@skip_platform(Platform.EMSCRIPTEN)
def test_batch_can_be_created_on_the_hidden_final_window():
    """Resources created before a window is shown stay with that window's context."""
    window = pyglet.window.Window(visible=False)
    shape = None
    try:
        window.switch_to()
        batch = Batch()
        shape = Circle(100, 100, 50, batch=batch)

        assert batch._context is window.context  # noqa: SLF001
        assert shape.batch is batch
    finally:
        if shape is not None:
            shape.delete()
        window.close()
