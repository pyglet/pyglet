"""macOS current-screen API placeholder."""

from __future__ import annotations

import sys

import pytest

if sys.platform != "darwin":
    pytest.skip("macOS-only tests", allow_module_level=True)

from pyglet.window.apple.cocoa import CocoaWindow


def test_current_screen_reports_unimplemented():
    with pytest.raises(NotImplementedError, match="macOS"):
        CocoaWindow.get_current_screen(object())
