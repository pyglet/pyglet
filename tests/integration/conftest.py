import pytest

import pyglet
from ..base.event_loop import event_loop  # noqa: TID252

@pytest.fixture(scope="module")
def test_window():
    """Hidden window for tests that require a current graphics context.

    .. warning:: Do not close this window from a test; doing so can affect later tests in the module.
    """
    test_window = pyglet.window.Window(visible=False)
    yield test_window
    test_window.close()
