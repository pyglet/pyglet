#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.gl import *
from pyglet.event import *

from layout.css import *
from layout.content import *
from layout.frame import *
from layout.locator import *
from layout.view import *
from layout.gl.device import *
from layout.gl.event import *
from layout.gl.image import *
from layout.builders.htmlbuilder import *
from layout.builders.xmlbuilder import *
from layout.builders.xhtmlbuilder import *

__all__ = ['Layout', 'select']

class GLLayout(LayoutEventDispatcher):
    # Disable this if you don't want the layout to resize with the window
    # and position itself to cover the entire window automatically.
    size_to_window = True       

    def __init__(self, render_device=None, locator=None):
        super(GLLayout, self).__init__()

        self.replaced_element_factories = []

        if not locator:
            locator = LocalFileLocator()
        self.locator = locator

        if not render_device:
            render_device = GLRenderDevice(self.locator)
        self.render_device = render_device

        self.document = Document()
        self.view = DocumentView(self.render_device, self.document)
        self.add_replaced_element_factory(ImageReplacedElementFactory(locator))
        
        # If the layout is added to a window event stack, the following
        # variables are taken care of automatically (x, y, viewport).

        # Position of layout within projection (window, +ve Y is up)
        self.x = 0
        self.y = 0

    def add_replaced_element_factory(self, factory):
        # XXX duplication
        self.replaced_element_factories.append(factory)
        self.view.frame_builder.add_replaced_element_factory(factory)

    def set_data(self, data, builder_class):
        self.document = Document()
        self.view.set_document(self.document)
        for factory in self.replaced_element_factories:
            self.view.frame_builder.add_replaced_element_factory(factory)
        builder  = builder_class(self.document)
        builder.feed(data)
        builder.close()
        self._mouse_over_elements = set()
        
    def set_xhtml(self, data):
        self.set_data(data, XHTMLBuilder)

    def set_html(self, data):
        self.set_data(data, HTMLBuilder)

    # Duplicate the public properties of DocumentView here for convenience

    def set_viewport_x(self, x):
        self.view.viewport_x = x
    viewport_x = property(lambda self: self.view.viewport_x, 
                          set_viewport_x)

    def set_viewport_y(self, y):
        self.view.viewport_y = y
    viewport_y = property(lambda self: self.view.viewport_y, 
                          set_viewport_y)

    def set_viewport_width(self, width):
        self.view.viewport_width = width
    viewport_width = property(lambda self: self.view.viewport_width, 
                              set_viewport_width)

    def set_viewport_height(self, height):
        self.view.viewport_height = height
    viewport_height = property(lambda self: self.view.viewport_height, 
                               set_viewport_height)


    canvas_width = property(lambda self: self.view.canvas_width)
    canvas_height = property(lambda self: self.view.canvas_height)

    def draw(self):
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(self.x, self.y, 0)
        self.view.draw()
        glPopMatrix()

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
            self.view.viewport_width = width
            self.view.viewport_height = height
            self.x = 0
            self.y = height
        self.constrain_viewport()
        return EVENT_UNHANDLED

    def on_mouse_scroll(self, x, y, dx, dy):
        self.viewport_x += dx * 30
        self.viewport_y -= dy * 30
        self.constrain_viewport()

    def on_mouse_press(self, x, y, button, modifiers):
        x -= self.x
        y -= self.y
        elements = self.view.get_elements_for_point(x, y)
        for element in elements[::-1]:
            handled = self.dispatch_event(element, 'on_mouse_press', 
                x, y, button, modifiers)
            if handled:
                return EVENT_HANDLED
        return EVENT_UNHANDLED

    def on_mouse_motion(self, x, y, dx, dy):
        x -= self.x
        y -= self.y
        elements = self.view.get_elements_for_point(x, y)
        elements_set = set(elements)
        for element in self._mouse_over_elements - elements_set:
            self.dispatch_event(element, 'on_mouse_leave', x, y)
            element.remove_pseudo_class('hover')
            self.document.element_style_modified(element)
        for element in elements_set - self._mouse_over_elements:
            self.dispatch_event(element, 'on_mouse_enter', x, y)
            element.add_pseudo_class('hover')
            self.document.element_style_modified(element)
        self._mouse_over_elements = elements_set

    def on_mouse_leave(self, x, y):
        x -= self.x
        y -= self.y
        for element in self._mouse_over_elements:
            self.dispatch_event(element, 'on_mouse_leave', x, y)
            element.remove_pseudo_class('hover')
            self.document.element_style_modified(element)
        self._mouse_over_elements = set()

# As long as there's not going to be any other render device around, call
# this one by a nicer name.
Layout = GLLayout


