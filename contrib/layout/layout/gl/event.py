#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet.event import EventDispatcher, EVENT_UNHANDLED
from layout.css import RuleSet, Selector, SimpleSelector


# Instead of each stack layer being a dictionary mapping event-name to
# event-function, each layer is a dictionary mapping event-name to 
# RuleSet

class LayoutEventDispatcher(EventDispatcher):
    def __init__(self):
        super(LayoutEventDispatcher, self).__init__()

    def set_handler(self, name, handler):
        '''Inspect handler for a selector and apply to the primary-set.
        If the handler has no selector, it is assumed to have a universal
        selector.
        '''
        if name not in self._event_stack[0]:
            self._event_stack[0][name] = RuleSet()
        ruleset = self._event_stack[0][name]
        if not hasattr(handler, 'selector'):
            handler.selector = universal_selector
        ruleset.add_rule(handler)

    def dispatch_event(self, element, event_type, *args):
        for frame in self._event_stack:
            ruleset = frame.get(event_type, None)
            if ruleset:
                handlers = ruleset.get_matching_rules(element)
                for handler in handlers:
                    ret = handler(element, *args)
                    if ret != EVENT_UNHANDLED:
                        return True

LayoutEventDispatcher.register_event_type('on_mouse_press')
LayoutEventDispatcher.register_event_type('on_mouse_enter')
LayoutEventDispatcher.register_event_type('on_mouse_leave')
        
def select(rule):
    selector = Selector.from_string(rule)
    def decorate(func):
        func.selector = selector
        return func
    return decorate

universal_selector = Selector(SimpleSelector(None, None, (), (), ()), ())
