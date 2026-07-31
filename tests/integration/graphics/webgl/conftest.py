from __future__ import annotations

import sys

import pytest

import pyglet


@pytest.fixture(scope="session")
def webgl_window():
    """Create one real browser canvas and WebGL2 context for the suite."""
    assert sys.platform == "emscripten"
    assert pyglet.compat_platform == "emscripten"

    # The browser process owns this session-scoped canvas. Calling close() here
    # dispatches pyglet's asynchronous WebLoop shutdown from synchronous pytest.
    return pyglet.window.Window(width=128, height=96, caption="pyglet WebGL tests")


@pytest.fixture(autouse=True)
def no_webgl_errors(webgl_window):
    """Keep GL errors attributable to the test that generated them."""
    gl = webgl_window.context.gl
    while gl.getError():
        pass

    yield

    assert gl.getError() == gl.NO_ERROR
