#!/usr/bin/env python

'''Not a browser (yet), just fetches pages and displays them.

Usage::
    browser.py http://meyerweb.com/eric/css/tests/css2/sec08-03a.htm

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: xhtml.py 366 2007-01-02 07:48:00Z Alex.Holkner $'

from pyglet.GL.VERSION_1_1 import *
from pyglet.layout import *
from pyglet.window import *
from pyglet.window.event import *
from pyglet.clock import *

from pyglet.text import *
from pyglet.layout.css import Stylesheet
from pyglet.layout.locator import create_locator

import sys
if len(sys.argv) < 2:
    print __doc__
    sys.exit(1)
url = sys.argv[1]

locator = create_locator(url)
file = locator.get_default_stream()

window = Window()
exit_handler = ExitHandler()
window.push_handlers(exit_handler)
offset_top = 0
layout_height = 0

def on_resize(width, height):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    layout.render_device.width = width
    layout.render_device.height = height
    layout.layout()

    # HACK; will have public accessor eventually
    global layout_height
    layout_height = 1200

def on_scroll(dx, dy):
    global offset_top
    offset_top -= dy * 30

layout = render_html(file, locator=locator)

window.push_handlers(on_resize=on_resize)
window.push_handlers(on_mouse_scroll=on_scroll)
on_resize(window.width, window.height)
glClearColor(1, 1, 1, 1)

clock = Clock()

while not exit_handler.exit:
    clock.tick()
    print 'FPS = %.2f\r' % clock.get_fps(),

    window.dispatch_events()
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    offset_top = max(min(offset_top, layout_height - window.height), 0)
    glTranslatef(0, window.height + offset_top, 0)
    layout.draw()
    window.flip()
