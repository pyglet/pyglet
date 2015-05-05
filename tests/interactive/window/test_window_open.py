from tests.interactive.interactive_test_base import (InteractiveTestCase,
        requires_user_action, requires_user_validation)

from pyglet import window
from pyglet.gl import *

@requires_user_validation
class WINDOW_OPEN(InteractiveTestCase):
    def open_window(self):
        return window.Window(200, 200)

    def draw_window(self, window, colour):
        window.switch_to()
        glClearColor(*colour)
        glClear(GL_COLOR_BUFFER_BIT)
        window.flip()

    def test_open_window(self):
        """Test that a window can be opened.

        Expected behaviour:
            One small window will be opened coloured purple.
        """
        w1 = self.open_window()
        self.draw_window(w1, (1, 0, 1, 1))
        w1.dispatch_events()
        self.user_verify('Do you see one small purple coloured window?')
        w1.close()

    def test_open_multiple_windows(self):
        """Test that multiple windows can be opened.

        Expected behaviour:
            Two small windows will be opened, one coloured yellow and the other
            purple.

            Close either window or press ESC to end the test.
        """
        w1 = self.open_window()
        w2 = self.open_window()
        self.draw_window(w1, (1, 0, 1, 1))
        self.draw_window(w2, (1, 1, 0, 1))
        w1.dispatch_events()
        w2.dispatch_events()
        self.user_verify('Do you see one small purple coloured window '
                         'and one small yellow coloured window?')
        w1.close()
        w2.close()
