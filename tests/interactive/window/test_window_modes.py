import pytest
import time

from tests.annotations import Platform, require_platform
from tests.base.interactive import InteractiveTestCase
from tests.interactive.window import window_util

from pyglet import window
from pyglet.gl import *
from pyglet.window.event import WindowEventLogger

@pytest.mark.requires_user_validation
class WINDOW_MINIMIZE_MAXIMIZE(InteractiveTestCase):
    """Test that window can be minimized and maximized.

    Expected behaviour:
        One window will be opened. It will be maximized and minimized.
    """
    def test_minimize_maximize(self):
        self.width, self.height = 200, 200
        self.w = w = window.Window(self.width, self.height, resizable=True)
        try:
            w.dispatch_events()
            self.user_verify('Is the window visible and not maximized?',
                             take_screenshot=False)

            w.maximize()
            w.dispatch_events()
            self.user_verify('Is the window maximized?',
                             take_screenshot=False)

            w.minimize()
            w.dispatch_events()
            self.user_verify('Is the window minimized?',
                             take_screenshot=False)

        finally:
            w.close()


@pytest.mark.requires_user_action
class WINDOW_ACTIVATE(InteractiveTestCase):
    """Test that the window can be activated (focus set).

    Expected behaviour:
        One window will be opened.  Every 5 seconds it will be activated;
        it should be come to the front and accept keyboard input (this will
        be shown on the terminal).

        On some OSes, the taskbar icon may flash (indicating the application
        requires attention) rather than moving the window to the foreground.  This
        is the correct behaviour.

        Press escape or close the window to finished the test.
    """
    def test_activate(self):
        w = window.Window(200, 200)
        try:
            w.push_handlers(WindowEventLogger())
            last_time = time.time()
            while not w.has_exit:
                if time.time() - last_time > 5:
                    w.activate()
                    last_time = time.time()
                    print('Activated window.')
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@pytest.mark.requires_user_action
class WINDOW_RESIZABLE(InteractiveTestCase):
    """Test that window can be resized.

    Expected behaviour:
        One window will be opened.  It should be resizable by the user. 

        Close the window or press ESC to end the test.
    """
    def test_resizable(self):
        self.width, self.height = 200, 200
        self.w = w = window.Window(self.width, self.height, resizable=True)
        try:
            glClearColor(1, 1, 1, 1)
            while not w.has_exit:
                window_util.draw_client_border(w)
                w.flip()
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@pytest.mark.requires_user_action
@require_platform(Platform.WINDOWS + Platform.OSX)
class WINDOW_MODE_SWITCH(InteractiveTestCase):
    """Test switching to available screen modes."""
    def on_text(self, text):
        text = text[:1]
        i = ord(text) - ord('a')
        if 0 <= i < len(self.modes):
            print('Switching to %s' % self.modes[i])
            self.w.screen.set_mode(self.modes[i])

    def on_expose(self):
        glClearColor(1, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        window_util.draw_client_border(self.w)
        self.w.flip()

    def test_set_fullscreen(self):
        self.w = w = window.Window(200, 200)
        try:
            self.modes = w.screen.get_modes()
            self.assertTrue(len(self.modes) > 0, msg='No modes available')
            print('Press a letter to switch to the corresponding mode:')
            for i, mode in enumerate(self.modes):
                print('%s: %s' % (chr(i + ord('a')), mode))

            w.push_handlers(self)
            self.on_expose()
            while not w.has_exit:
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)
