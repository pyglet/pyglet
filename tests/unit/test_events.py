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

    def mock_event2(self, *args, **kwargs):
        self.called = True
        self.args = args
        self.kwargs = kwargs
        return EVENT_HANDLED


class Child(pyglet.event.EventDispatcher):
    def __init__(self):
        self.calls = 0
        self.arg = None

    def mock_event(self, arg):
        self.calls += 1
        self.arg = arg
        return EVENT_HANDLED

    def other_method(self, arg):
        # This method should not be called by the event dispatcher
        assert False
Child.register_event_type('mock_event')
Child.register_event_type('mock_event2')


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


def test_push_handlers_instance_unknown_event(dispatcher):
    mock_instance_handler = MockInstanceHandler()
    dispatcher.register_event_type('mock_event_other')
    dispatcher.push_handlers(mock_instance_handler)
    with pytest.raises(EventException):
        dispatcher.dispatch_event('mock_event')

    result = dispatcher.dispatch_event('mock_event_other')
    assert result == EVENT_UNHANDLED


def test_handler_on_child():
    child = Child()
    result = child.dispatch_event('mock_event', 123)
    assert result == EVENT_HANDLED
    assert child.calls == 1
    assert child.arg == 123


def test_unknown_handler_on_child():
    child = Child()
    with pytest.raises(EventException):
        result = child.dispatch_event('other_method', 123)


def test_unhandled_event_on_child():
    child = Child()
    result = child.dispatch_event('mock_event2', 123)
    assert result == EVENT_UNHANDLED


def test_two_handlers():
    child = Child()
    called = False

    @child.event
    def mock_event(arg):
        assert arg == 123
        return EVENT_UNHANDLED

    result = child.dispatch_event('mock_event', 123)
    assert result == EVENT_HANDLED
    assert child.calls == 1
    assert child.arg == 123


def test_stop_propagation():
    child = Child()
    called = False

    @child.event
    def mock_event(arg):
        assert arg == 123
        return EVENT_HANDLED

    result = child.dispatch_event('mock_event', 123)
    assert result == EVENT_HANDLED
    assert child.calls == 0


def test_other_event_on_child():
    child = Child()
    called = False

    @child.event
    def mock_event2(arg):
        assert arg == 123
        return EVENT_UNHANDLED

    result = child.dispatch_event('mock_event2', 123)
    assert result == EVENT_UNHANDLED
    assert child.calls == 0


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


def test_remove_handler_obj():
    child = Child()
    handler = MockInstanceHandler()
    child.push_handlers(handler)

    result = child.dispatch_event('mock_event', 123)
    assert result == EVENT_HANDLED
    assert handler.called
    assert child.calls == 0

    handler.called = False
    result = child.dispatch_event('mock_event2', 123)
    assert result == EVENT_HANDLED
    assert handler.called
    assert child.calls == 0

    child.remove_handler(handler)

    handler.called = False
    result = child.dispatch_event('mock_event', 123)
    assert result == EVENT_HANDLED
    assert not handler.called
    assert child.calls == 1

    handler.called = False
    result = child.dispatch_event('mock_event2', 123)
    assert result == EVENT_UNHANDLED
    assert not handler.called
    assert child.calls == 1


def test_remove_method(dispatcher):
    dispatcher.register_event_type('mock_event')
    dispatcher.register_event_type('mock_event2')
    handler = MockInstanceHandler()
    dispatcher.push_handlers(handler)
    # Remove mock_handler but not mock_handler2
    dispatcher.remove_handlers(mock_event=handler)

    result = dispatcher.dispatch_event('mock_event')
    assert result == EVENT_UNHANDLED
    assert not handler.called

    result = dispatcher.dispatch_event('mock_event2')
    assert result == EVENT_HANDLED
    assert handler.called


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


def test_default_order(dispatcher):
    dispatcher.register_event_type('mock_event')
    invocations = []
    def handler1():
        invocations.append(1)
    def handler2():
        invocations.append(2)
    dispatcher.push_handlers(mock_event=handler1)
    dispatcher.push_handlers(mock_event=handler2)
    dispatcher.dispatch_event('mock_event')
    assert invocations == [2, 1]


def test_low_priority(dispatcher):
    dispatcher.register_event_type('mock_event')
    invocations = []
    def handler1():
        invocations.append(1)
    def handler2():
        invocations.append(2)
    dispatcher.push_handlers(mock_event=handler1)
    dispatcher.push_handlers(mock_event=handler2, priority=-1)
    dispatcher.dispatch_event('mock_event')
    assert invocations == [1, 2]


def test_high_priority(dispatcher):
    dispatcher.register_event_type('mock_event')
    invocations = []
    def handler1():
        invocations.append(1)
    def handler2():
        invocations.append(2)
    dispatcher.push_handlers(mock_event=handler1, priority=1)
    dispatcher.push_handlers(mock_event=handler2)
    dispatcher.dispatch_event('mock_event')
    assert invocations == [1, 2]


def test_priority_decorator_func(dispatcher):
    dispatcher.register_event_type('mock_event')
    invocations = []
    @pyglet.event.priority(1)
    def handler1():
        invocations.append(1)
    def handler2():
        invocations.append(2)
    dispatcher.push_handlers(mock_event=handler1)
    dispatcher.push_handlers(mock_event=handler2)
    dispatcher.dispatch_event('mock_event')
    assert invocations == [1, 2]


def test_priority_handler_decorator_func(dispatcher):
    dispatcher.register_event_type('mock_event')
    invocations = []
    @dispatcher.event('mock_event')
    @pyglet.event.priority(1)
    def handler1():
        invocations.append(1)
    @dispatcher.event('mock_event')
    def handler2():
        invocations.append(2)
    dispatcher.dispatch_event('mock_event')
    assert invocations == [1, 2]


def test_priority_decorator_method(dispatcher):
    dispatcher.register_event_type('mock_event')
    invocations = []
    class Handler1(object):
        @pyglet.event.priority(1)
        def mock_event(self):
            invocations.append(1)
    handler1 = Handler1()
    def handler2():
        invocations.append(2)
    dispatcher.push_handlers(handler1)
    dispatcher.push_handlers(mock_event=handler2)
    dispatcher.dispatch_event('mock_event')
    assert invocations == [1, 2]


def test_default_priority_class(dispatcher):
    dispatcher.register_event_type('mock_event')
    invocations = []
    class Handler1(object):
        def mock_event(self):
            invocations.append(1)
    handler1 = Handler1()
    def handler2():
        invocations.append(2)
    dispatcher.push_handlers(handler1)
    dispatcher.push_handlers(mock_event=handler2)
    dispatcher.dispatch_event('mock_event')
    assert invocations == [2, 1]


def test_dispatcher_handler():
    invocations = []
    class Dispatcher(pyglet.event.EventDispatcher):
        def mock_event(self):
            invocations.append(1)
    Dispatcher.register_event_type('mock_event')
    dispatcher = Dispatcher()
    def handler2():
        invocations.append(2)
    def handler3():
        invocations.append(3)
    dispatcher.push_handlers(mock_event=handler2)
    dispatcher.push_handlers(mock_event=handler3, priority=-1)
    dispatcher.dispatch_event('mock_event')
    assert invocations == [2, 1, 3]


def test_dispatcher_handler_prio():
    invocations = []
    class Dispatcher(pyglet.event.EventDispatcher):
        @pyglet.event.priority(1)
        def mock_event(self):
            invocations.append(1)
    Dispatcher.register_event_type('mock_event')
    dispatcher = Dispatcher()
    def handler2():
        invocations.append(2)
    def handler3():
        invocations.append(3)
    dispatcher.push_handlers(mock_event=handler2)
    dispatcher.push_handlers(mock_event=handler3, priority=-1)
    dispatcher.dispatch_event('mock_event')
    assert invocations == [1, 2, 3]
