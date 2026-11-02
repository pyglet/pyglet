from __future__ import annotations

from pathlib import Path

import pyglet
import pytest


@pytest.mark.parametrize("texture_class", ["Texture3D", "TextureArray"])
def test_image_sequence_defaults_to_unsigned_bytes(webgl_window, texture_class):
    """Keep unsigned image values when no storage type is explicitly supplied."""
    values = bytes((128, 192, 254, 255)) * 4
    image = pyglet.image.ImageData(2, 2, "RGBA", values)
    texture = getattr(pyglet.graphics, texture_class).create_for_images(
        [image], context=webgl_window.context,
    )
    try:
        assert texture.internal_format_type == "B"
        assert bytes(texture.fetch(z=0).get_bytes("RGBA", 8)) == values
    finally:
        texture.delete()


@pytest.mark.parametrize("data_type, values", [
    ("i", (-2147483648, -1, 0, 2147483647)),
    ("I", (0, 1, 2147483648, 4294967295)),
])
@pytest.mark.parametrize("blank_data", [False, True])
@pytest.mark.parametrize("kind", ["2d", "3d", "array"])
def test_integer_texture_allocation(webgl_window, data_type, values, blank_data, kind):
    """Allocate integer storage and mip levels with matching WebGL transfer types."""
    import js
    from pyglet.enums import TextureFilter, TextureType

    context = webgl_window.context
    gl = context.gl
    texture_class = {"2d": pyglet.graphics.Texture, "3d": pyglet.graphics.Texture3D,
                     "array": pyglet.graphics.TextureArray}[kind]
    kwargs = {"max_depth": 2} if kind == "array" else {}
    if kind == "3d":
        kwargs["tex_type"] = TextureType.TYPE_3D
    texture = texture_class.create(
        2, 2, internal_format_size=32, internal_format_type=data_type,
        filters=TextureFilter.NEAREST, blank_data=blank_data, context=context, **kwargs,
    )
    framebuffer = gl.createFramebuffer()
    previous_framebuffer = gl.getParameter(gl.FRAMEBUFFER_BINDING)
    component_type = js.Int32Array if data_type == "i" else js.Uint32Array
    gl_type = gl.INT if data_type == "i" else gl.UNSIGNED_INT
    try:
        assert gl.getError() == gl.NO_ERROR
        texture.init_mipmaps(2, blank_data=blank_data)
        assert gl.getError() == gl.NO_ERROR
        gl.bindFramebuffer(gl.FRAMEBUFFER, framebuffer)
        for level in range(2):
            width = 2 >> level
            if kind == "2d":
                gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, texture.target, texture.handle, level)
            else:
                gl.framebufferTextureLayer(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, texture.handle, level, 0)
            assert gl.checkFramebufferStatus(gl.FRAMEBUFFER) == gl.FRAMEBUFFER_COMPLETE
            pixels = component_type.new(width * width * 4)
            if blank_data:
                gl.readPixels(0, 0, width, width, gl.RGBA_INTEGER, gl_type, pixels)
                assert tuple(pixels.to_py()) == (0,) * (width * width * 4)
            source = component_type.new(values * (width * width))
            if kind == "2d":
                gl.texSubImage2D(texture.target, level, 0, 0, width, width, gl.RGBA_INTEGER, gl_type, source)
            else:
                gl.texSubImage3D(texture.target, level, 0, 0, 0, width, width, 1,
                                 gl.RGBA_INTEGER, gl_type, source)
            gl.readPixels(0, 0, width, width, gl.RGBA_INTEGER, gl_type, pixels)
            assert tuple(pixels.to_py()) == values * (width * width)
            assert gl.getError() == gl.NO_ERROR
    finally:
        gl.bindFramebuffer(gl.FRAMEBUFFER, previous_framebuffer)
        gl.deleteFramebuffer(framebuffer)
        texture.delete()


def test_texture_resource_cleanup_deletes_javascript_handle(webgl_window):
    """Release the real WebGL texture through the cleanup hook used by garbage collection."""
    gl = webgl_window.context.gl
    texture = pyglet.graphics.Texture.create(1, 1, context=webgl_window.context)
    handle = texture.handle
    try:
        texture.bind()
        assert gl.isTexture(handle)
        texture._delete_resource()
        assert texture.handle is None
        assert not gl.isTexture(handle)
        texture.delete()
        assert gl.getError() == gl.NO_ERROR
    finally:
        texture.delete()


@pytest.mark.parametrize("fmt, expected_name", [("RGBA", "RGBA"), ("BGRA", "RGBA"), ("BGR", "RGB")])
def test_pixel_format_normalizes_component_order(webgl_window, fmt, expected_name):
    """Resolve supported WebGL enums for native and convertible image component orders."""
    from pyglet.graphics.api.webgl.texture import _get_pixel_format

    image = pyglet.image.ImageData(1, 1, fmt, bytes(len(fmt)))
    pixel_format, data_type = _get_pixel_format(image)
    assert pixel_format == getattr(webgl_window.context.gl, expected_name)
    assert data_type == webgl_window.context.gl.UNSIGNED_BYTE


def test_upload_rejects_unsupported_pixel_format(webgl_window):
    """Reject an unsupported component layout without submitting invalid WebGL enums."""
    from pyglet.graphics import TextureFormatError

    texture = pyglet.graphics.Texture.create(1, 1, context=webgl_window.context)
    try:
        image = pyglet.image.ImageData(1, 1, "ABCDE", bytes(5))
        with pytest.raises(TextureFormatError, match="Unsupported WebGL pixel format"):
            texture.upload(image, 0, 0, 0)
        assert webgl_window.context.gl.getError() == webgl_window.context.gl.NO_ERROR
    finally:
        texture.delete()


def test_texture_array_creation_sets_distinct_sampler_filters(webgl_window):
    from pyglet.enums import TextureFilter

    gl = webgl_window.context.gl
    texture = pyglet.graphics.TextureArray.create(
        2, 2, filters=(TextureFilter.NEAREST, TextureFilter.LINEAR), max_depth=1, context=webgl_window.context,
    )
    try:
        texture.bind()
        assert gl.getTexParameter(texture.target, gl.TEXTURE_MIN_FILTER) == gl.NEAREST
        assert gl.getTexParameter(texture.target, gl.TEXTURE_MAG_FILTER) == gl.LINEAR
    finally:
        texture.delete()


def test_create_from_image_uses_supplied_context(webgl_window):
    import copy
    import js

    # A second canvas has independent GL object ownership.
    canvas = js.document.createElement("canvas")
    context = copy.copy(webgl_window.context)
    context.gl = canvas.getContext("webgl2")
    expected = bytes((19, 73, 127, 255)) * 4
    texture = pyglet.graphics.Texture.create_from_image(
        pyglet.image.ImageData(2, 2, "RGBA", expected), context=context,
    )
    try:
        assert context.gl.isTexture(texture.handle)
        assert texture._context is context
        assert bytes(texture.fetch().get_bytes("RGBA", 8)) == expected
        assert context.gl.getError() == context.gl.NO_ERROR
    finally:
        texture.delete()


def test_upload_byte_views_manage_copying(webgl_window):
    from pyglet.libs.emscripten import copy_to_js_uint8_array, zero_copy
    import js

    python_data = bytearray((1, 2, 3, 4))
    copied_view = copy_to_js_uint8_array(python_data)
    python_data[0] = 8
    assert copied_view[0] == 1

    with zero_copy(python_data) as js_view:
        python_data[0] = 9
        assert js_view[0] == 9

    javascript_data = js.Uint8Array.new((1, 2, 3, 4))
    with zero_copy(javascript_data) as js_view:
        assert js_view is javascript_data


def test_backed_buffer_reuses_persistent_byte_view(webgl_window):
    from pyglet.graphics.api.webgl.buffer import WebGLBufferObject, WebGLIndexedBufferObject

    buffer = WebGLIndexedBufferObject(webgl_window.context, size=4, data_type="B", stride=1, count=1)
    try:
        persistent_view = buffer.store.view

        buffer.set_bytes(bytes((1, 2, 3, 4)))
        buffer.commit()
        assert buffer.store.view is persistent_view
        assert WebGLBufferObject.get_bytes(buffer) == bytes((1, 2, 3, 4))

        buffer.resize(8)
        assert buffer.store.view is not persistent_view
        buffer.commit()
        assert WebGLBufferObject.get_bytes(buffer) == bytes((1, 2, 3, 4, 0, 0, 0, 0))
    finally:
        buffer.delete()


def test_rgba_texture_upload_and_readback(webgl_window):
    pixel = bytes((17, 83, 149, 211))
    source = pyglet.image.ImageData(4, 4, "RGBA", pixel * 16)
    texture = pyglet.graphics.Texture.create(4, 4, blank_data=True)

    try:
        texture.upload(source, 0, 0, 0)
        result = texture.get_image_data().get_bytes("RGBA", 16)
        assert bytes(result) == pixel * 16
    finally:
        texture.delete()


def test_compressed_texture_upload(webgl_window):
    gl = webgl_window.context.gl
    if gl.getExtension("WEBGL_compressed_texture_s3tc") is None:
        pytest.skip("S3TC texture compression is not supported.")

    image_path = Path(__file__).parents[3] / "data" / "images" / "rgba_dxt1.dds"
    image = pyglet.image.load(image_path)
    texture = image.get_texture()

    try:
        assert texture.width == image.width
        assert texture.height == image.height
        assert gl.getError() == gl.NO_ERROR
    finally:
        texture.delete()


def test_framebuffer_attachment_clear_and_readback(webgl_window):
    texture = pyglet.graphics.Texture.create(2, 2, blank_data=True)
    framebuffer = pyglet.graphics.Framebuffer()
    framebuffer.attach_texture(texture)
    gl = webgl_window.context.gl

    try:
        framebuffer.bind()
        assert framebuffer.is_complete
        gl.viewport(0, 0, 2, 2)
        gl.clearColor(1.0, 0.0, 0.0, 1.0)
        gl.clear(gl.COLOR_BUFFER_BIT)
        framebuffer.unbind()

        result = texture.get_image_data().get_bytes("RGBA", 8)
        assert bytes(result) == bytes((255, 0, 0, 255)) * 4
    finally:
        framebuffer.unbind()
        framebuffer.delete()
        texture.delete()
