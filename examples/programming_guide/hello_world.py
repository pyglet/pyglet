#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet import font
from pyglet import window

win = window.Window()

ft = font.load('Arial', 36)
text = font.Text(ft, 'Hello, World!')

while not win.has_exit:
    win.dispatch_events()

    win.clear()
    text.draw()
    win.flip()
