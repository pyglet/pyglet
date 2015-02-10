"""Testing the events"""


import unittest
import pyglet
from mock import Mock, MagicMock
from contextlib import contextmanager
from pyglet.event import NoHandlerException, EVENT_HANDLED, EVENT_UNHANDLED


class EventTestCase(unittest.TestCase):
    def setUp(self):
        self.d = pyglet.event.EventDispatcher()
        self.d._event_stack = ()
        try:
            del pyglet.event.EventDispatcher.event_types
        except AttributeError:
            pass

    @contextmanager
    def mock_context(self, called=True):
        self.mock = Mock(mock_event=Mock())
        self.mock.__name__ = 'mock_event'
        self.d.register_event_type('mock_event')
        yield
        result = self.d.dispatch_event('mock_event')
        if called:
            self.assertEqual(result, EVENT_HANDLED)
            self.assertTrue(self.mock.called)
        else:
            # self.assertEqual(result, EVENT_UNHANDLED)
            self.assertFalse(self.mock.called)

    def test_register_event_type(self):
        self.d.register_event_type('mock_event')

    def test_push_handlers_args(self):
        with self.mock_context():
            self.d.push_handlers(self.mock)

    def test_push_handlers_kwargs(self):
        with self.mock_context():
            self.d.push_handlers(mock_event=self.mock)

    def test_push_handlers_not_setup(self):
        self.d.push_handlers()

    def test_set_handlers_args(self):
        with self.mock_context():
            self.d.set_handlers(self.mock)

    def test_set_handlers_kwargs(self):
        with self.mock_context():
            self.d.set_handlers(mock_event=self.mock)

    def test_set_handlers_not_setup(self):
        self.d.set_handlers()

    def test_set_handler_dispatch(self):
        with self.mock_context():
            self.d.set_handler('mock_event', self.mock)

    def test_set_handler_not_setup(self):
        self.d.set_handler('mock_event', None)

    def test_pop_handlers(self):
        self.d.set_handler('mock_event', None)
        self.d.pop_handlers()
        with self.assertRaises(NoHandlerException):
            self.d.pop_handlers()

    def test_pop_handlers_not_setup(self):
        with self.assertRaises(NoHandlerException):
            self.d.pop_handlers()

    def test_remove_handlers_args(self):
        with self.mock_context(False):
            self.d.set_handler('mock_event', self.mock)
            self.d.remove_handlers('mock_event')

    def test_remove_handlers_kwargs(self):
        with self.mock_context(False):
            self.d.set_handler('mock_event', self.mock)
            self.d.remove_handlers(mock_event=self.mock)

    def test_remove_handlers_not_setup(self):
        self.d.remove_handlers()

    def test_remove_handler(self):
        with self.mock_context(False):
            self.d.set_handler('mock_event', self.mock)
            self.d.remove_handler('mock_event', self.mock)

    def test_dispatch_event_handled(self):
        self.d.register_event_type('mock_event')
        self.d.dispatch_event('mock_event')

    def test_dispatch_unhandled(self):
        self.d.register_event_type('mock_event')
        with self.assertRaises(NoHandlerException):
            self.d.dispatch_event('not_handled')

    def test_dispatch_event_not_setup(self):
        with self.assertRaises(NoHandlerException):
            self.d.dispatch_event('mock_event')
