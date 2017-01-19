#!/usr/bin/env python

'''Single view of a document.

Responsible for maintaining frame and style trees.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from layout.content import *
from layout.frame import *

class DocumentView(DocumentListener):
    document = None
    def __init__(self, render_device, document):
        self.render_device = render_device
        self.set_document(document)
        
        self._root_frame = None

        self._pending_reflow = set()
        self._pending_reconstruct = set()

        # Position of viewport on canvas (+ve Y is down).  Size of viewport
        # determines the initial containing block.
        self.viewport_x = 0
        self.viewport_y = 0
        self._viewport_width = 0 
        self._viewport_height = 0

    def set_document(self, document):
        if self.document:
            self.document.remove_listener(self)
        self.document = document
        self.document.add_listener(self)
        self.frame_builder = FrameBuilder(self.document, self.render_device)

    def on_set_root(self, element):
        self._pending_reconstruct.clear()
        self._pending_reconstruct.add(element)

    def on_element_modified(self, element):
        # Simple optimisation: ignore if root is pending (TODO ancestors, etc)
        if self.document.root in self._pending_reconstruct:
            return
        self._pending_reconstruct.add(element)

    def on_element_style_modified(self, element):
        frame = element.frame
        if frame:
            new_style = self.frame_builder.get_style_node(element)

            # Common case (style was not modified in a significant way):
            if new_style is frame.style:
                return

            differences = frame.style.get_specified_differences(new_style)
            if 'display' in differences:
                # Need to reconstruct and replace the parent (changing
                # display might affect siblings and presence of anonymous
                # frames).
                if element.parent:
                    self._pending_reconstruct.add(element.parent)
                else:
                    # display change on root.
                    self._pending_reconstruct.add(element)

            else:
                # All other style changes just need reflow.
                frame.style = new_style
                frame.purge_style_cache(differences)
                frame.mark_flow_dirty()
                self._pending_reflow.add(frame)
        else:
            # Reconstruct the parent, possible that frame can be created now.
            if element.parent:
                self._pending_reconstruct.add(element.parent)
            else:
                self._pending_reconstruct.add(element)

    def update_reconstruct(self):
        for element in self._pending_reconstruct:
            if not element.parent:
                assert element is self.document.root
                self._root_frame = \
                    self.frame_builder.build_frame(self.document.root)
                self._root_frame.containing_block = \
                    self.initial_containing_block()
                self._pending_reconstruct.clear()
                self.reflow_resize()
                break
            elif not element.frame:
                # Doesn't currently exist in flow, can ignore. (display
                # changes are pending on parent).
                pass
            else:
                parent_frame = element.parent.frame
                child_frame = element.frame
                # Find ancestor of child_frame that is direct descendent of
                # parent_frame (usually _is_ old_frame, unless there are 
                # anonymous frames in the way).
                while child_frame and child_frame.parent is not parent_frame:
                    child_frame = child_frame.parent
                if not child_frame:
                    # This can happen if several content changes occur before
                    # a reconstruct update occurs.  Solution is more careful
                    # checking of content hierarchy when adding to pending
                    # set.
                    warnings.warn('Frame ancestry does not match content.' +\
                        ' Element %r will not be updated' % element)
                    continue
                assert child_frame in parent_frame.children
                i = parent_frame.children.index(child_frame)

                new_frame = self.frame_builder.build_frame(element)
                if not new_frame:
                    # Eek, can't imagine how this can happen (display:none)
                    # handled at parent.
                    del parent_frame.children[i]
                    element.frame = None
                else:
                    new_frame.parent = parent_frame
                    parent_frame.children[i] = new_frame

                # Reflow parent (should take care of new frame's containing
                # block).
                parent_frame.mark_flow_dirty()
                self._pending_reflow.add(parent_frame)

        self._pending_reconstruct.clear()

    def reflow_resize(self):
        self.update_reconstruct()
        self._root_frame.containing_block = self.initial_containing_block()
        self._root_frame.mark_flow_dirty()
        self._pending_reflow.add(self._root_frame)

    def update_flow(self):
        self.update_reconstruct()
        for frame in self._pending_reflow:
            if not frame.flow_dirty:
                continue  # Already reflowed by some other pending op.

            frame = frame.get_flow_master()
            while True:
                # Reflow frame and all its dirty children, make note if
                # its dimensions change.
                old_metrics = frame.get_layout_metrics()
                frame.flow()
                new_metrics = frame.get_layout_metrics()
                # TODO: this won't catch changes to relative position because
                # these are computed at style, irrespective of flow.  This
                # is a problem because frame.position() is only called by
                # parent flow at the moment.

                # If the dimensions have changed, reflow the parent and 
                # its dirty children (usual case: no children will be dirty).
                if old_metrics != new_metrics and frame.parent:
                    frame = frame.parent
                else:
                    break

            if frame.parent:
                frame.resolve_bounding_box(
                    frame.parent.bounding_box_left,
                    frame.parent.bounding_box_top)
            else:
                frame.resolve_bounding_box(0, 0) # root frame

        self._pending_reflow.clear()

    def get_canvas_width(self):
        if not self._root_frame:
            return 0
        self.update_flow()
        # By convention with web browsers, don't allow viewport to show left
        # of origin.
        return self._root_frame.bounding_box_right
    canvas_width = property(get_canvas_width)

    def get_canvas_height(self):
        if not self._root_frame:
            return 0
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

        self.update_flow()

        self._root_frame.draw_cull(self.viewport_x, self.viewport_y, 
            self.render_device, 
            self.viewport_x, 
            -self.viewport_y, 
            self.viewport_x + self._viewport_width, 
            -self.viewport_y - self._viewport_height)

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


