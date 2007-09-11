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

    def parentDimensionsChanged(self):
        ir = self.parent.inner_rect

        # recalulate position
        new_x = util.parse_value(self.x_spec, ir.width)
        if new_x != self._x: self.x = new_x
        new_y = util.parse_value(self.y_spec, ir.height)
        if new_y != self._y: self.y = new_y
        new_z = util.parse_value(self.z_spec)
        if new_z != self._z: self.z = new_z

        # recalulate width / height
        # BUT unlike basic elements, do NOT default to filling parent
        # dimensions
        change = False
        if self.width_spec is not None:
            new_width = util.parse_value(self.width_spec, ir.width)
            if new_width != self._width:
                self.width = new_width
                change = True
        if self.height_spec is not None:
            new_height = util.parse_value(self.height_spec, ir.height)
            if new_height != self._height:
                self.height = new_height
                change = True

        if change:
            for child in self.children:
                child.parentDimensionsChanged()

        if self.scrollable:
            self.contents.layout()
        else:
            self.layout()

    def layoutDimensionsChanged(self, layout):
        # If our width / height weren't specified then adjust size to fit
        # contents.
        if self.width_spec is None:
            self.width = layout.width + self.padding*2
            if self.v_slider:
                self.width += self.v_slider.width
        if self.height_spec is None:
            self.height = layout.height + self.padding*2
            if self.h_slider:
                self.height += self.h_slider.height

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.

        If scrollable then put all children loaded into a container frame.
        '''
        kw = loadxml.parseAttributes(element)
        obj = cls(parent, **kw)
        for child in element.getchildren():
            if obj.scrollable:
                loadxml.getConstructor(child.tag)(child, obj.contents)
            else:
                loadxml.getConstructor(child.tag)(child, obj)
        if obj.scrollable:
            obj.contents.layout()
        else:
            obj.layout()
        return obj

    def delete(self):
        self.layout = None
        super(Frame, self).delete()

@event.default('frame')
def on_mouse_scroll(widget, x, y, dx, dy):
    if widget.scrollable:
        if dy and widget.v_slider is not None:
            slider = widget.v_slider
            slider.set_value(slider.value + dy * slider.step, event=True)
        if dx and widget.h_slider is not None:
            slider = widget.h_slider
            slider.set_value(slider.value + dx * slider.step, event=True)
        elif dy and widget.v_slider is None and widget.h_slider is not None:
            slider = widget.h_slider
            slider.set_value(slider.value + dy * slider.step, event=True)
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

    def parentDimensionsChanged(self):
        '''We're a scrolled frame - don't change position.
        '''
        ir = self.parent.inner_rect
        # recalulate width / height
        change = False
        if self.width_spec is not None:
            new_width = util.parse_value(self.width_spec, ir.width)
            if new_width != self._width:
                self.width = new_width
                change = True
        if self.height_spec is not None:
            new_height = util.parse_value(self.height_spec, ir.height)
            if new_height != self._height:
                self.height = new_height
                change = True

        if change:
            for child in self.children:
                child.parentDimensionsChanged()

    def checkForScrollbars(self):
        # XXX perhaps this should be on the parent
        h = self.height
        w = self.width

        # check to see whether the parent needs a slider
        p = self.parent
        pr = self.parent.inner_rect

        vc_width, vc_height = pr.width, pr.height

        self.y = vc_height - self.height

        change = False          # slider added or removed

        # add a vertical slider?
        if h > vc_height:
            if p.v_slider is not None:
                p.v_slider.delete()
            r = h - vc_height
            vc_width -= VerticalSlider.slider_size
            if w > vc_width:
                y = HorizontalSlider.slider_size
                h = vc_height - y
                r += y
            else:
                y = 0
                h = vc_height
            p.v_slider = VerticalSlider(p, 0, r, r, x=vc_width, y=y,
                height=h, step=16, classes=('-frame-vertical-slider',))
            change = True
        elif p.v_slider is not None:
            p.v_slider.delete()
            p.v_slider = None
            change = True

        # add a horizontal slider?
        if w > vc_width:
            if p.h_slider is not None:
                p.h_slider.delete()
            r = w - vc_width
            p.h_slider = HorizontalSlider(p, 0, r, 0, width=vc_width,
                step=16, classes=('-frame-horizontal-slider',))
            change = True
        elif p.h_slider is not None:
            p.h_slider.delete()
            p.h_slider = None
            change = True

        self.updateViewClip()

        if change:
            self.parentDimensionsChanged()

    def updateViewClip(self):
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

    def setY(self, value):
        self.y = -value
        p = self.parent
        if p.h_slider:
            self.y += p.h_slider.height
        self.updateViewClip()

    def setX(self, value):
        self.x = -value
        self.updateViewClip()


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
    def renderBorder(self, clipped):
        if self.border is None: return

        glColor4f(*self.border)

        # XXX handle clippped better
        x2, y2 = clipped.topright
        butx1 = self._button.x
        butx2 = self._button.x + self._button.width

        glBegin(GL_LINE_STRIP)
        glVertex2f(butx1, y2)
        if butx1 != clipped.x: glVertex2f(clipped.x, y2)
        glVertex2f(clipped.x, clipped.y)
        glVertex2f(x2, clipped.y)
        glVertex2f(x2, y2)
        if butx2 != x2: glVertex2f(butx2, y2)
        if self.bgcolor is not None:
            glColor4f(*self.bgcolor)
            glVertex2f(butx2-1, y2)
            glVertex2f(butx1+1, y2)
        glEnd()

    def delete(self):
        self._button = None
        super(TabFrame, self).delete()

    def layoutDimensionsChanged(self, layout):
        '''Let the tabs container know that this frame has changed size.
        '''
        super(TabFrame, self).layoutDimensionsChanged(layout)
        self.parent.layout()

class TabButton(Frame):
    '''Special button for inside a TabbedFrame that renders its border so
    it appears merged with the tab. Also performs more cleanup on delete().
    '''
    name = 'tab-button'
    is_focusable = False

    def __init__(self, parent, text=None, image=None, border="black",
            padding=1, halign="left", valign="bottom", font_size=None,
            **kw):
        super(TabButton, self).__init__(parent, border=border,
            padding=padding, **kw)

        if text is None and image is None:
            raise ValueError, 'text or image required'

        if image is not None: Image(self, image)
        if text is not None: Label(self, text, font_size=font_size)
        layouts.Horizontal(self, padding=2, halign=halign,
            valign=valign).layout()

    def renderBorder(self, clipped):
        '''Render the border in relative coordinates clipped to the
        indicated view.
        '''
        if self.border is None: return
        ox, oy = 0, 0
        ox2, oy2 = self.width, self.height
        cx, cy = clipped.bottomleft
        cx2, cy2 = clipped.topright

        glColor4f(*self.border)
        glBegin(GL_LINES)
        # left
        if ox == cx:
            glVertex2f(ox, cy)
            glVertex2f(ox, cy2)
        # right
        if ox2 == cx2:
            glVertex2f(ox2-1, cy)
            glVertex2f(ox2-1, cy2)
        # top
        if oy2 == cy2:
            glVertex2f(cx, oy2-1)
            glVertex2f(cx2, oy2-1)

        glEnd()

    def delete(self):
        self._frame = None
        self._top = None
        super(TabButton, self).delete()

class TabsLayout(layouts.Layout):
    '''A special layout that overlaps TabFrames.
    '''
    name = 'tabs-layout'

    def layout(self):
        for child in self.parent.children:
            child.width = self.width
            child.height = self.height
        self.parent.layoutDimensionsChanged(self)
        self.parent.parent.layout()

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

        self.top = Frame(self, is_transparent=True)
        self.top.layout = layouts.Horizontal(self.top, halign=self.halign,
            padding=2)
        self.bottom = Frame(self, is_transparent=True)
        self.bottom.layout = TabsLayout(self.bottom)
        self.layout = layouts.Vertical(self)
        self._active_frame = None

    def get_active(self):
        return self._active_frame._button
    active = property(get_active)

    default = []
    def newTab(self, text=None, image=None, border=default,
            bgcolor=default, scrollable=False, font_size=None, **kw):
        if border is self.default: border = self.border
        if bgcolor is self.default: bgcolor = self.bgcolor

        # this will resize the height of the top frame if necessary
        b = self.button_class(self.top, text=text, image=image,
            border=border, bgcolor=bgcolor, font_size=font_size, **kw)
        self.top.layout()
        b._top = self

        if scrollable:
            f = self.frame_class(self.bottom, scrollable=True,
                border=border, bgcolor=bgcolor, padding=2)
        else:
            f = self.frame_class(self.bottom, border=border,
                bgcolor=bgcolor, padding=2)
        b._frame = f
        f._button = b
        if self._active_frame is None:
            self._active_frame = f
        else:
            f.setVisible(False)
        return f

    def activate(self, tab):
        self._active_frame.setVisible(False)
        self._active_frame.setEnabled(False)
        self._active_frame = tab
        tab.setVisible(True)
        tab.setEnabled(True)

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.

        Create tabs for <tab> child tags.
        '''
        kw = loadxml.parseAttributes(element)
        obj = cls(parent, **kw)
        for child in element.getchildren():
            assert child.tag == 'tab'
            kw = loadxml.parseAttributes(child)
            label = kw.pop('label')
            tab = obj.newTab(label, **kw)
            for content in child.getchildren():
                loadxml.getConstructor(content.tag)(content, tab)
            tab.layout()
        obj.layout()
        return obj


@event.default('tab-button', 'on_click')
def on_tab_click(widget, *args):
    widget.getParent('tabbed-frame').activate(widget._frame)
    return event.EVENT_HANDLED

