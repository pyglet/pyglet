import sys
import xml.sax.saxutils

from pyglet.gl import *
from pyglet.window import mouse, key

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
    '''A menu that should appear under the mouse when activated.

    The static method `isActivatingClick(buttons, modifiers)` may be used
    to determine whether the menu should be shown.
    '''
    name = 'popup-menu'
    is_focusable = True
    def __init__(self, parent, items, **kw):
        super(PopupMenu, self).__init__(parent, border="black",
            is_visible=False, **kw)

        for n, (label, id) in enumerate(items):
            MenuItem(self, text=label, id=id, width='100%',
                bgcolor=((.95, .95, .95, 1), (1, 1, 1, 1))[n%2])

        self.layout = layouts.Vertical(self)

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
        kw = loadxml.parseAttributes(element)
        items = []
        for child in element.getchildren():
            text = xml.sax.saxutils.unescape(child.text)
            items.append((text, child.attrib['id']))
        return cls(parent, items, **kw)

    @staticmethod
    def isActivatingClick(button, modifiers):
        '''Determine whether the mouse button / modifiers combine to be a
        popup menu activation click or not.

        On all platforms a RMB click is allowed.
        On OS X a control-LMB is allowed.
        '''
        if sys.platform == 'darwin':
            if button & mouse.LEFT and modifiers & key.MOD_CTRL:
                return True
        return button & mouse.RIGHT

@event.default('popup-menu', 'on_gain_focus')
def on_menu_gain_focus(menu, method):
    # catch focus
    return event.EVENT_HANDLED

@event.default('popup-menu', 'on_lose_focus')
def on_menu_lose_focus(menu, method):
    menu.hide()
    return event.EVENT_HANDLED

