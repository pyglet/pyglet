#!/usr/bin/env python

'''Prints all window events to stdout.
'''

from pyglet import window
from pyglet.window.event import WindowEventLogger

win = window.Window()

win.push_handlers(WindowEventLogger())

while not win.has_exit:
    win.dispatch_events()
    win.clear()
    win.flip()
