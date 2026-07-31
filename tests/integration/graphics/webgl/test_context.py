from __future__ import annotations

from js import document  # noqa: F821

import pyglet

from pyglet.enums import GraphicsAPI


def test_webgl2_context_and_backend_are_selected(webgl_window):
    assert pyglet.options.backend == GraphicsAPI.WEBGL
    assert webgl_window.canvas.id == pyglet.options.pyodide.canvas_id
    assert document.getElementById(pyglet.options.pyodide.canvas_id) is not None

    info = webgl_window.context.get_info()
    assert info.get_opengl_api() == "webgl"
    assert info.have_version(2, 0)
    assert "WebGL 2" in info.get_version_string()
    assert info.MAX_TEXTURE_SIZE > 0
    assert info.MAX_VERTEX_ATTRIBS > 0


def test_window_resize_updates_the_canvas_and_viewport(webgl_window):
    webgl_window.set_size(96, 64)
    assert webgl_window.get_size() == (96, 64)
    assert webgl_window.canvas.width >= 96
    assert webgl_window.canvas.height >= 64

    webgl_window.context.set_current()
    webgl_window.context.gl.viewport(0, 0, 96, 64)
