#!/usr/bin/env python

'''Not a browser (yet), just fetches pages and displays them.

Usage::
    browser.py http://meyerweb.com/eric/css/tests/css2/sec08-03a.htm

    Press 'b' to dump boxes.
    Press 'f' to dump frames.
    Press 's' to dump source (base file only).
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: xhtml.py 366 2007-01-02 07:48:00Z Alex.Holkner $'

from pyglet.GL.VERSION_1_1 import *
from pyglet.layout import *
from pyglet.layout.event import *
from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.key import *
from pyglet.clock import *

from pyglet.text import *
from pyglet.layout.css import Stylesheet
from pyglet.layout.locator import create_locator

import textwrap
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
    layout.hack_offset = -window.height - offset_top

def print_box(box, indent=''):
    print '\n'.join(textwrap.wrap(repr(box), initial_indent=indent,
            subsequent_indent=indent))
    if box.children:
        for child in box.children:
            print_box(child, '  ' + indent)

def print_frame(frame, indent=''):
    print '\n'.join(textwrap.wrap(repr(frame), initial_indent=indent,
            subsequent_indent=indent))
    if hasattr(frame, 'children'):
        for child in frame.children:
            print_frame(child, '  ' + indent)

def on_key_press(symbol, modifiers):
    if symbol == K_B:
        print_box(layout.root_frame.children[0].box)
    if symbol == K_F:
        print_frame(layout.root_frame)
    if symbol == K_S:
        print repr(locator.get_default_stream().read())
    return True

def on_scroll(dx, dy):
    global offset_top
    offset_top -= dy * 30
    layout.hack_offset = -window.height - offset_top

layout = render_html(file, locator=locator)

@select('a')
def on_mouse_press(element, button, x, y, modifiers):
    url = element.attributes['href']
    print 'Going to %s...' % url
    file = locator.get_stream(url)

    from pyglet.layout.formatters.htmlformatter import HTMLFormatter
    from pyglet.layout.gl.image import ImageBoxGenerator
    render_device = create_render_device(locator)
    formatter = HTMLFormatter(render_device, locator)
    image_box_generator = ImageBoxGenerator(locator)
    formatter.add_generator(image_box_generator)
    box = formatter.format(file)
    layout.set_root(box)
    layout.layout()
layout.push_handlers(on_mouse_press)

window.push_handlers(layout)
window.push_handlers(on_resize=on_resize)
window.push_handlers(on_mouse_scroll=on_scroll)
window.push_handlers(on_key_press=on_key_press)
on_resize(window.width, window.height)
glClearColor(1, 1, 1, 1)

clock = Clock()

while not exit_handler.exit:
    clock.tick()
    print 'FPS = %.2f\r' % clock.get_fps(),

    window.dispatch_events()
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    #offset_top = max(min(offset_top, layout_height - window.height), 0)
    glTranslatef(0, window.height + offset_top, 0)
    layout.draw()
    window.flip()
