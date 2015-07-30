"""
Base classes for test cases using the normal pyglet application event loop.
"""

import pyglet
from pyglet.window import Window, key
from tests.interactive.interactive_test_base import InteractiveTestCase


class EventLoopTestCase(InteractiveTestCase):
    def test_run(self):
        w = QuestionWindow(self, "Description of the test.")
        pyglet.app.run()
        w.handle_result()



class QuestionWindow(Window):

    question = '(P)ass/(F)ail/(S)kip/(Q)uit?'
    key_pass = key.P
    key_fail = key.F
    key_skip = key.S
    key_quit = key.Q  # Not supported yet

    def __init__(self, test_case, description, *args, **kwargs):
        super(QuestionWindow, self).__init__(*args, **kwargs)

        self.test_case = test_case
        self.description = description

        self.create_label()

        self.result = None

    def create_label(self):
        self.label = pyglet.text.Label(self.description + '\n\n' + self.question)

    def on_draw(self):
        self.clear()
        self.label.draw()

    def on_key_press(self, symbol, modifiers):
        if symbol in (self.key_pass, self.key_fail, self.key_skip):
            self.result = symbol
            self.close()

        # Prevent handling of Escape to close the window
        return True

    def handle_result(self):
        if self.result is None:
            raise Exception('Did not receive valid input in question window')
        elif self.result == self.key_fail:
            # TODO: Ask input
            self.test_case.fail('Tester marked test failed')
        elif self.result == self.key_skip:
            self.test_case.skip('Tester marked test skipped')
        elif self.result == self.key_quit:
            # Not supported yet
            pass

