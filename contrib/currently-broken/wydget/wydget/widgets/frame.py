from pyglet.gl import *

from wydget import element, event, layouts, util, loadxml
from wydget.widgets.label import Label, Image

class FrameCommon(element.Element):
    need_layout = True
    def setDirty(self):
        super(FrameCommon, self).setDirty()
        self.need_layout = True

    def intrinsic_width(self):
        return self.layout.width + self.padding * 2
    def intrinsic_height(self):
        return self.layout.height + self.padding * 2

    scrollable = False
    def resize(self):
        if not super(FrameCommon, self).resize():
            return False

        if self.scrollable:
            if self.contents.checkForScrollbars():
                raise util.RestartLayout()

        if not self.need_layout:
            return True

        # make sure all the children have dimensions before trying
        # layout
        for c in self.children:
            c.resize()
            if c.height is None or c.width is None:
                return False
        self.layout()
        self.need_layout = False
        return True

    def delete(self):
        self.layout = None
        super(FrameCommon, self).delete()

class Frame(FrameCommon):
    name='frame'
    h_slider = None
    v_slider = None

    def __init__(self, parent, x=None, y=None, z=None, width=None,
            height=None, scrollable=False, scrollable_resize=False, **kw):
        self.layout = layouts.Layout(self)
        self.scrollable = scrollable
        self.scrollable_resize = scrollable_resize
        super(Frame, self).__init__(parent, x, y, z, width, height, **kw)

        if self.scrollable:
            self.contents = ContainerFrame(self, 0, 0, 0, None, None,
                is_transparent=True)
            self.contents.layout = layouts.Layout(self.contents)
            self.contents.setViewClip((0, 0, self.width, self.height))

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
        return obj

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


class ContainerFrame(FrameCommon):
    '''A special transparent frame that is used for frames with fixed size
    and scrolling contents -- this frame holds those contents.
    '''
    name = 'container-frame'

    def intrinsic_width(self):
        return self.layout.width + self.padding * 2
    def intrinsic_height(self):
        return self.layout.height + self.padding * 2

    def checkForScrollbars(self):
        # avoid circular import
        from wydget.widgets.slider import VerticalSlider, HorizontalSlider

        # XXX perhaps this should be on the parent
        h = self.layout.height
        w = self.layout.width

        # check to see whether the parent needs a slider
        p = self.parent
        pr = self.parent.inner_rect

        vc_width, vc_height = pr.width, pr.height

        self.y = vc_height - self.layout.height

        # see what we need
        v_needed = h > vc_height
        if v_needed and not self.parent.scrollable_resize:
            vc_width -= VerticalSlider.slider_size
        h_needed = w > vc_width
        if h_needed and not v_needed:
            v_needed = h > vc_height

        change = False          # slider added or removed

        # add a vertical slider?
        if v_needed:
            r = h - vc_height
            if h_needed and not self.parent.scrollable_resize:
                y = HorizontalSlider.slider_size
                h = vc_height - y
                r += y
            else:
                y = 0
                h = vc_height
            if p.v_slider is not None:
                # XXX update the range more sanely
                p.v_slider.range = r
            else:
                p.v_slider = VerticalSlider(p, 0, r, r, x=vc_width, y=y,
                    height=h, step=16, classes=('-frame-vertical-slider',))
                change = True
        elif p.v_slider is not None:
            p.v_slider.delete()
            p.v_slider = None
            change = True

        # add a horizontal slider?
        if h_needed:
            r = w - vc_width
            if p.h_slider is not None:
                p.h_slider.range = r
            else:
                p.h_slider = HorizontalSlider(p, 0, r, 0, x=0, y=0,
                    width=vc_width, step=16,
                    classes=('-frame-horizontal-slider',))
                change = True
        elif p.h_slider is not None:
            p.h_slider.delete()
            p.h_slider = None
            change = True

        #if change:
            # XXX really do need to do something here to resize contents
        return change

    def resize(self):
        if not super(ContainerFrame, self).resize():
            return False
        if self.parent.width is None:
            return False
        if self.parent.height is None:
            return False
        self.updateViewClip()
        return True

    def updateViewClip(self):
        p = self.parent
        pr = p.inner_rect
        vc_width, vc_height = pr.width, pr.height
        h_height = 0
        if p.v_slider and not self.parent.scrollable_resize:
            vc_width -= p.v_slider.width
        if p.h_slider and not self.parent.scrollable_resize:
            h_height = p.h_slider.height
            vc_height -= h_height
        self.setViewClip((-self.x, -self.y + h_height, vc_width, vc_height))

    def setY(self, value):
        self.y = -value
        p = self.parent
        if p.h_slider and not self.parent.scrollable_resize:
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

    def resize(self):
        if self.scrollable:
            self.width = self.parent.width
            self.height = self.parent.height
        return super(TabFrame, self).resize()

    def delete(self):
        self._button = None
        super(TabFrame, self).delete()


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
        self.layout = layouts.Horizontal(self, padding=2, halign=halign,
            valign=valign)

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

    def getChildren(self):
        '''Don't use scrollable tabs for sizing.
        '''
        return [c for c in super(TabsLayout, self).getChildren()
            if not c.scrollable]

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
        self.layout = layouts.Vertical(self, valign='bottom', padding=0)
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
        b._top = self

        if scrollable:
            f = self.frame_class(self.bottom, scrollable=True, x=0, y=0,
                border=border, bgcolor=bgcolor, padding=2,
                height='100%', width='100%')
            r = f.contents
        else:
            r = f = self.frame_class(self.bottom, border=border, x=0, y=0,
                bgcolor=bgcolor, padding=2, height='100%', width='100%')
        b._frame = f
        f._button = b
        if self._active_frame is None:
            self._active_frame = f
        else:
            f.setVisible(False)
        return r

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
        return obj


@event.default('tab-button', 'on_click')
def on_tab_click(widget, *args):
    widget.getParent('tabbed-frame').activate(widget._frame)
    return event.EVENT_HANDLED

