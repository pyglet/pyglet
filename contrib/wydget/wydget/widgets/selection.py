import xml.sax.saxutils

from pyglet.gl import *

from wydget import element, event, layouts, loadxml, util
from wydget.widgets.frame import Frame
from wydget.widgets.button import TextButton, Button

class Selection(Frame):
    name = 'selection'

    def __init__(self, parent, size=None, is_exclusive=False,
            color='black', bgcolor='white', is_vertical=True,
            alt_bgcolor='ccc', active_bgcolor='ffc',
            is_transparent=True, scrollable=True, font_size=None, **kw):
        self.is_vertical = is_vertical
        self.is_exclusive = is_exclusive

        if font_size is None:
            font_size = parent.getStyle().font_size
        else:
            font_size = util.parse_value(font_size, None)

        size = util.parse_value(size, None)

        if is_vertical:
            if size is not None:
                kw['height'] = size * font_size
        else:
            if size is not None:
                kw['width'] = size * font_size

        super(Selection, self).__init__(parent, bgcolor=bgcolor,
            scrollable=scrollable, is_transparent=is_transparent, **kw)
        if scrollable: f = self.contents
        else: f = self
        if is_vertical:
            f.layout = layouts.Vertical(f, valign='top', halign='center')
        else:
            f.layout = layouts.Horizontal(f, valign='top', halign='left')

        # specific attributes for Options
        self.color = util.parse_color(color)
        self.base_bgcolor = self.bgcolor
        self.alt_bgcolor = util.parse_color(alt_bgcolor)
        self.active_bgcolor = util.parse_color(active_bgcolor)
        self.font_size = font_size

    def clearOptions(self):
        if self.scrollable: self.contents.clear()
        else: self.clear()

    def addOption(self, label, id=None, **kw):
        if self.scrollable: f = self.contents
        else: f = self
        o = Option(f, text=label, id=id or label, **kw)
        f.layout.layout()

    def get_value(self):
        if self.scrollable: f = self.contents
        else: f = self
        return [c.id for c in f.children if c.is_active]
    value = property(get_value)

    @event.default('selection')
    def on_mouse_scroll(widget, x, y, dx, dy):
        if not widget.scrollable:
            return event.EVENT_UNHANDLED
        # XXX this needs revisiting
        if widget.v_slider is not None:
            widget.v_slider.bar.moveY(dy)
        if widget.h_slider is not None:
            widget.h_slider.bar.moveX(dx)
        return event.EVENT_HANDLED


class Option(TextButton):
    name = 'option'

    def __init__(self, parent, border=None, color=None, bgcolor=None,
            active_bgcolor=None, font_size=None, is_active=False,
            alt_bgcolor=None, id=None, **kw):
        self.is_active = is_active
        assert 'text' in kw, 'text required for Option'

        # default styling and width to parent settings
        select = parent.getParent('selection')
        if color is None:
            color = select.color

        if bgcolor is None:
            self.bgcolor = select.bgcolor
        else:
            self.bgcolor = util.parse_color(bgcolor)
        if alt_bgcolor is None:
            self.alt_bgcolor = select.alt_bgcolor
        else:
            self.alt_bgcolor = util.parse_color(alt_bgcolor)
        if active_bgcolor is None:
            self.active_bgcolor = select.active_bgcolor
        else:
            self.active_bgcolor = util.parse_color(active_bgcolor)

        if self.alt_bgcolor:
            n = len(parent.children)
            bgcolor = (self.bgcolor, self.alt_bgcolor)[n%2]

        if select.is_vertical and select.width_spec is not None:
            kw['width'] = select.inner_rect.width
        if font_size is None: font_size = select.font_size
        if id is None: id = kw['text']

        #kw['height'] = font_size
        super(Option, self).__init__(parent, border=border, bgcolor=bgcolor,
            font_size=font_size, color=color, id=id, **kw)

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
    widget.is_active = not widget.is_active
    select = widget.getParent('selection')
    if select.scrollable: f = select.contents
    else: f = select
    if widget.is_active and select.is_exclusive:
        for child in f.children:
            if child is not widget:
                child.is_active = None
    widget.getGUI().dispatch_event(select, 'on_change', select.value)
    return event.EVENT_HANDLED

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
