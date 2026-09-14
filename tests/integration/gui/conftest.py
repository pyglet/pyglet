import pytest

from pyglet.gui.frame import Frame


@pytest.fixture
def frame(test_window):
    gui_frame = Frame(test_window)
    yield gui_frame
    gui_frame.enable = False
