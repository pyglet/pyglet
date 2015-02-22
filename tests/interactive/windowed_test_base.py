"""Base class for interactive tests spawning a basic window."""

from inspect import cleandoc

from pyglet import gl
from pyglet.window import Window

from tests.interactive.interactive_test_base import InteractiveTestCase


class WindowedTestCase(InteractiveTestCase):
    """
    Base class for tests that show a window, render something in that window and then ask a 
    question to the user whether the contents are correct. Also takes a screenshot when the
    test is passed, so it can run without interaction afterwards.
    """

    # Defaults
    window_size = 200, 200
    window = None
    question = None

    # Methods to override in implementations
    def on_expose(self):
        pass

    def render(self):
        pass

    def draw(self):
        pass

    # Implementation of the base test class
    @classmethod
    def create_test_case(cls, name, description=None, decorators=None, **kwargs):
        def run_test(self):
            for name, value in kwargs.items():
                setattr(self, name, value)
            self._test_main()
        run_test.__name__ = name
        if description:
            run_test.__doc__ = cleandoc(description)
        if decorators:
            for decorator in decorators:
                run_test = decorator(run_test)
        setattr(cls, name, run_test)

    def _test_main(self):
        assert self.question

        width, height = self.window_size
        self.window = w = Window(width, height, visible=False, resizable=True)
        w.push_handlers(self)
        self.render()
        w.set_visible()
        w.dispatch_events()

        self.user_verify(cleandoc(self.question))

        w.close()

