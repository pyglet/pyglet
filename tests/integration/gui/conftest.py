import pytest

from pyglet.gui.manager import UIManager


@pytest.fixture
def manager(test_window):
    ui_manager = UIManager(test_window)
    yield ui_manager
    ui_manager.enable = False
