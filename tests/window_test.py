#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pyglet.window
from pyglet.window.event import *
from pyglet.GL.VERSION_1_1 import *

w1 = pyglet.window.create(200, 200)
glClearColor(1, 0, 1, 1)
glClear(GL_COLOR_BUFFER_BIT)
glFlush()
w1.flip()

w2 = pyglet.window.create(200, 200)
glClearColor(1, 1, 0, 1)
glClear(GL_COLOR_BUFFER_BIT)
glFlush()
w2.flip()

debug_handler = DebugEventHandler()
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

while not exit_handler.exit:
    w1.dispatch_events()
    w2.dispatch_events()

