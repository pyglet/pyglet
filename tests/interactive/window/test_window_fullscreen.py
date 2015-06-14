from __future__ import print_function
from __future__ import absolute_import
from builtins import range
from tests.interactive.interactive_test_base import (InteractiveTestCase,
        requires_user_action, requires_user_validation)

from pyglet import window
from pyglet.window.event import WindowEventLogger
from pyglet.window import key
from pyglet.gl import *

from . import window_util


@requires_user_action
class WINDOW_SET_FULLSCREEN(InteractiveTestCase):
    """Test that window can be set to and from various fullscreen sizes.

    Expected behaviour:
        One window will be opened.  Press a number to switch to the corresponding
        fullscreen size; hold control and press a number to switch back
        to the corresponding window size:

            0 - Default size
            1 - 320x200
            2 - 640x480
            3 - 800x600
            4 - 1024x768
            5 - 1280x800 (widescreen)
            6 - 1280x1024

        In all cases the window bounds will be indicated by a green rectangle
        which should be completely visible.

        All events will be printed to the terminal.

        Press ESC to end the test.
    """
    def on_key_press(self, symbol, modifiers):
        fullscreen = not modifiers & key.MOD_CTRL
        doing = fullscreen and 'Setting' or 'Restoring from'
        if symbol == key._0:
            print('%s default size' % doing)
            self.w.set_fullscreen(fullscreen)
            return
        elif symbol == key._1:
            width, height = 320, 200
        elif symbol == key._2:
            width, height = 640, 480
        elif symbol == key._3:
            width, height = 800, 600
        elif symbol == key._4:
            width, height = 1024, 768
        elif symbol == key._5:
            width, height = 1280, 800 # 16:10
        elif symbol == key._6:
            width, height = 1280, 1024
        else:
            return
        print('%s width=%d, height=%d' % (doing, width, height))
        self.w.set_fullscreen(fullscreen, width=width, height=height)

    def on_expose(self):
        glClearColor(1, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        window_util.draw_client_border(self.w)
        self.w.flip()

    def test_set_fullscreen(self):
        self.w = w = window.Window(200, 200)
        try:
            w.push_handlers(self)
            w.push_handlers(WindowEventLogger())
            self.on_expose()
            while not w.has_exit:
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_action
class WINDOW_INITIAL_FULLSCREEN(InteractiveTestCase):
    """Test that a window can be opened fullscreen.

    Expected behaviour:
        A fullscreen window will be created, with a flat purple colour.

        - Press 'g' to leave fullscreen mode and create a window.
        - Press 'f' to re-enter fullscreen mode.
        - All events will be printed to the console.  Ensure that mouse,
        keyboard and activation/deactivation events are all correct.

        Close either window or press ESC to end the test.
    """
    def on_key_press(self, symbol, modifiers):
        if symbol == key.F:
            print('Setting fullscreen.')
            self.w.set_fullscreen(True)
        elif symbol == key.G:
            print('Leaving fullscreen.')
            self.w.set_fullscreen(False)

    def on_expose(self):
        glClearColor(1, 0, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        self.w.flip()

    def test_initial_fullscreen(self):
        self.w = window.Window(fullscreen=True)
        try:
            self.w.push_handlers(self)
            self.w.push_handlers(WindowEventLogger())
            self.on_expose()
            while not self.w.has_exit:
                self.w.dispatch_events()
        finally:
            self.w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_validation
class MULTIPLE_SCREEN(InteractiveTestCase):
    """Test that screens can be selected for fullscreen.

    Expected behaviour:
        One window will be created fullscreen on the primary screen.  When you
        close this window, another will open on the next screen, and so
        on until all screens have been tested.

        Each screen will be filled with a different color:
        - Screen 0: Red
        - Screen 1: Green
        - Screen 2: Blue
        - Screen 3: Purple

        The test will end when all screens have been tested.
    """
    colours = [
        (1, 0, 0, 1),
        (0, 1, 0, 1),
        (0, 0, 1, 1),
        (1, 0, 1, 1)]
    colour_names = ('red', 'green', 'blue', 'purple')

    def open_next_window(self):
        screen = self.screens[self.index]
        self.w = window.Window(screen=screen, fullscreen=True)

    def on_expose(self):
        self.w.switch_to()
        glClearColor(*self.colours[self.index])
        glClear(GL_COLOR_BUFFER_BIT)
        self.w.flip()

    def test_multiple_screen(self):
        display = window.get_platform().get_default_display()
        self.screens = display.get_screens()
        for i in range(len(self.screens)):
            self.index = i
            self.open_next_window()
            try:
                self.on_expose()
                self.w.dispatch_events()
                self.user_verify('Do you see a {} full screen window on screen {}?'.format(
                    self.colour_names[i], i+1))
            finally:
                self.w.close()

