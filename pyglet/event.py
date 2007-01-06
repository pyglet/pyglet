#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import inspect

EVENT_HANDLED = None 
EVENT_UNHANDLED = 1 

class EventException(Exception):
    pass

class EventHandler(object):
    def __init__(self):
        self._event_stack = [{}]

    @classmethod
    def register_event_type(cls, name):
        if not hasattr(cls, 'event_types'):
            cls.event_types = []
        cls.event_types.append(name)
        return name

    def push_handlers(self, *args, **kwargs):
        self._event_stack.insert(0, {})
        self.set_handlers(*args, **kwargs)

    def set_handlers(self, *args, **kwargs):
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
        self._event_stack[0][name] = handler

    def pop_handlers(self):
        del self._event_stack[0]

    def dispatch_event(self, event_type, *args):
        for frame in self._event_stack:
            handler = frame.get(event_type, None)
            if handler:
                ret = handler(*args)
                if ret != EVENT_UNHANDLED:
                    break
        return None

    def dispatch_events(self):
        raise NotImplementedError('Abstract; this method needs overriding')

