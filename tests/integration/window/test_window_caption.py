import sys
import pytest
import pyglet


window_captions = [u'テスト.py', u'\u00bfHabla espa\u00f1ol?', 'test']


def test_window_caption():
    """Test that the Window caption is correctly set on instantiation. """
    for test_caption in window_captions:
        window = pyglet.window.Window(caption=test_caption, visible=False)
        try:
            assert window.caption == test_caption
            assert window.visible is False
        finally:
            window.close()


def test_window_caption_from_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that the window caption is set from sys.argv[0], if none is explicitly set. """
    for test_caption in window_captions:

        # Override sys.argv[0] so that the file name appears to be the caption:
        monkeypatch.setattr(sys, 'argv', [test_caption, *sys.argv[1:]])

        # The window caption should be set to the file name:
        window = pyglet.window.Window(visible=False)
        try:
            assert window.caption == test_caption
            assert window.visible is False
        finally:
            window.close()


def test_window_caption_setter():
    window = pyglet.window.Window(caption="initial", visible=False)
    try:
        window.set_caption("updated")
        assert window.caption == "updated"
        assert window.visible is False
    finally:
        window.close()


@pytest.mark.requires_visible_window
def test_window_visibility_toggle():
    window = pyglet.window.Window(visible=False)
    assert window.visible is False
    window.set_visible(True)
    assert window.visible is True
    window.set_visible(False)
    assert window.visible is False
    window.close()
