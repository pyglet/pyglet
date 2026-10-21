from __future__ import annotations

from pathlib import Path

import pyglet
import pytest


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


@pytest.mark.parametrize("layout", ["region", "padded", "negative_pitch", "bgra"])
def test_texture_streamer_upload_layouts(webgl_window, layout):
    expected = bytes((1, 2, 3, 255, 4, 5, 6, 255, 7, 8, 9, 255, 10, 11, 12, 255))
    if layout == "region":
        source = pyglet.image.ImageData(3, 3, "RGBA", bytes(range(36))).get_region(1, 1, 2, 2)
        expected = bytes(range(16, 24)) + bytes(range(28, 36))
    elif layout == "padded":
        source = pyglet.image.ImageData(2, 2, "RGBA", expected[:8] + b"pad!" + expected[8:] + b"pad!", pitch=12)
    elif layout == "negative_pitch":
        source = pyglet.image.ImageData(2, 2, "RGBA", expected[8:] + expected[:8], pitch=-8)
    else:
        source = pyglet.image.ImageData(2, 2, "BGRA", b"".join(expected[i:i + 4][2::-1] + expected[i + 3:i + 4]
                                                               for i in range(0, len(expected), 4)))
    texture = pyglet.graphics.Texture.create(2, 2, context=webgl_window.context)
    streamer = pyglet.graphics.TextureStreamer(webgl_window)
    try:
        upload = streamer.queue_upload(texture, source)
        streamer.submit()
        webgl_window.context.gl.finish()
        streamer.process()
        assert upload.completed
        assert bytes(texture.fetch().get_bytes("RGBA", 8)) == expected
        download = streamer.queue_download(texture)
        streamer.submit()
        webgl_window.context.gl.finish()
        streamer.process()
        assert download.completed
        assert bytes(download.image_data.get_bytes("RGBA", 8)) == expected
        assert not webgl_window.context.gl.getParameter(webgl_window.context.gl.PIXEL_PACK_BUFFER_BINDING)
    finally:
        streamer.delete()
        texture.delete()


@pytest.mark.parametrize("texture_class", ["Texture", "Texture3D", "TextureArray"])
def test_texture_streamer_mipmap_and_layer_bounds(webgl_window, texture_class):
    from pyglet.image.base import ImageException

    cls = getattr(pyglet.graphics, texture_class)
    if texture_class == "Texture":
        texture = cls.create(4, 4, context=webgl_window.context)
        z = 0
    else:
        images = [pyglet.image.ImageData(4, 4, "RGBA", bytes(64)) for _ in range(4)]
        texture = cls.create_for_images(images, context=webgl_window.context)
        z = 1
    texture.generate_mipmaps()
    streamer = pyglet.graphics.TextureStreamer(webgl_window)
    try:
        with pytest.raises(ImageException):
            streamer.queue_download(texture, width=3, level=1)
        with pytest.raises(ImageException):
            streamer.queue_upload(texture, pyglet.image.ImageData(3, 3, "RGBA", bytes(36)), level=1)
        expected = bytes((12, 34, 56, 255)) * 4
        upload = streamer.queue_upload(texture, pyglet.image.ImageData(2, 2, "RGBA", expected), z=z, level=1)
        streamer.submit()
        webgl_window.context.gl.finish()
        streamer.process()
        assert upload.completed
        download = streamer.queue_download(texture, z=z, level=1)
        streamer.submit()
        webgl_window.context.gl.finish()
        streamer.process()
        assert (download.image_data.width, download.image_data.height) == (2, 2)
        assert bytes(download.image_data.get_bytes("RGBA", 8)) == expected
    finally:
        streamer.delete()
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
