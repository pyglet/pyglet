import pyglet

from pyglet.graphics.api.gl import gl
from pyglet.graphics.api.gl2.framebuffer import GL2Framebuffer
from tests.annotations import GraphicsAPIGroups, require_graphics_api


pytestmark = require_graphics_api(GraphicsAPIGroups.GL2)


def test_gles2_fetch_uses_gl2_framebuffer_and_restores_state(test_window):
    test_window.switch_to()
    context = test_window.context
    texture = pyglet.graphics.Texture.create(2, 2, blank_data=True, context=context)
    framebuffer = GL2Framebuffer(context=context)
    framebuffer.bind()
    expected = gl.GLint()
    context.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING, expected)

    try:
        texture.fetch()
        if context.info.pixel_transfer.direct_texture_readback:
            return
        assert isinstance(context.pixel_readback.get_framebuffer(), GL2Framebuffer)

        actual = gl.GLint()
        context.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING, actual)
        assert actual.value == expected.value
    finally:
        framebuffer.unbind()
        framebuffer.delete()
