# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2020 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

"""Event dispatch framework.

All objects that produce events in pyglet implement :py:class:`~pyglet.event.EventDispatcher`,
providing a consistent interface for registering and manipulating event
handlers.  A commonly used event dispatcher is `pyglet.window.Window`.

Event types
===========

For each event dispatcher there is a set of events that it dispatches; these
correspond with the type of event handlers you can attach.  Event types are
identified by their name, for example, ''on_resize''.

If you are creating a new class which implements
:py:class:`~pyglet.event.EventDispatcher`, or want to add new events
to an existing dispatcher, you must call `EventDispatcher.register_event_type`
for each event type:

    class MyDispatcher(pyglet.event.EventDispatcher):
        # ...

    MyDispatcher.register_event_type('on_resize')

Attaching event handlers
========================

An event handler is simply a function or method, that is called when system or
program event happens. There are several ways to add a handler for an event.

When the dispatcher object is available as a global variable, it is convenient
to use the `event` decorator:

    @window.event
    def on_resize(width, height):
        # ...

Here `window` is a variable containing an instance of `pyglet.window.Window`,
which inherits from `EventDispatcher` class. This decorator assumes that
the function is named after the event. To use the decorator with a function with
another name, pass the name of the event as the argument for the decorator:

    @window.event('on_resize')
    def my_resize_handler(width, height);
        # ...

The most universal way to add an event handler is to call the `push_handlers`
method on the dispatcher object:

    window.push_handlers(on_resize)
    window.push_handlers(on_resize=my_handler)
    window.push_handlers(on_resize=obj.my_handler)
    window.push_handlers(obj)

This methods accepts both positional and keyword parameters. In case of keyword
arguments, the name of the event matches the name of the argument. Otherwise,
the name of the passed function or method is used as the event name.

If an object is passed as a positional argument, all its methods that match
the names of registered events are added as handlers. For example:

    class MyDispatcher(pyglet.event.EventDispatcher):
        # ...
    MyDispatcher.register_event_type('on_resize')
    MyDispatcher.register_event_type('on_keypress')

    class Listener(object):
        def on_resize(self, w, h):
            # ...

        def on_keypress(self, key):
            # ...

        def other_method(self):
            # ...

    dispatcher = MyDispatcher()
    listener = Listener()
    dispatcher.push_handlers(listener)

In this example both `listener.on_resize` and `listener.on_keypress` are
registered as handlers for respective events, but `listener.other_method` is
not affected, because it doesn't correspond to a registered event type.

Finally, yet another option is to subclass the dispatcher and override the event
handler methods::

    class MyDispatcher(pyglet.event.EventDispatcher):
        def on_resize(self, width, height):
            # ...

If both a parent class and the child class have a handler for the same event,
only the child's version of the method is invoked. If both event handlers are
needed, the child's handler must explicitly call the parent's handler:

    class ParentDispatcher(pyglet.event.EventDispatcher):
        def on_resize(self, w, h);
            # ...

    class ChildDispatcher(ParentDispatcher):
        def on_resize(self, w, h):
            super().on_resize(w, h)
            # ...

Multiple handlers for an event
==============================

A single event can be handled by multiple handlers. The handlers are invoked in
the order opposite to the order of their registration. So, the handler
registered last will be the first to be invoke when the event is fired.

An event handler can return the value `pyglet.event.EVENT_HANDLED` to prevent
running the subsequent handlers. Alternatively if the handle returns
`pyglet.event.EVENT_UNHANDLED` or doesn't return an explicit value, the next
event handler will be called (if there is one).

Stopping the event propagation is useful to prevent a single user action from
being handled by two unrelated systems. For instance, in game using WASD keys
for movement, should suppress movement when a chat window is opened: the
"keypress" event should be handled by the chat or by the character
movement system, but not both.

Removing event handlers
=======================

In most cases it is not necessary to remove event handlers manually. When
the handler is an object method, the event dispatcher keeps only a weak
reference to it. It means, that the dispatcher will not prevent the object from
being deleted when it goes out of scope. In that case the handler will be
silently removed from the list of handlers.

.. note::

    This means the following example will not work, because the pushed object
    will fall out of scope and be collected::

        dispatcher.push_handlers(MyHandlerClass())

    Instead, you must make sure to keep a reference to the object before pushing
    it. For example::

        my_handler_instance = MyHandlerClass()
        dispatcher.push_handlers(my_handler_instance)

When explicit removal of handlers is required, the method `remove_handlers`
can be used. Its arguments are the same as the arguments of `push_handlers`:

    dispatcher.remove_handlers(on_resize)
    dispatcher.remove_handlers(on_resize=my_handler)
    dispatcher.remove_handlers(on_resize=obj.my_handler)
    dispatcher.remove_handlers(obj)

When an object is passed as a positional parameter to `remove_handlers`, all its
methods are removed from the handlers, regardless of their names.

Dispatching events
==================

pyglet uses a single-threaded model for all application code. Normally event
handlers are invoked while running an event loop by calling

    pyglet.app.run()

or

    event_loop = pyglet.app.EventLoop()
    event_loop.run()

Application code can invoke events directly by calling the method
`dispatch_event` of `EventDispatcher`:

    dispatcher.dispatch_event('on_resize', 640, 480)

The first argument of this method is the event name, that has to be previously
registered using `register_event_type` class method. The rest of the arguments
are pass to event handlers.

The handlers of an event fired by calling `dispatch_event` are called directly
from this method. If any of the handlers returns `EVENT_HANDLED`, then
`dispatch_event` also returns `EVENT_HANDLED` otherwise (or if there weren't
any handlers for a given event) it returns `EVENT_UNHANDLED`.
"""

import inspect

from functools import partial
from weakref import WeakMethod


EVENT_HANDLED = True
EVENT_UNHANDLED = None


class EventException(Exception):
    """An exception raised when an event handler could not be attached.
    """
    pass


class EventDispatcher(object):
    """Generic event dispatcher interface.

    See the module docstring for usage.
    """
    # This field will contain the queues of event handlers for every supported
    # event type. It is lazily initialized when the first event handler is added
    # to the class. After that it contains a dictionary of lists, in which
    # handlers are sorted according to their priority:
    #     {'on_event': [handler1, handler2]}
    # Handlers are invoked until any one of them returns EVENT_HANDLED
    _handlers = None

    @classmethod
    def register_event_type(cls, name):
        """Registers an event type with the dispatcher.

        Registering event types allows the dispatcher to validate event
        handler names as they are attached, and to search attached objects for
        suitable handlers.

        :Parameters:
            `name` : str
                Name of the event to register.
        """
        if not hasattr(cls, 'event_types'):
            cls.event_types = []
        cls.event_types.append(name)

    def _get_names_from_handler(self, handler):
        """Yields event names handled by a handler function, method or object.
        """
        if callable(handler) and hasattr(handler, '__name__'):
            # Take the name of a function or a method.
            yield handler.__name__
        else:
            # Iterate through all the methods of an object and yield those that
            # match registered events.
            for name in dir(handler):
                if (name in self.event_types and
                    callable(getattr(handler, name))):
                    yield name

    def _finalize_weak_method(self, name, weak_method):
        """Called to remove dead WeakMethods from handlers."""
        handlers = self._handlers[name]
        i = 0
        # This is not the most efficient way of removing several elements from
        # an array, but in almost all cases only one element has to be removed.
        while i < len(handlers):
            if handlers[i] is weak_method:
                del handlers[i]
            else:
                i += 1

    def _remove_handler_from_queue(self, handlers_queue, handler):
        """Remove all instances of a handler from a queue for a single event.

        If `handler` is an object, then all the methods bound to this object
        will be removed from the queue.
        """
        i = 0
        # This is not the most efficient way of removing several elements from
        # an array, but in almost all cases only one element has to be removed.
        while i < len(handlers_queue):
            registered_handler = handlers_queue[i]
            if isinstance(registered_handler, WeakMethod):
                # Wrapped in WeakMethod in `push_handler`.
                registered_handler = registered_handler()
            if (registered_handler is handler or
                getattr(registered_handler, '__self__', None) is handler):
                del handlers_queue[i]
            else:
                i += 1

    def push_handler(self, name, handler):
        """Adds a single event handler.

        If the `handler` parameter is callable, it will be registered directly.
        Otherwise it's expected to be an object having a method with a name
        matching the name of the event.
        """
        if not hasattr(self.__class__, 'event_types'):
            self.__class__.event_types = []
        if name not in self.event_types:
            raise EventException('Unknown event "{}"'.format(name))
        if not callable(handler):
            # If handler is not callable, search for in it for a method with
            # a name matching the name of the event.
            if hasattr(handler, name):
                method = getattr(handler, name)
                if not callable(method):
                    raise EventException(
                        'Field {} on "{}" is not callable'.format(
                            name, repr(handler)))
                handler = method
            else:
                raise EventException(
                    '"{}" is not callable and doesn\'t have '
                    'a method "{}"'.format(repr(handler), name))
        if inspect.ismethod(handler):
            handler = WeakMethod(handler, partial(
                self._finalize_weak_method, name))

        # Create handler queues if necessary.
        if self._handlers is None:
            self._handlers = {}
            self.push_handlers(self)
        if name not in self._handlers:
            self._handlers[name] = []

        self._handlers[name].insert(0, handler)

    def push_handlers(self, *args, **kwargs):
        """Adds new handlers to registered events.

        Multiple positional and keyword arguments can be provided.

        For a keyword argument, the name of the event is taken from the name
        of the argument. If the argument is callable, it is used
        as a handler directly. If the argument is an object, it is searched for
        a method with the name matching the name of the event/argument.

        When a callable named object (usually a function or a method) is passed
        as a positional argument, its name is used as the event name. When
        an object is passed as a positional argument, it is scanned for methods
        with names that match the names of registered events. These methods are
        added as handlers for the respective events.

        EventException is raised if the event name is not registered.
        """
        if not hasattr(self.__class__, 'event_types'):
            self.__class__.event_types = []

        for handler in args:
            for name in self._get_names_from_handler(handler):
                self.push_handler(name, handler)

        for name, handler in kwargs.items():
            self.push_handler(name, handler)

    def remove_handler(self, name_or_handler=None, handler=None, name=None):
        """Removes a single event handler.

        Can be called in one of the following ways:

            dispatcher.remove_handler(my_handler)
            dispatcher.remove_handler(handler=my_handler)
            dispatcher.remove_handler("event_name", my_handler)
            dispatcher.remove_handler(name="event_name", handler=my_handler)

        If the event name is specified, only the queue of handlers for that
        event is scanned, and the handler is removed from it. Otherwise all
        handler queues are scanned and the handler is removed from all of them.

        If the handler is an object, then all the registered handlers that are
        bound to this object are removed. Unlike `push_handler`, the method
        names in the class are not taken into account.

        No error is raised if the event handler is not set.
        """
        if handler is None:
            # Called with one positional argument (example #1)
            assert name is None
            assert name_or_handler is not None
            handler = name_or_handler
        elif name is not None:
            # Called with keyword arguments for handler and name (example #4)
            assert name_or_handler is None
        else:
            # Called with two positional arguments, or only with handler as
            # a keyword argument (examples #2, #3)
            name = name_or_handler

        if name is not None:
            if name in self._handlers:
                self._remove_handler_from_queue(self._handlers[name], handler)
        else:
            for handlers_queue in self._handlers.values():
                self._remove_handler_from_queue(handlers_queue, handler)

    def remove_handlers(self, *args, **kwargs):
        """Removes event handlers from the event handlers queue.

        See :py:meth:`~pyglet.event.EventDispatcher.push_handlers` for the
        accepted argument types. Handlers, passed as positional arguments
        are removed from all events, regardless of their names.

        No error is raised if any handler does not appear among
        the registered handlers.
        """
        for handler in args:
            self.remove_handler(None, handler)

        for name, handler in kwargs.items():
            self.remove_handler(name, handler)

    def dispatch_event(self, event_type, *args):
        """Dispatch a single event to the attached handlers.

        The event is propagated to all handlers from from the top of the stack
        until one returns `EVENT_HANDLED`.  This method should be used only by
        :py:class:`~pyglet.event.EventDispatcher` implementors; applications
        should call the ``dispatch_events`` method.

        Since pyglet 1.2, the method returns `EVENT_HANDLED` if an event
        handler returned `EVENT_HANDLED` or `EVENT_UNHANDLED` if all events
        returned `EVENT_UNHANDLED`.  If no matching event handlers are in the
        stack, ``False`` is returned.

        :Parameters:
            `event_type` : str
                Name of the event.
            `args` : sequence
                Arguments to pass to the event handler.

        :rtype: bool or None
        :return: (Since pyglet 1.2) `EVENT_HANDLED` if an event handler
            returned `EVENT_HANDLED`; `EVENT_UNHANDLED` if one or more event
            handlers were invoked but returned only `EVENT_UNHANDLED`;
            otherwise ``False``.  In pyglet 1.1 and earlier, the return value
            is always ``None``.

        """
        if not hasattr(self.__class__, 'event_types'):
            self.__class__.event_types = []
        if event_type not in self.event_types:
            raise EventException(
                'Attempted to dispatch an event of unknown event type "{}". '
                'Event types have to be registered by calling '
                'DispatcherClass.register_event_type({})'.format(
                    event_type, repr(event_type)))

        if self._handlers is None:
            # Initialize the handlers with the object itself.
            self._handlers = {}
            self.push_handlers(self)

        handlers_queue = self._handlers.get(event_type, ())
        for handler in handlers_queue:
            if isinstance(handler, WeakMethod):
                handler = handler()
                assert handler is not None
            try:
                if handler(*args):
                    return EVENT_HANDLED
            except TypeError as exception:
                self._raise_dispatch_exception(
                    event_type, args, handler, exception)

        return EVENT_UNHANDLED

    def _raise_dispatch_exception(self, event_type, args, handler, exception):
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
        if (n_handler_args > n_args and handler_defaults and
                n_handler_args - len(handler_defaults) <= n_args):
            n_handler_args = n_args

        if n_handler_args != n_args:
            if inspect.isfunction(handler) or inspect.ismethod(handler):
                descr = "'%s' at %s:%d" % (handler.__name__,
                                           handler.__code__.co_filename,
                                           handler.__code__.co_firstlineno)
            else:
                descr = repr(handler)

            raise TypeError("The '{0}' event was dispatched with {1} arguments, "
                            "but your handler {2} accepts only {3} arguments.".format(
                                event_type, len(args), descr, len(handler_args)))
        else:
            raise exception

    def event(self, *args):
        """Function decorator for an event handler.

        Usage::

            win = window.Window()

            @win.event
            def on_resize(self, width, height):
                # ...

        or::

            @win.event('on_resize')
            def foo(self, width, height):
                # ...

        """
        if len(args) == 0:                      # @window.event()
            def decorator(func):
                name = func.__name__
                self.push_handler(name, func)
                return func
            return decorator
        elif inspect.isroutine(args[0]):        # @window.event
            func = args[0]
            name = func.__name__
            self.push_handler(name, func)
            return args[0]
        elif isinstance(args[0], str):          # @window.event('on_resize')
            name = args[0]

            def decorator(func):
                self.push_handler(name, func)
                return func
            return decorator
