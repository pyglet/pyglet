import xml.sax.saxutils

from pyglet.window import mouse
from pyglet.gl import *

from wydget import element, event, layouts, loadxml, util, data
from wydget.widgets.frame import Frame
from wydget.widgets.button import TextButton, Button
from wydget.widgets.label import Label, Image

class Selection(Frame):
    name = 'selection'

    def __init__(self, parent, items=[], size=None, is_exclusive=False,
            color='black', bgcolor='white', is_vertical=True,
            alt_bgcolor='ccc', active_bgcolor='ffc', item_pad=0,
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
            f.layout = layouts.Vertical(f, valign='top', padding=item_pad,
                halign='center')
        else:
            f.layout = layouts.Horizontal(f, valign='top',
                padding=item_pad, halign='left')

        # specific attributes for Options
        self.color = util.parse_color(color)
        self.base_bgcolor = self.bgcolor
        self.alt_bgcolor = util.parse_color(alt_bgcolor)
        self.active_bgcolor = util.parse_color(active_bgcolor)
        self.font_size = font_size

        for label, id, kw in items:
            self.addOption(label, id, **kw)

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.
        '''
        kw = loadxml.parseAttributes(element)

        items = []
        for child in element.getchildren():
            assert child.tag == 'option'
            text = xml.sax.saxutils.unescape(child.text)
            childkw = loadxml.parseAttributes(child)
            items.append((text, child.attrib.get('id'), childkw))

        size = int(kw.pop('size', 0))
        if size == 1:
            obj = SelectionBar(parent, items, **kw)
        else:
            obj = Selection(parent, items, size=size, **kw)
        return obj

    def clearOptions(self):
        if self.scrollable: self.contents.clear()
        else: self.clear()

    def addOption(self, label, id=None, **kw):
        if self.scrollable: f = self.contents
        else: f = self
        o = Option(f, text=label, id=id or label, **kw)
        f.layout()

    def get_value(self):
        if self.scrollable: f = self.contents
        else: f = self
        return [c.id for c in f.children if c.is_active]
    value = property(get_value)

    @event.default('selection')
    def on_mouse_scroll(widget, x, y, dx, dy):
        if not widget.scrollable:
            return event.EVENT_UNHANDLED
        if widget.v_slider is not None:
            widget.v_slider.stepToMaximum(dy)
        if widget.h_slider is not None:
            widget.h_slider.stepToMaximum(dx)
        return event.EVENT_HANDLED


class SelectionBar(Frame):
    name = 'selection-bar'

    is_vertical = True
    def __init__(self, parent, items, font_size=None, border="black",
            color='black', bgcolor='white', 
            alt_bgcolor='ccc', active_bgcolor='ffc', item_pad=0,
            **kw):
        super(SelectionBar, self).__init__(parent, border=border,
            bgcolor=bgcolor, **kw)
        self.layout = layouts.Horizontal(self, valign='center',
            only_visible=True)

        # specific attributes for Options
        self.color = util.parse_color(color)
        self.base_bgcolor = self.bgcolor
        self.alt_bgcolor = util.parse_color(alt_bgcolor)
        self.active_bgcolor = util.parse_color(active_bgcolor)
        self.font_size = font_size

        self.label = Label(self, items[0][0], font_size=font_size,
            color=color)

        Image(self, self.arrow, color=(0, 0, 0, 1))

        # set up the popup item - try to make it appear in front
        self.contents = Frame(self, is_visible=False, border="black", z=.5)
        self.contents.layout = layouts.Vertical(self.contents)

        # add the menu items and resize the main box if necessary
        width = height = 0
        for n, (label, id, kw) in enumerate(items):
            i = Option(self.contents, text=label, id=id, **kw)
            width = max(width, i.width)
            height = max(height, i.height)

        self.value = self.contents.children[0].id

        # fix up contents size
        for i in self.contents.children:
            i.width = width
        self.contents.layout()

        # fix label width so it fits largest selection
        self.label.width = width + self.padding*2
        self.label.height = height + self.padding*2
        self.layout()

        # reposition so the selection drops down over first item
        r = self.contents.rect
        r.top = self.inner_rect.top
        self.contents.y = r.y

    @classmethod
    def get_arrow(cls):
        if not hasattr(cls, 'image_object'):
            cls.image_object = data.load_gui_image('slider-arrow-down.png')
        return cls.image_object
    def _get_arrow(self): return self.get_arrow()
    arrow = property(_get_arrow)

    def get_value(self):
        return self._value

    def set_value(self, value):
        for item in self.contents.children:
            if item.id == value: break
        else:
            raise ValueError, '%r not a valid child item id'%(value,)
        self.label.setText(item.text)
        self.label.width = self.inner_rect.width
        self._value = value
    value = property(get_value, set_value)

    def addOption(self, label, id=None, **kw):
        Option(self.contents, text=label, id=id or label, **kw)
        self.contents.layout()

    @event.default('selection-bar')
    def on_click(widget, x, y, button, modifiers, click_count):
        if not button & mouse.LEFT:
            return event.EVENT_UNHANDLED
        # XXX position contents so the active item is over the label
        contents = widget.contents
        if contents.is_visible:
            contents.setVisible(False)
            contents.loseFocus()
        else:
            contents.setVisible(True)
            contents.gainFocus()
        return event.EVENT_HANDLED

    @event.default('selection-bar', 'on_gain_focus')
    def on_gain_focus(widget):
        # catch focus
        return event.EVENT_HANDLED

    @event.default('selection-bar', 'on_lose_focus')
    def on_lose_focus(widget):
        widget.contents.setVisible(False)
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
        if select is None:
            select = parent.getParent('selection-bar')
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
        kw = loadxml.parseAttributes(element)
        kw['text'] = xml.sax.saxutils.unescape(element.text)
        obj = cls(parent, **kw)
        for child in element.getchildren():
            loadxml.getConstructor(element.tag)(child, obj)
        return obj

    def renderBackground(self, clipped):
        '''Select the correct image to render.
        '''
        if self.is_active and self.active_bgcolor:
            self.bgcolor = self.active_bgcolor
        else:
            self.bgcolor = self.base_bgcolor
        super(TextButton, self).renderBackground(clipped)

@event.default('selection-bar option')
def on_click(widget, *args):
    select = widget.getParent('selection-bar')
    select.value = widget.id
    select.contents.setVisible(False)
    select.contents.loseFocus()
    widget.getGUI().dispatch_event(select, 'on_change', select.value)
    return event.EVENT_HANDLED

@event.default('selection option')
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

