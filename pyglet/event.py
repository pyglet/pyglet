"""Event dispatch framework.

All objects that produce events in pyglet implement :py:class:`~pyglet.event.EventDispatcher`,
providing a consistent interface for registering and manipulating event
handlers.  A commonly used event dispatcher is `pyglet.window.Window`.

Event types
===========

For each event dispatcher there is a set of events that it dispatches; these
correspond with the type of event handlers you can attach.  Event types are
identified by their name, for example, ''on_resize''.  If you are creating a
new class which implements :py:class:`~pyglet.event.EventDispatcher`, you must call
`EventDispatcher.register_event_type` for each event type.

Attaching event handlers
========================

An event handler is simply a function or method.  You can attach an event
handler by setting the appropriate function on the instance::

    def on_resize(width, height):
        # ...
    dispatcher.on_resize = on_resize

There is also a convenience decorator that reduces typing::

    @dispatcher.event
    def on_resize(width, height):
        # ...

You may prefer to subclass and override the event handlers instead::

    class MyDispatcher(DispatcherClass):
        def on_resize(self, width, height):
            # ...

Event handler stack
===================

When attaching an event handler to a dispatcher using the above methods, it
replaces any existing handler (causing the original handler to no longer be
called).  Each dispatcher maintains a stack of event handlers, allowing you to
insert an event handler "above" the existing one rather than replacing it.

There are two main use cases for "pushing" event handlers:

* Temporarily intercepting the events coming from the dispatcher by pushing a
  custom set of handlers onto the dispatcher, then later "popping" them all
  off at once.
* Creating "chains" of event handlers, where the event propagates from the
  top-most (most recently added) handler to the bottom, until a handler
  takes care of it.

Use `EventDispatcher.push_handlers` to create a new level in the stack and
attach handlers to it.  You can push several handlers at once::

    dispatcher.push_handlers(on_resize, on_key_press)

If your function handlers have different names to the events they handle, use
keyword arguments::

    dispatcher.push_handlers(on_resize=my_resize, on_key_press=my_key_press)

After an event handler has processed an event, it is passed on to the
next-lowest event handler, unless the handler returns `EVENT_HANDLED`, which
prevents further propagation.

To remove all handlers on the top stack level, use
`EventDispatcher.pop_handlers`.

Note that any handlers pushed onto the stack have precedence over the
handlers set directly on the instance (for example, using the methods
described in the previous section), regardless of when they were set.
For example, handler ``foo`` is called before handler ``bar`` in the following
example::

    dispatcher.push_handlers(on_resize=foo)
    dispatcher.on_resize = bar

Dispatching events
==================

pyglet uses a single-threaded model for all application code.  Event
handlers are only ever invoked as a result of calling
EventDispatcher.dispatch_events`.

It is up to the specific event dispatcher to queue relevant events until they
can be dispatched, at which point the handlers are called in the order the
events were originally generated.

This implies that your application runs with a main loop that continuously
updates the application state and checks for new events::

    while True:
        dispatcher.dispatch_events()
        # ... additional per-frame processing

Not all event dispatchers require the call to ``dispatch_events``; check with
the particular class documentation.

.. note::

    In order to prevent issues with garbage collection, the
    :py:class:`~pyglet.event.EventDispatcher` class only holds weak
    references to pushed event handlers. That means the following example
    will not work, because the pushed object will fall out of scope and be
    collected::

        dispatcher.push_handlers(MyHandlerClass())

    Instead, you must make sure to keep a reference to the object before pushing
    it. For example::

        my_handler_instance = MyHandlerClass()
        dispatcher.push_handlers(my_handler_instance)

"""
from __future__ import annotations

import inspect
import os.path

from functools import partial
from typing import TYPE_CHECKING, Literal, Union
from weakref import WeakMethod

import pyglet

if TYPE_CHECKING:
    from typing import Any, Callable, Generator


EVENT_HANDLED = True
EVENT_UNHANDLED = None

EVENT_HANDLE_STATE = Union[Literal[True], None]


class EventException(Exception):  # noqa: N818
    """An exception raised when an event handler could not be attached."""


class EventDispatcher:
    """Generic event dispatcher interface.

    See the module docstring for usage.
    """
    event_types: list
    # Placeholder empty stack; real stack is created only if needed
    _event_stack: tuple | list = ()

    @classmethod
    def register_event_type(cls: type[object], name: str) -> str:
        """Register an event type with the dispatcher.

        Before dispatching events, they must first be registered by name.
        Registering event types allows the dispatcher to validate event
        handler names as they are attached, and to search attached objects
        for suitable handlers.
        """
        if not hasattr(cls, 'event_types'):
            cls.event_types = []  # type: ignore reportAttributeAccessIssue
        cls.event_types.append(name)  # type: ignore reportAttributeAccessIssue
        return name

    def push_handlers(self, *args: Any, **kwargs: Any) -> None:
        """Push a new level onto the handler stack, and add 0 or more handlers.

        This method first pushes a new level to the top of the handler stack.
        It then attaches any handlers that were passed to this new level.

        If keyword arguments are given, they name the event type to attach.
        Otherwise, a callable's ``__name__`` attribute will be used. Any
        other object may also be specified, in which case it will be searched
        for callables with event names.
        """
        # Create event stack if necessary
        if type(self._event_stack) is tuple:
            self._event_stack = []

        # Place dict full of new handlers at beginning of stack
        self._event_stack.insert(0, {})  # type: ignore reportAttributeAccessIssue
        self.set_handlers(*args, **kwargs)

    def _get_handlers(self, args: list, kwargs: dict) -> Generator[tuple[str, Callable], None, None]:
        """Implement handler matching on arguments for set_handlers and remove_handlers."""
        for obj in args:
            if inspect.isroutine(obj):
                # Single magically named function
                name: str = obj.__name__
                if name not in self.event_types:
                    msg = f'Unknown event "{name}"'
                    raise EventException(msg)
                if inspect.ismethod(obj):
                    yield name, WeakMethod(obj, partial(self._remove_handler, name))
                else:
                    yield name, obj
            else:
                # Single instance with magically named methods
                for name in dir(obj):
                    if name in self.event_types:
                        meth = getattr(obj, name)
                        yield name, WeakMethod(meth, partial(self._remove_handler, name))

        for name, handler in kwargs.items():
            # Function for handling given event (no magic)
            if name not in self.event_types:
                msg = f'Unknown event "{name}"'
                raise EventException(msg)
            if inspect.ismethod(handler):
                yield name, WeakMethod(handler, partial(self._remove_handler, name))
            else:
                yield name, handler

    def set_handlers(self, *args: Any, **kwargs: Any) -> None:
        """Attach one or more event handlers to the top level of the handler stack.

        See :py:meth:`~pyglet.event.EventDispatcher.push_handlers` for the accepted
        argument types.
        """
        # Create event stack if necessary
        if type(self._event_stack) is tuple:
            self._event_stack = [{}]

        for name, handler in self._get_handlers(args, kwargs):
            self.set_handler(name, handler)

    def set_handler(self, name: str, handler: Callable) -> None:
        """Attach a single event handler."""
        # Create event stack if necessary
        if type(self._event_stack) is tuple:
            self._event_stack = [{}]

        self._event_stack[0][name] = handler

    def pop_handlers(self) -> None:
        """Pop the top level of event handlers off the stack."""
        assert self._event_stack, 'No handlers pushed'

        del self._event_stack[0]

    def remove_handlers(self, *args: Any, **kwargs: Any) -> None:
        """Remove event handlers from the event stack.

        See :py:meth:`~pyglet.event.EventDispatcher.push_handlers` for the
        accepted argument types. All handlers are removed from the first stack
        frame that contains any of the given handlers. No error is raised if
        any handler does not appear in that frame, or if no stack frame
        contains any of the given handlers.

        If the stack frame is empty after removing the handlers, it is
        removed from the stack.  Note that this interferes with the expected
        symmetry of :py:meth:`~pyglet.event.EventDispatcher.push_handlers` and
        :py:meth:`~pyglet.event.EventDispatcher.pop_handlers`.
        """
        handlers = list(self._get_handlers(args, kwargs))

        # Find the first stack frame containing any of the handlers
        def find_frame() -> dict | None:
            for _frame in self._event_stack:
                for _name, _handler in handlers:
                    if _name not in _frame:
                        continue
                    if _frame[_name] == _handler:
                        return _frame
            return None

        frame = find_frame()

        # No frame matched; no error.
        if not frame:
            return

        # Remove each handler from the frame.
        for name, handler in handlers:
            try:
                if frame[name] == handler:
                    del frame[name]
            except KeyError:  # noqa: PERF203
                pass

        # Remove the frame if it's empty.
        if not frame:
            self._event_stack.remove(frame)

    def remove_handler(self, name: str, handler: Callable) -> None:
        """Remove a single event handler.

        The given event handler is removed from the first handler stack frame
        it appears in.  The handler must be the exact same callable as passed
        to `set_handler`, `set_handlers` or
        :py:meth:`~pyglet.event.EventDispatcher.push_handlers`; and the name
        must match the event type it is bound to.

        No error is raised if the event handler is not set.
        """
        for frame in self._event_stack:
            try:
                if frame[name] == handler:
                    del frame[name]
                    break
            except KeyError:
                pass

    def _remove_handler(self, name: str, handler: Callable) -> None:
        """Used internally to remove all handler instances for the given event name.

        This is normally called from a dead ``WeakMethod`` to remove itself from the
        event stack.
        """
        # Iterate over a copy as we might mutate the list
        for frame in list(self._event_stack):

            if name in frame:
                try:
                    if frame[name] == handler:
                        del frame[name]
                        if not frame:
                            self._event_stack.remove(frame)
                except TypeError:
                    # weakref is already dead
                    pass

    def dispatch_event(self, event_type: str, *args: Any) -> bool | None:
        """Dispatch an event to the attached event handlers.

        The event is propagated to all registered event handlers
        in the stack, starting and the top and going down. If any
        registered event handler returns ``EVENT_HANDLED``, no further
        handlers down the stack will receive this event.

        This method has several possible return values. If any event
        handler has returned ``EVENT_HANDLED``, then this method will
        also return ``EVENT_HANDLED``. If not, this method will return
        ``EVENT_UNHANDLED``. If there were no events registered to
        receive this event, ``False`` is returned.

        Returns:
            ``EVENT_HANDLED`` if any event handler returned ``EVENT_HANDLED``;
            ``EVENT_UNHANDLED`` if one or more event handlers were invoked
            without any of them returning `EVENT_HANDLED`; ``False`` if no
            event handlers were registered.
        """
        assert hasattr(self, 'event_types'), (
            "No events registered on this EventDispatcher. "
            "You need to register events with the class method "
            "EventDispatcher.register_event_type('event_name')."
        )
        assert event_type in self.event_types, f"{event_type} not found in {self}.event_types == {self.event_types}"

        invoked = False

        # Search handler stack for matching event handlers
        for frame in list(self._event_stack):
            handler = frame.get(event_type, None)
            if not handler:
                continue
            if isinstance(handler, WeakMethod):
                handler = handler()
                assert handler is not None
            try:
                invoked = True
                if handler(*args):
                    return EVENT_HANDLED
            except TypeError as exception:
                self._raise_dispatch_exception(event_type, args, handler, exception)

        # Check instance for an event handler
        try:
            if getattr(self, event_type)(*args):
                return EVENT_HANDLED
        except AttributeError as e:
            event_op = getattr(self, event_type, None)
            if callable(event_op):
                raise e
        except TypeError as exception:
            self._raise_dispatch_exception(event_type, args, getattr(self, event_type), exception)
        else:
            invoked = True

        if invoked:
            return EVENT_UNHANDLED

        return False

    def post_event(self, event_type: str, *args: Any) -> bool | None:
        """Post an event to the main application thread.

        Unlike the :py:meth:`~pyglet.event.EventDispatcher.dispatch_event`
        method, this method does not dispatch events directly. Instead, it
        hands off the dispatch call to the main application thread. This
        ensures that any event handlers are also executed in the main thread.

        This method aliases :py:meth:`~pyglet.app.PlatformEventLoop.post_event`,
        which can be seen for more information on behavior.
        """
        pyglet.app.platform_event_loop.post_event(self, event_type, *args)

    def _raise_dispatch_exception(self, event_type: str, args: Any, handler: Callable, exception: Exception) -> None:
        # A common problem in applications is having the wrong number of
        # arguments in an event handler.  This is caught as a TypeError in
        # dispatch_event but the error message is obfuscated.
        #
        # Here we check if there is indeed a mismatch in argument count,
        # and construct a more useful exception message if so.  If this method
        # doesn't find a problem with the number of arguments, the error
        # is re-raised as if we weren't here.

        n_args = len(args)

        # Inspect the handler
        argspecs = inspect.getfullargspec(handler)
        handler_args = argspecs.args
        handler_varargs = argspecs.varargs
        handler_defaults = argspecs.defaults

        n_handler_args = len(handler_args)

        # Remove "self" arg from handler if it's a bound method
        if inspect.ismethod(handler) and handler.__self__:
            n_handler_args -= 1

        # Allow *args varargs to overspecify arguments
        if handler_varargs:
            n_handler_args = max(n_handler_args, n_args)

        # Allow default values to overspecify arguments
        if handler_defaults and n_handler_args > n_args >= n_handler_args - len(handler_defaults):
            n_handler_args = n_args

        # Construct a more informative message
        if n_handler_args != n_args:
            if inspect.isfunction(handler) or inspect.ismethod(handler):
                _, filename = os.path.split(handler.__code__.co_filename)
                descr = f"'{handler.__name__}' in {filename}:{handler.__code__.co_firstlineno}"
            else:
                descr = repr(handler)

            if 'self' in handler_args:
                handler_args.remove('self')

            caller_name = f"{self.__class__.__name__}.{event_type}"
            msg = (f"The '{caller_name}' event was dispatched with {n_args} arguments:  {list(args)},\n"
                   f"but your handler {descr} is written to expect {n_handler_args} arguments: {handler_args}")
            raise TypeError(msg)

        raise exception

    def _dump_handlers(self) -> None:

        for level, handlers in enumerate(self._event_stack):
            print(f"level: {level}")

            for event_type, handler in handlers.items():
                print(f" - '{event_type}': {handler}")

    # Decorator

    def event(self, *args: Any) -> Callable:
        """Function decorator for an event handler.

        If the function or method name matches the event name,
        the decorator can be added without arguments. Likewise,
        if the name does not match, you can provide the target
        event name by passing it as an argument.

        Name matches::

            win = window.Window()

            @win.event
            def on_resize(self, width, height):
                # ...

        Name does not match::

            @win.event('on_resize')
            def foo(self, width, height):
                # ...

        """
        # @window.event()
        if len(args) == 0:

            def decorator(function: Callable) -> Callable:
                func_name = function.__name__
                self.set_handler(func_name, function)
                return function

            return decorator

        # @window.event
        if inspect.isroutine(args[0]):
            func = args[0]
            name = func.__name__
            self.set_handler(name, func)
            return args[0]

        # @window.event('on_resize')
        if isinstance(args[0], str):
            name = args[0]

            def decorator(function: Callable) -> Callable:
                self.set_handler(name, function)
                return function

            return decorator

        msg = "Argument must be the name of the event as a `str`."
        raise TypeError(msg)
