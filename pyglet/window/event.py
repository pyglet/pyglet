#!/usr/bin/env python
'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pyglet.window.key
from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED, EventDispatcher

class WindowEventDispatcher(EventDispatcher):
    pass

# symbolic names for the window events
EVENT_KEY_PRESS = WindowEventDispatcher.register_event_type('on_key_press')
EVENT_KEY_RELEASE = WindowEventDispatcher.register_event_type('on_key_release')
EVENT_TEXT = WindowEventDispatcher.register_event_type('on_text')
EVENT_MOUSE_MOTION = \
    WindowEventDispatcher.register_event_type('on_mouse_motion')
EVENT_MOUSE_DRAG = WindowEventDispatcher.register_event_type('on_mouse_drag')
EVENT_MOUSE_PRESS = WindowEventDispatcher.register_event_type('on_mouse_press')
EVENT_MOUSE_RELEASE = \
    WindowEventDispatcher.register_event_type('on_mouse_release')
EVENT_MOUSE_SCROLL = \
    WindowEventDispatcher.register_event_type('on_mouse_scroll')
EVENT_MOUSE_ENTER = WindowEventDispatcher.register_event_type('on_mouse_enter')
EVENT_MOUSE_LEAVE = WindowEventDispatcher.register_event_type('on_mouse_leave')
EVENT_CLOSE = WindowEventDispatcher.register_event_type('on_close')
EVENT_EXPOSE = WindowEventDispatcher.register_event_type('on_expose')
EVENT_RESIZE = WindowEventDispatcher.register_event_type('on_resize')
EVENT_MOVE = WindowEventDispatcher.register_event_type('on_move')
EVENT_ACTIVATE = WindowEventDispatcher.register_event_type('on_activate')
EVENT_DEACTIVATE = WindowEventDispatcher.register_event_type('on_deactivate')
EVENT_SHOW = WindowEventDispatcher.register_event_type('on_show')
EVENT_HIDE = WindowEventDispatcher.register_event_type('on_hide')
EVENT_CONTEXT_LOST = \
    WindowEventDispatcher.register_event_type('on_context_lost')
EVENT_CONTEXT_STATE_LOST = \
    WindowEventDispatcher.register_event_type('on_context_state_lost')

# symbolic names for the mouse buttons
MOUSE_LEFT_BUTTON =   1 << 0
MOUSE_MIDDLE_BUTTON = 1 << 1
MOUSE_RIGHT_BUTTON =  1 << 2

def _modifiers_to_string(modifiers):
    mod_names = []
    if modifiers & pyglet.window.key.MOD_SHIFT:
        mod_names.append('MOD_SHIFT')
    if modifiers & pyglet.window.key.MOD_CTRL:
        mod_names.append('MOD_CTRL')
    if modifiers & pyglet.window.key.MOD_ALT:
        mod_names.append('MOD_ALT')
    if modifiers & pyglet.window.key.MOD_CAPSLOCK:
        mod_names.append('MOD_CAPSLOCK')
    if modifiers & pyglet.window.key.MOD_NUMLOCK:
        mod_names.append('MOD_NUMLOCK')
    if modifiers & pyglet.window.key.MOD_COMMAND:
        mod_names.append('MOD_COMMAND')
    if modifiers & pyglet.window.key.MOD_OPTION:
        mod_names.append('MOD_OPTION')
    return '|'.join(mod_names)

def _buttons_to_string(buttons):
    button_names = []
    if buttons & MOUSE_LEFT_BUTTON:
        button_names.append('MOUSE_LEFT_BUTTON')
    if buttons & MOUSE_MIDDLE_BUTTON:
        button_names.append('MOUSE_MIDDLE_BUTTON')
    if buttons & MOUSE_RIGHT_BUTTON:
        button_names.append('MOUSE_RIGHT_BUTTON')
    return '|'.join(button_names)

def _symbol_to_string(symbol):
    return pyglet.window.key._key_names.get(symbol, str(symbol))

# Does nothing, but shows prototypes.
class EventHandler(object):
    def on_key_press(self, symbol, modifiers):
        pass

    def on_key_release(self, symbol, modifiers):
        pass

    def on_text(self, text):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_mouse_press(self, button, x, y, modifiers):
        '''
            "button" is one of:
                MOUSE_LEFT_BUTTON = 1
                MOUSE_MIDDLE_BUTTON = 2
                MOUSE_RIGHT_BUTTON = 4
        '''
        pass

    def on_mouse_release(self, button, x, y, modifiers):
        pass

    def on_mouse_scroll(self, dx, dy):
        pass

    def on_close(self):
        pass

    def on_mouse_enter(self, x, y):
        pass

    def on_mouse_leave(self, x, y):
        pass

    def on_expose(self):
        pass

    def on_resize(self, width, height):
        pass

    def on_move(self, x, y):
        pass

    def on_activate(self):
        pass

    def on_deactivate(self):
        pass

    def on_show(self):
        pass

    def on_hide(self):
        pass

    def on_context_lost(self):
        pass

    def on_context_state_lost(self):
        pass

class ExitHandler(object):
    '''Simple handler that detects the window close button or escape key
    press.
    '''
    has_exit = False
    def on_close(self):
        self.has_exit = True
    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.K_ESCAPE:
            self.has_exit = True
        return EVENT_UNHANDLED

class KeyboardStateHandler(dict):
    '''Simple handler that tracks the state of keys on the keyboard. If a
    key is pressed then this handler holds a True value for it.

    For example:

        >>> keyboard = KeyboardStateHandler()
        >>> # hold down the "up" arrow
        >>> keyboard[K_UP]
        True
        >>> keyboard[K_DOWN]
        False
    '''
    def on_key_press(self, symbol, modifiers):
        self[symbol] = True
        return EVENT_UNHANDLED
    def on_key_release(self, symbol, modifiers):
        self[symbol] = False
        return EVENT_UNHANDLED
    def __getitem__(self, key):
        return self.get(key, False)

class DebugEventHandler(object):
    def on_key_press(self, symbol, modifiers):
        print 'on_key_press(symbol=%s, modifiers=%s)' % (
            _symbol_to_string(symbol), _modifiers_to_string(modifiers))
        return EVENT_UNHANDLED

    def on_key_release(self, symbol, modifiers):
        print 'on_key_release(symbol=%s, modifiers=%s)' % (
            _symbol_to_string(symbol), _modifiers_to_string(modifiers))
        return EVENT_UNHANDLED

    def on_text(self, text):
        print 'on_text(text=%r)' % text
        return EVENT_UNHANDLED

    def on_mouse_motion(self, x, y, dx, dy):
        print 'on_mouse_motion(x=%d, y=%d, dx=%d, dy=%d)' % (x, y, dx, dy)
        return EVENT_UNHANDLED

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        print 'on_mouse_drag(x=%d, y=%d, dx=%d, dy=%d, '\
                            'buttons=%s, modifiers=%s)' % (
              x, y, dx, dy, 
              _buttons_to_string(buttons),
              _modifiers_to_string(modifiers))
        return EVENT_UNHANDLED

    def on_mouse_press(self, button, x, y, modifiers):
        print 'on_mouse_press(button=%r, x=%d, y=%d, modifiers=%s)' % (
            button, x, y, _modifiers_to_string(modifiers))
        return EVENT_UNHANDLED

    def on_mouse_release(self, button, x, y, modifiers):
        print 'on_mouse_release(button=%r, x=%d, y=%d, modifiers=%s)' % (
            button, x, y, _modifiers_to_string(modifiers))
        return EVENT_UNHANDLED

    def on_mouse_scroll(self, dx, dy):
        print 'on_mouse_scroll(dx=%f, dy=%f)' % (dx, dy)
        return EVENT_UNHANDLED

    def on_close(self):
        print 'on_destroy()'
        return EVENT_UNHANDLED

    def on_mouse_enter(self, x, y):
        print 'on_mouse_enter(x=%d, y=%d)' % (x, y)
        return EVENT_UNHANDLED

    def on_mouse_leave(self, x, y):
        print 'on_mouse_leave(x=%d, y=%d)' % (x, y)
        return EVENT_UNHANDLED

    def on_expose(self):
        print 'on_expose()'
        return EVENT_UNHANDLED

    def on_resize(self, width, height):
        print 'on_resize(width=%d, height=%d)' % (width, height)
        return EVENT_UNHANDLED

    def on_move(self, x, y):
        print 'on_move(x=%d, y=%d)' % (x, y)
        return EVENT_UNHANDLED

    def on_activate(self):
        print 'on_activate()'
        return EVENT_UNHANDLED

    def on_deactivate(self):
        print 'on_deactivate()'
        return EVENT_UNHANDLED

    def on_show(self):
        print 'on_show()'
        return EVENT_UNHANDLED

    def on_hide(self):
        print 'on_hide()'
        return EVENT_UNHANDLED

    def on_context_lost(self):
        print 'on_context_lost()'
        return EVENT_UNHANDLED

    def on_context_state_lost(self):
        print 'on_context_state_lost()'
        return EVENT_UNHANDLED
