"""Testing the events"""


import types
import pytest
import pyglet
from tests import mock
from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED


@pytest.fixture
def dispatcher():
    d = pyglet.event.EventDispatcher()
    d.register_event_type('mock_event')
    yield d


@pytest.fixture
def mock_handler():
    """Mock instance with method for handling event."""
    mock_handler = mock.Mock(
        mock_event=mock.Mock(return_value=True),
        name='mock_handler'
    )
    yield mock_handler


@pytest.fixture
def mock_fn():
    """Mock function for handling event."""
    # We copy the spec from types.FunctionType so that our mock is seen as
    # a real user function. inspect.isroutine(our_mock) would return True.
    mock_fn = mock.Mock(return_value=True, spec=types.FunctionType)
    mock_fn.__name__ = 'mock_event'
    yield mock_fn


def test_register_event_type():
    d = pyglet.event.EventDispatcher()
    d.register_event_type('mock_event')


def test_dispatch_event_handled(dispatcher):
    dispatcher.mock_event = mock.Mock(return_value=True)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert dispatcher.mock_event.called


def test_push_handlers_args(dispatcher, mock_handler):
    dispatcher.push_handlers(mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_handler.mock_event.called


def test_push_handlers_kwargs(dispatcher, mock_fn):
    dispatcher.push_handlers(mock_event=mock_fn)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_fn.called


def test_push_handlers_not_setup(dispatcher):
    dispatcher.push_handlers()


def test_set_handlers_args(dispatcher, mock_handler):
    dispatcher.set_handlers(mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_handler.mock_event.called


def test_set_handlers_kwargs(dispatcher, mock_fn):
    dispatcher.set_handlers(mock_event=mock_fn)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_fn.called


def test_set_handlers_not_setup(dispatcher):
    dispatcher.set_handlers()


def test_set_handler_dispatch(dispatcher, mock_fn):
    dispatcher.set_handler('mock_event', mock_fn)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_fn.called


def test_set_handler_not_setup(dispatcher):
    dispatcher.set_handler('mock_event', None)


def test_pop_handlers(dispatcher):
    dispatcher.set_handler('mock_event', None)
    dispatcher.pop_handlers()
    result = dispatcher.dispatch_event('mock_event')
    assert result is False


def test_pop_handlers_not_setup(dispatcher):
    with pytest.raises(AssertionError):
        dispatcher.pop_handlers()


def test_remove_handlers_args(dispatcher, mock_fn):
    dispatcher.set_handlers(mock_fn)
    dispatcher.remove_handlers(mock_fn)
    result = dispatcher.dispatch_event('mock_event')
    assert result is False
    assert not mock_fn.called


def test_remove_handlers_kwargs(dispatcher, mock_fn):
    dispatcher.set_handlers(mock_fn)
    dispatcher.remove_handlers(mock_event=mock_fn)
    result = dispatcher.dispatch_event('mock_event')
    assert result is False
    assert not mock_fn.called


def test_remove_handlers_not_setup(dispatcher):
    dispatcher.remove_handlers()


def test_remove_handler(dispatcher, mock_fn):
    dispatcher.set_handler('mock_event', mock_fn)
    dispatcher.remove_handler('mock_event', mock_fn)
    result = dispatcher.dispatch_event('mock_event')
    assert result is False
    assert not mock_fn.called


def test_dispatch_unhandled(dispatcher, mock_fn):
    mock_fn.return_value = None
    dispatcher.set_handlers(mock_fn)
    result = dispatcher.dispatch_event('mock_event')
    assert result is EVENT_UNHANDLED
    assert mock_fn.called


def test_dispatch_event_not_setup(dispatcher):
    result = dispatcher.dispatch_event('mock_event')
    assert result is False


def test_dispatch_wrong_arguments(dispatcher):
    def mock_event():
        pass
    dispatcher.set_handlers(mock_event)
    with pytest.raises(TypeError) as exception:
        dispatcher.dispatch_event('mock_event', 'wrong argument')
    error_msg = str(exception.value)
    msg1 = ("The 'mock_event' event was dispatched with 1 arguments, "
            "but the handler 'mock_event' at")
    msg2 = "is written with 0 arguments."
    assert msg1 in error_msg
    assert msg2 in error_msg


@pytest.mark.parametrize("ExceptionType", [
    TypeError, AttributeError
])
def test_handler_raises_TypeError(ExceptionType, dispatcher):
    def mock_event():
        raise ExceptionType("Custom message")
    dispatcher.set_handlers(mock_event)
    with pytest.raises(ExceptionType) as exception:
        dispatcher.dispatch_event('mock_event')
    assert "Custom message" == str(exception.value)
