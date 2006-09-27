#!/usr/bin/env python
'''
The event implementation scoreboard

                                     X11  Win  OSX
 EVENT_KEYPRESS / _KEYRELEASE         X    X    X
 EVENT_TEXT                           X
 EVENT_TEXT_???   (cursor control)
 EVENT_BUTTONPRESS / _BUTTONRELEASE   X
 EVENT_MOUSEMOTION                    X
 EVENT_CLOSE                          X     (possibly rename WINDOWCLOSE?)
 EVENT_POINTERIN / _POINTEROUT  (pointer in / out of window)
 window expose
 window resize
 window move
 window minimize / expose?

XXX I just noticed pyglet/event.py which needs to match all this

OPEN QUESTIONS
--------------

1. If there's no handler for EVENT_CLOSE we probably want to have the
   application just sys.exit() -- otherwise the close button on X11 does
   nothing.

2. EVENT_MOUSEMOTION could supply the callback with a relative movement
   amount. I propose that this be reset to (0, 0) on:

   - the very first callback
   - the first move after an EVENT_POINTERIN

3. Can we generate EVENT_POINTERIN / _POINTEROUT across all platforms?

   For X11, the actual events to listen to are EnterNotify and LeaveNotify
   which explicitly track the pointer.

4. Do we also want to track input focus?


XLIB NOTES
----------

It'd be nice if we didn't have Xlib handlers set up for these if we're not
actually listening for them:
 - mouse movement (generates *many* unnecessary events)
 - WM_DELETE_WINDOW (maybe? if we don't listen for it then the WM will
   DestroyWindow us -- see point #1 in `OPEN QUESTIONS`_)

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pyglet.window.key
from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED, EventHandler

class WindowEventHandler(EventHandler):
    pass

EVENT_KEYPRESS = WindowEventHandler.register_event_type('on_keypress')
EVENT_KEYRELEASE = WindowEventHandler.register_event_type('on_keyrelease')
EVENT_TEXT = WindowEventHandler.register_event_type('on_text')
EVENT_MOUSEMOTION = WindowEventHandler.register_event_type('on_mousemotion')
EVENT_BUTTONPRESS = WindowEventHandler.register_event_type('on_buttonpress')
EVENT_BUTTONRELEASE = WindowEventHandler.register_event_type('on_buttonrelease')
EVENT_CLOSE = WindowEventHandler.register_event_type('on_close')

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

    def on_mousemotion(self, x, y):
        pass

    def on_buttonpress(self, button, x, y, modifiers):
        pass

    def on_buttonrelease(self, button, x, y, modifiers):
        pass

    def on_close(self):
        pass

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

    def on_mousemotion(self, x, y):
        print 'on_mousemotion(x=%d, y=%d)' % (x, y)
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

