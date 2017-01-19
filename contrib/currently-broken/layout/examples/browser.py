#!/usr/bin/env python

'''Not a browser (yet), just fetches pages and displays them.

Usage::
    browser.py http://meyerweb.com/eric/css/tests/css2/sec08-03a.htm

    Press 'v' to dump source (base file only).
    Press 'e' to dump elements.
    Press 'f' to dump frames.
    Press 'w' to dump frames using flowed children.
    Press 's' to dump frames and style nodes.
    Press left/right keys with ctrl or shift to resize window width.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: xhtml.py 366 2007-01-02 07:48:00Z Alex.Holkner $'

from pyglet.gl import *
from pyglet.window import Window
from pyglet.window import key
from pyglet import clock

from layout import *
from layout.locator import *

import textwrap
import sys

if len(sys.argv) < 2:
    print __doc__
    sys.exit(1)
url = sys.argv[1]

locator = create_locator(url)
file = locator.get_default_stream()

window = Window(visible=False, resizable=True)
offset_top = 0
layout_height = 0

layout = Layout(locator=locator)
layout.set_html(locator.get_default_stream().read())

@select('a')
def on_mouse_press(element, x, y, button, modifiers):
    url = element.attributes['href']
    print 'Going to %s...' % url
    file = locator.get_stream(url)
    layout.set_html(file.read())

layout.push_handlers(on_mouse_press)
window.push_handlers(layout)

@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.V:
        print repr(layout.locator.get_default_stream().read())
    if symbol == key.E:
        layout.document.root.pprint()
    if symbol == key.F:
        layout.view._root_frame.pprint()
    if symbol == key.W:
        layout.view._root_frame.pprint_flowed()
    if symbol == key.S:
        layout.view._root_frame.pprint_style()
    if symbol == key.LEFT and modifiers & key.key.MOD_CTRL:
        window.width -= 1
    if symbol == key.LEFT and modifiers & key.key.MOD_SHIFT:
        window.width -= 10
    if symbol == key.RIGHT and modifiers & key.key.MOD_CTRL:
        window.width += 1
    if symbol == key.RIGHT and modifiers & key.key.MOD_SHIFT:
        window.width += 10
    print 'window size is %dx%d' % (window.width, window.height)

glClearColor(1, 1, 1, 1)
window.set_visible()

while not window.has_exit:
    clock.tick()
    print 'FPS = %.2f\r' % clock.get_fps(),

    window.dispatch_events()
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    layout.draw()
    window.flip()
