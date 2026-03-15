import pytest

import pyglet

from pyglet.graphics.atlas import AllocatorException, TextureAtlas, TextureBin, TextureArrayBin
from pyglet.graphics.texture import TextureArraySizeExceeded
from pyglet.image import ImageData
from tests.annotations import GraphicsAPI, skip_graphics_api


def _solid_rgba_image(width: int, height: int, color: tuple[int, int, int, int]) -> ImageData:
    return ImageData(width, height, "RGBA", bytes(color) * (width * height))


def test_texture_atlas_add_with_border_and_upload(gl3_context):
    gl3_context.switch_to()

    atlas = TextureAtlas(width=8, height=8)
    image = _solid_rgba_image(2, 2, (255, 0, 0, 255))

    region = atlas.add(image, border=1)

    assert (region.x, region.y) == (1, 1)
    assert (region.width, region.height) == (2, 2)
    assert atlas.allocator.used_area == 16

    fetched = bytes(region.get_image_data().get_bytes("RGBA", region.width * 4))
    assert fetched == bytes([255, 0, 0, 255]) * 4


def test_texture_atlas_raises_when_no_space(gl3_context):
    gl3_context.switch_to()

    atlas = TextureAtlas(width=4, height=4)
    atlas.add(_solid_rgba_image(4, 4, (1, 2, 3, 255)))

    with pytest.raises(AllocatorException):
        atlas.add(_solid_rgba_image(1, 1, (9, 8, 7, 255)))


def test_texture_bin_creates_new_atlas_when_full(gl3_context):
    gl3_context.switch_to()

    texture_bin = TextureBin(texture_width=64, texture_height=64)
    image = _solid_rgba_image(64, 64, (10, 20, 30, 255))

    region_a = texture_bin.add(image)
    assert len(texture_bin.atlases) == 1

    region_b = texture_bin.add(image)
    assert len(texture_bin.atlases) == 2
    assert region_a.owner is texture_bin.atlases[0].texture
    assert region_b.owner is texture_bin.atlases[1].texture


@skip_graphics_api(GraphicsAPI.GL2)
def test_texture_array_bin_creates_new_array_when_depth_full(gl3_context):
    gl3_context.switch_to()

    array_bin = TextureArrayBin(texture_width=4, texture_height=4, max_depth=2)
    image = _solid_rgba_image(4, 4, (1, 2, 3, 255))

    region_0 = array_bin.add(image)
    region_1 = array_bin.add(image)

    assert len(array_bin.arrays) == 1
    assert region_0.z == 0
    assert region_1.z == 1

    region_2 = array_bin.add(image)
    assert len(array_bin.arrays) == 2
    assert region_2.z == 0
    assert region_2.owner is array_bin.arrays[1]


@skip_graphics_api(GraphicsAPI.GL2)
def test_texture_array_bin_raises_for_oversized_image(gl3_context):
    gl3_context.switch_to()

    array_bin = TextureArrayBin(texture_width=4, texture_height=4, max_depth=2)

    with pytest.raises(TextureArraySizeExceeded):
        array_bin.add(_solid_rgba_image(5, 4, (1, 2, 3, 255)))
