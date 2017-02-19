import operator
import math

from wydget import util
from wydget.widgets.label import Label

TOP = 'top'
BOTTOM = 'bottom'
LEFT = 'left'
RIGHT = 'right'
CENTER = 'center'
FILL = 'fill'

intceil = lambda i: int(math.ceil(i))

class Layout(object):
    '''Absolute positioning layout -- also base class for other layouts.

    Elements in the parent are positioined using absolute coordinates in
    the parent's coordinate space.

    "only_visible" -- limits the layout to only those elements which are
                      is_visible (note NOT isVisible - parent visibility
                      obviously makes no sense in this context)
    "ignore"       -- set of elements to ignore when running layout 

    Child elements who do not specify their x and y coordinates will be
    placed at 0 on the missing axis/axes.
    '''
    def __init__(self, parent, only_visible=False, ignore=None):
        self.parent = parent
        self.only_visible = only_visible
        self.ignore = ignore

    def __repr__(self):
        return '<%s %dx%d>'%(self.__class__.__name__, self.width, self.height)

    def _default_positions(self):
        # determine all the simple default poisitioning, including
        # converting None values to 0
        for c in self.getChildren():
            if c.x is None:
                if c.x_spec.spec is None:
                    c.x = 0
                elif c.x_spec.is_fixed:
                    c.x = c.x_spec.calculate()
            if c.y is None:
                if c.y_spec.spec is None:
                    c.y = 0
                elif c.y_spec.is_fixed:
                    c.y = c.y_spec.calculate()
            if c.z is None:
                c.z = 0

    def layout(self):
        self._default_positions()

        # can't layout if we don't have dimensions to layout *in*
        assert self.parent.height is not None and self.parent.width is not None

        # position
        for c in self.getChildren():
            if c.x is None or c.x_spec.percentage is not None:
                c.x = c.x_spec.calculate()
            if c.y is None or c.y_spec.percentage is not None:
                c.y = c.y_spec.calculate()
            if c.z is None:
                c.z = 0

    def __call__(self):
        self.layout()

    def get_height(self):
        if not self.parent.children: return 0
        self._default_positions()
        return intceil(max(c.y + c.min_height for c in self.getChildren()))
    height = property(get_height)

    def get_width(self):
        if not self.parent.children: return 0
        self._default_positions()
        return intceil(max(c.x + c.min_width for c in self.getChildren()))
    width = property(get_width)

    def getChildren(self):
        l = []
        for c in self.parent.children:
            if self.only_visible and not c.is_visible:
                continue
            if self.ignore is not None and c in self.ignore:
                continue
            l.append(c)
        return l

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the a layout from the XML element and handle children.
        '''
        kw = loadxml.parseAttributes(element)
        parent.layout = layout = cls(parent, **kw)

        for child in element.getchildren():
            loadxml.getConstructor(child.tag)(child, layout.parent)
        return layout


class Vertical(Layout):
    name = 'vertical'

    def __init__(self, parent, valign=TOP, halign=LEFT, padding=0,
            wrap=None, **kw):
        self.valign = valign
        self.halign = halign
        self.padding = util.parse_value(padding)
        self.wrap = wrap and util.Dimension(wrap, parent, parent, 'height')
        super(Vertical, self).__init__(parent, *kw)

    def get_height(self):
        if self.valign == FILL:
            ph = self.parent.height
            if ph is not None:
                # fill means using the available height
                return int(self.parent.inner_rect.height)
        vis = self.getChildren()
        if not vis: return 0
        if self.wrap:
            if self.parent.height_spec:
                # parent height or widest child if higher than parent
                return intceil(max(self.wrap.specified(),
                    max(c.min_height for c in vis)))
            else:
                # height of highest row
                return intceil(max(sum(c.min_height for c in column) +
                    self.padding * (len(column)-1)
                        for column in self.determineColumns()))
        return intceil(sum(c.min_height for c in vis) +
            self.padding * (len(vis)-1))
    height = property(get_height)

    def get_width(self):
        vis = self.getChildren()
        if not vis: return 0
        if self.wrap:
            cols = self.determineColumns()
            return sum(max(c.min_width for c in col) for col in cols) + \
                self.padding * (len(cols)-1)
        return intceil(max(c.min_width for c in vis))
    width = property(get_width)

    def determineColumns(self):
        cols = [[]]
        ch = 0
        wrap = self.wrap and self.wrap.calculate()
        for c in self.getChildren():
            if wrap and ch and ch + c.min_height > wrap:
                ch = 0
                cols.append([])
            col = cols[-1]
            col.append(c)
            ch += c.min_height + self.padding
        if not cols[-1]: cols.pop()
        return cols

    def layout(self):
        # can't layout if we don't have dimensions to layout *in*
        assert self.parent.height is not None and self.parent.width is not None
        for child in self.getChildren():
            assert child.height is not None and child.width is not None, \
                '%r missing dimensions'%child

        # now get the area available for our layout
        rect = self.parent.inner_rect

        # Determine starting X coord
        x = 0
        if self.halign == CENTER:
            x = rect.width//2 - self.width//2
        elif self.halign == RIGHT:
            x = rect.width - self.width

        wrap = self.wrap and self.wrap.calculate()

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

            if wrap:
                x += self.padding + cw


class Horizontal(Layout):
    name = 'horizontal'

    def __init__(self, parent, halign=LEFT, valign=TOP, padding=0,
            wrap=None, **kw):
        self.halign = halign
        self.valign = valign
        self.padding = util.parse_value(padding)
        self.wrap = wrap and util.Dimension(wrap, parent, parent, 'height')
        super(Horizontal, self).__init__(parent, **kw)

    def get_width(self):
        if self.halign == FILL:
            pw = self.parent.width
            if pw is not None:
                # fill means using the available width
                return int(self.parent.inner_rect.width)
        vis = self.getChildren()
        if not vis: return 0
        if self.wrap:
            if self.parent.width_spec:
                # parent width or widest child if wider than parent
                return intceil(max(self.wrap.specified(),
                    max(c.min_width for c in vis)))
            else:
                # width of widest row
                return max(sum(c.min_width for c in row) +
                    self.padding * (len(row)-1)
                        for row in self.determineRows())
        return intceil(sum(c.min_width for c in vis) +
            self.padding * (len(vis)-1))
    width = property(get_width)

    def get_height(self):
        vis = self.getChildren()
        if not vis: return 0
        if self.wrap:
            rows = self.determineRows()
            return intceil(sum(max(c.min_height for c in row) for row in rows) +
                self.padding * (len(rows)-1))
        return intceil(max(c.min_height for c in vis))
    height = property(get_height)

    def determineRows(self):
        rows = [[]]
        rw = 0
        wrap = self.wrap and self.wrap.calculate()
        for c in self.getChildren():
            if wrap and rw and rw + c.min_width > wrap:
                rw = 0
                rows.append([])
            row = rows[-1]
            row.append(c)
            rw += c.min_width + self.padding
        if not rows[-1]: rows.pop()
        return rows

    def layout(self):
        # can't layout if we don't have dimensions to layout *in*
        assert self.parent.height is not None and self.parent.width is not None

        # now get the area available for our layout
        rect = self.parent.inner_rect

        # Determine starting y coordinate at top of parent.
        if self.valign == BOTTOM:
            y = self.height
        elif self.valign == CENTER:
            y = rect.height//2 - self.height//2 + self.height
        elif self.valign == TOP:
            y = rect.height

        wrap = self.wrap and self.wrap.calculate()

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

            for i, child in enumerate(row):
                if fill_padding and i == len(row) - 1: 
                    child.x = int(rect.width - child.width)
                else:
                    child.x = int(x)
                    x += int(child.width + fill_padding)
                if self.valign == BOTTOM:
                    child.y = int(y)
                elif self.valign == CENTER:
                    child.y = int(y + (rh//2 - child.height//2))
                elif self.valign == TOP:
                    child.y = int(y + (rh - child.height))

            if wrap:
                y -= self.padding


class Grid(Layout):
    '''A simple table layout that sets column widths in child rows to fit
    all child data.

    Note that this layout ignores *cell* visibility but honors *row*
    visibility for layout purposes.
    '''
    name = 'grid'

    # XXX column alignments
    def __init__(self, parent, colpad=0, rowpad=0, colaligns=None, **kw):
        self.colaligns = colaligns
        self.colpad = util.parse_value(colpad, 0)
        self.rowpad = util.parse_value(rowpad, 0)
        super(Grid, self).__init__(parent, **kw)

    def columnWidths(self):
        columns = []
        children = self.getChildren()
        if not children:
            return []
        N = len(children[0].children)
        for i in range(N):
            w = []
            for row in children:
                pad = i < N-1 and self.colpad or 0
                col = row.children[i]
                w.append(col.min_width + pad)
            columns.append(max(w))
        return columns

    def get_width(self):
        return intceil(sum(self.columnWidths()))
    width = property(get_width)

    def get_height(self):
        children = self.getChildren()
        h = intceil(sum(max(e.min_height for e in c.children) + c.padding*2
            for c in children))
        return intceil(h + (len(children)-1) * self.rowpad)
    height = property(get_height)

    def layout(self):
        children = self.getChildren()

        # determine column widths
        columns = self.columnWidths()

        # column alignments
        colaligns = self.colaligns

        # right, now position everything
        y = self.height
        for row in children:
            y -= row.height
            rp2 = row.padding * 2
            row.y = y
            row.x = 0
            x = 0
            for i, elem in enumerate(row.children):
                elem.x = x
                if colaligns is not None:
                    if colaligns[i] == 'r':
                        elem.x += columns[i] - elem.width - rp2
                    elif colaligns[i] == 'c':
                        elem.x += (columns[i] - rp2)//2 - elem.width//2
                    elif colaligns[i] == 'f':
                        elem.width = columns[i] - rp2
                elem.y = row.inner_height - elem.height
                x += columns[i]
            y -= self.rowpad


class Form(Grid):
    name = 'form'

    def __init__(self, *args, **kw):
        if 'colaligns' not in kw:
            kw['colaligns'] = 'rl'
        super(Form, self).__init__(*args, **kw)

    def addElement(self, label, element, **kw):
        from wydget.widgets.frame import Frame

        row = Frame(self.parent, is_transparent=True)
        if label:
            element._label = Label(row, label, **kw)
        else:
            element._label = None
            Frame(row, is_transparent=True, width=0, height=0)

        # move the element to the row
        element.parent.children.remove(element)
        row.children.append(element)
        element.parent = row

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
            layout.addElement(ckw['label'], content)
        return layout


import loadxml
for klass in [Vertical, Horizontal, Grid, Form]:
    loadxml.xml_registry[klass.name] = klass

