"""Tests for window settings."""

import time

from tests.interactive.interactive_test_base import (InteractiveTestCase,
        requires_user_action, requires_user_validation)
from tests.interactive.window import window_util

from pyglet.gl import *
from pyglet import image
from pyglet.window import key, Window, ImageMouseCursor
from pyglet.window.event import WindowEventLogger


@requires_user_action
class WINDOW_SET_EXCLUSIVE_KEYBOARD(InteractiveTestCase):
    """Test that exclusive keyboard mode can be set.

    Expected behaviour:
        One window will be opened.  Press 'e' to enable exclusive mode and 'E'
        to disable exclusive mode.

        In exclusive mode:
        - Pressing system keys, the Expose keys, etc., should have no effect
        besides displaying as keyboard events.
            - On OS X, the Power switch is not disabled (though this is possible
            if desired, see source).
            - On OS X, the menu bar and dock will disappear during keyboard
            exclusive mode.
            - On Windows, only Alt+Tab is disabled.  A user can still switch away
            using Ctrl+Escape, Alt+Escape, the Windows key or Ctrl+Alt+Del.
        - Switching to another application (i.e., with the mouse) should make
        these keys work normally again until this application regains focus.

        Close the window or press ESC to end the test.
    """
    def on_key_press(self, symbol, modifiers):
        print 'Pressed %s with modifiers %s' % \
            (key.symbol_string(symbol), key.modifiers_string(modifiers))

        if symbol == key.E:
            exclusive = not (modifiers & key.MOD_SHIFT)
            self.w.set_exclusive_keyboard(exclusive)
            print 'Exclusive keyboard is now %r' % exclusive

    def on_key_release(self, symbol, modifiers):
        print 'Released %s with modifiers %s' % \
            (key.symbol_string(symbol), key.modifiers_string(modifiers))

    def test_set_exclusive_keyboard(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height)
        try:
            w.push_handlers(self)
            while not w.has_exit:
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_action
class WINDOW_SET_EXCLUSIVE_MOUSE(InteractiveTestCase):
    """Test that exclusive mouse mode can be set.

    Expected behaviour:
        One window will be opened.  Press 'e' to enable exclusive mode and 'E'
        to disable exclusive mode.

        In exclusive mode:
        - the mouse cursor should be invisible
        - moving the mouse should generate events with bogus x,y but correct
        dx and dy.
        - it should not be possible to switch applications with the mouse
        - if application loses focus (i.e., with keyboard), the mouse should
        operate normally again until focus is returned to the app, in which
        case it should hide again.

        Close the window or press ESC to end the test.
    """
    def on_key_press(self, symbol, modifiers):
        if symbol == key.E:
            exclusive = not (modifiers & key.MOD_SHIFT)
            self.w.set_exclusive_mouse(exclusive)
            print 'Exclusive mouse is now %r' % exclusive

    def on_mouse_motion(self, x, y, dx, dy):
        print 'on_mousemotion(x=%f, y=%f, dx=%f, dy=%f)' % (x, y, dx, dy)

    def test_set_exclusive_mouse(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height)
        try:
            w.push_handlers(self)
            while not w.has_exit:
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_action
class WINDOW_SET_FULLSCREEN(InteractiveTestCase):
    """Test that window can be set fullscreen and back again.

    Expected behaviour:
        One window will be opened.  

        - press "f" to enter fullscreen mode.
        - press "g" to leave fullscreen mode.

        All events will be printed to the terminal.

        Close the window or press ESC to end the test.
    """
    def on_key_press(self, symbol, modifiers):
        if symbol == key.F:
            print 'Setting fullscreen.'
            self.w.set_fullscreen(True)
        elif symbol == key.G:
            print 'Leaving fullscreen.'
            self.w.set_fullscreen(False)

    def on_expose(self):
        glClearColor(1, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        self.w.flip()

    def test_set_fullscreen(self):
        self.w = w = Window(200, 200)
        try:
            w.push_handlers(self)
            w.push_handlers(WindowEventLogger())
            self.on_expose()
            while not w.has_exit:
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_validation
class WINDOW_SET_ICON(InteractiveTestCase):
    """Test that window icon can be set.

    Expected behaviour:
        One window will be opened.  It will have an icon depicting a yellow
        "A".
    """
    def test_set_icon(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height)
        try:
            w.set_icon(image.load(self.get_test_data_file('images', 'icon1.png')))
            w.dispatch_events()
            self.user_verify('Does the window have a yellow A icon?')
        finally:
            w.close()


@requires_user_validation
class WINDOW_SET_ICON_SIZES(InteractiveTestCase):
    """Test that window icon can be set for multiple sizes.

    Expected behaviour:
        One window will be opened.  The window's icon depends on the icon
        size:

        16x16 icon is a yellow "1"
        32x32 icon is a purple "2"
        48x48 icon is a cyan "3"
        72x72 icon is a red "4"
        128x128 icon is a blue "5"

        For other sizes, the operating system may select the closest match and
        scale it (Linux, Windows), or interpolate between two or more images
        (Mac OS X).
    """
    def test_set_icon_sizes(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height)
        try:
            w.set_icon(image.load(self.get_test_data_file('images', 'icon_size1.png')),
                    image.load(self.get_test_data_file('images', 'icon_size2.png')),
                    image.load(self.get_test_data_file('images', 'icon_size3.png')),
                    image.load(self.get_test_data_file('images', 'icon_size4.png')),
                    image.load(self.get_test_data_file('images', 'icon_size5.png')))
            w.dispatch_events()
            self.user_verify('Does the window have the icon corresponding to the correct size?')
        finally:
            w.close()


@requires_user_action
class WINDOW_SET_LOCATION(InteractiveTestCase):
    """Test that window location can be set.

    Expected behaviour:
        One window will be opened.  The window's location will be printed
        to the terminal.  

        - Use the arrow keys to move the window.

        Close the window or press ESC to end the test.
    """
    def on_key_press(self, symbol, modifiers):
        x, y = self.w.get_location()
        if symbol == key.LEFT:
            x -= 10
        if symbol == key.RIGHT:
            x += 10
        if symbol == key.UP:
            y -= 10
        if symbol == key.DOWN:
            y += 10
        self.w.set_location(x, y)
        print 'Window location set to %dx%d.' % (x, y)
        print('Window location now: %dx%d.' % self.w.get_location())
        self.assertSequenceEqual((x, y), self.w.get_location())

    def test_set_location(self):
        self.w = w = Window(200, 200)
        try:
            w.push_handlers(self)
            while not w.has_exit:
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_action
class WINDOW_SET_MIN_MAX_SIZE(InteractiveTestCase):
    """Test that minimum and maximum window size can be set.

    Expected behaviour:
        One window will be opened.  The window's dimensions will be printed
        to the terminal.  Initially the window has no minimum or maximum
        size (besides any OS-enforced limit).

        - press "n" to set the minimum size to be the current size.
        - press "x" to set the maximum size to be the current size.

        You should see a green border inside the window but no red.

        Close the window or press ESC to end the test.
    """
    def on_resize(self, width, height):
        print 'Window size is %dx%d.' % (width, height)
        self.width, self.height = width, height

    def on_key_press(self, symbol, modifiers):
        if symbol == key.N:
            self.w.set_minimum_size(self.width, self.height)
            print 'Minimum size set to %dx%d.' % (self.width, self.height)
        elif symbol == key.X:
            self.w.set_maximum_size(self.width, self.height)
            print 'Maximum size set to %dx%d.' % (self.width, self.height)

    def test_min_max_size(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height, resizable=True)
        try:
            w.push_handlers(self)
            while not w.has_exit:
                window_util.draw_client_border(w)
                w.flip()
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_action
class WINDOW_SET_MOUSE_CURSOR(InteractiveTestCase):
    """Test that image mouse cursor can be set.

    Expected behaviour:
        One window will be opened.  The mouse cursor in the window will be
        a custom cursor.

        Close the window or press ESC to end the test.
    """
    def on_mouse_motion(self, x, y, dx, dy):
        print 'on_mousemotion(x=%f, y=%f, dx=%f, dy=%f)' % (x, y, dx, dy)

    def test_set_mouse_cursor(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height)
        try:
            img = image.load(self.get_test_data_file('images', 'cursor.png'))
            w.set_mouse_cursor(ImageMouseCursor(img, 4, 28))
            w.push_handlers(self)
            glClearColor(1, 1, 1, 1)
            while not w.has_exit:
                glClear(GL_COLOR_BUFFER_BIT)
                w.flip()
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_action
class WINDOW_SET_MOUSE_PLATFORM_CURSOR(InteractiveTestCase):
    """Test that mouse cursor can be set to a platform-dependent image.

    Expected behaviour:
        One window will be opened.  Press the left and right arrow keys to cycle
        through the system mouse cursors.  The current cursor selected will
        be printed to the terminal.

        Note that not all cursors are unique on each platform; for example,
        if a platform doesn't define a cursor for a given name, a suitable
        replacement (e.g., a plain arrow) will be used instead.

        Close the window or press ESC to end the test.
    """
    i = 0
    def on_key_press(self, symbol, modifiers):
        names = [
            self.w.CURSOR_DEFAULT,
            self.w.CURSOR_CROSSHAIR,
            self.w.CURSOR_HAND,
            self.w.CURSOR_HELP,
            self.w.CURSOR_NO,
            self.w.CURSOR_SIZE,
            self.w.CURSOR_SIZE_UP,
            self.w.CURSOR_SIZE_UP_RIGHT,
            self.w.CURSOR_SIZE_RIGHT,
            self.w.CURSOR_SIZE_DOWN_RIGHT,
            self.w.CURSOR_SIZE_DOWN,
            self.w.CURSOR_SIZE_DOWN_LEFT,
            self.w.CURSOR_SIZE_LEFT,
            self.w.CURSOR_SIZE_UP_LEFT,
            self.w.CURSOR_SIZE_UP_DOWN,
            self.w.CURSOR_SIZE_LEFT_RIGHT,
            self.w.CURSOR_TEXT,
            self.w.CURSOR_WAIT,
            self.w.CURSOR_WAIT_ARROW,
        ]
        if symbol == key.ESCAPE:
            self.w.on_close()
        if symbol == key.RIGHT:
            self.i = (self.i + 1) % len(names)
        elif symbol == key.LEFT:
            self.i = (self.i - 1) % len(names)
        cursor = self.w.get_system_mouse_cursor(names[self.i])
        self.w.set_mouse_cursor(cursor)
        print 'Set cursor to "%s"' % names[self.i]

        return True

    def test_set_visible(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height)
        try:
            w.push_handlers(self)
            while not w.has_exit:
                glClear(GL_COLOR_BUFFER_BIT)
                w.flip()
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_action
class WINDOW_SET_MOUSE_VISIBLE(InteractiveTestCase):
    """Test that mouse cursor can be made visible and hidden.

    Expected behaviour:
        One window will be opened.  Press 'v' to hide mouse cursor and 'V' to
        show mouse cursor.  It should only affect the mouse when within the
        client area of the window.

        Close the window or press ESC to end the test.
    """
    def on_key_press(self, symbol, modifiers):
        if symbol == key.V:
            visible = (modifiers & key.MOD_SHIFT)
            self.w.set_mouse_visible(visible)
            print 'Mouse is now %s' % (visible and 'visible' or 'hidden')

    def on_mouse_motion(self, x, y, dx, dy):
        print 'on_mousemotion(x=%f, y=%f, dx=%f, dy=%f)' % (x, y, dx, dy)

    def test_set_visible(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height)
        try:
            w.push_handlers(self)
            while not w.has_exit:
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_action
class WINDOW_SET_SIZE(InteractiveTestCase):
    """Test that window size can be set.

    Expected behaviour:
        One window will be opened.  The window's dimensions will be printed
        to the terminal.

        - press "x" to increase the width
        - press "X" to decrease the width
        - press "y" to increase the height
        - press "Y" to decrease the height

        You should see a green border inside the window but no red.

        Close the window or press ESC to end the test.
    """
    def on_key_press(self, symbol, modifiers):
        delta = 20
        if modifiers & key.MOD_SHIFT:
            delta = -delta
        if symbol == key.X:
            self.width += delta
        elif symbol == key.Y:
            self.height += delta
        self.w.set_size(self.width, self.height)
        print 'Window size set to %dx%d.' % (self.width, self.height)

    def test_set_size(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height, resizable=True)
        try:
            w.push_handlers(self)
            while not w.has_exit:
                window_util.draw_client_border(w)
                w.flip()
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_validation
class WINDOW_SET_VISIBLE(InteractiveTestCase):
    """Test that the window can be hidden and shown.

    Expected behaviour:
        One window will be opened. It will toggle between
        hidden and shown.
    """
    def test_set_visible(self):
        w = Window(200, 200)
        try:
            w.push_handlers(WindowEventLogger())
            w.dispatch_events()
            self.user_verify('Is the window visible?', take_screenshot=False)

            w.set_visible(False)
            w.dispatch_events()
            self.user_verify('Is the window no longer visible?', take_screenshot=False)

            w.set_visible(True)
            w.dispatch_events()
            self.user_verify('Is the window visible again?', take_screenshot=False)

        finally:
            w.close()


@requires_user_action
class WINDOW_SET_VSYNC(InteractiveTestCase):
    """Test that vsync can be set.

    Expected behaviour:
        A window will alternate between red and green fill.

        - Press "v" to toggle vsync on/off.  "Tearing" should only be visible
            when vsync is off (as indicated at the terminal).

        Not all video drivers support vsync.  On Linux, check the output of
        `tools/info.py`:

        - If GLX_SGI_video_sync extension is present, should work as expected.
        - If GLX_MESA_swap_control extension is present, should work as expected.
        - If GLX_SGI_swap_control extension is present, vsync can be enabled,
            but once enabled, it cannot be switched off (there will be no error
            message).
        - If none of these extensions are present, vsync is not supported by
            your driver, but no error message or warning will be printed.

        Close the window or press ESC to end the test.
    """
    colors = [(1, 0, 0, 1), (0, 1, 0, 1)]
    color_index = 0

    def open_window(self):
        return Window(200, 200, vsync=False)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.V:
            vsync = not self.w1.vsync
            self.w1.set_vsync(vsync)
            print 'vsync is %r' % self.w1.vsync

    def draw_window(self, window, colour):
        window.switch_to()
        glClearColor(*colour)
        glClear(GL_COLOR_BUFFER_BIT)
        window.flip()

    def test_open_window(self):
        self.w1 = self.open_window()
        try:
            self.w1.push_handlers(self)
            print 'vsync is %r' % self.w1.vsync
            while not self.w1.has_exit:
                self.color_index = 1 - self.color_index
                self.draw_window(self.w1, self.colors[self.color_index])
                self.w1.dispatch_events()
        finally:
            self.w1.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_action
class WINDOW_SET_CAPTION(InteractiveTestCase):
    """Test that the window caption can be set.

    Expected behaviour:
        Two windows will be opened, one with the caption "Window caption 1"
        counting up every second; the other with a Unicode string including
        some non-ASCII characters.

        Press escape or close either window to finished the test.
    """
    def test_caption(self):
        try:
            w1 = Window(400, 200, resizable=True)
            w2 = Window(400, 200, resizable=True)
            count = 1
            w1.set_caption('Window caption %d' % count)
            w2.set_caption(u'\u00bfHabla espa\u00f1ol?')
            last_time = time.time()
            while not (w1.has_exit or w2.has_exit):
                if time.time() - last_time > 1:
                    count += 1
                    w1.set_caption('Window caption %d' % count)
                    last_time = time.time()
                w1.dispatch_events()
                w2.dispatch_events()
        finally:
            w1.close()
            w2.close()
        self.user_verify('Pass test?', take_screenshot=False)


@requires_user_action
class WINDOW_FIXED_SET_SIZE(InteractiveTestCase):
    """Test that a non-resizable window's size can be set.

    Expected behaviour:
        One window will be opened.  The window's dimensions will be printed
        to the terminal.

        - press "x" to increase the width
        - press "X" to decrease the width
        - press "y" to increase the height
        - press "Y" to decrease the height

        You should see a green border inside the window but no red.

        Close the window or press ESC to end the test.
    """
    def on_key_press(self, symbol, modifiers):
        delta = 20
        if modifiers & key.MOD_SHIFT:
            delta = -delta
        if symbol == key.X:
            self.width += delta
        elif symbol == key.Y:
            self.height += delta
        self.w.set_size(self.width, self.height)
        print 'Window size set to %dx%d.' % (self.width, self.height)

    def test_set_size(self):
        self.width, self.height = 200, 200
        self.w = w = Window(self.width, self.height)
        try:
            w.push_handlers(self)
            while not w.has_exit:
                window_util.draw_client_border(w)
                w.flip()
                w.dispatch_events()
        finally:
            w.close()
        self.user_verify('Pass test?', take_screenshot=False)


