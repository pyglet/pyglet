"""Testing the events"""
import gc
import types

from tests import mock

import pytest
import pyglet

from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED


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
    """Event handler mock."""
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


class ClassInstanceHandler:
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



@pytest.fixture
def class_instance_handler(dispatcher):
    """Class event handler.

    If a class instance is given to push_handlers, and it implements methods with
    the same names as the events, those will become event handlers.
    """
    dispatcher.register_event_type('mock_event')
    return ClassInstanceHandler()


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


def test_push_handlers_instance(dispatcher, class_instance_handler):
    dispatcher.register_event_type('mock_event')
    dispatcher.push_handlers(class_instance_handler)
    result = dispatcher.dispatch_event('mock_event', 1, 2)
    assert result == EVENT_HANDLED
    assert class_instance_handler.called
    assert class_instance_handler.args == (1, 2)
    assert class_instance_handler.kwargs == {}


def test_push_handlers_not_setup(dispatcher):
    dispatcher.push_handlers()
    assert dispatcher._event_stack == [{}]


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
    assert dispatcher._event_stack == [{}]


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
    with pytest.raises(AssertionError):
        dispatcher.dispatch_event('not_handled')


def test_dispatch_event_not_setup(dispatcher):
    with pytest.raises(AssertionError):
        dispatcher.dispatch_event('mock_event')


class DummyHandler:
    def mock_event(self):
        return True


def test_weakref_to_instance_method(dispatcher):
    import weakref
    dispatcher.register_event_type('mock_event')
    handler = DummyHandler()
    watcher = mock.Mock()
    weakref.finalize(handler, watcher)
    dispatcher.push_handlers(handler.mock_event)
    del handler
    gc.collect()    # ensure references are cleared
    assert watcher.called


def test_weakref_to_instance(dispatcher):
    import weakref
    dispatcher.register_event_type('mock_event')
    handler = DummyHandler()
    watcher = mock.Mock()
    weakref.finalize(handler, watcher)
    dispatcher.push_handlers(handler)
    del handler
    gc.collect()    # ensure references are cleared
    assert watcher.called


@pytest.mark.parametrize(
    ('push_handler', 'expected_callbacks'),
    [
        (lambda dispatcher, handler: dispatcher.push_handlers(handler.mock_event), 1),
        (lambda dispatcher, handler: dispatcher.push_handlers(handler), 1),
        (lambda dispatcher, handler: dispatcher.push_handlers(mock_event=handler.mock_event), 1),
    ],
)
def test_weakref_handler_paths_have_no_removal_callbacks(dispatcher, monkeypatch, push_handler, expected_callbacks):
    dispatcher.register_event_type('mock_event')
    callbacks = []
    weak_method = pyglet.event.WeakMethod

    def track_callback(method, callback=None):
        callbacks.append(callback)
        return weak_method(method, callback)

    monkeypatch.setattr(pyglet.event, 'WeakMethod', track_callback)
    push_handler(dispatcher, DummyHandler())

    assert callbacks == [None] * expected_callbacks


def test_weakref_deleted_when_instance_is_deleted(dispatcher):
    dispatcher.register_event_type('mock_event')
    handler = DummyHandler()
    dispatcher.push_handlers(handler.mock_event)
    del handler
    gc.collect()    # ensure references are cleared
    result = dispatcher.dispatch_event('mock_event')
    assert result is False


def test_dispatch_event_ignores_dead_weak_method_handler(dispatcher):
    import weakref
    dispatcher.register_event_type('mock_event')
    handler = DummyHandler()
    dispatcher.set_handler('mock_event', weakref.WeakMethod(handler.mock_event))
    del handler
    gc.collect()    # ensure references are cleared
    result = dispatcher.dispatch_event('mock_event')
    assert result is False
    assert not dispatcher._event_stack


def test_remove_handlers_removes_weakref_to_instance_method(dispatcher):
    dispatcher.register_event_type('mock_event')
    handler = DummyHandler()
    dispatcher.push_handlers(handler.mock_event)

    dispatcher.remove_handlers(handler.mock_event)

    result = dispatcher.dispatch_event('mock_event')
    assert result is False


def test_remove_handlers_removes_weakref_to_instance(dispatcher):
    dispatcher.register_event_type('mock_event')
    handler = DummyHandler()
    dispatcher.push_handlers(handler)

    dispatcher.remove_handlers(handler)

    result = dispatcher.dispatch_event('mock_event')
    assert result is False


def test_dispatch_event_removes_dead_weak_handler_and_continues_to_lower_frame(dispatcher):
    dispatcher.register_event_type('mock_event')
    lower_handler = mock.Mock(spec=types.FunctionType)
    lower_handler.__name__ = 'mock_event'
    lower_handler.return_value = EVENT_HANDLED
    weak_handler = DummyHandler()
    dispatcher.push_handlers(lower_handler)
    dispatcher.push_handlers(weak_handler.mock_event)
    del weak_handler
    gc.collect()

    result = dispatcher.dispatch_event('mock_event')

    assert result == EVENT_HANDLED
    assert lower_handler.called
    assert dispatcher._event_stack == [{'mock_event': lower_handler}]


def test_dispatch_event_removes_dead_weak_handler_from_non_empty_frame(dispatcher):
    dispatcher.register_event_type('mock_event')
    dispatcher.register_event_type('mock_event2')
    handler = ClassInstanceHandler()
    dispatcher.push_handlers(handler)
    del handler
    gc.collect()

    result = dispatcher.dispatch_event('mock_event')

    assert result is False
    assert len(dispatcher._event_stack) == 1
    assert 'mock_event' not in dispatcher._event_stack[0]
    assert 'mock_event2' in dispatcher._event_stack[0]
