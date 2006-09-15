#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pyglet.window
import time

from pyglet.GL.VERSION_1_1 import *

factory = pyglet.window.WindowFactory()
factory.config._attributes['doublebuffer'] = 1
w1 = factory.create()
glClearColor(1, 0, 1, 1)
glClear(GL_COLOR_BUFFER_BIT)
glFlush()
w1.flip()

w2 = factory.create()
glClearColor(1, 1, 0, 1)
glClear(GL_COLOR_BUFFER_BIT)
glFlush()
w2.flip()

while True:
    for e in w2.get_events():
        print e
    for e in w1.get_events():
        print e
'''

    window.switch_to()
    glClear(GL_COLOR_BUFFER_BIT)
    window.flip()

    w2.switch_to()
    glClear(GL_COLOR_BUFFER_BIT)
    w2.flip()
'''


