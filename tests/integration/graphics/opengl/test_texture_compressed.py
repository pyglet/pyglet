from ctypes import byref
from pathlib import Path

import pyglet
import pytest

from pyglet.graphics.api.gl import gl
from tests.annotations import GraphicsAPIGroups, require_graphics_api


pytestmark = require_graphics_api(GraphicsAPIGroups.DESKTOP_GL)

_image_path = Path(__file__).parents[3] / "data" / "images"


def _level_dimensions(context, texture, level: int) -> tuple[int, int]:
    width = gl.GLint()
    height = gl.GLint()
    context.glGetTexLevelParameteriv(texture.target, level, gl.GL_TEXTURE_WIDTH, byref(width))
    context.glGetTexLevelParameteriv(texture.target, level, gl.GL_TEXTURE_HEIGHT, byref(height))
    return width.value, height.value


def test_compressed_texture_uploads_dds_mip_chain(test_window):
    test_window.switch_to()
    context = test_window.context
    if not context.core.have_extension("GL_ARB_texture_compression_bptc"):
        pytest.skip("BPTC texture compression is not supported.")

    image = pyglet.image.load(_image_path / "rgba_bc7.dds")
    texture = image.get_texture()

    assert texture.mipmap_count == len(image.mipmap_data) + 1
    for level in range(texture.mipmap_count):
        assert _level_dimensions(context, texture, level) == (
            max(1, image.width >> level),
            max(1, image.height >> level),
        )


def test_compressed_texture_generates_mip_chain(test_window):
    test_window.switch_to()
    context = test_window.context
    if not (
        context.core.have_extension("GL_EXT_texture_compression_s3tc")
        or context.core.have_extension("GL_EXT_texture_compression_dxt1")
    ):
        pytest.skip("S3TC texture compression is not supported.")

    image = pyglet.image.load(_image_path / "rgba_dxt1.dds")
    texture = image.get_texture()
    texture.generate_mipmaps()

    assert texture.mipmap_count == image.width.bit_length()
    assert _level_dimensions(context, texture, texture.mipmap_count - 1) == (1, 1)
