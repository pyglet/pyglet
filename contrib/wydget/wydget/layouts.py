import operator

from wydget import util
from wydget.widgets.label import Label

TOP = 'top'
BOTTOM = 'bottom'
LEFT = 'left'
RIGHT = 'right'
CENTER = 'center'
FILL = 'fill'

class Layout(object):
    '''Absolute positioning layout -- also base class for other layouts.

    Elements in the parent are positioined using absolute coordinates in
    the parent's coordinate space.

    "only_visible" -- limits the layout to only those elements which are
                      is_visible (note NOT isVisible - parent visibility
                      obviously makes no sense in this context)
    '''
    def __init__(self, parent, only_visible=False):
        self.only_visible = only_visible
        self.parent = parent

    def __repr__(self):
        return '<%s %dx%d>'%(self.__class__.__name__, self.width, self.height)

    def layout(self):
        # XXX use signal?
        self.parent.layoutDimensionsChanged(self)

    def __call__(self):
        self.layout()

    def get_height(self):
        if not self.parent.children: return 0
        return max(c.y + c.height for c in self.parent.children
            if not self.only_visible or c.is_visible)
    height = property(get_height)

    def get_width(self):
        if not self.parent.children: return 0
        return max(c.x + c.width for c in self.parent.children
            if not self.only_visible or c.is_visible)
    width = property(get_width)

    def getChildren(self):
        return [c for c in self.parent.children
            if not self.only_visible or c.is_visible]

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the a layout from the XML element and handle children.
        '''
        kw = loadxml.parseAttributes(element)
        parent.layout = layout = cls(parent, **kw)

        for child in element.getchildren():
            loadxml.getConstructor(child.tag)(child, layout.parent)
        layout()

        return layout


class Vertical(Layout):
    name = 'vertical'

    def __init__(self, parent, valign=CENTER, halign=None, padding=0,
            wrap=None, **kw):
        self.valign = valign
        self.halign = halign
        self.padding = util.parse_value(padding, parent.inner_rect.height)
        self.wrap = util.parse_value(wrap, parent.inner_rect.height)
        if wrap and halign is None:
            # we need to align somewhere to wrap
            self.halign = self.LEFT
        super(Vertical, self).__init__(parent, *kw)

    def get_height(self):
        ph = self.parent.inner_rect.height
        if self.valign == FILL:
            # fill means using the available height
            return ph
        vis = self.getChildren()
        if not vis: return 0
        if self.wrap:
            if self.parent.height_spec:
                # parent height or widest child if higher than parent
                return max(self.wrap, max(c.height for c in vis))
            else:
                # height of highest row
                return max(sum(c.height for c in column) +
                    self.padding * (len(column)-1)
                        for column in self.determineColumns())
        return sum(c.height for c in vis) + self.padding * (len(vis)-1)
    height = property(get_height)

    def get_width(self):
        vis = self.getChildren()
        if not vis: return 0
        if self.wrap:
            cols = self.determineColumns()
            return sum(max(c.width for c in col) for col in cols) + \
                self.padding * (len(cols)-1)
        return max(c.width for c in vis)
    width = property(get_width)

    def determineColumns(self):
        cols = [[]]
        ch = 0
        for c in self.getChildren():
            if self.wrap and ch and ch + c.height > self.wrap:
                ch = 0
                cols.append([])
            col = cols[-1]
            col.append(c)
            ch += c.height + self.padding
        if not cols[-1]: cols.pop()
        return cols

    def layout(self):
        # give the parent a chance to resize before we layout
        self.parent.layoutDimensionsChanged(self)

        # now get the area available for our layout
        rect = self.parent.inner_rect

        # Determine starting X coord
        x = 0
        if self.halign == CENTER:
            x = rect.width//2 - self.width//2
        elif self.halign == RIGHT:
            x = rect.width - self.width

        fill_padding = self.padding
        for col in self.determineColumns():
            # column width is width of widest child
            cw = max(child.width for child in col)

            # height of this column
            if self.valign == FILL:
                h = rect.height
            else:
                h = sum(c.height for c in col) + self.padding * (len(col)-1)

            # vertical align for this column
            if self.valign == BOTTOM:
                y = h
            elif self.valign == TOP:
                y = rect.height
            elif self.valign == CENTER:
                y = rect.height//2 - h//2 + h
            elif self.valign == FILL:
                y = rect.height
                if len(col) == 1:
                    fill_padding = 0
                else:
                    h = sum(c.height for c in col)
                    fill_padding = (rect.height - h)/float(len(col)-1)

            # now layout the columns
            for child in col:
                y -= child.height
                child.y = int(y)
                y -= fill_padding
                if self.halign == LEFT:
                    child.x = int(x)
                elif self.halign == CENTER:
                    child.x = int(x + (cw//2 - child.width//2))
                elif self.halign == RIGHT:
                    child.x = int(x + (cw - child.width))

            if self.wrap:
                x += self.padding + cw

        super(Vertical, self).layout()


class Horizontal(Layout):
    name = 'horizontal'

    def __init__(self, parent, halign=CENTER, valign=None, padding=0,
            wrap=None, **kw):
        self.halign = halign
        self.valign = valign
        self.wrap = util.parse_value(wrap, parent.inner_rect.width)
        if wrap and valign is None:
            # we need to align somewhere to wrap
            self.valign = self.BOTTOM
        self.padding = util.parse_value(padding, parent.inner_rect.width)
        super(Horizontal, self).__init__(parent, **kw)

    def get_width(self):
        pw = self.parent.inner_rect.width
        if self.halign == FILL:
            # fill means using the available width
            return pw
        vis = self.getChildren()
        if not vis: return 0
        if self.wrap:
            if self.parent.width_spec:
                # parent width or widest child if wider than parent
                return max(self.wrap, max(c.width for c in vis))
            else:
                # width of widest row
                return max(sum(c.width for c in row) +
                    self.padding * (len(row)-1)
                        for row in self.determineRows())
        return sum(c.width for c in vis) + self.padding * (len(vis)-1)
    width = property(get_width)

    def get_height(self):
        vis = self.getChildren()
        if not vis: return 0
        if self.wrap:
            rows = self.determineRows()
            return sum(max(c.height for c in row) for row in rows) + \
                self.padding * (len(rows)-1)
        return max(c.height for c in vis)
    height = property(get_height)

    def determineRows(self):
        rows = [[]]
        rw = 0
        for c in self.getChildren():
            if self.wrap and rw and rw + c.width > self.wrap:
                rw = 0
                rows.append([])
            row = rows[-1]
            row.append(c)
            rw += c.width + self.padding
        if not rows[-1]: rows.pop()
        return rows

    def layout(self):
        # give the parent a chance to resize before we layout
        self.parent.layoutDimensionsChanged(self)

        # now get the area available for our layout
        rect = self.parent.inner_rect

        # Determine starting y coordinate at top of parent.
        if self.valign == BOTTOM:
            y = self.height
        elif self.valign == CENTER:
            y = rect.height//2 - self.height//2 + self.height
        elif self.valign == TOP:
            y = rect.height

        fill_padding = self.padding
        for row in self.determineRows():
            rh = max(child.height for child in row)
            if self.valign is not None:
                y -= rh

            # width of this row
            if self.halign == FILL:
                w = rect.width
            else:
                w = sum(c.width for c in row) + self.padding * (len(row)-1)

            # horizontal align for this row
            x = 0
            if self.halign == RIGHT:
                x = int(rect.width - w)
            elif self.halign == CENTER:
                x = rect.width//2 - w//2
            elif self.halign == FILL:
                if len(row) == 1:
                    fill_padding = 0
                else:
                    w = sum(c.width for c in row)
                    fill_padding = (rect.width - w)/float(len(row)-1)

            for child in row:
                child.x = int(x)
                x += int(child.width + fill_padding)
                if self.valign == BOTTOM:
                    child.y = int(y)
                elif self.valign == CENTER:
                    child.y = int(y + (rh//2 - child.height//2))
                elif self.valign == TOP:
                    child.y = int(y + (rh - child.height))

            if self.wrap:
                y -= self.padding

        super(Horizontal, self).layout()


class Grid(Layout):
    '''A simple table layout that sets column widths in child rows to fit
    all child data.

    Note that this layout ignores *cell* visibility but honors *row*
    visibility for layout purposes.
    '''
    name = 'grid'

    # XXX column alignments
    def __init__(self, parent, colpad=0, rowpad=0, **kw):
        self.colpad = util.parse_value(colpad, 0)
        self.rowpad = util.parse_value(rowpad, 0)
        super(Grid, self).__init__(parent, **kw)

    def columnWidths(self):
        columns = []
        children = self.getChildren()
        N = len(children[0].children)
        for i in range(N):
            w = []
            for row in children:
                pad = i < N-1 and self.colpad or 0
                col = row.children[i]
                w.append(col.width + col.padding * 2 + pad)
            columns.append(max(w))
        return columns

    def get_width(self):
        return sum(self.columnWidths())
    width = property(get_width)

    def get_height(self):
        children = self.getChildren()
        h = sum(max(e.height for e in c.children) + c.padding * 2
            for c in children)
        return h + (len(children)-1) * self.rowpad
    height = property(get_height)

    def layout(self):
        # give the parent a chance to resize before we layout
        self.parent.layoutDimensionsChanged(self)

        children = self.getChildren()

        # determine column widths
        columns = self.columnWidths()

        # right, now position everything
        y = self.height
        for row in children:
            y -= row.height
            row.y = y
            x = 0
            for i, col in enumerate(row.children):
                col.x = x
                x += columns[i]
            row.layout()
            y -= self.rowpad

        super(Grid, self).layout()


class Form(Layout):
    name = 'form'

    def __init__(self, parent, valign=TOP, label_width='25%', padding=4,
            **kw):
        self.valign = valign
        self.label_width = util.parse_value(label_width,
            parent.inner_rect.width)
        self.padding = padding
        self.elements = []
        super(Form, self).__init__(parent, **kw)

    def get_width(self):
        l = [c.width + c._label_dim[0] for c in self.elements
            if not self.only_visible or c.is_visible]
        return max(l) + self.padding
    width = property(get_width)

    def get_height(self):
        l = [max(c.height, c._label_dim[1]) for c in self.elements
            if not self.only_visible or c.is_visible]
        return sum(l) + self.padding * (len(l)-1)
    height = property(get_height)

    def addElement(self, label, element, expand_element=False,
            halign='right', **kw):
        self.elements.append(element)
        if expand_element:
            pw = self.parent.inner_rect.width
            element.width = pw - (self.label_width + self.padding)
        # XXX alignment
        if label:
            l = element._label = Label(self.parent, label,
                width=self.label_width, halign=halign, **kw)
            element._label_dim = (l.width, l.height)
        else:
            element._label = None
            element._label_dim = (self.label_width, 0)

    def layout(self):
        # give the parent a chance to resize before we layout
        self.parent.layoutDimensionsChanged(self)

        # now get the area available for our layout
        rect = self.parent.inner_rect

        h = self.height

        vis = [c for c in self.elements if c.is_visible]

        if self.valign == TOP:
            y = rect.height
        elif self.valign == CENTER:
            y = rect.height//2 + h//2
        elif self.valign == BOTTOM:
            y = h

        for element in vis:
            element.x = self.label_width + self.padding
            y -= max(element.height, element._label_dim[1])
            element.y = y
            if element._label: element._label.y = y
            y -= self.padding

        super(Form, self).layout()

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the a layout from the XML element and handle children.
        '''
        kw = loadxml.parseAttributes(element)
        parent.layout = layout = cls(parent, **kw)

        for child in element.getchildren():
            assert child.tag == 'row', '<form> children must be <row>'
            ckw = loadxml.parseAttributes(child)
            l = child.getchildren()
            if not l: return
            assert len(l) == 1, '<row> may only have one (or no) child'
            content = loadxml.getConstructor(l[0].tag)(l[0], parent)
            layout.addElement(ckw['label'], content, ckw.get('expand'))

        layout()
        return layout


import loadxml
for klass in [Vertical, Horizontal, Grid, Form]:
    loadxml.xml_registry[klass.name] = klass

