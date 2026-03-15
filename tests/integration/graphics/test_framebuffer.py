from ctypes import byref

import pyglet

from pyglet.enums import ComponentFormat, FramebufferAttachment
from pyglet.graphics.api.gl import gl
from tests.annotations import skip_graphics_api, GraphicsAPI


def _get_bound_framebuffer_id() -> int:
    binding = gl.GLint()
    gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING, byref(binding))
    return binding.value


@skip_graphics_api(GraphicsAPI.GL2)
def test_framebuffer_creation_and_binding(gl3_context):
    gl3_context.switch_to()

    framebuffer = pyglet.graphics.Framebuffer(context=gl3_context.context)
    try:
        assert framebuffer.id > 0
        assert framebuffer.width == 0
        assert framebuffer.height == 0

        framebuffer.bind()
        assert _get_bound_framebuffer_id() == framebuffer.id

        framebuffer.unbind()
        assert _get_bound_framebuffer_id() == 0
    finally:
        framebuffer.delete()


@skip_graphics_api(GraphicsAPI.GL2)
def test_framebuffer_attach_texture_and_readback(gl3_context):
    gl3_context.switch_to()

    framebuffer = pyglet.graphics.Framebuffer(context=gl3_context.context)
    texture = pyglet.graphics.Texture.create(2, 2, blank_data=True, context=gl3_context.context)
    try:
        framebuffer.attach_texture(texture)
        assert framebuffer.width == 2
        assert framebuffer.height == 2

        framebuffer.bind()
        try:
            assert framebuffer.is_complete
            assert framebuffer.get_status() == "Framebuffer is complete."

            gl.glViewport(0, 0, 2, 2)
            gl.glDisable(gl.GL_DEPTH_TEST)
            gl.glDisable(gl.GL_BLEND)
            gl.glClearColor(1.0, 0.0, 0.0, 1.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        finally:
            framebuffer.unbind()

        data = bytes(texture.get_image_data().get_bytes("RGBA", 8))
        assert data == bytes([255, 0, 0, 255]) * 4
    finally:
        framebuffer.delete()
        texture.delete()


@skip_graphics_api(GraphicsAPI.GL2)
def test_framebuffer_attach_depth_renderbuffer(gl3_context):
    gl3_context.switch_to()

    framebuffer = pyglet.graphics.Framebuffer(context=gl3_context.context)
    texture = pyglet.graphics.Texture.create(4, 4, blank_data=True, context=gl3_context.context)
    depth_buffer = pyglet.graphics.Renderbuffer(
        gl3_context.context,
        4,
        4,
        component_format=ComponentFormat.D,
        bit_size=16,
    )
    try:
        framebuffer.attach_texture(texture)
        framebuffer.attach_renderbuffer(depth_buffer, attachment=FramebufferAttachment.DEPTH)

        assert framebuffer.width == 4
        assert framebuffer.height == 4

        framebuffer.bind()
        try:
            assert framebuffer.is_complete
            assert framebuffer.get_status() == "Framebuffer is complete."
        finally:
            framebuffer.unbind()
    finally:
        framebuffer.delete()
        depth_buffer.delete()
        texture.delete()
