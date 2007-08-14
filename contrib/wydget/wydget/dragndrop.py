
from pyglet.window import mouse

import event

def DragHandler(rule, buttons=mouse.LEFT):
    class _DragHandler(object):
        original_position = None
        mouse_buttons = buttons

        @event.select(rule)
        def on_drag(self, widget, x, y, dx, dy, buttons, modifiers):
            if not buttons & self.mouse_buttons:
                return event.EVENT_UNHANDLED
            if self.original_position is None:
                self.original_position = (widget.x, widget.y, widget.z)
                widget.z += 1
            widget.x += dx; widget.y += dy
            return event.EVENT_HANDLED

        @event.select(rule)
        def on_drag_complete(self, widget, x, y, buttons, modifiers, ok):
            if ok:
                widget.z = self.original_position[2]
                self.original_position = None
            else:
                if self.original_position is None: return
                widget.x, widget.y, widget.z = self.original_position
                self.original_position = None
            return event.EVENT_HANDLED
    return _DragHandler()

