from ctypes import Array, byref, c_float

import pyglet
import pytest

from pyglet.enums import ComponentFormat
from pyglet.graphics import Texture
from pyglet.graphics.api.gl import gl
from pyglet.graphics.api.gl.framebuffer import GLFramebuffer
from pyglet.image import ImageData, ImageException
from tests.annotations import GraphicsAPIGroups, require_graphics_api


pytestmark = require_graphics_api(GraphicsAPIGroups.GL3)


def test_read_pixels_returns_zero_copy_typed_buffer(test_window):
    test_window.switch_to()
    texture = pyglet.graphics.Texture.create(2, 2, blank_data=True, context=test_window.context)

    pixels = texture.read_pixels()

    assert pixels.format == ComponentFormat.RGBA
    assert pixels.data_type == "B"
    assert isinstance(pixels.data, Array)
    assert pixels.pitch == 8

    image_data = pixels.to_image_data()
    assert image_data._current_data is pixels.data  # noqa: SLF001


@require_graphics_api(GraphicsAPIGroups.GLES)
def test_gles_fetch_restores_framebuffer_and_pack_state(test_window):
    test_window.switch_to()
    context = test_window.context
    texture = pyglet.graphics.Texture.create(2, 2, blank_data=True, context=context)
    framebuffer = GLFramebuffer(context=context)
    framebuffer.bind()
    expected = gl.GLint()
    context.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING, expected)
    context.glPixelStorei(gl.GL_PACK_ALIGNMENT, 8)

    try:
        texture.fetch()
        scratch_framebuffer = context.pixel_readback.get_framebuffer()
        texture.fetch()
        assert context.pixel_readback.get_framebuffer() is scratch_framebuffer

        actual = gl.GLint()
        context.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING, actual)
        assert actual.value == expected.value
        pack_alignment = gl.GLint()
        context.glGetIntegerv(gl.GL_PACK_ALIGNMENT, pack_alignment)
        assert pack_alignment.value == 8
    finally:
        context.glPixelStorei(gl.GL_PACK_ALIGNMENT, 4)
        framebuffer.unbind()
        framebuffer.delete()


@require_graphics_api(GraphicsAPIGroups.DESKTOP_GL)
def test_float_texture_read_pixels(test_window):
    test_window.switch_to()
    values = tuple(i / 16 for i in range(16))
    source = (c_float * len(values))(*values)
    texture = pyglet.graphics.Texture.create(
        2,
        2,
        internal_format=ComponentFormat.RGBA,
        internal_format_size=32,
        internal_format_type="f",
        blank_data=False,
        context=test_window.context,
    )
    context = test_window.context
    context.glBindTexture(texture.target, texture.id)
    context.glTexSubImage2D(texture.target, 0, 0, 0, 2, 2, gl.GL_RGBA, gl.GL_FLOAT, source)

    pixels = texture.read_pixels()

    assert pixels.data_type == "f"
    assert pixels.pitch == 2 * 4 * 4
    assert tuple(pixels.data) == values
    with pytest.raises(NotImplementedError, match="read_pixels"):
        texture.fetch()


def test_create_immutable_texture(test_window):
    context = test_window.context
    if not context.info.features.texture_storage:
        pytest.skip("Immutable texture storage is not supported by this context.")

    texture = Texture.create(4, 2, immutable=True, mipmap_levels=2, context=context)
    try:
        immutable = gl.GLint()
        max_level = gl.GLint()
        context.glGetTexParameteriv(texture.target, gl.GL_TEXTURE_IMMUTABLE_FORMAT, byref(immutable))
        context.glGetTexParameteriv(texture.target, gl.GL_TEXTURE_MAX_LEVEL, byref(max_level))

        assert texture.immutable
        assert texture.mipmap_count == 2
        assert texture.valid_mipmaps == (0, 1)
        assert immutable.value == gl.GL_TRUE
        assert max_level.value == 1

        data = bytes((9, 9, 9, 255)) * 2
        texture.upload(ImageData(2, 1, "RGBA", data), 0, 0, 0, level=1)
        texture.generate_mipmaps()
        assert texture.mipmap_count == 2
        with pytest.raises(ImageException, match="fixed at creation"):
            texture.init_mipmaps()
    finally:
        texture.delete()
