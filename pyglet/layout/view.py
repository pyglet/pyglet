#!/usr/bin/env python

'''Single view of a document.

Responsible for maintaining frame and style trees.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.layout.content import *
from pyglet.layout.frame import *

class DocumentView(DocumentListener):
    def __init__(self, render_device, document):
        self.render_device = render_device
        self.document = document
        self.document.add_listener(self)
        self.frame_builder = FrameBuilder(self.document, self.render_device)

        self._root_frame = None

        self._require_reconstruct = False # Temporary HACK

        # Position of viewport on canvas (+ve Y is down).  Size of viewport
        # determines the initial containing block.
        self.viewport_x = 0
        self.viewport_y = 0
        self._viewport_width = 0 
        self._viewport_height = 0

    def on_set_root(self, element):
        self._require_reconstruct = True

    def on_element_modified(self, element):
        self._require_reconstruct = True

    def on_element_style_modified(self, element):
        frame = element.frame
        if frame:
            frame.style = self.frame_builder.get_style_node(element)
            frame.purge_style_cache()
            frame.mark_flow_dirty()

    def reflow_resize(self):
        if self._require_reconstruct:
            self._root_frame = self.frame_builder.build_frame(self.document.root)
            self._root_frame.containing_block = self.initial_containing_block()
        self._root_frame.containing_block = self.initial_containing_block()
        self._root_frame.mark_flow_dirty()

    def update_flow(self):
        if self._require_reconstruct:
            self._root_frame = self.frame_builder.build_frame(self.document.root)
            self._root_frame.containing_block = self.initial_containing_block()
            self._require_reconstruct = False
        if self._root_frame.flow_dirty:
            self._root_frame.flow()
            self._root_frame.resolve_bounding_box(0, 0)

    def get_canvas_width(self):
        self.update_flow()
        # By convention with web browsers, don't allow viewport to show left
        # of origin.
        return self._root_frame.bounding_box_right
    canvas_width = property(get_canvas_width)

    def get_canvas_height(self):
        self.update_flow()
        # By convention with web browsers, don't allow viewport to show above
        # of origin.
        return -self._root_frame.bounding_box_bottom
    canvas_height = property(get_canvas_height)

    def set_viewport_width(self, width):
        self._viewport_width = width
        self.reflow_resize()
    viewport_width = property(lambda self: self._viewport_width, 
                              set_viewport_width)

    def set_viewport_height(self, height):
        self._viewport_height = height
        self.reflow_resize()
    viewport_height = property(lambda self: self._viewport_height, 
                               set_viewport_height)

    def draw(self):
        if self._viewport_width <= 0 or self._viewport_height <= 0: 
            return

        if self._root_frame.flow_dirty:
            self._root_frame.flow()
            self._root_frame.resolve_bounding_box(0, 0)

        self._root_frame.draw(self.viewport_x, self.viewport_y, 
            self.render_device)

    def get_frames_for_point(self, x, y):
        x += self.viewport_x
        y -= self.viewport_y
        return self._root_frame.get_frames_for_point(x, y)

    def get_elements_for_point(self, x, y):
        elements = [frame.element for frame in self.get_frames_for_point(x, y)]

        # Remove adjacent duplicates
        unique_elements = []
        last_e = None
        for e in elements:
            if e is not last_e:
                last_e = e
                unique_elements.append(e)
        return unique_elements

    def initial_containing_block(self):
        return ContainingBlock(self._viewport_width, self._viewport_height)


