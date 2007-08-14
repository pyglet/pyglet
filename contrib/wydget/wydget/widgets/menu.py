import xml.sax.saxutils

from pyglet.gl import *
from pyglet.window import mouse

from wydget import event, layouts, loadxml
from wydget.widgets.frame import Frame
from wydget.widgets.label import Label

class MenuItem(Label):
    name = 'menu-item'

@event.default('menu-item')
def on_element_enter(item, x, y):
    item._save_bgcolor = item.bgcolor
    item.bgcolor = (.9, .9, 1, 1)
    return event.EVENT_HANDLED

@event.default('menu-item')
def on_element_leave(item, x, y):
    item.bgcolor = item._save_bgcolor
    return event.EVENT_HANDLED

@event.default('menu-item')
def on_click(widget, *args):
    menu = widget.parent
    menu.hide()
    return event.EVENT_HANDLED


class PopupMenu(Frame):
    name = 'popup-menu'
    is_focusable = True
    def __init__(self, parent, items, **kw):
        super(PopupMenu, self).__init__(parent, border="black",
            is_visible=False, **kw)

        for n, (label, id) in enumerate(items):
            MenuItem(self, text=label, id=id, is_blended=True,
                bgcolor=((.95, .95, .95, 1), (1, 1, 1, 1))[n%2])

        layouts.Vertical(self).layout()

        iw = self.inner_rect.width
        for element in self.children: element.width = iw

    def expose(self, mouse):
        w = self.getGUI().window
        w, h = w.width, w.height
        self.center = map(int, mouse)
        if self.x < 0: self.x = 0
        if self.y < 0: self.y = 0
        if self.x + self.width > w: self.x = w - self.width
        if self.y + self.height > h: self.y = h - self.height
        self.setVisible(True)
        self.gainFocus()

    def hide(self):
        self.setVisible(False)

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.

        If scrollable then put all children loaded into a container frame.
        '''
        kw = loadxml.parseAttributes(parent, element)
        items = []
        for child in element.getchildren():
            text = xml.sax.saxutils.unescape(child.text)
            items.append((text, child.attrib['id']))
        return cls(parent, items, **kw)

@event.default('popup-menu', 'on_gain_focus')
def on_menu_gain_focus(menu):
    # catch focus
    return event.EVENT_HANDLED

@event.default('popup-menu', 'on_lose_focus')
def on_menu_lose_focus(menu):
    menu.hide()
    return event.EVENT_HANDLED


class DropDownItem(Label):
    name = 'drop-item'

@event.default('drop-item')
def on_element_enter(item, x, y):
    item._save_bgcolor = item.bgcolor
    item.bgcolor = (.9, .9, 1, 1)
    return event.EVENT_HANDLED

@event.default('drop-item')
def on_element_leave(item, x, y):
    item.bgcolor = item._save_bgcolor
    return event.EVENT_HANDLED

@event.default('drop-item')
def on_click(item, *args):
    menu = item.getParent('drop-menu')
    menu.value = item.id
    item.parent.setVisible(False)
    menu.label.setVisible(True)
    return event.EVENT_HANDLED


class DropDownMenu(Frame):
    name = 'drop-menu'

    def __init__(self, parent, items, font_size=None, border="black",
            bgcolor="white", **kw):
        super(DropDownMenu, self).__init__(parent, border=border,
            bgcolor=bgcolor, **kw)

        self.font_size = font_size
        label, value = items[0]
        self.label = Label(self, label, classes=('-drop-down-button',),
            font_size=font_size)

        # set up the popup item
        self.contents = Frame(self, is_visible=False, border="black",
            classes=('-drop-down-menu',))

        # add the menu items and resize the main box if necessary
        width = height = 0
        for n, (label, id) in enumerate(items):
            i = DropDownItem(self.contents, text=label, id=id, is_blended=True,
                bgcolor=((.95, .95, .95, 1), (1, 1, 1, 1))[n%2],
                font_size=font_size)
            if self.width_spec is None:
                width = max(width, i.width)
            if self.height_spec is None:
                height = max(height, i.height)

        self.value = value

        # fix up contents size
        for i in self.contents.children:
            i.width = width
        layouts.Vertical(self.contents).layout()
        if self.width_spec is None:
            self.width = width + self.padding*2
        if self.height_spec is None:
            self.height = height + self.padding*2
        self.label.width = self.inner_rect.width

        # now position the contents
        self.contents.y = self.y - self.contents.height//2 - 1
        self.contents.x = self.width//2 - self.contents.width//2 - 1

        self.dump()

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

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.

        If scrollable then put all children loaded into a container frame.
        '''
        kw = loadxml.parseAttributes(parent, element)
        items = []
        for child in element.getchildren():
            text = xml.sax.saxutils.unescape(child.text)
            items.append((text, child.attrib['id']))
        return cls(parent, items, **kw)

@event.default('.-drop-down-button')
def on_click(widget, x, y, button, modifiers, click_count):
    if not button & mouse.LEFT:
        return event.EVENT_UNHANDLED
    # XXX position contents so the active item is over the label
    widget.parent.contents.setVisible(True)
    widget.setVisible(False)
    widget.parent.contents.gainFocus()
    return event.EVENT_HANDLED

@event.default('.-drop-down-menu')
def on_gain_focus(frame):
    # catch focus
    return event.EVENT_HANDLED

@event.default('.-drop-down-menu')
def on_lose_focus(frame):
    frame.setVisible(False)
    frame.parent.label.setVisible(True)
    return event.EVENT_HANDLED

