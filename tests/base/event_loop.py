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

from .interactive import InteractiveFixture


@pytest.fixture
def event_loop(request):
    return EventLoopFixture(request)


class EventLoopFixture(InteractiveFixture):
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

    branch_coverage = {
        "get_document_1": False,  # Text document is None
        "get_document_2": False,  # Text document is not None
        "handle_answer_1": False,
        "handle_answer_2": False,
        "handle_answer_3": False,
        "handle_answer_4": False,
        "draw_text_1": False,  # text_batch is not None
        "draw_text_2": False,  # text_batch is None
        "tear_down_1": False,  # window is not None
        "tear_down_2": False   # window is None
    }

    def __init__(self, request):
        super().__init__(request)
        self._request = request
        self.window = None
        self.text_batch = None
        self.text_document = None
        self.answer = None
        request.addfinalizer(self.tear_down)

    def tear_down(self):
        if self.window:
            self.branch_coverage["tear_down_1"] = True
            self.window.close()
            self.window = None
        else:
            self.branch_coverage["tear_down_2"] = True

    def create_window(self, **kwargs):
        combined_kwargs = {}
        combined_kwargs.update(self.base_options)
        combined_kwargs.update(kwargs)
        self.window = Window(**combined_kwargs)
        self.window.push_handlers(self)
        return self.window

    def get_document(self):
        if self.text_document is None:
            self.branch_coverage["get_document_1"] = True
            self._create_text()
        else:
            self.branch_coverage["get_document_2"] = True
        return self.text_document

    def _create_text(self):
        assert self.window is not None
        self.text_batch = Batch()
        self.text_document = FormattedDocument()
        layout = TextLayout(self.text_document, self.window.width, self.window.height,
                            multiline=True, wrap_lines=True, batch=self.text_batch)
        layout.content_valign = 'bottom'

    def add_text(self, text):
        self.get_document()
        self.text_document.insert_text(len(self.text_document.text), text)

    def ask_question(self, description=None, screenshot=True):
        """Ask a question inside the test window. By default takes a screenshot and validates
        that too."""
        if self.window is None:
            self.create_window()
        self.add_text('\n\n')
        if description:
            self.add_text(description)
        self.add_text(self.question)
        self.answer = None
        caught_exception = None
        try:
            if self.interactive:
                self.run_event_loop()
                self.handle_answer()
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

    def handle_answer(self):
        if self.answer is None:
            self.branch_coverage["handle_answer_1"] = True
            raise Exception('Did not receive valid input in question window')
        elif self.answer == self.key_fail:
            self.branch_coverage["handle_answer_2"] = True
            pytest.fail('Tester marked test failed')
        elif self.answer == self.key_skip:
            self.branch_coverage["handle_answer_3"] = True
            pytest.skip('Tester marked test skipped')
        elif self.answer == self.key_quit:
            self.branch_coverage["handle_answer_4"] = True
            pytest.exit('Tester requested to quit')

    def print_coverage(self):
        for branch, hit in EventLoopFixture.branch_coverage.items():
            print(f"{branch} was {'hit' if hit else 'not hit'}")

    def ask_question_no_window(self, description=None):
        """Ask a question to verify the current test result. Uses the console or an external gui
        as no window is available."""
        super().ask_question(description)

    def run_event_loop(self, duration=None):
        if duration:
            clock.schedule_once(self.interrupt_event_loop, duration)
        pyglet.app.run()

    def interrupt_event_loop(self, *args, **kwargs):
        pyglet.app.exit()

    @staticmethod
    def schedule_once(callback, dt=.1):
        clock.schedule_once(callback, dt)

    def on_draw(self):
        self.clear()
        self.draw_text()

    def clear(self):
        gl.glClearColor(*self.clear_color)
        self.window.clear()

    def draw_text(self):
        if self.text_batch is not None:
            self.branch_coverage["draw_text_1"] = True
            self.text_batch.draw()
        else:
            self.branch_coverage["draw_text_2"] = True

    def on_key_press(self, symbol, modifiers):
        if symbol in (self.key_pass, self.key_fail, self.key_skip, self.key_quit):
            self.answer = symbol
            self.interrupt_event_loop()

        # Prevent handling of Escape to close the window
        return True


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


# Mocking the 'request' and 'pytest' needed for the original fixture setup
class MockRequest:
    # Satisfying interface requirement
    def addfinalizer(self, finalizer_func):
        pass

# Prevent pytest.exit from actually stopping the script
def mock_pytest_fail(message):
    print("Mock fail:", message)

def mock_pytest_skip(message):
    print("Mock skip:", message)

def mock_pytest_exit(message):
    print("Mock exit:", message)

# Replace the real pytest functions with mock functions
pytest.fail = mock_pytest_fail
pytest.skip = mock_pytest_skip
pytest.exit = mock_pytest_exit

# Using the mocked request
event_loop = EventLoopFixture(request=MockRequest())

# Ensuring self.window is not None, these functions would of never been reached if so
event_loop.create_window() 


# Testing get_document
print("Testing get_document when text_document is None:")
event_loop.text_document = None 
document = event_loop.get_document()  
print("Document after creation:", document)
event_loop.print_coverage()

print("Testing get_document with pre-existing document:")
event_loop.text_document = "Pre-existing document"
document = event_loop.get_document()
print("Document when already exists:", document)
event_loop.print_coverage()


# Testing handle_answer for all cases
print("\nTesting handle_answer when answer is None:")
event_loop.answer = None
try:
    event_loop.handle_answer()
except Exception as e:
    print("Caught exception when answer is None:", str(e))
event_loop.print_coverage()

print("\nTesting handle_answer when answer is key_fail:")
event_loop.answer is not None
try:
    event_loop.handle_answer()
except Exception as e:
    print("Caught exception when answer is key_fail:", str(e))
event_loop.print_coverage()

print("\nTesting handle_answer when answer is key_skip:")
event_loop.answer is not None
try:
    event_loop.handle_answer()
except Exception as e:
    print("Caught exception when answer is key_skip:", str(e))
event_loop.print_coverage()

print("\nTesting handle_answer when answer is key_quit:")
event_loop.answer is not None
try:
    event_loop.handle_answer()
except Exception as e:
    print("Caught exception when answer is key_quit:", str(e))
event_loop.print_coverage()

# Tests for draw_text
def test_draw_text_with_batch(event_loop):
    event_loop.create_window()
    event_loop.text_batch = Batch()
    event_loop.on_draw()
    event_loop.print_coverage()
    assert event_loop.branch_coverage["draw_text_1"]

def test_draw_text_without_batch(event_loop):
    event_loop.create_window()
    event_loop.text_batch = None
    event_loop.on_draw()
    event_loop.print_coverage()
    assert event_loop.branch_coverage["draw_text_2"]

# Additional tests to ensure comprehensive coverage

def test_draw_text_after_create_text(event_loop):
    event_loop.create_window()
    event_loop._create_text()
    event_loop.on_draw()
    event_loop.print_coverage()
    assert event_loop.branch_coverage["draw_text_1"]

# Tests for tear_down
def test_tear_down_with_window(event_loop):
    event_loop.create_window()
    event_loop.tear_down()
    event_loop.print_coverage()
    assert event_loop.branch_coverage["tear_down_1"]

def test_tear_down_without_window(event_loop):
    event_loop.tear_down()
    event_loop.print_coverage()
    assert event_loop.branch_coverage["tear_down_2"]

print("\nTesting draw_text with text_batch:")
event_loop.create_window()
event_loop.text_batch = Batch()
event_loop.on_draw()
event_loop.print_coverage()

print("\nTesting draw_text without text_batch:")
event_loop.create_window()
event_loop.text_batch = None
event_loop.on_draw()
event_loop.print_coverage()

print("\nTesting draw_text after create_text:")
event_loop.create_window()
event_loop._create_text()
event_loop.on_draw()
event_loop.print_coverage()

# Tests for tear_down
"""print("\nTesting tear_down with window:")
event_loop.create_window()
event_loop.tear_down()
event_loop.print_coverage()

print("\nTesting tear_down without window:")
event_loop.tear_down()
event_loop.print_coverage()"""