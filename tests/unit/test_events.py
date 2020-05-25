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


@pytest.fixture
def mock_instance_handler(dispatcher):
    """Class event handler.

    If an instance is given to push_handlers and it implements methods with similar
    names as the events, those will become event handlers. This mock imitates this
    behaviour.
    """
    dispatcher.register_event_type('mock_event')
    mock_instance_handler = mock.Mock()
    mock_handler = mock.Mock(spec=types.MethodType)
    mock_handler.__name__ = 'mock_event'
    mock_instance_handler.mock_event = mock_handler
    return mock_instance_handler


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


def test_push_handlers_instance(dispatcher, mock_instance_handler):
    dispatcher.push_handlers(mock_instance_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    # Cannot just check that mock_instance_handler.mock_event.called is True because
    # EventDispatcher took a WeakMethod of a Mock, and it cannot reconstruct the
    # original Mock method. But we check instead that mock_instance_handler had a
    # method call.
    calls = mock_instance_handler.method_calls
    assert len(calls) == 1
    name, args, kwargs = calls[0]
    assert name == 'mock_event.__self__'


def test_push_handlers_not_setup(dispatcher):
    dispatcher.push_handlers()
    assert dispatcher._event_stack == ()


def test_set_handlers_args(dispatcher, mock_handler):
    dispatcher.set_handlers(mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_handler.called


def test_set_handlers_kwargs(dispatcher, mock_handler):
    dispatcher.set_handlers(mock_event=mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_handler.called


def test_set_handlers_not_setup(dispatcher):
    dispatcher.set_handlers()
    assert dispatcher._event_stack == ()


def test_set_handler_dispatch(dispatcher, mock_handler):
    dispatcher.set_handler('mock_event', mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_HANDLED
    assert mock_handler.called


def test_set_handler_not_setup(dispatcher, mock_handler):
    dispatcher.set_handler('mock_event', None)
    result = dispatcher.dispatch_event('mock_event')
    assert result is False
    assert not mock_handler.called


def test_pop_handlers(dispatcher, mock_handler):
    dispatcher.set_handler('mock_event', None)
    dispatcher.pop_handlers()
    with pytest.raises(AssertionError):
        dispatcher.pop_handlers()


def test_pop_handlers_not_setup(dispatcher):
    with pytest.raises(AssertionError):
        dispatcher.pop_handlers()


def test_remove_handlers_args(dispatcher, mock_handler):
    dispatcher.set_handler('mock_event', mock_handler)
    dispatcher.remove_handlers(mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result is False
    assert not mock_handler.called


def test_remove_handlers_kwargs(dispatcher, mock_handler):
    dispatcher.set_handler('mock_event', mock_handler)
    dispatcher.remove_handlers(mock_event=mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result is False
    assert not mock_handler.called


def test_remove_handlers_not_setup(dispatcher):
    assert dispatcher.remove_handlers() is None


def test_remove_handler(dispatcher, mock_handler):
    dispatcher.set_handler('mock_event', mock_handler)
    dispatcher.remove_handler('mock_event', mock_handler)
    result = dispatcher.dispatch_event('mock_event')
    assert result is False
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
    assert result is False


class MockDispatcher(pyglet.event.EventDispatcher):
    def __init__(self):
        self.handled = []

    def on_mock_event1(self):
        self.handled.append('MockDispatcher')

    def on_mock_event2(self):
        self.handled.append('MockDispatcher')

    @pyglet.event.intercept
    def on_mock_event3(self):
        self.handled.append('MockDispatcher')

    @pyglet.event.intercept
    def on_mock_event4(self):
        self.handled.append('MockDispatcher')


MockDispatcher.register_event_type('on_mock_event1')
MockDispatcher.register_event_type('on_mock_event2')
MockDispatcher.register_event_type('on_mock_event3')
MockDispatcher.register_event_type('on_mock_event4')


class MockListener1(object):
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.dispatcher.push_handlers(self)

    def on_mock_event1(self):
        self.dispatcher.handled.append('MockListener1')

    def on_mock_event2(self):
        self.dispatcher.handled.append('MockListener1')

    def on_mock_event3(self):
        self.dispatcher.handled.append('MockListener1')

    @pyglet.event.intercept
    def on_mock_event4(self):
        self.dispatcher.handled.append('MockListener1')

class MockListener2(object):
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.dispatcher.push_handlers(self)

    def on_mock_event1(self):
        self.dispatcher.handled.append('MockListener2')

    def on_mock_event2(self):
        self.dispatcher.handled.append('MockListener2')
        return EVENT_HANDLED

    def on_mock_event3(self):
        self.dispatcher.handled.append('MockListener2')

    def on_mock_event4(self):
        self.dispatcher.handled.append('MockListener2')


def test_listener_then_dispatcher():
    dispatcher = MockDispatcher()
    listener1 = MockListener1(dispatcher)
    listener2 = MockListener2(dispatcher)
    result = dispatcher.dispatch_event('on_mock_event1')
    assert result is EVENT_UNHANDLED
    assert (dispatcher.handled ==
            ['MockListener2', 'MockListener1', 'MockDispatcher'])


def test_listener_handles():
    dispatcher = MockDispatcher()
    listener1 = MockListener1(dispatcher)
    listener2 = MockListener2(dispatcher)
    result = dispatcher.dispatch_event('on_mock_event2')
    assert result is EVENT_HANDLED
    assert (dispatcher.handled == ['MockListener2'])


def test_func_listener():
    dispatcher = MockDispatcher()
    @dispatcher.event
    def on_mock_event1():
        dispatcher.handled.append('func')
    result = dispatcher.dispatch_event('on_mock_event1')
    assert result is EVENT_UNHANDLED
    assert (dispatcher.handled == ['func', 'MockDispatcher'])


def test_func_listener_overrides():
    dispatcher = MockDispatcher()
    listener1 = MockListener1(dispatcher)
    listener2 = MockListener2(dispatcher)
    @dispatcher.event
    def on_mock_event1():
        dispatcher.handled.append('func')
    result = dispatcher.dispatch_event('on_mock_event1')
    assert result is EVENT_UNHANDLED
    # The top handler on the stack (MockListener2) got overwritten by
    # the decorator.
    assert (dispatcher.handled == ['func', 'MockListener1', 'MockDispatcher'])

def test_dispatcher_intercepts():
    dispatcher = MockDispatcher()
    listener1 = MockListener1(dispatcher)
    listener2 = MockListener2(dispatcher)
    result = dispatcher.dispatch_event('on_mock_event3')
    assert result is EVENT_UNHANDLED
    # Handler on the dispatcher is annotated @intercept, so it's called first.
    assert (dispatcher.handled ==
            ['MockDispatcher', 'MockListener2', 'MockListener1'])

def test_listener_intercepts():
    dispatcher = MockDispatcher()
    listener1 = MockListener1(dispatcher)
    listener2 = MockListener2(dispatcher)
    result = dispatcher.dispatch_event('on_mock_event4')
    assert result is EVENT_UNHANDLED
    # Handler on the dispatcher is annotated @intercept, so it's called first.
    # After that the handler on MockListener1 is called because it's also
    # annotated as intercept, but was added later.
    assert (dispatcher.handled ==
            ['MockDispatcher', 'MockListener1', 'MockListener2'])
