from __future__ import annotations

from pathlib import Path

import pyglet
import pytest


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
