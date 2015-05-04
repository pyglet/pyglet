from pyglet import window
from tests.interactive.windowed_test_base import WindowedTestCase


class WindowStylesTest(WindowedTestCase):
    """Test available window styles."""
    pass

WindowStylesTest.create_test_case(
        name='test_style_borderless',
        description='Test that window style can be borderless.',
        question='Do you see one borderless window?',
        window_options={'style': window.Window.WINDOW_STYLE_BORDERLESS}
        )

WindowStylesTest.create_test_case(
        name='test_style_tool',
        description='Test that window style can be tool.',
        question='Do you see one tool-styled window?',
        window_options={'style': window.Window.WINDOW_STYLE_TOOL}
        )

WindowStylesTest.create_test_case(
        name='test_style_dialog',
        description='Test that window style can be dialog.',
        question='Do you see one dialog-styled window?',
        window_options={'style': window.Window.WINDOW_STYLE_DIALOG}
        )

