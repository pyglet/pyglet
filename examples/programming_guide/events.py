#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet import window
from pyglet.window import key
from pyglet.window import mouse

win = window.Window()

def on_key_press(symbol, modifiers):
    if symbol == key.A:
        print 'The "A" key was pressed.'
    elif symbol == key.LEFT:
        print 'The left arrow key was pressed.'
    elif symbol == key.ENTER:
        print 'The enter key was pressed.'

win.on_key_press = on_key_press

def on_mouse_press(x, y, button, modifiers):
    if button == mouse.MOUSE_LEFT_BUTTON:
        print 'The left mouse button was pressed.'

win.on_mouse_press = on_mouse_press

while not win.has_exit:
    win.dispatch_events()

    win.clear()
    win.flip()
