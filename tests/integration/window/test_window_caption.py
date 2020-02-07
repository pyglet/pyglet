import sys
import pyglet


window_captions = [u'テスト.py', u'\u00bfHabla espa\u00f1ol?', 'test']


def test_window_caption():
    """Test that the Window caption is correctly set on instantiation. """
    for test_caption in window_captions:
        window = pyglet.window.Window(caption=test_caption)
        assert window.caption == test_caption
        window.close()


def test_window_caption_from_argv():
    """Test that the window caption is set from sys.argv[0], if none is explicity set. """
    for test_caption in window_captions:

        # Override sys.argv[0] so that the file name appears to be the caption:
        sys.argv[0] = test_caption

        # The window caption should be set to the file name:
        window = pyglet.window.Window()
        assert window.caption == test_caption
        window.close()
