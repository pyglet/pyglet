#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os

from pyglet import image
from pyglet import window

win = window.Window()

img_filename = os.path.join(os.path.dirname(__file__), 'kitten.jpg')
img = image.load(img_filename)

while not win.has_exit:
    win.dispatch_events()

    win.clear()
    img.blit(0, 0)
    win.flip()
