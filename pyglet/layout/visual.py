#!/usr/bin/env python

'''Control rendering and viewport.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.layout.frame import *

class VisualLayout(object):
    def __init__(self, render_device):
        self.render_device = render_device
        self._document = None
        self._root_frame = None
        self._need_reflow = True
        self._need_reconstruct = True

        # Position of viewport on canvas (+ve Y is down).  Size of viewport
        # determines the initial containing block.
        self.viewport_x = 0
        self.viewport_y = 0
        self._viewport_width = 0 
        self._viewport_height = 0

    def set_document(self, document):
        self._document = document
        self._need_reconstruct = True
    document = property(lambda self: self._document, set_document)

    def get_canvas_width(self):
        if not self._document:
            return 0
        if self._need_reflow:
            self.reflow()
        # By convention with web browsers, don't allow viewport to show left
        # of origin.
        return self._root_frame.bounding_box_right
    canvas_width = property(get_canvas_width)

    def get_canvas_height(self):
        if not self._document:
            return 0
        if self._need_reflow:
            self.reflow()
        # By convention with web browsers, don't allow viewport to show above
        # of origin.
        return -self._root_frame.bounding_box_bottom
    canvas_height = property(get_canvas_height)

    def set_viewport_width(self, width):
        self._viewport_width = width
        self._need_reflow = True
    viewport_width = property(lambda self: self._viewport_width, 
                              set_viewport_width)

    def set_viewport_height(self, height):
        self._viewport_height = height
        self._need_reflow = True
    viewport_height = property(lambda self: self._viewport_height, 
                               set_viewport_height)

    def draw(self):
        if self._viewport_width <= 0 or self._viewport_height <= 0: 
            return

        if not self.document:
            return

        if self._need_reflow:
            self.reflow()

        self._root_frame.draw(self.viewport_x, self.viewport_y, 
            self.render_device)

    def reconstruct(self):
        self._need_reconstruct = False
        frame_builder = FrameBuilder(self.document, self.render_device)
        self._root_frame = frame_builder.build_frame(self.document.root)
        self._need_reflow = True

    def reflow(self):
        if self._need_reconstruct:
            self.reconstruct()
        initial_containing_block = self.initial_containing_block()
        if initial_containing_block.width <= 0:
            return
        self._need_reflow = False
        self._root_frame.flow(initial_containing_block)
        self._root_frame.resolve_bounding_box(0, 0)

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


