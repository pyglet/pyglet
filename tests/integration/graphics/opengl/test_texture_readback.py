from ctypes import Array, c_float

import pyglet
import pytest

from pyglet.enums import ComponentFormat
from pyglet.graphics.api.gl import gl
from pyglet.graphics.api.gl.framebuffer import GLFramebuffer
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
