"""Testing the events"""


import pytest
import types
import sys
import pyglet
from tests import mock
from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED, EventException


@pytest.fixture
def dispatcher():
    """Event dispatcher to test"""
    dispatcher = pyglet.event.EventDispatcher()
    yield dispatcher
    # Let's remove previous handlers
    dispatcher._event_stack = ()
    try:
        del pyglet.event.EventDispatcher.event_types
    except AttributeError:
        pass


@pytest.fixture
def mock_handler(dispatcher):
    "Event handler mock."
    # Make a mock behave like a function by replicating the FunctionType specs.
    # Function objects provide these attributes:
    # __doc__         documentation string
    # __name__        name with which this function was defined
    # __code__        code object containing compiled function bytecode
    # __defaults__    tuple of any default values for arguments
    # __globals__     global namespace in which this function was defined
    # __annotations__ dict of parameter annotations
    # __kwdefaults__  dict of keyword only parameters with defaults
    dispatcher.register_event_type('mock_event')
    mock_handler = mock.Mock(spec=types.FunctionType)
    mock_handler.__name__ = 'mock_event'
    return mock_handler


class MockInstanceHandler(object):
    called = False
    args = None
    kwargs = None

    def mock_event(self, *args, **kwargs):
        self.called = True
        self.args = args
        self.kwargs = kwargs
        return EVENT_HANDLED


def test_register_event_type(dispatcher):
    dispatcher.register_event_type('mock_event')
    assert len(dispatcher.event_types) == 1


def test_push_handlers_args(dispatcher, mock_handler):
    dispatcher.push_handlers(mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_handler.called


def test_push_handlers_kwargs(dispatcher, mock_handler):
    dispatcher.push_handlers(mock_event=mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_handler.called


def test_push_handlers_instance(dispatcher):
    mock_instance_handler = MockInstanceHandler()
    dispatcher.register_event_type('mock_event')
    dispatcher.push_handlers(mock_instance_handler)
    result = dispatcher.dispatch_event('mock_event', 1, 2)
    assert result == EVENT_HANDLED
    assert mock_instance_handler.called
    assert mock_instance_handler.args == (1, 2)
    assert mock_instance_handler.kwargs == {}


def test_push_handlers_args(dispatcher, mock_handler):
    dispatcher.push_handlers(mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_handler.called


def test_push_handlers_kwargs(dispatcher, mock_handler):
    dispatcher.push_handlers(mock_event=mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_handler.called


def test_push_handler_dispatch(dispatcher, mock_handler):
    dispatcher.push_handler('mock_event', mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_handler.called


def test_push_bad_handler(dispatcher):
    dispatcher.register_event_type('mock_event')
    with pytest.raises(EventException):
        dispatcher.push_handler('mock_event', None)


def test_remove_handlers_args(dispatcher, mock_handler):
    dispatcher.push_handler('mock_event', mock_handler)
    dispatcher.remove_handlers(mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result is EVENT_UNHANDLED
    assert not mock_handler.called


def test_remove_handlers_kwargs(dispatcher, mock_handler):
    dispatcher.push_handler('mock_event', mock_handler)
    dispatcher.remove_handlers(mock_event=mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result is EVENT_UNHANDLED
    assert not mock_handler.called


def test_remove_handlers_not_setup(dispatcher):
    assert dispatcher.remove_handlers() is None


def test_remove_handler(dispatcher, mock_handler):
    dispatcher.push_handler('mock_event', mock_handler)
    dispatcher.remove_handler('mock_event', mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result is EVENT_UNHANDLED
    assert not mock_handler.called


def test_dispatch_unhandled_event(dispatcher):
    dispatcher.register_event_type('mock_event')
    with pytest.raises(EventException):
        dispatcher.dispatch_event('not_handled')


def test_dispatch_event_not_setup(dispatcher):
    with pytest.raises(EventException):
        dispatcher.dispatch_event('mock_event')


class DummyHandler:
    def mock_event(self):
        return True


@pytest.mark.skipif(sys.version_info < (3, 4), reason="requires python3.4")
def test_weakref_to_instance_method(dispatcher):
    import weakref
    dispatcher.register_event_type('mock_event')
    handler = DummyHandler()
    watcher = mock.Mock()
    weakref.finalize(handler, watcher)
    dispatcher.push_handlers(handler.mock_event)
    handler = None
    assert watcher.called


@pytest.mark.skipif(sys.version_info < (3, 4), reason="requires python3.4")
def test_weakref_to_instance(dispatcher):
    import weakref
    dispatcher.register_event_type('mock_event')
    handler = DummyHandler()
    watcher = mock.Mock()
    weakref.finalize(handler, watcher)
    dispatcher.push_handlers(handler)
    handler = None
    assert watcher.called


@pytest.mark.skipif(sys.version_info < (3, 4), reason="requires python3.4")
def test_weakref_deleted_when_instance_is_deleted(dispatcher):
    dispatcher.register_event_type('mock_event')
    handler = DummyHandler()
    dispatcher.push_handlers(handler.mock_event)
    handler = None
    result = dispatcher.dispatch_event('mock_event')
    assert result is EVENT_UNHANDLED
