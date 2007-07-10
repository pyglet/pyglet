import xml.sax.saxutils

from pyglet.gl import *

from wydget import element, event, layouts, loadxml, util
from wydget.widgets.frame import Frame
from wydget.widgets.button import TextButton, Button

class Selection(Frame):
    name = 'selection'

    def __init__(self, parent, size=None, is_exclusive=False,
            color=(0, 0, 0, 1), bgcolor=(1, 1, 1, 1), is_vertical=True,
            alt_bgcolor=(.9, .9, .9, 1), active_bgcolor=(1, .8, .8, 1),
            font_size=None, **kw):
        self.is_vertical = is_vertical
        self.is_exclusive = is_exclusive

        if font_size is None:
            font_size = parent.getStyle().font_size
        else:
            font_size = util.parse_value(font_size, None)

        if is_vertical:
            if size is not None:
                kw['height'] = size * font_size
        else:
            # XXX size really doesn't make sense...
            if size is not None:
                kw['width'] = size * font_size
            kw['height'] = font_size + 16   # XXX slider size

        kw['scrollable'] = True
        kw['is_transparent'] = True

        super(Selection, self).__init__(parent, bgcolor=bgcolor, **kw)
        if is_vertical:
            self.contents.layout = layouts.Vertical(self.contents, valign='top')
        else:
            self.contents.layout = layouts.Horizontal(self.contents,
                valign='top', halign='left')

        # specific attributes for Options
        self.color = util.parse_color(color)
        self.base_bgcolor = self.bgcolor
        self.alt_bgcolor = util.parse_color(alt_bgcolor)
        self.active_bgcolor = util.parse_color(active_bgcolor)
        self.font_size = font_size

    def clearOptions(self):
        self.contents.clear()

    def addOption(self, label, id=None):
        o = Option(self.contents, text=label, id=id or label)
        self.contents.layout.layout()

    def get_value(self):
        return [c.id for c in self.contents.children if c.is_active]
    value = property(get_value)

    @event.default('selection')
    def on_mouse_scroll(widget, x, y, dx, dy):
        if widget.scrollable:
            if widget.v_slider is not None:
                # XXX is this really setting the correct value?!?
                widget.v_slider.setCurrent(widget.v_slider.current + dy)
            if widget.h_slider is not None:
                widget.h_slider.setCurrent(widget.h_slider.current + dx)
            return event.EVENT_HANDLED
        return event.EVENT_UNHANDLED

class Option(TextButton):
    name = 'option'

    def __init__(self, parent, border=None, color=None, bgcolor=None,
            active_bgcolor=None, font_size=None, is_active=False,
            id=None, **kw):
        self.is_active = is_active
        assert 'text' in kw, 'text required for Option'

        # default styling and width to parent settings
        select = parent.parent
        if color is None:
            color = select.color
        if bgcolor is None:
            n = len(parent.children)
            bgcolor = (select.bgcolor, select.alt_bgcolor)[n%2]
        if active_bgcolor is None:
            self.active_bgcolor = select.active_bgcolor
        else:
            self.active_bgcolor = util.parse_color(active_bgcolor)
        if select.is_vertical and select.width_spec is not None:
            kw['width'] = select.inner_rect.width
        if font_size is None: font_size = select.font_size
        if id is None: id = kw['text']

        kw['height'] = font_size
        super(Option, self).__init__(parent, border=border, bgcolor=bgcolor,
            font_size=font_size, id=id, **kw)

        # fix up widths
        if select.is_vertical:
            width = max(c.width for c in parent.children)
            for c in parent.children: c.width = width

    def setText(self, text):
        return super(Option, self).setText(text, additional=('active', ))

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.
        '''
        kw = loadxml.parseAttributes(parent, element)
        kw['text'] = xml.sax.saxutils.unescape(element.text)
        obj = cls(parent, **kw)
        for child in element.getchildren():
            loadxml.getConstructor(element.tag)(child, obj)
        return obj

    def render(self, rect):
        '''Select the correct image to render.
        '''
        if self.is_active and self.active_bgcolor:
            self.bgcolor = self.active_bgcolor
            self.image = self.active_image
        else:
            self.image = self.base_image
            self.bgcolor = self.base_bgcolor
        super(Button, self).render(rect)

@event.default('option')
def on_click(widget, *args):
    # XXX exclusive mode
    widget.is_active = not widget.is_active
    select = widget.parent.parent
    if widget.is_active and select.is_exclusive:
        for child in select.contents.children:
            if child is not widget:
                child.is_active = None
    widget.getGUI().dispatch_event(select, 'on_change', select.value)
    return event.EVENT_UNHANDLED

'''
XXX focus and keyboard interaction
@event.default('option')
def on_gain_focus(widget):
    widget.is_over = True
    # let the event propogate to any parent
    return event.EVENT_UNHANDLED

@event.default('option')
def on_lose_focus(widget):
    widget.is_over = False
    # let the event propogate to any parent
    return event.EVENT_UNHANDLED
'''
