#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pyglet.window
from pyglet.window.event import *
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

debug_handler = DebugEventHandler()
class ExitHandler(object):
    running = True
    def on_close(self):
        self.running = False
    def on_keypress(self, symbol, modifiers):
        if symbol == pyglet.window.key.K_ESCAPE:
            self.running = False
        return EVENT_UNHANDLED
exit_handler = ExitHandler()
def do_nothing(*args): pass
def on_text(text):
    print 'ON_TEXT(%r)'%text

# set up our funky strange event handlers on the purple window
w1.push_handlers(debug_handler, on_keypress=do_nothing,
    on_keyrelease=do_nothing)
w1.push_handlers(exit_handler)
w1.push_handlers(on_text)

w2.push_handlers(exit_handler)

while exit_handler.running:
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


