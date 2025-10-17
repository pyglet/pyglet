import pytest

import pyglet
from ..base.event_loop import event_loop  # noqa: TID252

@pytest.fixture(scope="module")
def gl3_context():
    """Global OpenGL context for tests that require an OpenGL context.

    .. warning:: Any test that uses this should not destroy the context or unexpected behavior can occur.
    """
    window = pyglet.window.Window(visible=False)
    yield window
    window.close()
