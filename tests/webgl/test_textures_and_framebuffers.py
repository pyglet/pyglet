from __future__ import annotations

import pyglet


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
