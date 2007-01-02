#!/usr/bin/env python

'''Example of a custom replaced element for XHTML layout.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: xml_css.py 322 2006-12-26 12:53:18Z Alex.Holkner $'

from ctypes import *

from pyglet.GL.VERSION_1_1 import *
from pyglet.GLU.VERSION_1_1 import *
from pyglet.window import *
from pyglet.window.event import *
from pyglet.clock import *

from pyglet.text import *
from pyglet.layout import *
from pyglet.layout.base import *
from pyglet.layout.formatters.xhtmlformatter import XHTMLFormatter

data = '''<?xml version="1.0"?>
<html>  
  <head>
    <style>
    </style>
  </head>
  <body>
    <h1>Replaced element example</h1>

    <p>Replaced elements are drawn by the application.  You write a class
    and attach it to the XML formatter to handle desired element names.
    pyglet includes such a box generator to create image replaced element
    boxes.</p>

    <p>Here we've created a custom replaced element tag: "&lt;cube&gt;":
    <cube/>.  Layout is handled by pyglet.layout, and rendering is handled by
    the application.  Of course, the usual CSS properties can be applied:</p>

    <p><cube style="width:100%;border:1px solid;background-color:aqua" /></p>

    <p>This example also demonstrates use of the slightly lower-level layout
    APIs rather than using the render_xhtml() function.</p>
    
  </body>
</html> '''

class CubeBox(Box):
    intrinsic_width = 32
    intrinsic_height = 32
    intrinsic_ratio = 1.

    angle = 0

    def __init__(self):
        from pyglet.model.geometric import cube_list
        self.cube = cube_list()

    def draw(self, render_device, left, top, right, bottom):

        glPushAttrib(GL_CURRENT_BIT | GL_LIGHTING_BIT | GL_ENABLE_BIT)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_DEPTH_TEST)
        glColor3f(1, .5, .5)

        # This is a somewhat complicated way of setting up a projection
        # into the render box.  It's a bit hacky, really it should read
        # the modelview (instead of window.height + offset_top).  We
        # should encapsulate this somewhere because it's useful.

        # Should also be setting up clipping planes around the render area.
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        width = right - left
        height = top - bottom
        centerx = left + width / 2
        centery = bottom + height / 2 + window.height + offset_top
        glTranslatef(-1, -1, 0)
        glTranslatef(centerx * 2 / window.width, 
                     centery * 2 / window.height, 0)
        glScalef(width / window.width, height / window.height, 1)
        gluPerspective(70., width / float(height), 1, 100)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Done setting up the projection, everything hereon is "normal"
        vec4 = (c_float * 4)
        glLightfv(GL_LIGHT0, GL_POSITION, vec4(1, 2, 1, 0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, vec4(.7, .7, .7, 1))

        glTranslatef(0, 0, -3)
        glRotatef(30, 1, 0, 0)
        glRotatef(self.angle, 0, 1, 0)
        self.cube.draw()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glPopAttrib()

class CubeGenerator(BoxGenerator):
    accept_names = ['cube']

    def create_box(self, name, attrs):
        return CubeBox()

def render_custom_xhtml(data):
    '''Create a layout for data similar to `render_xhtml`, but attach our
    custom box generator.'''
    render_device = create_render_device()
    formatter = XHTMLFormatter(render_device)
    cube_generator = CubeGenerator()
    formatter.add_generator(cube_generator)
    return render(data, formatter)

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
    #layout_height = layout.frame.children[-1].border_bottom
    layout_height = 1000

def on_scroll(dx, dy):
    global offset_top
    offset_top -= dy * 30


if __name__ == '__main__':
    # Create a window, attach the usual event handlers
    window = Window()
    exit_handler = ExitHandler()
    window.push_handlers(exit_handler)
    window.push_handlers(on_resize=on_resize)
    window.push_handlers(on_mouse_scroll=on_scroll)

    offset_top = 0
    layout_height = 0
    layout = render_custom_xhtml(data)

    on_resize(window.width, window.height)
    glClearColor(1, 1, 1, 1)

    clock = Clock()

    while not exit_handler.exit:
        dt = clock.tick()
        CubeBox.angle += dt * 50
        print 'FPS = %.2f\r' % clock.get_fps(),

        window.dispatch_events()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        offset_top = max(min(offset_top, layout_height - window.height), 0)
        glTranslatef(0, window.height + offset_top, 0)
        layout.draw()
        window.flip()
