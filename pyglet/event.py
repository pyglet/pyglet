#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from SDL import *

_stack = [{}]

def push():
    _stack.insert(0, {})

def pop():
    del _stack[0]

def pump():
    event = SDL_PollEventAndReturn()
    while event:
        dispatch(event)
        event = SDL_PollEventAndReturn()

def dispatch(event):
    dispatcher = dispatchers.get(event.type)
    if not dispatcher:
        dispatcher = dispatch_user

    for frame in _stack:
        handler = frame.get(event.type, None)
        if handler:
            if not dispatcher(handler, event):
                break

def dispatch_active(handler, event):
    return handler(event.state, event.gain)

def dispatch_key(handler, event):
    return handler(event.keysym.unicode, event.keysym.sym, event.keysym.mod)

def dispatch_mousemotion(handler, event):
    return handler(event.x, event.y)

def dispatch_mousebutton(handler, event):
    return handler(event.button, event.x, event.y)

def dispatch_joyaxis(handler, event):
    return handler(event.axis, event.value)

def dispatch_joyball(handler, event):
    return handler(event.ball, event.xrel, event.yrel)

def dispatch_joyhat(handler, event):
    return handler(event.hat, event.value)

def dispatch_joybutton(handler, event):
    return handler(event.button)

def dispatch_quit(handler, event):
    return handler()

def dispatch_resize(handler, event):
    return handler(event.w, event.h)

def dispatch_expose(handler, event):
    return handler()

def dispatch_user(handler, event):
    return handler(event)

dispatchers = {
    SDL_ACTIVEEVENT:    dispatch_active,
    SDL_KEYUP:          dispatch_key,
    SDL_KEYDOWN:        dispatch_key,
    SDL_MOUSEMOTION:    dispatch_mousemotion,
    SDL_MOUSEBUTTONDOWN:dispatch_mousebutton,
    SDL_MOUSEBUTTONUP:  dispatch_mousebutton,
    SDL_JOYAXISMOTION:  dispatch_joyaxis,
    SDL_JOYBALLMOTION:  dispatch_joyball,
    SDL_JOYHATMOTION:   dispatch_joyhat,
    SDL_JOYBUTTONDOWN:  dispatch_joybutton,
    SDL_JOYBUTTONUP:    dispatch_joybutton,
    SDL_QUIT:           dispatch_quit,
    SDL_VIDEORESIZE:    dispatch_resize,
    SDL_VIDEOEXPOSE:    dispatch_expose
}

def on_active(handler):
    _stack[0][SDL_ACTIVEEVENT] = handler

def on_keyup(handler):
    _stack[0][SDL_KEYUP] = handler

def on_keydown(handler):
    _stack[0][SDL_KEYDOWN] = handler

def on_mousemotion(handler):
    _stack[0][SDL_MOUSEMOTION] = handler

def on_mousedown(handler):
    _stack[0][SDL_MOUSEDOWN] = handler

def on_mouseup(handler):
    _stack[0][SDL_MOUSEUP] = handler

def on_joyaxismotion(handler):
    _stack[0][SDL_JOYAXISMOTION] = handler

def on_joyballmotion(handler):
    _stack[0][SDL_JOYBALLMOTION] = handler

def on_joyhatmotion(handler):
    _stack[0][SDL_JOYHATMOTION] = handler

def on_joybuttondown(handler):
    _stack[0][SDL_JOYBUTTONDOWN] = handler

def on_joybuttonup(handler):
    _stack[0][SDL_JOYBUTTONUP] = handler

def on_quit(handler):
    _stack[0][SDL_QUIT] = handler

def on_resize(handler):
    _stack[0][SDL_VIDEORESIZE] = handler

def on_expose(handler):
    _stack[0][SDL_VIDEOEXPOSE] = handler

def on_user(handler):
    _stack[0][SDL_USEREVENT] = handler

# Default quit behaviour
_quit = False
def is_quit():
    return _quit

def post_quit():
    global _quit
    _quit = True

def _quit_key_handler(character, symbol, modifiers):
    if symbol ==  SDLK_ESCAPE:
        post_quit()

on_quit(post_quit)
on_keydown(_quit_key_handler)
