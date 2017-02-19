'''Define the core `Element` class from which all gui widgets are derived.

All gui elements have:

- the parent widget
- an id, element name and list of classes
- a list of children widgets
- a position in 3D space, relative to their parent's position
- dimensions available as width, height, rect and inner_rect
- scaling factors in x and y
- visibility, enabled and transparent flags
- a border colour, padding and background colour


Display Model
-------------

The basic shape of an element is defined by the x, y, width and height
attributes.

Borders are drawn on the inside of the element's rect as a single pixel
line in the specified border colour. If no padding is specified then the
padding will automatically be set to 1 pixel.

There is an additional rect defined which exists inside the padding, if
there is any. This is available as the ``inner_rect`` attribute.

Finally each element may define a "view clip" which will restrict the
rendering of the item and its children to a limited rectangle.


Sizing 
------

Elements may specify one of the following for width and height:

1. a fixed value (in pixels)            TODO: allow em sizes?
2. a fixed value in em units using the active style for the element. This
   method calculates an *inner* dimension, so padding is added on.
2. a percentage of their parent size (using the inner rect of the parent)
3. no value, thus the element is sized to be the minimum necessary to 
   display contents correctly

Elements have three properties for each of width and height:

    <dimension>_spec    -- the specification, one of the above
    min_<dimension>     -- the minimum size based on element contents and
                           positioning
    <dimension>         -- the calculated size

Subclasses if Element define:

    intrinsic_<dimension> -- the size of the element contents

If <dimension> depends on parent sizing and that sizing is unknown then it
should be None. This indicates that sizing calculation is needed.

'''
import inspect
import math

from pyglet.gl import *

from wydget import loadxml
from wydget import event
from wydget import util 

intceil = lambda i: int(math.ceil(i))

class Element(object):
    '''A GUI element.

    x, y, z         -- position *relative to parent*
    width, height   -- for hit area
    is_transparent  -- is this element displayed*?
    is_visible      -- is this element *and its children* displayed*?
    is_enabled      -- is this element *and its children* enabled?
    is_modal        -- is this element capturing all user input?
    children        -- Elements I hold
    parent          -- container I belong to
    id              -- my id (auto-allocated if none given)

    border          -- Colour of the border around the element. If set,
                       padding is defaulted to 1 unless otherwise specified.
                       (see `colour specification`_)
    padding         -- 
    bgcolor         -- 

    *: elements not displayed also do not receive events.

    Positioning and Dimension Specification
    ---------------------------------------

    The positioning and dimensions arguments may be specifed as simple numeric
    values or as percentages of the parent's *inner* rectangle measurement.


    Colour Specification
    --------------------

    All colours (border and bgcolor here, but other colours on various widgets)
    may be specified as a 4-tuple of floats in the 0-1 range for (red, green,
    blue, alpha). Alternatively any valid CSS colour specification may be used
    ("#FFF", "red", etc).
    '''
    is_focusable = False

    # each GUI element (widget, etc) must define its own name attribute
    # name
    classes = ()

    view_clip = None

    _x = _y = _width = _height = None

    def __init__(self, parent, x, y, z, width, height, padding=0,
            border=None, bgcolor=None, is_visible=True, is_enabled=True,
            is_transparent=False, children=None, id=None, classes=()):
        self.parent = parent
        self.id = id or self.allocateID()
        self.classes = classes
        self.children = children or []

        # colors, border and padding
        self.bgcolor = util.parse_color(bgcolor)
        self.border = util.parse_color(border)
        self._padding = util.parse_value(padding)
        if border:
            # force enough room to see the border
            self._padding += 1

        # save off the geometry specifications
        self.x_spec = util.Position(x, self, parent, 'width')
        self.y_spec = util.Position(y, self, parent, 'height')
        self._z = util.parse_value(z) or 0
        self.width_spec = util.Dimension(width, self, parent, 'width')
        self.height_spec = util.Dimension(height, self, parent, 'height')

        # attempt to calculate now what we can
        if self.x_spec.is_fixed:
            self.x = self.x_spec.calculate()
        if self.y_spec.is_fixed:
            self.y = self.y_spec.calculate()
        if self.width_spec.is_fixed:
            self.width = self.width_spec.calculate()
        if self.height_spec.is_fixed:
            self.height = self.height_spec.calculate()

        self.is_visible = is_visible
        self.is_enabled = is_enabled
        self.is_modal = False
        self.is_transparent = is_transparent

        self._event_handlers = {}

        # add this new element to its parent
        self.parent.addChild(self)

        # indicate we need geometry calculation 
        self.resetGeometry()

    _next_id = 1
    def allocateID(self):
        id = '%s-%d'%(self.__class__.__name__, Element._next_id)
        Element._next_id += 1
        return id

    def set_x(self, value):
        self._x = value
        self.setDirty()
    x = property(lambda self: self._x and int(self._x), set_x)

    def set_y(self, value):
        self._y = value
        self.setDirty()
    y = property(lambda self: self._y and int(self._y), set_y)

    def set_z(self, value):
        self._z = value
        self.setDirty()
    z = property(lambda self: self._z and int(self._z), set_z)

    def set_width(self, value):
        self._width = value
        self.setDirty()
    width = property(lambda self: self._width and intceil(self._width),
        set_width)

    def set_height(self, value):
        self._height = value
        self.setDirty()
    height = property(lambda self: self._height and intceil(self._height),
        set_height)

    def set_padding(self, value):
        self._padding = value
        self.setDirty()
    padding = property(lambda self: self._padding and int(self._padding),
        set_padding)

    def get_rect(self):
        return util.Rect(int(self._x), int(self._y), self.width, self.height)
    rect = property(get_rect)

    def get_inner_rect(self):
        p = self._padding
        return util.Rect(int(p), int(p), intceil(self._width - p*2),
            intceil(self._height - p*2))
    inner_rect = property(get_inner_rect)

    def get_inner_width(self):
        return intceil(self._width - self._padding*2)
    inner_width = property(get_inner_width)

    def get_inner_height(self):
        return intceil(self._height - self._padding*2)
    inner_height = property(get_inner_height)

    def get_min_width(self):
        '''Return the minimum width required for this element.

        If the width relies on some parent element's dimensions, then just
        return the intrinsic_width for the element.
        '''
        if self.width_spec.value is not None:
            return self.width_spec.value
        width = self.width
        if width is None:
            width = self.intrinsic_width()
        return width
    min_width = property(get_min_width)
    def intrinsic_width(self):
        raise NotImplementedError('intrinsic_width on %r'%self.__class__)

    def get_min_height(self):
        '''Return the minimum height required for this element.

        If the height relies on some parent element's dimensions, then just
        return the intrinsic_height for the element.
        '''
        if self.height_spec.value is not None:
            return self.height_spec.value
        height = self.height
        if height is None:
            height = self.intrinsic_height()
        return height
    min_height = property(get_min_height)
    def intrinsic_height(self):
        raise NotImplementedError('intrinsic_height on %r'%self.__class__)

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.
        '''
        kw = loadxml.parseAttributes(element)
        obj = cls(parent, **kw)
        for child in element.getchildren():
            loadxml.getConstructor(child.tag)(child, obj)
        return obj

    def addChild(self, child):
        '''Add the child element to this container.

        The child is register()ed with the GUI and this element's geometry
        is reset (if not fixed) so it will be reshaped upon the next
        top-level GUI layout().
        '''
        self.children.append(child)
        child.parent = self
        self.getGUI().register(child)
        self.resetGeometry()

    def getParent(self, selector):
        '''Get the first parent selected by the selector.

        XXX at the moment, just does name
        '''
        if isinstance(selector, str):
            if selector[0] in '.#':
                raise NotImplementedError(
                    'lookup by id and class not yet supported')
            selector = [s.strip() for s in selector.split(',')]
        if self.name in selector: return self
        return self.parent.getParent(selector)

    def holds(self, element):
        '''Return True if the element is a child of this element or its
        children.
        '''
        for child in self.children:
            if child is element:
                return True
            if child.holds(element):
                return True
        return False

    def resetGeometry(self):
        if not self.width_spec.is_fixed:
            self._width = None
        if not self.height_spec.is_fixed:
            self._height = None
        for child in self.children:
            child.resetGeometry()
        # this is going to be called *a lot*
        self.setDirty()

    def resize(self):
        '''Determine position and dimension.

        Return boolean whether we are able to calculate all values or
        whether we need parent dimensions to continue.
        '''
        ok = True
        if self._width is None:
            w = self.width_spec.calculate()
            # if we calculated the value write it through the property so
            # that subclasses may react to the altered dimension
            if w is None: ok = False
            else: self.width = w
        if self._height is None:
            h = self.height_spec.calculate()
            if h is None: ok = False
            else: self.height = h
        return ok

    def getRects(self, view_clip=None, exclude=None):
        '''Determine the drawing parameters for this element and its
        children.

        Returns a list of (element, (x, y, z, clipped)) where:

           (x, y, z) is the screen location to render at
           clipped   is the relative rectangle to render
        '''
        if not self.is_visible: return []

        # figure my rect
        r = util.Rect(self._x, self._y, self._width, self._height)
        if view_clip is not None:
            r = r.intersect(view_clip)
        if r is None: return []

        x, y, z = self._x, self._y, self._z

        # translate the view clip into this element's coordinate space
        clipped = self.rect
        clipped.x -= x
        clipped.y -= y
        if view_clip:
            view_clip = view_clip.copy()
            view_clip.x -= x
            view_clip.y -= y
            clipped = clipped.intersect(view_clip)
            if not clipped:
                return []

        rects = []
        if not self.is_transparent:
            rects.append((self, (x, y, z, clipped)))
        if not self.children:
            return rects

        # shift child elements and view clip for left & bottom padding 
        pad = self._padding
        x += pad
        y += pad
        if view_clip is not None:
            view_clip = view_clip.copy()
            view_clip.x -= pad
            view_clip.y -= pad

        # clip by this element's view clip
        if self.view_clip is not None:
            if view_clip is not None:
                view_clip = view_clip.intersect(self.view_clip)
            else:
                view_clip = self.view_clip

        if not view_clip: return rects

        for child in self.children:
            if exclude is child: continue
            for obj, (ox, oy, oz, c) in child.getRects(view_clip,
                    exclude):
                rects.append((obj, (ox+x, oy+y, oz+z, c)))
        return rects

    def setViewClip(self, rect):
        self.view_clip = util.Rect(*rect)

    def draw(self, x, y, z, clipped):
        '''Draw me given the parameters:

        `rect`      -- absolute coordinates of the element on screen
                       taking into account all translation and scaling
        `z`         -- z position
        `clipped`   -- recangle to draw in *relative* coordinates
                       to pass to render()

        This method is not invoked if self.is_transparent or
        not self.is_visible.
        '''
        # translate
        glPushMatrix()
        glTranslatef(int(x), int(y), z)

        # render the common Element stuff - border and background
        attrib = GL_CURRENT_BIT
        bg, border = self.bgcolor, self.border
        if (bg and bg[-1] != 1) or (border and border[-1] != 1):
            attrib |= GL_ENABLE_BIT
        glPushAttrib(attrib)
        if attrib & GL_ENABLE_BIT:
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_BLEND)
        self.renderBackground(clipped)
        self.renderBorder(clipped)
        glPopAttrib()

        # translate padding
        if self._padding:
            glTranslatef(self._padding, self._padding, 0)

        # now render the element
        self.render(clipped)

        glPopMatrix()

    def render(self, clipped):
        '''Render the element in relative coordinates clipped to the
        indicated view.
        '''
        pass

    def renderBackground(self, clipped):
        '''Render the background in relative coordinates clipped to the
        indicated view.
        '''
        if self.bgcolor is None: return
        glColor4f(*self.bgcolor)
        x2, y2 = clipped.topright
        glRectf(clipped.x, clipped.y, x2, y2)

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
        # bottom
        if oy == cy:
            glVertex2f(cx, oy)
            glVertex2f(cx2, oy)
        # top
        if oy2 == cy2:
            glVertex2f(cx, oy2-1)
            glVertex2f(cx2, oy2-1)

        glEnd()

    def isEnabled(self):
        return self.is_enabled and self.parent.isEnabled()

    def setEnabled(self, is_enabled):
        self.is_enabled = is_enabled

    def isVisible(self):
        return self.is_visible and self.parent.isVisible()

    def setVisible(self, is_visible):
        self.is_visible = is_visible
        self.getGUI().layoutNeeded()

    def setDirty(self):
        self.getGUI().setDirty()

    def isFocused(self):
        return self is self.getGUI().focused_element

    def setModal(self, element=None):
        '''Have this element capture all user input.
        '''
        if element is None: element = self
        self.parent.setModal(element)

    def gainFocus(self):
        self.getGUI().setFocus(self, source='code')

    def hasFocus(self):
        return self.getGUI().focused_element is self

    def loseFocus(self):
        self.getGUI().setFocus(None, source='code')

    def clearSelection(self):
        '''The element has previously indicated that it has data for the
        clipboard, but it has now been superceded by another element.
        '''
        pass

    def getStyle(self):
        return self.parent.getStyle()

    def getGUI(self):
        return self.parent.getGUI()

    def get(self, spec):
        return self.getGUI().get(spec)

    def calculateAbsoluteCoords(self, x, y):
        x += self._x + self.parent.padding; y += self._y + self.parent.padding
        return self.parent.calculateAbsoluteCoords(x, y)

    def calculateRelativeCoords(self, x, y):
        x -= self._x + self.padding; y -= self._y + self.padding
        return self.parent.calculateRelativeCoords(x, y)

    def reparent(self, new_parent):
        x, y = self.parent.calculateAbsoluteCoords(self._x, self._y)
        self.x, self.y = new_parent.calculateRelativeCoords(x, y)
        self.parent.children.remove(self)
        new_parent.children.append(self)
        self.parent = new_parent
        self.setDirty()

    def replace(self, old, new):
        '''Replace the "old" widget with the "new" one.

        It is assumed that "new" is already a child of this element.
        '''
        self.children.remove(new)
        old_index = self.children.index(old)
        old.delete()
        self.children.insert(old_index, new)

    def clear(self):
        for child in list(self.children): child.delete()
        self.children = []

    def delete(self):
        self.resetGeometry()
        gui = self.getGUI()
        # clear modality?
        if self.is_modal: gui.setModal(None)
        gui.dispatch_event(self, 'on_delete')
        self.parent.children.remove(self)
        gui.unregister(self)
        self.clear()

    def dump(self, s=''):
        print s + str(self)
        for child in self.children: child.dump(s+' ')

    def __repr__(self):
        return '<%s %r at (%s, %s, %s) (%sx%s) pad=%s>'%(
            self.__class__.__name__, self.id, self._x, self._y, self._z,
            self._width, self._height, self._padding)

