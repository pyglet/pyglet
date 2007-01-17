#!/usr/bin/env python

'''Not a browser (yet), just fetches pages and displays them.

Usage::
    browser.py http://meyerweb.com/eric/css/tests/css2/sec08-03a.htm

    Press 'v' to dump source (base file only).
    Press 'e' to dump elements.
    Press 'f' to dump frames.
    Press 'w' to dump frames using flowed children.
    Press 's' to dump frames and style nodes.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: xhtml.py 366 2007-01-02 07:48:00Z Alex.Holkner $'

from pyglet.GL.VERSION_1_1 import *
from pyglet.layout import *
from pyglet.layout.locator import *
from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *
from pyglet.clock import *

from pyglet.text import *

import textwrap
import sys

if len(sys.argv) < 2:
    print __doc__
    sys.exit(1)
url = sys.argv[1]

locator = create_locator(url)
file = locator.get_default_stream()

window = Window(visible=False)
offset_top = 0
layout_height = 0

def on_key_press(symbol, modifiers):
    if symbol == K_V:
        print repr(layout.locator.get_default_stream().read())
    if symbol == K_E:
        layout.document.root.pprint()
    if symbol == K_F:
        layout.view._root_frame.pprint()
    if symbol == K_W:
        layout.view._root_frame.pprint_flowed()
    if symbol == K_S:
        layout.view._root_frame.pprint_style()
    return True

layout = Layout(locator=locator)
layout.set_html(locator.get_default_stream().read())

@select('a')
def on_mouse_press(element, button, x, y, modifiers):
    url = element.attributes['href']
    print 'Going to %s...' % url
    file = locator.get_stream(url)
    layout.set_html(file.read())

layout.push_handlers(on_mouse_press)

window.push_handlers(layout)
window.push_handlers(on_key_press=on_key_press)

glClearColor(1, 1, 1, 1)
clock = Clock()
window.set_visible()

while not window.has_exit:
    clock.tick()
    print 'FPS = %.2f\r' % clock.get_fps(),

    window.dispatch_events()
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    layout.draw()
    window.flip()
