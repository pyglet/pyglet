"""
Tests for events on windows.
"""

import random

from pyglet import font
from pyglet import gl
from pyglet.window import key, Window

from tests.interactive.interactive_test_base import InteractiveTestCase, requires_user_action


class WindowEventsTestCase(InteractiveTestCase):
    """
    Base class that shows a window displaying instructions for the test. Then it waits for events
    to continue. Optionally the user can fail the test by pressing Escape.
    """

    # Defaults
    window_size = 400, 200
    window = None
    question = None

    def setUp(self):
        self.finished = False
        self.failure = None
        self.label = None

    def fail_test(self, failure):
        self.failure = failure
        self.finished = True

    def pass_test(self):
        self.finished = True

    def _render_question(self):
        fnt = font.load('')
        self.label = font.Text(fnt, text=self.question, x=10, y=self.window_size[1]-20)

    def _draw(self):
        gl.glClearColor(0.5, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glLoadIdentity()
        self.label.draw()
        self.window.flip()

    def _test_main(self):
        assert self.question

        width, height = self.window_size
        self.window = w = Window(width, height, visible=False, resizable=False)
        w.push_handlers(self)
        self._render_question()
        w.set_visible()

        while not self.finished and not w.has_exit:
            self._draw()
            w.dispatch_events()

        w.close()

        # TODO: Allow entering reason of failure if user aborts
        self.assertTrue(self.finished, msg="Test aborted")
        self.assertIsNone(self.failure, msg=self.failure)


@requires_user_action
class KeyPressWindowEventTestCase(WindowEventsTestCase):
    number_of_checks = 10
    keys = [key.A, key.B, key.C, key.D, key.E, key.F, key.G, key.H, key.I, key.J, key.K, key.L,
            key.M, key.N, key.O, key.P, key.Q, key.R, key.S, key.T, key.U, key.V, key.W, key.X,
            key.Y, key.Z]

    def setUp(self):
        super(KeyPressWindowEventTestCase, self).setUp()
        self.symbol = None
        self.modifiers = None
        self.pressed = False
        self.checks_passed = 0

    def on_key_press(self, symbol, modifiers):
        if self.pressed:
            self.fail_test('Key already pressed, no release received.')

        elif self._check_key(symbol, modifiers):
            self.pressed = True

    def on_key_release(self, symbol, modifiers):
        if self._check_key(symbol, modifiers):
            self.pressed = False
            self.checks_passed += 1
            if self.checks_passed == self.number_of_checks:
                self.pass_test()
            else:
                self._select_next_key()

    def _select_next_key(self):
        self.symbol = random.choice(self.keys)
        self.modifiers = 0

        self.question = """Please press and release:

{}


Press Esc if test does not pass.""".format(key.symbol_string(self.symbol))
        self._render_question()

    def _check_key(self, symbol, modifiers):
        if not self.symbol:
            self.fail_test('No more key presses/releases expected.')
            return False

        if self.symbol != symbol:
            self.fail_test('Received key "{}", but expected "{}"'.format(key.symbol_string(symbol),
                                                                         key.symbol_string(self.symbol)))
            return False
        if self.modifiers != modifiers:
            self.fail_test('Received modifiers "{}", but expected "{}"'.format(key.modifiers_string(modifiers),
                                                                               key.modifiers_string(self.modifiers)))
            return False

        return True

    def test_key_press_release(self):
        """Show several keys to press. Check that the event is triggered for the correct key."""
        self._select_next_key()
        self._test_main()
