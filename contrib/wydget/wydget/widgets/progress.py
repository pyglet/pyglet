from pyglet.gl import *

from wydget import loadxml
from wydget import util
from wydget.widgets.label import Label

class Progress(Label):
    name = 'progress'
    def __init__(self, parent, value=0.0, show_value=True,
            bar_color='gray', bgcolor=(.3, .3, .3, 1), color='white',
            width=None, height=16, halign='center', valign='center', **kw):

        self._value = util.parse_value(value, 0)
        self.show_value = show_value
        self.bar_color = util.parse_color(bar_color)

        super(Progress, self).__init__(parent, ' ', width=width,
            height=height, bgcolor=bgcolor, color=color, halign=halign,
            valign=valign, **kw)

        if self.show_value:
            self.text = '%d%%'%(value * 100)

    def set_value(self, value):
        self._value = value
        if self.show_value:
            self.text = '%d%%'%(value * 100)
    value = property(lambda self: self._value, set_value)

    def renderBackground(self, rect):
        super(Progress, self).renderBackground(rect)
        r = rect.copy()
        r.width *= self._value
        b, self.bgcolor = self.bgcolor, self.bar_color
        super(Progress, self).renderBackground(r)
        self.bgcolor = b

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.
        '''
        kw = loadxml.parseAttributes(element)
        obj = cls(parent, **kw)
        for child in element.getchildren():
            loadxml.getConstructor(element.tag)(child, obj)
        return obj

