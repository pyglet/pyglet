from pyglet.gl import *

from wydget import element, event, layouts, util, loadxml
from wydget.widgets.slider import VerticalSlider, HorizontalSlider
from wydget.widgets.label import Label, Image

class Frame(element.Element):
    name='frame'
    layout = None
    h_slider = None
    v_slider = None

    def __init__(self, parent, x=0, y=0, z=0, width=None, height=None,
            scrollable=False, **kw):

        self.scrollable = scrollable

        super(Frame, self).__init__(parent, x, y, z, width, height, **kw)

        if self.scrollable:
            contents = self.contents = ContainerFrame(self)
            contents.layout = layouts.Layout(contents)
            contents.setViewClip((0, 0, self.width, self.height))
        else:
            self.layout = layouts.Layout(self)

    def layoutDimensionsChanged(self, layout):
        # If our width / height weren't specified then adjust size to fit
        # contents.
        if self.width_spec is None:
            self.width = layout.width + self.padding*2
            if self.v_slider: self.width += self.v_slider.width
        if self.height_spec is None:
            self.height = layout.height + self.padding*2
            if self.h_slider: self.height += self.h_slider.height

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.

        If scrollable then put all children loaded into a container frame.
        '''
        kw = loadxml.parseAttributes(parent, element)
        obj = cls(parent, **kw)
        for child in element.getchildren():
            if obj.scrollable:
                loadxml.getConstructor(child.tag)(child, obj.contents)
            else:
                loadxml.getConstructor(child.tag)(child, obj)
        if obj.scrollable:
            obj.contents.layout.layout()
        else:
            obj.layout.layout()
        return obj


@event.default('frame')
def on_mouse_scroll(widget, x, y, dx, dy):
    if widget.scrollable:
        if widget.v_slider is not None:
            # XXX is this really setting the correct value?!?
            widget.v_slider.setCurrent(widget.v_slider.current + dy)
        if widget.h_slider is not None:
            widget.h_slider.setCurrent(widget.h_slider.current + dx)
        return event.EVENT_HANDLED
    return event.EVENT_UNHANDLED


class ContainerFrame(element.Element):
    '''A special transparent frame that is used for frames with fixed size
    and scrolling contents -- this frame holds those contents.
    '''
    name = 'container-frame'

    def __init__(self, parent, padding=0, is_transparent=True, **kw):
        super(ContainerFrame, self).__init__(parent, 0, 0, 0, None, None,
            padding=padding, is_transparent=is_transparent, **kw)
        self.checkForScrollbars()

    def layoutDimensionsChanged(self, layout):
        # If our width / height weren't specified then adjust size to fit
        # contents.
        if self.width_spec is None:
            self.width = layout.width + self.padding*2
            changed = True
        if self.height_spec is None:
            self.height = layout.height + self.padding*2
            changed = True

        # pass on the resize to parent
        # XXX perhaps the scrollbars handling should be in here...
        self.parent.layoutDimensionsChanged(self)
        self.checkForScrollbars()


    def checkForScrollbars(self):
        # XXX perhaps this should be on the parent
        h = self.height
        w = self.width

        # check to see whether the parent needs a slider
        p = self.parent
        pr = self.parent.inner_rect

        vc_width, vc_height = pr.width, pr.height

        yoffset = 0
        self.y = 0
        if h > vc_height:
            if p.v_slider is not None:
                p.v_slider.delete()
            r = h - vc_height
            vc_width -= VerticalSlider.slider_size
            if w > vc_width:
                yoffset = HorizontalSlider.slider_size
                h = vc_height - yoffset
                r += yoffset
            else:
                h = vc_height
            self.y = -r
            p.v_slider = VerticalSlider(p, 0, r, r, x=vc_width, y=yoffset,
                height=h, classes=('-frame-vertical-slider',))
        elif p.v_slider is not None:
            p.v_slider.delete()
            p.v_slider = None

        if w > vc_width:
            if p.h_slider is not None:
                p.h_slider.delete()
            r = w - vc_width
            yoffset = HorizontalSlider.slider_size
            self.y += yoffset
            vc_height -= yoffset
            p.h_slider = HorizontalSlider(p, 0, r, 0, width=vc_width,
                classes=('-frame-horizontal-slider',))
        elif p.h_slider is not None:
            p.h_slider.delete()
            p.h_slider = None

        self.setViewClip((0, -self.y + yoffset, vc_width, vc_height))

    def setY(self, value):
        self.y = -value
        p = self.parent
        pr = p.inner_rect
        vc_width, vc_height = pr.width, pr.height
        h_height = 0
        if p.v_slider:
            vc_width -= p.v_slider.width
        if p.h_slider:
            h_height = p.h_slider.height
            vc_height -= h_height
            self.y += h_height
        self.setViewClip((-self.x, -self.y + h_height, vc_width, vc_height))

    def setX(self, value):
        self.x = -value
        p = self.parent
        pr = p.inner_rect
        vc_width, vc_height = pr.width, pr.height
        h_height = 0
        if p.v_slider:
            vc_width -= p.v_slider.width
        if p.h_slider:
            h_height = p.h_slider.height
            vc_height -= h_height
        self.setViewClip((-self.x, -self.y + h_height, vc_width, vc_height))


@event.default('.-frame-vertical-slider')
def on_change(widget, value):
    widget.parent.contents.setY(int(value))
    return event.EVENT_HANDLED

@event.default('.-frame-horizontal-slider')
def on_change(widget, value):
    widget.parent.contents.setX(int(value))
    return event.EVENT_HANDLED


class TabFrame(Frame):
    '''Special frame for inside a TabbedFrame that renders its border so
    it appears merged with the button. Also performs more cleanup on delete().
    '''
    name = 'tab-frame'
    def renderBorder(self, rect, clipped):
        if self.border is None: return

        glColor4f(*self.border)

        # XXX handle clippped
        x2, y2 = rect.topright
        butx1 = self._button.x
        butx2 = self._button.x + self._button.width

        glBegin(GL_LINE_STRIP)
        glVertex2f(butx1, y2)
        if butx1 != rect.x: glVertex2f(rect.x, y2)
        glVertex2f(rect.x, rect.y)
        glVertex2f(x2, rect.y)
        glVertex2f(x2, y2)
        if butx2 != x2: glVertex2f(butx2, y2)
        glEnd()

    def delete(self):
        self._button = None
        super(Frame, self).delete()


class TabButton(Frame):
    '''Special button for inside a TabbedFrame that renders its border so
    it appears merged with the tab. Also performs more cleanup on delete().
    '''
    name = 'tab-button'
    is_focusable = False

    def __init__(self, parent, text=None, image=None, border="black",
            padding=1, halign="left", valign="bottom", **kw):
        super(TabButton, self).__init__(parent, border=border,
            padding=padding, **kw)

        if text is None and image is None:
            raise ValueError, 'text or image required'

        if image is not None: Image(self, image)
        if text is not None: Label(self, text)
        layouts.Horizontal(self, padding=2, halign=halign,
            valign=valign).layout()

    def renderBorder(self, rect, clipped):
        if self.border is None: return
        # XXX handle clippped
        glColor4f(*self.border)
        x2, y2 = rect.topright
        glBegin(GL_LINE_STRIP)
        glVertex2f(rect.x, rect.y)
        glVertex2f(rect.x, y2-1)
        glVertex2f(x2-1, y2-1)
        glVertex2f(x2-1, rect.y)
        glEnd()

    def delete(self):
        self._frame = None
        self._top = None
        super(Frame, self).delete()


class TabbedFrame(Frame):
    '''A collection of frames, one active at a time.

    Container frames must be created using the newTab method. It in turn
    uses the button_class and frame_class attributes to create the tabs.
    '''
    name = 'tabbed-frame'
    button_class = TabButton
    frame_class = TabFrame

    def __init__(self, parent, is_transparent=True, halign='left', **kw):
        super(TabbedFrame, self).__init__(parent,
            is_transparent=is_transparent, **kw)

        self.halign = halign

        self.top = Frame(self, width="100%", is_transparent=True)
        self.bottom = Frame(self, width="100%", is_transparent=True)

    def get_active(self):
        return self._active_frame._button
    active = property(get_active)

    default = []
    def newTab(self, text=None, image=None, border=default,
            bgcolor=default, scrollable=False, **kw):
        if border is self.default: border = self.border
        if bgcolor is self.default: bgcolor = self.bgcolor
        b = self.button_class(self.top, text=text, image=image,
            border=border, bgcolor=bgcolor, **kw)

        # this will resize the height of the top frame if necessary
        b._top = self
        layouts.Horizontal(self.top, halign=self.halign, padding=2).layout()

        # XXX need a signal or something?
        self.bottom.height = self.bottom.height_spec = self.top.y = self.height-self.top.height

        vis = not self.bottom.children
        if scrollable:
            f = self.frame_class(self.bottom, scrollable=True,
                is_visible=vis, border=border, bgcolor=bgcolor, padding=2)
        else:
            f = self.frame_class(self.bottom, width="100%", height="100%",
                is_visible=vis, border=border, bgcolor=bgcolor, padding=2)
        b._frame = f
        f._button = b
        if vis: self._active_frame = f
        return f

@event.default('tab-button', 'on_click')
def on_tab_click(widget, *args):
    widget._top._active_frame.setVisible(False)
    widget._top._active_frame.setEnabled(False)
    widget._top._active_frame = widget._frame
    widget._frame.setVisible(True)
    widget._frame.setEnabled(True)
    return event.EVENT_HANDLED


