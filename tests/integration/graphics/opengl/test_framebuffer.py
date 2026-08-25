from ctypes import byref

import pyglet
import pytest

from pyglet.enums import ComponentFormat, FramebufferAttachment, FramebufferTarget
from pyglet.graphics.api.gl import gl
from tests.annotations import skip_graphics_api, GraphicsAPIGroups


def _get_bound_framebuffer_id() -> int:
    binding = gl.GLint()
    gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING, byref(binding))
    return binding.value


def test_framebuffer_creation_and_binding(test_window):
    test_window.switch_to()

    framebuffer = pyglet.graphics.Framebuffer(context=test_window.context)
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


def test_framebuffer_attach_texture_and_readback(test_window):
    test_window.switch_to()

    framebuffer = pyglet.graphics.Framebuffer(context=test_window.context)
    texture = pyglet.graphics.Texture.create(2, 2, blank_data=True, context=test_window.context)
    try:
        framebuffer.attach_texture(texture)
        assert framebuffer.width == 2
        assert framebuffer.height == 2

        framebuffer.bind()
        try:
            assert framebuffer.is_complete
            assert framebuffer.get_status() == "Framebuffer is complete."
        finally:
            framebuffer.unbind()

        gl.glViewport(0, 0, 2, 2)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_BLEND)
        gl.glClearColor(1.0, 0.0, 0.0, 1.0)
        framebuffer.clear()
        assert gl.glGetError() == gl.GL_NO_ERROR

        data = bytes(texture.get_image_data().get_bytes("RGBA", 8))
        assert data == bytes([255, 0, 0, 255]) * 4
    finally:
        framebuffer.delete()
        texture.delete()


def test_framebuffer_attach_depth_renderbuffer(test_window):
    test_window.switch_to()

    framebuffer = pyglet.graphics.Framebuffer(context=test_window.context)
    texture = pyglet.graphics.Texture.create(4, 4, blank_data=True, context=test_window.context)
    depth_buffer = pyglet.graphics.Renderbuffer(
        4,
        4,
        component_format=ComponentFormat.D,
        bit_size=16,
        context=test_window.context,
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


@skip_graphics_api(GraphicsAPIGroups.GL2)
def test_framebuffer_context_restores_separate_draw_and_read_bindings(test_window):
    test_window.switch_to()
    target = pyglet.graphics.Framebuffer(context=test_window.context)
    draw_framebuffer = pyglet.graphics.Framebuffer(
        target=FramebufferTarget.DRAW,
        context=test_window.context,
    )
    read_framebuffer = pyglet.graphics.Framebuffer(
        target=FramebufferTarget.READ,
        context=test_window.context,
    )

    try:
        draw_framebuffer.bind()
        read_framebuffer.bind()

        with target:
            assert _get_bound_framebuffer_id() == target.id

        draw_binding = gl.GLint()
        read_binding = gl.GLint()
        gl.glGetIntegerv(gl.GL_DRAW_FRAMEBUFFER_BINDING, byref(draw_binding))
        gl.glGetIntegerv(gl.GL_READ_FRAMEBUFFER_BINDING, byref(read_binding))
        assert draw_binding.value == draw_framebuffer.id
        assert read_binding.value == read_framebuffer.id
    finally:
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        target.delete()
        draw_framebuffer.delete()
        read_framebuffer.delete()


def test_render_texture_context_draws_clears_and_restores_state(test_window):
    test_window.switch_to()
    original_camera = test_window.camera
    viewport_type = gl.GLint * 4
    original_viewport_values = viewport_type()
    gl.glGetIntegerv(gl.GL_VIEWPORT, original_viewport_values)
    original_viewport = tuple(original_viewport_values)
    handler_count = len(test_window._event_stack)  # noqa: SLF001
    target = pyglet.graphics.RenderTexture(32, 16)
    assert len(test_window._event_stack) == handler_count  # noqa: SLF001
    rectangle = pyglet.shapes.Rectangle(4, 3, 12, 8, color=(255, 0, 0))

    try:
        with target:
            assert test_window.camera is target.camera
            assert _get_bound_framebuffer_id() == target.framebuffer.id
            rectangle.draw()

        assert test_window.camera is original_camera
        assert _get_bound_framebuffer_id() == 0
        actual_viewport = viewport_type()
        gl.glGetIntegerv(gl.GL_VIEWPORT, actual_viewport)
        assert tuple(actual_viewport) == original_viewport

        pixels = bytes(target.texture.fetch().get_bytes("RGBA", target.width * 4))
        rgba = list(zip(*(iter(pixels),) * 4))
        assert any(red > 0 and alpha > 0 for red, _, _, alpha in rgba)
        assert any(alpha == 0 for _, _, _, alpha in rgba)

        with target:
            pass
        assert bytes(target.texture.fetch().get_bytes("RGBA", target.width * 4)) == bytes(target.width * target.height * 4)

        with pytest.raises(RuntimeError, match="test restoration"), target:
            raise RuntimeError("test restoration")
        assert test_window.camera is original_camera
        assert _get_bound_framebuffer_id() == 0
    finally:
        rectangle.delete()
        target.delete()
        assert target.texture.id is not None
        target.texture.delete()


def test_render_texture_restores_custom_camera_auto_viewport(test_window):
    test_window.switch_to()
    camera = pyglet.window.camera.Camera2D(test_window)
    original_viewport = camera.viewport
    assert camera.view._auto_viewport  # noqa: SLF001
    target = pyglet.graphics.RenderTexture(24, 12, camera=camera, depth=True)

    try:
        assert target.depth_buffer is not None
        with target:
            assert camera.viewport == (0, 0, 24, 12)
        assert camera.viewport == original_viewport
        assert camera.view._auto_viewport  # noqa: SLF001
    finally:
        target.delete(delete_texture=True)
        test_window.remove_handlers(camera)


def test_render_texture_contexts_can_be_nested(test_window):
    test_window.switch_to()
    original_camera = test_window.camera
    outer = pyglet.graphics.RenderTexture(32, 16)
    inner = None

    try:
        with outer:
            assert test_window.camera is outer.camera
            assert _get_bound_framebuffer_id() == outer.framebuffer.id

            # Construction must preserve an already-bound render target too.
            inner = pyglet.graphics.RenderTexture(8, 4)
            assert _get_bound_framebuffer_id() == outer.framebuffer.id

            with inner:
                assert test_window.camera is inner.camera
                assert _get_bound_framebuffer_id() == inner.framebuffer.id

            assert test_window.camera is outer.camera
            assert _get_bound_framebuffer_id() == outer.framebuffer.id

        assert test_window.camera is original_camera
        assert _get_bound_framebuffer_id() == 0
    finally:
        if inner is not None:
            inner.delete(delete_texture=True)
        outer.delete(delete_texture=True)


def test_texture_render_target_reuses_framebuffer_and_camera(test_window):
    test_window.switch_to()
    target = pyglet.graphics.TextureRenderTarget()
    framebuffer = target.framebuffer
    camera = target.camera
    rectangle = pyglet.shapes.Rectangle(1, 1, 4, 4, color=(255, 0, 0))
    textures = []

    try:
        failed_texture = None
        with pytest.raises(RuntimeError, match="failed render"), target.render_to_texture(4, 4) as failed_texture:
            raise RuntimeError("failed render")
        assert failed_texture.id is None
        assert target.texture is None

        for width, height in ((16, 8), (32, 12)):
            with target.render_to_texture(width, height) as texture:
                textures.append(texture)
                assert target.texture is texture
                assert target.width == width
                assert target.height == height
                rectangle.draw()

            assert target.texture is None
            assert target.framebuffer is framebuffer
            assert target.camera is camera

        assert textures[0].id != textures[1].id
        assert (textures[0].width, textures[0].height) == (16, 8)
        assert (textures[1].width, textures[1].height) == (32, 12)
        for texture in textures:
            pixels = bytes(texture.fetch().get_bytes("RGBA", texture.width * 4))
            assert any(alpha > 0 for alpha in pixels[3::4])
    finally:
        rectangle.delete()
        target.delete()
        for texture in textures:
            texture.delete()
