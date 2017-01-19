import datetime
import xml.sax.saxutils

from pyglet.gl import *

from wydget import element, event, layouts, loadxml, util
from wydget.widgets.frame import Frame, ContainerFrame
from wydget.widgets.slider import VerticalSlider, HorizontalSlider
from wydget.widgets.label import Label

class Table(element.Element):
    name = 'table'
    h_slider = None
    v_slider = None

    def __init__(self, parent, size=None, is_exclusive=False,
            color=(0, 0, 0, 1), bgcolor=(1, 1, 1, 1),
            alt_bgcolor=(.9, .9, .9, 1), active_bgcolor=(1, .8, .8, 1),
            x=0, y=0, z=0, width='100%', height=None, **kw):
        font_size = parent.getStyle().font_size
        size = util.parse_value(size, None)
        if size is not None:
            height = (size + 1) * font_size

        self.is_exclusive = is_exclusive

        super(Table, self).__init__(parent, x, y, z, width, height,
            bgcolor=bgcolor, **kw)

        # rows go in under the heading
        #self.contents = TableContainer(self)
        self.contents = ContainerFrame(self)
        self.contents.layout = layouts.Layout(self.contents)
        self.contents.checkForScrollbars()

        # specific attributes for rows
        self.color = util.parse_color(color)
        self.base_bgcolor = self.bgcolor
        self.alt_bgcolor = util.parse_color(alt_bgcolor)
        self.active_bgcolor = util.parse_color(active_bgcolor)

    def get_inner_rect(self):
        p = self.padding
        font_size = self.getStyle().font_size
        return util.Rect(p, p, self.width - p*2, self.height - p*2 - font_size)
    inner_rect = property(get_inner_rect)

    def layoutDimensionsChanged(self, layout):
        pass

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.

        If scrollable then put all children loaded into a container frame.
        '''
        kw = loadxml.parseAttributes(element)
        obj = cls(parent, **kw)
        for child in element.getchildren():
            if child.tag == 'row':
                Row.fromXML(child, obj.contents)
            elif child.tag == 'heading':
                obj.heading = Heading.fromXML(child, obj)
                obj.heading.layout.layout()
            else:
                raise ValueError, 'unexpected tag %r'%child.tag
        obj.contents.layout.layout()
        return obj

class Heading(Frame):
    name = 'heading'

    def __init__(self, parent, width='100%', bgcolor='aaa', **kw):
        kw['y'] = parent.height - parent.getStyle().font_size
        super(Heading, self).__init__(parent, width=width, **kw)
        self.layout = layouts.Horizontal(self, valign='top', halign='fill',
            padding=2)


class Row(Frame):
    name = 'row'

    def __init__(self, parent, border=None, color=None, bgcolor=None,
            active_bgcolor=None, is_active=False, width='100%', **kw):
        self.is_active = is_active

        # default styling and width to parent settings
        n = len(parent.children)
        table = parent.parent
        if color is None:
            color = table.color
        if bgcolor is None:
            bgcolor = (table.bgcolor, table.alt_bgcolor)[n%2]
        if active_bgcolor is None:
            self.active_bgcolor = table.active_bgcolor
        else:
            self.active_bgcolor = util.parse_color(active_bgcolor)

        font_size = parent.getStyle().font_size
        kw['y'] = n * font_size
        kw['height'] = font_size
        super(Row, self).__init__(parent, border=border, bgcolor=bgcolor,
            width=width, **kw)
        self.base_bgcolor = bgcolor

    def renderBackground(self, clipped):
        '''Select the correct background color to render.
        '''
        if self.is_active and self.active_bgcolor:
            self.bgcolor = self.active_bgcolor
        else:
            self.bgcolor = self.base_bgcolor
        super(Row, self).renderBackground(clipped)



class Cell(Label):
    name = 'cell'

    def __init__(self, parent, value, type='string', **kw):
        self.value = value
        self.type = type
        self.column = len(parent.children)
        kw['x'] = parent.parent.parent.heading.children[self.column].x
        if type == 'time':
            if value.hour:
                text = '%d:%02d:%02d'%(value.hour, value.minute, value.second)
            else:
                text = '%d:%02d'%(value.minute, value.second)
        else:
            text = str(value)
        super(Cell, self).__init__(parent, text, **kw)

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.
        '''
        kw = loadxml.parseAttributes(element)
        text = xml.sax.saxutils.unescape(element.text)

        t = kw.get('type')
        if t == 'integer':
            value = int(text)
        elif t == 'time':
            if ':' in text:
                # (h:)m:s value
                value = map(int, text.split(':'))
                if len(value) == 2: m, s = value[0], value[1]
                else: h, m, s = value[0], value[1], value[2]
            else:
                # seconds value
                value = int(text)
                s = value % 60
                m = (value / 60) % 60
                h = value / 360
            value = datetime.time(h, m, s)
        else:
            value = text

        obj = cls(parent, value, **kw)

        #for child in element.getchildren():
        #    loadxml.getConstructor(element.tag)(child, obj)
        return obj

