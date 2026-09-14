import pytest

import pyglet
from pyglet.gui.ninepatch import NinePatch
from pyglet.text.document import UnformattedDocument
from pyglet.text.layout import TextLayout


def image(width=30, height=30):
    return pyglet.image.ImageData(width, height, "RGBA", bytes((255, 255, 255, 255)) * width * height)


def test_nine_patch_renders_fixed_edges_and_stretched_center(test_window):
    patch = NinePatch(image(), width=60, height=90)

    vertices = patch._get_vertices()

    assert vertices[:12] == (0, 0, 0, 10, 0, 0, 50, 0, 0, 60, 0, 0)
    assert vertices[-12:] == (0, 90, 0, 10, 90, 0, 50, 90, 0, 60, 90, 0)
    patch.delete()


def test_nine_patch_updates_real_vertex_attributes(test_window):
    patch = NinePatch(image(), width=60, height=90)

    patch.position = (4, 5, 6)
    patch.rotation = 45
    patch.color = (1, 2, 3)
    patch.opacity = 128

    assert patch.position == (4, 5, 6)
    assert tuple(patch._vertex_list.translate[:3]) == (4, 5, 6)
    assert tuple(patch._vertex_list.rotation[:1]) == (45,)
    assert patch.color == (1, 2, 3, 128)
    assert tuple(patch._vertex_list.colors[:4]) == (1, 2, 3, 128)
    patch.delete()


def test_nine_patch_resize_recalculates_named_anchor(test_window):
    patch = NinePatch(image(), width=60, height=90, anchor="center")

    patch.width = 80
    patch.height = 100

    assert patch.anchor_position == (40, 50)
    patch.delete()


def test_nine_patch_rejects_scaling_and_generic_update(test_window):
    patch = NinePatch(image())

    with pytest.raises(NotImplementedError, match="width"):
        patch.scale
    with pytest.raises(NotImplementedError, match="width"):
        patch.scale_x
    with pytest.raises(NotImplementedError, match="height"):
        patch.scale_y
    with pytest.raises(NotImplementedError, match="NinePatch"):
        patch.update()
    patch.delete()


def test_create_around_real_text_layout_uses_its_bounds(test_window):
    layout = TextLayout(UnformattedDocument("Layout"), 10, 20, 7, 100, 40)
    patch = NinePatch.create_around_layout(image(), layout, border=3)

    assert patch.position == (layout.left - 3, layout.bottom - 3, layout.z - 1)
    assert (patch.width, patch.height) == (layout.right - layout.left + 6, layout.top - layout.bottom + 6)
    patch.delete()
    layout.delete()
