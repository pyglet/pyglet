"""
Base classes for test cases using the normal pyglet application event loop.
"""

import pyglet
from pyglet.window import Window
from tests.interactive_test_base import InteractiveTestCase


class EventLoopTestCase(InteractiveTestCase):
    def test_run():
        pyglet.app.run()



class QuestionWindow(Window):

    question = '(P)ass/(F)ail/(S)kip/(Q)uit?'

    def __init__(self, test_case, description, *args, **kwargs):
        super(QuestionWindow, self).__init__(*args, **kwargs)

        self.test_case = test_case
        self.description = description

        self.create_label()

    def create_label(self):
        self.label = pyglet.text.Label(self.description)

    def on_draw(self):
        self.clear()
        self.label.draw()
