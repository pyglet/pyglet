from ctypes import Array, byref, c_float, c_int, c_uint

import pyglet
import pytest

from pyglet.enums import ComponentFormat, TextureFilter
from pyglet.graphics import Texture
from pyglet.graphics.api.gl import gl
from pyglet.graphics.api.gl.framebuffer import GLFramebuffer
from pyglet.graphics import TextureError, TextureFormatError
from pyglet.graphics.api.gl.texture import _get_internal_format
from pyglet.image import ImageData
from tests.annotations import GraphicsAPIGroups, require_graphics_api


pytestmark = require_graphics_api(GraphicsAPIGroups.GL3)


@pytest.mark.parametrize("source_format", ["RGB", "BGR"])
def test_rgb_upload_to_rgba_texture_is_opaque(test_window, source_format):
    test_window.switch_to()
    pixels = [(0, 20, 30), (40, 50, 60)]
    data = bytes(value for pixel in pixels for value in (pixel if source_format == "RGB" else pixel[::-1]))
    texture = Texture.create(2, 1, context=test_window.context)
    try:
        texture.bind()
        texture.upload(ImageData(2, 1, source_format, data), 0, 0, 0)
        assert bytes(texture.fetch().get_bytes("RGBA", 8)) == bytes((0, 20, 30, 255, 40, 50, 60, 255))
    finally:
        texture.delete()


def test_texture_array_creation_sets_distinct_sampler_filters(test_window):
    test_window.switch_to()
    context = test_window.context
    texture = pyglet.graphics.TextureArray.create(
        2, 2, filters=(TextureFilter.NEAREST, TextureFilter.LINEAR), max_depth=1, context=context,
    )
    try:
        texture.bind()
        value = gl.GLint()
        context.glGetTexParameteriv(texture.target, gl.GL_TEXTURE_MIN_FILTER, value)
        assert value.value == gl.GL_NEAREST
        context.glGetTexParameteriv(texture.target, gl.GL_TEXTURE_MAG_FILTER, value)
        assert value.value == gl.GL_LINEAR
    finally:
        texture.delete()


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


@require_graphics_api(GraphicsAPIGroups.MODERN_DESKTOP_GL)
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
        with pytest.raises(TextureError, match="fixed at creation"):
            texture.init_mipmaps()
    finally:
        texture.delete()


@pytest.mark.parametrize("data_type, component_type, values", [
    ("i", c_int, (-2147483648, -1, 0, 2147483647)),
    ("I", c_uint, (0, 1, 2147483648, 4294967295)),
])
def test_integer_texture_read_pixels(test_window, data_type, component_type, values):
    """Preserve signedness and full 32-bit values during typed integer readback."""
    test_window.switch_to()
    context = test_window.context
    texture = Texture.create(
        1, 1, internal_format_size=32, internal_format_type=data_type,
        blank_data=False, context=context,
    )
    try:
        source = (component_type * len(values))(*values)
        gl_type = gl.GL_INT if data_type == "i" else gl.GL_UNSIGNED_INT
        context.glTexSubImage2D(texture.target, 0, 0, 0, 1, 1, gl.GL_RGBA_INTEGER, gl_type, source)
        pixels = texture.read_pixels()
        assert pixels.data_type == data_type
        assert pixels.pitch == 16
        assert tuple(pixels.data) == values
    finally:
        texture.delete()


def test_deleted_texture_cannot_be_read_or_used_as_region_owner(test_window):
    """Allow repeated deletion while rejecting readback and regions of deleted storage."""
    test_window.switch_to()
    texture = Texture.create(1, 1, context=test_window.context)
    texture.delete()
    texture.delete()
    assert texture.handle is None
    with pytest.raises(TextureError, match="Cannot read a deleted texture"):
        texture.read_pixels()
    with pytest.raises(TextureError, match="Cannot create a region of a deleted texture"):
        texture.get_region(0, 0, 1, 1)


@pytest.mark.parametrize("fmt, data_type", [("ABCDE", "B"), ("RGBA", "q")])
def test_upload_rejects_unsupported_pixel_format_or_data_type(test_window, fmt, data_type):
    """Reject unsupported component layouts and types before submitting invalid GL enums."""
    test_window.switch_to()
    texture = Texture.create(1, 1, context=test_window.context)
    try:
        image = ImageData(1, 1, fmt, bytes(16), data_type=data_type)
        with pytest.raises(TextureFormatError, match="Unsupported pixel format"):
            texture.upload(image, 0, 0, 0)
    finally:
        texture.delete()


@pytest.mark.parametrize("component_format, bit_size", [("XYZ", 8), (ComponentFormat.RGBA, 7)])
def test_invalid_internal_format_raises_texture_format_error(component_format, bit_size):
    """Distinguish unknown component layouts and missing sized GL formats from other texture errors."""
    with pytest.raises(TextureFormatError):
        _get_internal_format(component_format, bit_size)
