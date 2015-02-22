"""
Interactive tests for pyglet.font
"""

from inspect import cleandoc
import unittest
import sys

from pyglet import gl
from pyglet import font
from pyglet.window import Window

from tests.interactive.interactive_test_base import InteractiveTestCase

class FontTestBase(InteractiveTestCase):
    """
    Default test implementation. Use by creating a subclass and then calling the
    `create_test_case` class method with the name of the test case and any class/instance
    variables to set. This should be called outside the class definition!
    """

    # Defaults
    font_name = ''
    font_size = 24
    text = 'Quickly brown fox'
    window_size = 200, 200
    question = None
    color = 1, 1, 1, 1

    def on_expose(self):
        gl.glClearColor(0.5, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glLoadIdentity()
        self.draw()
        self.window.flip()

    def render(self):
        fnt = font.load(self.font_name, self.font_size) 
        self.label = font.Text(fnt, self.text, 10, 10, color=self.color)

    def draw(self):
        self.label.draw()

    @classmethod
    def create_test_case(cls, name, description=None, **kwargs):
        def run_test(self):
            for name, value in kwargs.items():
                setattr(self, name, value)
            self._test_main()
        run_test.__name__ = name
        if description:
            run_test.__doc__ = cleandoc(description)
        setattr(cls, name, run_test)

    def _test_main(self):
        if not self.question:
            return

        width, height = self.window_size
        self.window = w = Window(width, height, visible=False, resizable=True)
        w.push_handlers(self)
        self.render()
        w.set_visible()
        w.dispatch_events()

        self.user_verify(cleandoc(self.question))

        w.close()

