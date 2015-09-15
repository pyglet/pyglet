"""
Base classes for test cases using the normal pyglet application event loop.
"""

import pytest

import pyglet
from pyglet import clock
from pyglet import gl
from pyglet.graphics import Batch
from pyglet.text.document import FormattedDocument
from pyglet.text.layout import TextLayout
from pyglet.window import Window, key

from .interactive_test_base import InteractiveFixture


@pytest.fixture
def event_loop(request):
    return EventLoopFixture(request)


class TestWindow(Window):

    question = '\n\n(P)ass/(F)ail/(S)kip/(Q)uit?'
    key_pass = key.P
    key_fail = key.F
    key_skip = key.S
    key_quit = key.Q
    clear_color = 1, 1, 1, 1
    base_options = {
            'width': 300,
            'height': 300,
            }

    def __init__(self, fixture, **kwargs):
        combined_kwargs = {}
        combined_kwargs.update(self.base_options)
        combined_kwargs.update(kwargs)
        super(TestWindow, self).__init__(**combined_kwargs)

        self._fixture = fixture
        self.answer = None
        self._create_text()

    def _create_text(self):
        self.batch = Batch()
        self.document = FormattedDocument()
        layout = TextLayout(self.document, self.width, self.height,
                multiline=True, wrap_lines=True, batch=self.batch)
        layout.content_valign = 'bottom'

    def add_text(self, text):
        self.document.insert_text(len(self.document.text), text)

    def ask_question(self):
        self.document.insert_text(len(self.document.text), self.question)
        self.answer = None

    def on_draw(self):
        gl.glClearColor(*self.clear_color)
        self.clear()
        self.batch.draw()

    def on_key_press(self, symbol, modifiers):
        if symbol in (self.key_pass, self.key_fail, self.key_skip, self.key_quit):
            self.answer = symbol
            self._fixture.interrupt_event_loop()

        # Prevent handling of Escape to close the window
        return True

    def handle_answer(self):
        if self.answer is None:
            raise Exception('Did not receive valid input in question window')
        elif self.answer == self.key_fail:
            # TODO: Ask input
            pytest.fail('Tester marked test failed')
        elif self.answer == self.key_skip:
            pytest.skip('Tester marked test skipped')
        elif self.answer == self.key_quit:
            pytest.exit('Tester requested to quit')


class EventLoopFixture(InteractiveFixture):

    window_class = TestWindow

    def __init__(self, request):
        super(EventLoopFixture, self).__init__(request)
        self._request = request
        self.window = None
        request.addfinalizer(self.tear_down)

    def create_window(self, **kwargs):
        self.window = self.window_class(fixture=self, **kwargs)
        return self.window

    def add_text(self, text):
        assert self._window is not None
        self.window.add_text(text)

    def ask_question(self, description=None, screenshot=True):
        """Ask a question inside the test window. By default takes a screenshot and validates
        that too."""
        assert self.window is not None
        self.window.add_text('\n\n')
        if description:
            self.window.add_text(description)
        self.window.ask_question()
        caught_exception = None
        try:
            if self.interactive:
                self.run_event_loop()
                self.window.handle_answer()
            else:
                self.run_event_loop(0.1)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            caught_exception = ex
        finally:
            if screenshot:
                try:
                    screenshot_name = self._take_screenshot(self.window)
                    if caught_exception is None and not self.interactive:
                        self._check_screenshot(screenshot_name)
                except:
                    if not caught_exception:
                        raise
            if caught_exception:
                raise caught_exception

    def ask_question_no_window(self, description=None):
        """Ask a question to verify the current test result. Uses the console or an external gui
        as no window is available."""
        super(EventLoopFixture, self).ask_question(description)

    def run_event_loop(self, duration=None):
        if duration:
            clock.schedule_once(self.interrupt_event_loop, duration)
        pyglet.app.run()

    def interrupt_event_loop(self, *args, **kwargs):
        pyglet.app.exit()

    def tear_down(self):
        if self.window:
            self.window.close()
            self.window = None


def test_question_pass(event_loop):
    event_loop.create_window()
    event_loop.ask_question('If you read this text, you should let the test pass.')

def test_question_fail(event_loop):
    event_loop.create_window()
    with pytest.raises(pytest.fail.Exception):
        event_loop.ask_question('Please press F to fail this test.')

def test_question_skip(event_loop):
    event_loop.create_window()
    event_loop.ask_question('Please press S to skip the rest of this test.')
    pytest.fail('You should have pressed S')


