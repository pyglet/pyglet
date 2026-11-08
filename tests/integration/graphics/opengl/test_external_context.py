from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import Mock

import pytest

import pyglet
from pyglet.graphics import GraphicsIntegrationError
from pyglet.graphics.api.gl import ExternalOpenGLContext, gl
from pyglet.window import Window
from tests.annotations import GraphicsAPIGroups, Platform, require_graphics_api, skip_platform


pytestmark = [require_graphics_api(GraphicsAPIGroups.GL3), skip_platform(Platform.HOST_DRIVEN)]


@pytest.fixture
def host_window() -> Iterator[Window]:
    """Provide a hidden native context owned independently of the adapter."""
    window = Window(width=16, height=16, visible=False)
    try:
        yield window
    finally:
        window.close()


@pytest.mark.parametrize('already_current', [False, True])
def test_wrap_current_context_without_creating_a_window(host_window: Window, already_current: bool) -> None:
    """Wrap an existing context and initialize GL without creating another window."""
    host_window.switch_to()
    windows = set(pyglet.app.windows)
    # A host may supply an already-current context and need no activation call.
    make_current = Mock(wraps=(lambda: None) if already_current else host_window.switch_to)
    adapter = ExternalOpenGLContext(make_current)
    try:
        # Construction must leave the owner's context alone.
        make_current.assert_not_called()
        assert pyglet.graphics.api.core.current_context is host_window.context
        assert set(pyglet.app.windows) == windows

        adapter.set_current()
        make_current.assert_called_once_with()
        assert pyglet.graphics.api.core.current_context is adapter
        assert adapter.glGetString(gl.GL_VERSION)
        assert adapter.info.was_queried

        adapter.release()
        assert not pyglet.graphics.api.core.current_context
        assert set(pyglet.app.windows) == windows
        assert not host_window.visible
    finally:
        adapter.destroy()


def test_wrapped_context_renders_and_presents(host_window: Window) -> None:
    """Render a pixel through the adapter and invoke host presentation and release callbacks."""
    present = Mock()
    done_current = Mock()
    adapter = ExternalOpenGLContext(host_window.switch_to, present=present, done_current=done_current)
    try:
        with adapter.frame():
            adapter.set_clear_color(1, 0, 0, 1)
            adapter.clear()
            pixel = (gl.GLubyte * 4)()
            adapter.glReadPixels(0, 0, 1, 1, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, pixel)
            assert tuple(pixel)[:3] == (255, 0, 0)

        present.assert_called_once_with()
        done_current.assert_called_once_with()
        assert adapter.frame_index == 1
        assert not adapter.frame_active
        assert not pyglet.graphics.api.core.current_context
    finally:
        adapter.destroy()


def test_destroy_leaves_native_context_and_host_resources_alive(host_window: Window) -> None:
    """Destroy the adapter while preserving the host's native context and texture."""
    host_window.switch_to()
    texture = pyglet.graphics.Texture.create(1, 1, blank_data=True, context=host_window.context)
    adapter = ExternalOpenGLContext(host_window.switch_to)
    try:
        adapter.set_current()
        assert adapter.glIsTexture(texture.id)
        adapter.destroy()

        host_window.switch_to()
        assert host_window.context.glIsTexture(texture.id)
        version = host_window.context.glGetString(gl.GL_VERSION)
        assert version
        with pytest.raises(GraphicsIntegrationError, match='destroyed'):
            adapter.set_current()
    finally:
        adapter.destroy()
        host_window.switch_to()
        texture.delete()


@pytest.mark.parametrize('activation_succeeds', [False, True])
def test_failed_host_activation_clears_tracking(host_window: Window, activation_succeeds: bool) -> None:
    """Reject failed host activation and clear pyglet's current-context tracking."""
    make_current = Mock(return_value=activation_succeeds)
    adapter = ExternalOpenGLContext(make_current, is_current=lambda: False)
    try:
        with pytest.raises(GraphicsIntegrationError, match='failed to make'):
            adapter.set_current()
        make_current.assert_called_once_with()
        assert not pyglet.graphics.api.core.current_context
    finally:
        # There is deliberately no usable host callback for destroy().
        adapter.invalidate()
        host_window.switch_to()
