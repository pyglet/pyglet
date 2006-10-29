#!/usr/bin/env python
'''

OPEN QUESTIONS
--------------

1. If there's no handler for EVENT_CLOSE we probably want to have the
   application just sys.exit() -- otherwise the close button on X11 does
   nothing.

2. EVENT_MOUSEMOTION could supply the callback with a relative movement
   amount. I propose that this be reset to (0, 0) on:

   - the very first callback
   - the first move after an EVENT_ENTER

3. Can we generate EVENT_ENTER / _LEAVE across all platforms?

   X11 gives us mouse motion information with these events.

4. Do we also want to track input focus?

XLIB NOTES
----------

It'd be nice if we didn't have Xlib handlers set up for these if we're not
actually listening for them:
 - mouse movement (generates *many* unnecessary events)
    - <ah> this would invalidate public members window.mouse.x/y -- but
      there's no reason for these to be public anyway...?
 - WM_DELETE_WINDOW (maybe? if we don't listen for it then the WM will
   DestroyWindow us -- see point #1 in `OPEN QUESTIONS`_)

Resize and move are handled by a bunch of different events:

- ResizeRequest (reports another client's attempts to change the size of a
  window)
- ConfigureNotify (reports actual changes to a window's state, such as
  size, position, border, and stacking order)
- ConfigureRequest (reports when another client initiates a configure window
  request on any child of a specified window)

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pyglet.window.key
from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED, EventHandler

class WindowEventHandler(EventHandler):
    pass

# symbolic names for the window events
EVENT_KEYPRESS = WindowEventHandler.register_event_type('on_keypress')
EVENT_KEYRELEASE = WindowEventHandler.register_event_type('on_keyrelease')
EVENT_TEXT = WindowEventHandler.register_event_type('on_text')
EVENT_MOUSEMOTION = WindowEventHandler.register_event_type('on_mousemotion')
EVENT_BUTTONPRESS = WindowEventHandler.register_event_type('on_buttonpress')
EVENT_BUTTONRELEASE = WindowEventHandler.register_event_type('on_buttonrelease')
EVENT_CLOSE = WindowEventHandler.register_event_type('on_close')
EVENT_ENTER = WindowEventHandler.register_event_type('on_enter')
EVENT_LEAVE = WindowEventHandler.register_event_type('on_leave')
EVENT_EXPOSE = WindowEventHandler.register_event_type('on_expose')
EVENT_RESIZE = WindowEventHandler.register_event_type('on_resize')
EVENT_MOVE = WindowEventHandler.register_event_type('on_move')

# symbolic names for the mouse buttons
MOUSE_LEFT_BUTTON = 1
MOUSE_MIDDLE_BUTTON = 2
MOUSE_RIGHT_BUTTON = 3
MOUSE_SCROLL_UP = 4
MOUSE_SCROLL_DOWN = 5

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

def _symbol_to_string(symbol):
    return pyglet.window.key._key_names.get(symbol, str(symbol))

# Does nothing, but shows prototypes.
class EventHandler(object):
    def on_keypress(self, symbol, modifiers):
        pass

    def on_keyrelease(self, symbol, modifiers):
        pass

    def on_text(self, text):
        pass

    def on_mousemotion(self, x, y, dx, dy):
        pass

    def on_buttonpress(self, button, x, y, modifiers):
        '''
            "button" is one of:
                MOUSE_LEFT_BUTTON = 1
                MOUSE_MIDDLE_BUTTON = 2
                MOUSE_RIGHT_BUTTON = 3
                MOUSE_SCROLL_UP = 4
                MOUSE_SCROLL_DOWN = 5
        '''
        pass

    def on_buttonrelease(self, button, x, y, modifiers):
        pass

    def on_close(self):
        pass

    def on_enter(self, x, y):
        pass

    def on_leave(self, x, y):
        pass

    def on_expose(self):
        pass

    def on_resize(self, width, height):
        pass

    def on_move(self, x, y):
        pass


class ExitHandler(object):
    '''Simple handler that detects the window close button or escape key
    press.
    '''
    exit = False
    def on_close(self):
        self.exit = True
    def on_keypress(self, symbol, modifiers):
        if symbol == pyglet.window.key.K_ESCAPE:
            self.exit = True
        return EVENT_UNHANDLED


class DebugEventHandler(object):
    def on_keypress(self, symbol, modifiers):
        print 'on_keypress(symbol=%s, modifiers=%s)' % (
            _symbol_to_string(symbol), _modifiers_to_string(modifiers))
        return EVENT_UNHANDLED

    def on_keyrelease(self, symbol, modifiers):
        print 'on_keyrelease(symbol=%s, modifiers=%s)' % (
            _symbol_to_string(symbol), _modifiers_to_string(modifiers))
        return EVENT_UNHANDLED

    def on_text(self, text):
        print 'on_text(text=%r)' % text
        return EVENT_UNHANDLED

    def on_mousemotion(self, x, y, dx, dy):
        print 'on_mousemotion(x=%d, y=%d, dx=%d, dy=%d)' % (x, y, dx, dy)
        return EVENT_UNHANDLED

    def on_buttonpress(self, button, x, y, modifiers):
        print 'on_buttonpress(button=%r, x=%d, y=%d, modifiers=%s)' % (
            button, x, y, _modifiers_to_string(modifiers))
        return EVENT_UNHANDLED

    def on_buttonrelease(self, button, x, y, modifiers):
        print 'on_buttonrelease(button=%r, x=%d, y=%d, modifiers=%s)' % (
            button, x, y, _modifiers_to_string(modifiers))
        return EVENT_UNHANDLED

    def on_close(self):
        print 'on_destroy()'
        return EVENT_UNHANDLED

    def on_enter(self, x, y):
        print 'on_enter(x=%d, y=%d)' % (x, y)
        return EVENT_UNHANDLED

    def on_leave(self, x, y):
        print 'on_leave(x=%d, y=%d)' % (x, y)
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

