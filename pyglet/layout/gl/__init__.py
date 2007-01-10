#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.GL.VERSION_1_1 import *
from pyglet.event import *
from pyglet.layout.visual import *
from pyglet.layout.css import *
from pyglet.layout.locator import *
from pyglet.layout.formatters.xmlformatter import *
from pyglet.layout.formatters.xhtmlformatter import *
from pyglet.layout.formatters.htmlformatter import *
from pyglet.layout.gl.device import *
from pyglet.layout.gl.event import *
from pyglet.layout.gl.image import *

from pyglet.layout.content import *
from pyglet.layout.frame import *
from pyglet.layout.xmlbuilder import *

__all__ = ['Layout', 'select']

class GLLayout(LayoutEventDispatcher):
    # Disable this if you don't want the layout to resize with the window
    # and position itself to cover the entire window automatically.
    size_to_window = True       

    def __init__(self, render_device=None, locator=None):
        super(GLLayout, self).__init__()

        if not locator:
            locator = LocalFileLocator()
        self.locator = locator

        if not render_device:
            render_device = GLRenderDevice(self.locator)
        self._visual = VisualLayout(render_device)
        self.render_device = render_device
        
        # If the layout is added to a window event stack, the following
        # variables are taken care of automatically (x, y, viewport).

        # Position of layout within projection (window, +ve Y is up)
        self.x = 0
        self.y = 0

        # Additional box generators to add to formatters
        self.generators = []

    def set_xhtml(self, data):
        self.document = Document()
        content_builder = XHTMLBuilder(self.document)
        content_builder.feed(data)
        content_builder.close()
        self.document.root.pprint()
        frame_builder = FrameBuilder(self.document, self.render_device)
        root_frame = frame_builder.build_frame(self.document.root)
        root_frame.pprint_style()

    '''
    def set_xml(self, data, stylesheet):
        formatter = XMLFormatter(self._visual.render_device, self.locator)
        formatter.add_stylesheet(stylesheet)
        self.set_data(data, formatter)

    def set_xhtml(self, data):
        formatter = XHTMLFormatter(self._visual.render_device, self.locator)
        image_box_generator = ImageBoxGenerator(self.locator)
        formatter.add_generator(image_box_generator)
        self.set_data(data, formatter)

    def set_html(self, data):
        formatter = HTMLFormatter(self._visual.render_device, self.locator)
        image_box_generator = ImageBoxGenerator(self.locator)
        formatter.add_generator(image_box_generator)
        self.set_data(data, formatter)

    def set_data(self, data, formatter):
        for generator in self.generators:
            formatter.add_generator(generator)
        self._visual.root_box = formatter.format(data)
        self._mouse_over_elements = set()

    def add_generator(self, generator):
        self.generators.append(generator)
    '''

    # Duplicate the public properties of VisualLayout here for convenience

    def set_viewport_x(self, x):
        self._visual.viewport_x = x
    viewport_x = property(lambda self: self._visual.viewport_x, 
                          set_viewport_x)

    def set_viewport_y(self, y):
        self._visual.viewport_y = y
    viewport_y = property(lambda self: self._visual.viewport_y, 
                          set_viewport_y)

    def set_viewport_width(self, width):
        self._visual.viewport_width = width
    viewport_width = property(lambda self: self._visual.viewport_width, 
                              set_viewport_width)

    def set_viewport_height(self, height):
        self._visual.viewport_height = height
    viewport_height = property(lambda self: self._visual.viewport_height, 
                               set_viewport_height)


    canvas_width = property(lambda self: self._visual.canvas_width)
    canvas_height = property(lambda self: self._visual.canvas_height)

    def draw(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(self.x,
                self.x + self._visual.viewport_width,
                self.y - self._visual.viewport_height,
                self.y,
                -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(self.x, self.y, 0)

        self._visual.draw()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def constrain_viewport(self):
        '''Ensure the viewport is not showing anything that's not the
        canvas, unless the canvas is smaller than the viewport, in which
        case it will be aligned top/left.
        '''
        if self.canvas_width < self.viewport_width:
            self.viewport_x = 0
        else:
            self.viewport_x = min(max(0, self.viewport_x), 
                self.canvas_width - self.viewport_width)
        if self.canvas_height < self.viewport_height:
            self.viewport_y = 0
        else:
            self.viewport_y = min(max(0, self.viewport_y), 
                self.canvas_height - self.viewport_height)

    # Window event handlers.
    def on_resize(self, width, height):
        if self.size_to_window:
            self._visual.viewport_width = width
            self._visual.viewport_height = height
            self.x = 0
            self.y = height
        self.constrain_viewport()
        return EVENT_UNHANDLED

    def on_mouse_scroll(self, dx, dy):
        self.viewport_x += dx * 30
        self.viewport_y -= dy * 30
        self.constrain_viewport()

    def on_mouse_press(self, button, x, y, modifiers):
        x -= self.x
        y -= self.y
        elements = self._visual.get_elements_for_point(x, y)
        for element in elements[::-1]:
            handled = self.dispatch_event(element, 'on_mouse_press', 
                button, x, y, modifiers)
            if handled:
                return EVENT_HANDLED
        return EVENT_UNHANDLED

    def on_mouse_motion(self, x, y, dx, dy):
        x -= self.x
        y -= self.y
        elements = self._visual.get_elements_for_point(x, y)
        elements_set = set(elements)
        for element in self._mouse_over_elements - elements_set:
            self.dispatch_event(element, 'on_mouse_leave', x, y)
            element.remove_pseudo_class('hover')
        for element in elements_set - self._mouse_over_elements:
            self.dispatch_event(element, 'on_mouse_enter', x, y)
            element.add_pseudo_class('hover')
        self._mouse_over_elements = elements_set

    def on_mouse_leave(self, x, y):
        x -= self.x
        y -= self.y
        for element in self._mouse_over_elements:
            self.dispatch_event(element, 'on_mouse_leave', x, y)
            element.remove_pseudo_class('hover')
        self._mouse_over_elements = set()

# As long as there's not going to be any other render device around, call
# this one by a nicer name.
Layout = GLLayout


