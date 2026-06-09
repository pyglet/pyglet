import pytest

from tests.base.interactive import InteractiveTestCase

from pyglet import app, clock, window


@pytest.mark.requires_user_validation
class WINDOW_OPEN(InteractiveTestCase):
    def open_window(self):
        return window.Window(200, 200)

    def draw_window(self, window, colour):
        window.switch_to()
        window.context.set_clear_color(*colour)
        window.clear()
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

    @pytest.mark.requires_user_action
    def test_open_multiple_windows(self):
        """Test that multiple windows can be opened.

        Expected behaviour:
            Two small windows will be opened, one coloured yellow and the other
            purple.

            Close either window or press ESC to end the test.
        """
        w1 = self.open_window()
        w2 = self.open_window()

        def _exit_if_window_closed(_dt):
            if w1.has_exit or w2.has_exit:
                app.exit()

        try:
            self.draw_window(w1, (1, 0, 1, 1))
            self.draw_window(w2, (1, 1, 0, 1))
            clock.schedule_interval(_exit_if_window_closed, 1 / 30)
            app.run(interval=None)
        finally:
            clock.unschedule(_exit_if_window_closed)
            w1.close()
            w2.close()

        self.user_verify('Pass test?', take_screenshot=False)
