#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pyglet.window.key

EVENT_HANDLED = None 
EVENT_UNHANDLED = 1 

_event_types = []
def _make_event(name):
    _event_types.append(name)
    return name

EVENT_KEYPRESS = _make_event('on_keypress')
EVENT_KEYRELEASE = _make_event('on_keyrelease')
EVENT_TEXT = _make_event('on_text')
EVENT_MOUSEMOTION = _make_event('on_mousemotion')
EVENT_BUTTONPRESS = _make_event('on_buttonpress')
EVENT_BUTTONRELEASE = _make_event('on_buttonrelease')

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
    return '+'.join(mod_names)

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

    def on_mousemotion(self, position, modifiers):
        pass

    def on_buttonpress(self, button, modifiers):
        pass

    def on_buttonrelease(self, button, modifiers):
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

    def on_mousemotion(self, position):
        print 'on_mousemotion(position=%r)' % (position, )
        return EVENT_UNHANDLED

    def on_buttonpress(self, button, modifiers):
        print 'on_buttonpress(button=%r, modifiers=%s)' % (button,
            _modifiers_to_string(modifiers))
        return EVENT_UNHANDLED

    def on_buttonrelease(self, button, modifiers):
        print 'on_buttonrelease(button=%r, modifiers=%s)' % (button,
            _modifiers_to_string(modifiers))
        return EVENT_UNHANDLED

