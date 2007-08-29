from pyglet.gl import *
from pyglet import clock
from pyglet.window import key, mouse

from wydget import element, event, util, anim, data

class Checkbox(element.Element):
    name='checkbox'
    is_focusable = True

    def __init__(self, parent, value=False,
            x=0, y=0, z=0, width=None, height=None, **kw):
        self.parent = parent
        self.value = value

        self.width_spec = width
        self.height_spec = height

        # XXX this is somewhat common (see FrameCommon, and other elements probably need to do this stuff too)
        # now calculate them if necessary
        ir = parent.inner_rect
        iw, ih = ir.width, ir.height
        width = util.parse_value(width, iw)
        if width is None: width = 16
        height = util.parse_value(height, ih)
        if height is None: height = 16

        super(Checkbox, self).__init__(parent, x, y, z, width, height, **kw)

    def render(self, rect):
        # XXX handle rect (and use images...)
        glPushAttrib(GL_CURRENT_BIT)
        glColor4f(.85, .85, .85, 1)

        w, h = 16, 16
        glRectf(1, 1, w, h)
        if self.value:
            glColor4f(0, 0, 0, 1)
            w8, h8 = w//8, h//8
            glBegin(GL_LINE_STRIP)
            glVertex2f(1+w8, 1+4*h8)
            glVertex2f(1+3*w8, 1+h8)
            glVertex2f(1+7*w8, 1+7*h8)
            glEnd()
        glPopAttrib()

@event.default('checkbox')
def on_click(widget, *args):
    widget.value = not widget.value
    return event.EVENT_UNHANDLED

@event.default('checkbox')
def on_text(self, text):
    if text in (' \r'):
        self.getGUI().dispatch_event(self, 'on_click', 0, 0, mouse.LEFT, 0, 1)
        return event.EVENT_HANDLED
    return event.EVENT_UNHANDLED

