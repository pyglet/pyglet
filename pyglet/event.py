#!/usr/bin/env python

'''Generic event dispatcher framework.

All objects that produce events in pyglet implement `EventDispatcher`,
providing a consistent interface for registering and manipulating event
handlers.  The most commonly used event dispatcher is `pyglet.window.Window`.

Event types
===========

For each event dispatcher there is a set of events that it dispatches; these
correspond with the type of event handlers you can attach.  Event types are
identified by their name, for example, ''on_resize''.  If you are creating a
new class which implements `EventDispatcher`, you must call
`EventDispatcher.register_event_type` for each event type.

Attaching event handlers
========================

An event handler is simply a function or method.  You can attach an event
handler to a dispatcher in several ways with `EventDispatcher.set_handlers`:

1. By implicitly using the name of the function as the event type::

       def on_resize(width, height):
           # ...
       dispatcher.set_handlers(on_resize)

2. By explicitly specifying the event type with a keyword argument::

       def my_on_resize(width, height):
           # ...
       dispatcher.set_handlers(on_resize=my_on_resize)

3. By supplying an instance with methods corresponding to the event types::

       class ResizeHandler(object):
            def on_resize(self, width, height):
                # ...
       dispatcher.set_handlers(ResizeHandler())

4. Using the `event` function decorator::

       @dispatcher.event
       def on_resize(width, height):
           # ...

The `EventDispatcher.set_handlers` method will actually accept any number
of event handlers, and will attach them all simultaneously.

You can also attach events more directly:

5. By setting a closure directly on the instance::

       def on_resize(width, height):
           # ...
       dispatcher.on_resize = on_resize


6. By subclassing the dispatcher and overriding the event::

       class MyDispatcher(DispatcherClass):
           def on_resize(self, width, height):
               # ...

Note that these methods (5 and 6) affect the handler "below" the last handler
on the stack (described below); you should only use them if you are not using
the handler stack.

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
* Creating "chains" of event handlers, where the event propogates from the
  top-most (most recently added) handler to the bottom, until a handler
  takes care of it.

Use `EventDispatcher.push_handlers` to create a new level in the stack and
attach handlers to it.  This method parses its arguments in the same way as
`EventDispatcher.set_handlers`::

    dispatcher.push_handlers(on_resize=temp_on_resize,
                             on_key_press=temp_on_key_press)

After an event handler has processed an event, it is passed on to the
next-lowest event handler, unless the handler returns `EVENT_HANDLED`, which
prevents further propogation.

To remove all handlers on this stack level (those specified in `push_handlers`
as well as any subsequent `set_handlers` calls), use
`EventDispatcher.pop_handlers`.

Dispatching events
==================

pyglet uses a single-threaded model for all application code.  Events are
never called except when explicitly calling `EventDispatcher.dispatch_events`.
It is up to the specific event dispatcher to queue relevant events until they
can be dispatched, at which point the handlers are called in the order the
events were originally generated.

This implies that your application runs with a main loop that continously
updates the application state and checks for new events::

    while True:
        dispatcher.dispatch_events()
        # ... additional per-frame processing

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import inspect

EVENT_HANDLED = True 
EVENT_UNHANDLED = None

class EventException(Exception):
    pass

class EventDispatcher(object):
    '''Generic event dispatcher interface.

    See the module docstring for usage.
    '''
    # Placeholder empty stack; real stack is created only if needed
    _event_stack = ()

    @classmethod
    def register_event_type(cls, name):
        '''Register an event type with the dispatcher.

        Registering event types allows the dispatcher to validate event
        handler names as they are attached, and to search attached objects for
        suitable handlers.
        '''
        if not hasattr(cls, 'event_types'):
            cls.event_types = []
        cls.event_types.append(name)
        return name

    def push_handlers(self, *args, **kwargs):
        '''Push a level onto the top of the handler stack, then attach zero or
        more event handlers.

        See `set_handlers` for the accepted argument types.
        '''
        # Create event stack if necessary
        if type(self._event_stack) is tuple:
            self._event_stack = [{}]

        # Place dict full of new handlers at beginning of stack
        self._event_stack.insert(0, {})
        self.set_handlers(*args, **kwargs)

    def set_handlers(self, *args, **kwargs):
        '''Attach one or more event handlers.  
        
        If keyword arguments are given, they name the event type to attach.
        Otherwise, a callable's `__name__` attribute will be used.  Any other
        object may also be specified, in which case it will be searched for
        callables with event names.
        '''
        # Create event stack if necessary
        if type(self._event_stack) is tuple:
            self._event_stack = [{}]

        for object in args:
            if inspect.isroutine(object):
                # Single magically named function
                name = object.__name__
                if name not in self.event_types:
                    raise EventException('Unknown event "%s"' % name)
                self.set_handler(name, object)
            else:
                # Single instance with magically named methods
                for name, handler in inspect.getmembers(object):
                    if name in self.event_types:
                        self.set_handler(name, handler)
        for name, handler in kwargs.items():
            # Function for handling given event (no magic)
            if name not in self.event_types:
                raise EventException('Unknown event "%s"' % name)
            self.set_handler(name, handler)

    def set_handler(self, name, handler):
        '''Attach a single event handler.

        :Parameters:
            `name` : str
                Name of the event type to attach to.
            `handler` : callable
                Event handler to attach.

        '''
        # Create event stack if necessary
        if type(self._event_stack) is tuple:
            self._event_stack = [{}]

        self._event_stack[0][name] = handler

    def pop_handlers(self):
        '''Pop the top level of event handlers off the stack.
        '''
        assert self._event_stack and 'No handlers pushed'

        del self._event_stack[0]

    def dispatch_event(self, event_type, *args):
        '''Dispatch a single event to the attached handlers, propogating
        from the top of the stack until one returns `EVENT_UNHANDLED`.
        This method should be used only by `EventDispatcher` implementors;
        applications should call `dispatch_events`.

        :Parameters:
            `event_type` : str
                Name of the event.
            `args` : sequence
                Arguments to pass to the event handler.

        '''
        # Search handler stack for matching event handlers
        for frame in self._event_stack:
            handler = frame.get(event_type, None)
            if handler:
                ret = handler(*args)
                if ret != EVENT_UNHANDLED:
                    return

        # Check instance for an event handler
        if hasattr(self, event_type):
            getattr(self, event_type)(*args)

    def dispatch_events(self):
        '''Call attached event handlers for all queued events.
        '''
        raise NotImplementedError('Abstract; this method needs overriding')


    def event(self, *args):
        '''Function decorator for an event handler.  
        
        Usage::

            win = window.Window()

            @win.event
            def on_resize(self, width, height):
                # ...


        or::

            @win.event('on_resize')
            def foo(self, width, height):
                # ...

        '''
        if len(args) == 0:                      # @window.event()
            def decorator(func):
                self.set_handlers(func)
                return func
            return decorator
        elif inspect.isroutine(args[0]):        # @window.event
            self.set_handlers(args[0])
            return args[0]
        elif type(args[0]) in (str, unicode):   # @window.event('on_resize')
            name = args[0]
            def decorator(func):
                self.set_handler(name, func) 
                return func
            return decorator
