import inspect
import time

from pyglet.event import (EventDispatcher, EVENT_UNHANDLED, EVENT_HANDLED,
    EventException)
from pyglet.window import key

from layout.css import Rule, RuleSet, Selector, SimpleSelector

# partially snarfed from layout.gl.event
# Instead of each stack layer being a dictionary mapping event-name to
# event-function, each layer is a dictionary mapping event-name to 
# RuleSet

'''
Events:

    Passed through if handled:

        on_mouse_motion(self, x, y, dx, dy):
        on_mouse_press(self, x, y, button, modifiers):
        on_mouse_release(self, x, y, button, modifiers):
        on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        on_mouse_scroll(self, x, y, dx, dy):
        on_key_press(self, symbol, modifiers):
        on_text(self, text):
        on_text_motion(self, motion):
        on_text_motion_select(self, motion):
  
    New:

        on_change(element, value)
           the element's "value" changed (eg. text in a text input)

        on_click(element, x, y, buttons, modifiers, click_count)
           the element was clicked. the click_count argument indicates how
           many times the element has been clicked in rapid succession.

        on_drag(element, x, y, dx, dy, buttons, modifiers)
           press on listening element followed by mouse movement

        on_element_enter(element, x, y)
           the mouse is over the element

        on_element_leave(element, x, y)
           the mouse is no longer over the element

        on_drag_enter(element, x, y, dragged_element)
           the dragged_element is being dragged over the stationary element

        on_drag_leave(element, x, y, dragged_element)
           the dragged_element is no longer being dragged over the
           stationary element

        on_drag_complete(element, x, y, buttons, modifiers, ok)
           release after dragging listening element, ok is return code
           from dropped-on element's on_element_drop

        on_drop(element, x, y, button, modifiers, element)
            element drag-n-dropped on listening element

        on_element_enter(element, x, y)
            mouse has entered listening element's rect

        on_element_leave(element, x, y)
            mouse has left listening element's rect

        on_gain_focus(element)
            listening element gains focus

        on_lose_focus(element)
            listening element loses focus
'''

POSITIONAL_EVENTS = set('on_mouse_motion on_mouse_press on_mouse_release on_mouse_drag on_mouse_scroll on_drag on_element_enter on_element_leave on_drag_enter on_drag_leave on_drag_complete on_drop on_enter on_leave'.split())

class GUIEventDispatcher(EventDispatcher):

    default_event_handlers = {}

    def __init__(self):
        EventDispatcher.__init__(self)
        assert isinstance(self._event_stack, tuple)
        self._event_stack = [self.default_event_handlers]

    @classmethod
    def set_default_handler(cls, name, selector, handler):
        '''Inspect handler for a selector and apply to the primary-set.
        If the handler has no selector, it is assumed to have a universal
        selector.
        '''
        if name not in cls.default_event_handlers:
            cls.default_event_handlers[name] = RuleSet()
        ruleset = cls.default_event_handlers[name]
        ruleset.add_rule(Rule(selector, handler))

    def select(self, rule, event_name=None):
        # XXX assume passed an element with an id to select on
        if not isinstance(rule, str):
            rule = '#' + rule.id

        def decorate(func):
            func.selectors = [Selector.from_string(r.strip())
                for r in rule.split(',')]
            if event_name is not None:
                func.event_name = event_name
            self.push_handlers(func)
            return func
        return decorate

    def set_handlers(self, *args, **kwargs):
        '''Attach one or more event handlers to the top level of the handler
        stack.
        
        See `push_handlers` for the accepted argument types.
        '''
        # Create event stack if necessary
        if type(self._event_stack) is tuple:
            self._event_stack = [{}]

        for object in args:
            if inspect.isroutine(object):
                # Single magically named function
                name = getattr(object, 'event_name', object.__name__)
                if name not in self.event_types:
                    raise EventException('Unknown event "%s"' % name)
                self.set_handler(name, object)
            else:
                # Single instance with magically named methods
                for name, handler in inspect.getmembers(object):
                    name = getattr(handler, 'event_name', name)
                    if name in self.event_types:
                        self.set_handler(name, handler)
        for name, handler in kwargs.items():
            # Function for handling given event (no magic)
            if name not in self.event_types:
                raise EventException('Unknown event "%s"' % name)
            self.set_handler(name, handler)

    def set_handler(self, name, handler):
        '''Inspect handler for a selector and apply to the primary-set.
        If the handler has no selector, it is assumed to have a universal
        selector.
        '''
        if name not in self._event_stack[0]:
            self._event_stack[0][name] = RuleSet()
        ruleset = self._event_stack[0][name]
        #if not hasattr(handler, 'selector'):
            #handler.selector = universal_selector
        for selector in handler.selectors:
            ruleset.add_rule(Rule(selector, handler))

    def dispatch_event(self, element, event_type, *args, **kw):
        update_active=kw.get('update_active', True)
        if element.isEnabled():
            for frame in self._event_stack:
                ruleset = frame.get(event_type, None)
                if ruleset:
                    rules = ruleset.get_matching_rules(element)
                    for rule in rules:
                        handler = rule.declaration_set
                        try:
                            ret = handler(element, *args)
                        except TypeError, message:
                            print 'ERROR CALLING  %r (%r, *%r)]'%(handler,
                                element, args)
                            raise
                        if ret != EVENT_UNHANDLED:
                            # update the currently-active element
                            if update_active:
                                self.active_element = element
                            return True

        # not handled, so pass the event up to parent element
        if element.parent is not None:
            return self.dispatch_event(element.parent, event_type, *args, **kw)

    # NOW THE EVENT HANDLERS
    active_element = None
    is_dragging_element = False
    mouse_press_element = None
    drag_over_element = None
    over_element = None
    focused_element = None
    # XXX record the element and timestamp for generating EVENT_MOUSE_HOVER
    hover_element = None

    _rects = None
    def setDirty(self):
        self._rects = None

    def setFocus(self, element):
        # gain focus first so some elements are able to detect whether their
        # child has been focused
        if element is not None and self.focused_element is not element:
            ae = self.active_element
            self.dispatch_event(element, 'on_gain_focus')
            if self.active_element is not ae:
                # focus was caught by some parent element
                element = self.active_element
            else:
                # focus was uncaught - stay with the element targetted
                self.active_element = element

        if (self.focused_element is not None and
                self.focused_element is not element):
            self.dispatch_event(self.focused_element, 'on_lose_focus',
                update_active=False)

        self.focused_element = element

    def getRects(self, exclude=None):
        if self._rects is not None and exclude is not None:
            return self._rects

        rects = []
        clip = self.rect
        for element in self.children:
            if element is exclude: continue
            rects.extend(element.getRects(clip, exclude=exclude))
        rects.reverse()
        if exclude:
            self._rects = rects
        return rects

    def determineHit(self, x, y, exclude=None):
        rects = self.getRects(exclude)

        # and now who did we hit?
        for o, (ox, oy, oz, w, h) in rects:
            if x < ox: continue
            if y < oy: continue
            if x > ox + w: continue
            if y > oy + h: continue
            return o
        return None

    def on_mouse_motion(self, x, y, dx, dy):
        element = self.determineHit(x, y)
        if element is not self.over_element:
            if self.over_element is not None and self.over_element.is_enabled:
                self.dispatch_event(self.over_element, 'on_element_leave', x, y)

            if element is not None and element.is_enabled:
                self.dispatch_event(element, 'on_element_enter', x, y)

            if self.debug_display is not None:
                self.debug_display.setText(repr(element))

            #if mouse stable (not moving)? and 1 second has passed
            #    element.on_element_hover(x, y)

        self.over_element = element
        return EVENT_HANDLED

    def on_mouse_enter(self, x, y):
        return self.on_mouse_motion(x, y, 0, 0)

    def on_mouse_leave(self, x, y):
        if self.over_element is not None and self.over_element.is_enabled:
            self.dispatch_event(self.over_element, 'on_element_leave', x, y)
        self.over_element = None
        return EVENT_HANDLED

    def on_mouse_press(self, x, y, button, modifiers):
        element = self.determineHit(x, y)
        if element is None: return EVENT_UNHANDLED
        if not element.is_enabled: return EVENT_UNHANDLED

        # remember the pressed element so that we can:
        # 1. pass it mouse drag events even if the mouse moves off its hit area
        # 2. TODO pass it a "lost mouse focus" event?
        self.active_element = element
        self.mouse_press_element = element
        self.is_dragging_element = False

        # switch focus
        self.setFocus(element)

        return self.dispatch_event(element, 'on_mouse_press', x, y, button,
            modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.active_element is not None:
            # see if the previously-pressed element wants...

            # an on_mouse_drag event
            handled = self.dispatch_event(self.active_element,
                'on_mouse_drag', x, y, dx, dy, buttons, modifiers)
            if handled == EVENT_HANDLED:
                if self.mouse_press_element is not None:
                    self.dispatch_event(self.mouse_press_element,
                        'on_mouse_release', x, y, buttons, modifiers,
                        update_active=False)
                    self.mouse_press_element = None
                return EVENT_HANDLED

            # or an on_drag event
            handled = self.dispatch_event(self.active_element, 'on_drag',
                x, y, dx, dy, buttons, modifiers)
            if handled == EVENT_HANDLED:
                if self.mouse_press_element is not None:
                    self.dispatch_event(self.mouse_press_element,
                        'on_mouse_release', x, y, buttons, modifiers,
                        update_active=False)
                    self.mouse_press_element == None

                # tell the element we've dragged the active element over
                element = self.determineHit(x, y, exclude=self.active_element)
                if element is not self.drag_over_element:
                    if self.drag_over_element is not None:
                        self.dispatch_event(self.drag_over_element,
                            'on_drag_leave', x, y, self.active_element,
                            update_active=False)
                if element is not None and element.is_enabled:
                    self.dispatch_event(element, 'on_drag_enter', x, y,
                        self.active_element, update_active=False)
                self.drag_over_element = element

                self.is_dragging_element = True
                return EVENT_HANDLED

        # regular event pass-through
        element = self.determineHit(x, y)
        if element is None: return EVENT_UNHANDLED
        if not element.is_enabled:
            self.active_element = None
            # XXX mouse_leave??
            return EVENT_UNHANDLED

        if self.active_element is not element:
            # XXX mouse_over??
            self.active_element = element

        self.is_dragging_element = False

        return self.dispatch_event(element, 'on_mouse_drag', x, y, dx, dy,
            buttons, modifiers)

    _last_click = 0
    def on_mouse_release(self, x, y, button, modifiers):
        if self.is_dragging_element:
            # the on_drop check will most likely alter the active element
            active = self.active_element
            element = self.determineHit(x, y, exclude=active)

            # see if the element underneath wants the active element
            if element is not None and element.is_enabled:
                ok = self.dispatch_event(element, 'on_drop', x, y, button,
                    modifiers, active) == EVENT_HANDLED
            else:
                ok = False

            # now tell the active element what's going on
            handled = self.dispatch_event(active,
                'on_drag_complete', x, y, button, modifiers, ok)

            # clear state - we're done
            self.active_element = None
            self.is_dragging_element = False
            return handled

        # XXX do we want to pass the release event to this element?
        # (most user-interfaces don't pass a "click" event to a button that's
        # no longer under the mouse.)
        self.active_element = None

        # regular mouse press/release click
        element = self.determineHit(x, y)
        if element is None: return EVENT_UNHANDLED
        if not element.is_enabled:
            return EVENT_UNHANDLED

        handled =  self.dispatch_event(element, 'on_mouse_release', x, y,
            button, modifiers)
        if handled == EVENT_HANDLED:
            return EVENT_HANDLED

        now = time.time()
        if now - self._last_click < .25:
            self._click_count += 1
        else:
            self._click_count = 1
        self._last_click = now

        return self.dispatch_event(element, 'on_click', x, y, button,
            modifiers, self._click_count)

    def on_mouse_scroll(self, x, y, dx, dy):
        element = self.determineHit(x, y)
        if element is None: return EVENT_UNHANDLED
        return self.dispatch_event(element, 'on_mouse_scroll', x, y, dx, dy)

    # the following are special -- they will be sent to the currently-focused
    # element rather than being dispatched
    def on_key_press(self, symbol, modifiers):
        handled = EVENT_UNHANDLED
        if self.focused_element is not None:
            handled = self.dispatch_event(self.focused_element,
                'on_key_press', symbol, modifiers)
        if handled == EVENT_UNHANDLED and symbol == key.TAB:
            if modifiers & key.MOD_SHIFT:
                self.focusNextElement(-1)
            else:
                self.focusNextElement()
        return handled

    def on_text(self, text):
        if self.focused_element is None: return
        return self.dispatch_event(self.focused_element, 'on_text', text)

    def on_text_motion(self, motion):
        if self.focused_element is None: return
        return self.dispatch_event(self.focused_element, 'on_text_motion',
            motion)

    def on_text_motion_select(self, motion):
        if self.focused_element is None: return
        return self.dispatch_event(self.focused_element, 'on_text_select',
            motion)


# EVENTS IN and OUT
GUIEventDispatcher.register_event_type('on_mouse_motion')
GUIEventDispatcher.register_event_type('on_mouse_press')
GUIEventDispatcher.register_event_type('on_mouse_release')
GUIEventDispatcher.register_event_type('on_mouse_enter')
GUIEventDispatcher.register_event_type('on_mouse_leave')
GUIEventDispatcher.register_event_type('on_mouse_drag')
GUIEventDispatcher.register_event_type('on_mouse_scroll')

GUIEventDispatcher.register_event_type('on_key_press')
GUIEventDispatcher.register_event_type('on_text')
GUIEventDispatcher.register_event_type('on_text_motion')
GUIEventDispatcher.register_event_type('on_text_motion_select')

# EVENTS OUT
GUIEventDispatcher.register_event_type('on_change')
GUIEventDispatcher.register_event_type('on_click')
GUIEventDispatcher.register_event_type('on_drag')
GUIEventDispatcher.register_event_type('on_drag_enter')
GUIEventDispatcher.register_event_type('on_drag_leave')
GUIEventDispatcher.register_event_type('on_drag_complete')
GUIEventDispatcher.register_event_type('on_drop')
GUIEventDispatcher.register_event_type('on_element_enter')
GUIEventDispatcher.register_event_type('on_element_leave')
GUIEventDispatcher.register_event_type('on_gain_focus')
GUIEventDispatcher.register_event_type('on_lose_focus')
        

def select(rule, event_name=None):
    # XXX assume passed an element with an id to select on
    if not isinstance(rule, str):
        rule = '#' + rule.id

    def decorate(func):
        func.selectors = [Selector.from_string(r.strip())
            for r in rule.split(',')]
        if event_name is not None:
            func.event_name = event_name
        return func
    return decorate


def default(rule, event_name=None):
    def decorate(func):
        name = event_name or func.__name__
        if name not in GUIEventDispatcher.event_types:
            raise EventException('Unknown event "%s"' % name)
        for r in rule.split(','):
            selector = Selector.from_string(r.strip())
            GUIEventDispatcher.set_default_handler(name, selector, func)
        return func
    return decorate


universal_selector = Selector(SimpleSelector(None, None, (), (), ()), ())

