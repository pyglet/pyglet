#!/usr/bin/env python

'''Example of a custom replaced element for XHTML layout.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: xml_css.py 322 2006-12-26 12:53:18Z Alex.Holkner $'

from ctypes import *

from pyglet.gl import *
from pyglet.window import Window
from pyglet import clock

from layout import *
from layout.frame import *

data = '''<?xml version="1.0"?>
<html>  
  <head>
    <style>
       .big { width:100%;border:1px solid;background-color:aqua }
       .big:hover {background-color:fuschia}
    </style>
  </head>
  <body>
    <h1>Replaced element example</h1>

    <p>Replaced elements are drawn by the application.  You write a class
    and attach it to the layout (or at a lower level, to the frame builder)
    to handle desired element names.
    pyglet includes such a factory to create image replaced element
    frames.</p>

    <p>Here we've created a custom replaced element tag: "&lt;cube&gt;":
    <cube/>.  Layout is handled by pyglet/contrib/layout, and rendering is handled by
    the application.  Of course, the usual CSS properties can be applied:</p>

    <p><cube class="big" /></p>

    <p>If you click on the cube you might even get an event handled.</p>    
  </body>
</html> '''

class CubeDrawable(ReplacedElementDrawable):
    intrinsic_width = 32
    intrinsic_height = 32
    intrinsic_ratio = 1.

    angle = 0

    def __init__(self):
        from model.geometric import cube_list
        self.cube = cube_list()

    def draw(self, frame, render_device, left, top, right, bottom):

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
        centery = bottom + height / 2 + window.height
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

class CubeReplacedElementFactory(ReplacedElementFactory):
    accept_names = ['cube']

    def create_drawable(self, element):
        return CubeDrawable()

# Create a window, attach the usual event handlers
window = Window(visible=False, resizable=True)

layout = Layout()
layout.add_replaced_element_factory(CubeReplacedElementFactory())
layout.set_xhtml(data)
window.push_handlers(layout)

@select('cube')
def on_mouse_press(element, x, y, button, modifiers):
    global rate
    rate = -rate
layout.push_handlers(on_mouse_press)

glClearColor(1, 1, 1, 1)

window.set_visible()

rate = 50

while not window.has_exit:
    dt = clock.tick()
    CubeDrawable.angle += dt * rate
    print 'FPS = %.2f\r' % clock.get_fps(),

    window.dispatch_events()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    layout.draw()
    window.flip()
