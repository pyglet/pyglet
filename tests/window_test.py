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

class EventHandler(object):
    running = True
    def on_keypress(self, symbol, modifiers):
        if symbol == pyglet.window.key.K_ESCAPE:
            self.running = False
main_handler = EventHandler()
w1.push_handlers(main_handler)
w2.push_handlers(main_handler)

while main_handler.running:
    w1.dispatch_events()
    w2.dispatch_events()

'''
    w1.switch_to()
    glClear(GL_COLOR_BUFFER_BIT)
    w1.flip()

    w2.switch_to()
    glClear(GL_COLOR_BUFFER_BIT)
    w2.flip()
'''


