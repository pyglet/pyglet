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
attributes. This rect may be scaled by the sx and sy properties (about the
x, y corner - only the width and height are scaled).

Borders are drawn on the inside of the element's rect as a single pixel
line in the specified border colour. If no padding is specified then the
padding will automatically be set to 1 pixel.

There is an additional rect defined which exists inside the padding, if
there is any. This is available as the ``inner_rect`` attribute.

Finally each element may define a "view clip" which will restrict the
rendering of the item and its children to a limited rectangle.
'''
import inspect

from pyglet.gl import *

import loadxml
import event
import util 

class Element(object):
    '''A GUI element.

    x, y, z         -- position *relative to parent*
    width, height   -- for hit area
    sx, sy          -- scaling in x and y axis
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

    _x = _y = _z = _width = _height = 0

    def __init__(self, parent, x, y, z, width, height, padding=None,
            sx=1., sy=1., border=None, bgcolor=None,
            is_visible=True, is_enabled=True, is_transparent=False,
            children=None, id=None, classes=(), render=None,
            renderBackground=None, renderBorder=None):
        self.parent = parent
        self.children = children or []

        ir = parent.inner_rect
        self._x = util.parse_value(x, ir.width)
        self._y = util.parse_value(y, ir.height)
        self._z = util.parse_value(z)

        # save off the width / height specs for later recalculation
        self._width = util.parse_value(width, ir.width)
        self.width_spec = width
        self._height = util.parse_value(height, ir.height)
        self.height_spec = height

        # default to the parent dimensions if we're completely stuck
        if width is None:
            self._width = ir.width
        if height is None:
            self._height = ir.height

        # colors, border and padding
        self.bgcolor = util.parse_color(bgcolor)
        self.border = util.parse_color(border)
        if padding is None:
            if border:
                # force enough room to see the border
                padding = 1
            else:
                padding = 0
        self._padding = util.parse_value(padding, 0)

        self._sx, self._sy = sx, sy

        self.is_visible = is_visible
        self.is_enabled = is_enabled
        self.is_modal = False
        self.is_transparent = is_transparent
        self.id = id or self.allocateID()
        self.classes = classes

        # rendering overrides
        if render is not None:
            self.render = render
        if renderBackground is not None:
            self.renderBackground = renderBackground
        if renderBorder is not None:
            self.renderBorder = renderBorder

        self._event_handlers = {}

        # add this new element to its parent
        self.parent.addChild(self)

    _next_id = 1
    def allocateID(self):
        id = '%s-%d'%(self.__class__.__name__, Element._next_id)
        Element._next_id += 1
        return id

    def get_x(self): return self._x
    def set_x(self, value):
        self._x = value
        # XXX just update my rect
        self.getGUI().setDirty()
    x = property(get_x, set_x)

    def get_y(self): return self._y
    def set_y(self, value):
        self._y = value
        # XXX just update my rect
        self.getGUI().setDirty()
    y = property(get_y, set_y)

    def get_z(self): return self._z
    def set_z(self, value):
        self._z = value
        # XXX just update my rect
        self.getGUI().setDirty()
    z = property(get_z, set_z)

    def get_width(self): return self._width * self._sx
    def set_width(self, value):
        self._width = value
        # XXX just update my rect
        self.getGUI().setDirty()
    width = property(get_width, set_width)

    def get_height(self): return self._height * self._sy
    def set_height(self, value):
        self._height = value
        # XXX just update my rect
        self.getGUI().setDirty()
    height = property(get_height, set_height)

    def get_padding(self): return self._padding * self._sx # XXX yuck
    def set_padding(self, value):
        self._padding = value
        # XXX just update my rect
        self.getGUI().setDirty()
    padding = property(get_padding, set_padding)

    def get_sx(self): return self._sx
    def set_sx(self, value):
        self._sx = float(value)
        # XXX just update my rect
        self.getGUI().setDirty()
    sx = property(get_sx, set_sx)

    def get_sy(self): return self._sy
    def set_sy(self, value):
        self._sy = float(value)
        # XXX just update my rect
        self.getGUI().setDirty()
    sy = property(get_sy, set_sy)

    def get_center(self):
        return (self._x + self.width/2, self._y + self.height/2)
    def set_center(self, (x, y)):
        self._x = x - self.width // 2
        self._y = y - self.height // 2
        # XXX just update my rect
        self.getGUI().setDirty()
    center = property(get_center, set_center)

    def get_rect(self):
        return util.Rect(self._x, self._y, self.width, self.height)
    rect = property(get_rect)

    def get_inner_rect(self):
        px = self.padding * self.sx
        py = self.padding * self.sy
        return util.Rect(px, py, self.width - px*2, self.height - py*2)
    inner_rect = property(get_inner_rect)

    @classmethod
    def fromXML(cls, element, parent):
        '''Create the object from the XML element and attach it to the parent.
        '''
        kw = loadxml.parseAttributes(parent, element)
        obj = cls(parent, **kw)
        for child in element.getchildren():
            loadxml.getConstructor(child.tag)(child, obj)
        return obj

    def addChild(self, child):
        self.children.append(child)
        child.parent = self
        self.getGUI().registerID(child)

    def getParent(self, selector):
        '''Get the first parent selected by the selector.

        XXX at the moment, just does name
        '''
        if self.name == selector: return self
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

    def dump(self, s=''):
        print s + str(self)
        for child in self.children: child.dump(s+' ')

    def __repr__(self):
        return '<%s %r at (%s, %s, %s) (%sx%s) pad=%s>'%(
            self.__class__.__name__, self.id, self.x, self.y, self.z,
            self.width, self.height, self.padding)

    def isEnabled(self):
        return self.is_enabled and self.parent.isEnabled()

    def isVisible(self):
        return self.is_visible and self.parent.isVisible()

    def setVisible(self, is_visible):
        self.is_visible = is_visible
        self.getGUI().setDirty()

    def setEnabled(self, is_enabled):
        self.is_enabled = is_enabled

    def getRects(self, view_clip=None, exclude=None):
        '''Determine the drawing parameters for this element and its
        children.

        Returns a list of (element, (x, y, z, sx, sy, clipped)) where:

           (x, y, z) is the screen location to render at
           (sx, sy)  is the scale to render at
           clipped   is the relative rectangle to render
        '''
        if not self.is_visible: return []

        # figure my rect
        r = util.Rect(self._x, self._y, self._width * self._sx,
            self._height * self._sy)
        if view_clip is not None:
            r = r.intersect(view_clip)
        if r is None: return []

        x, y, z, sx, sy = self._x, self._y, self._z, self._sx, self._sy

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
            rects.append((self, (x, y, z, sx, sy, clipped)))

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
            for obj, (ox, oy, oz, osx, osy, c) in child.getRects(view_clip,
                    exclude):
                rects.append((obj, (ox*sx+x, oy*sy+y, oz+z, osx, osy, c)))
        return rects

    def setViewClip(self, rect):
        self.view_clip = util.Rect(*rect)

    def draw(self, x, y, z, sx, sy, clipped):
        '''Draw me given the parameters:

        `rect`      -- absolute coordinates of the element on screen
                       taking into account all translation and scaling
        `sx`, `sy`  -- scaling factors
        `z`         -- z position
        `clipped`   -- recangle to draw in *relative* coordinates
                       to pass to render()

        This method is not invoked if self.is_transparent or
        not self.is_visible.
        '''
        # translate
        glPushMatrix()
        glTranslatef(x, y, z)

       # print '**', self
       # print (x, y, z)
       # print clipped

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

        # scale if necessary
        if sx != 1 or sy != 1:
            glScalef(sx, sy, 1)

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

    def parentDimensionsChanged(self):
        '''Indicate to the child that the parent rect has changed and it
        may have the opportunity to resize.'''
        pass

    def setModal(self, element=None):
        '''Have this element capture all user input.
        '''
        if element is None: element = self
        self.parent.setModal(element)

    def gainFocus(self):
        self.getGUI().setFocus(self)

    def hasFocus(self):
        return self.getGUI().focused_element is self

    def loseFocus(self):
        self.getGUI().setFocus(None)

    def clearSelection(self):
        '''The element has previously indicated that it has data for the
        clipboard, but it has now been superceded by another element.
        '''
        pass

    def getStyle(self):
        return self.parent.getStyle()

    def getGUI(self):
        return self.parent.getGUI()

    def getByID(self, id):
        if id == self.id: return self
        for child in self.children:
            match = child.getByID(id)
            if match is not None: return match
        return None

    def calculateAbsoluteCoords(self, x, y):
        x += self._x; y += self._y
        return self.parent.calculateAbsoluteCoords(x, y)

    def calculateRelativeCoords(self, x, y):
        x -= self._x + self.padding; y -= self._y + self.padding
        return self.parent.calculateRelativeCoords(x, y)

    def reparent(self, new_parent):
        x, y = self.parent.calculateAbsoluteCoords(self._x, self._y)
        self._x, self._y = new_parent.calculateRelativeCoords(x, y)
        self.parent.children.remove(self)
        new_parent.children.append(self)
        self.parent = new_parent
        self.getGUI().setDirty()

    def replace(self, old, new):
        '''Replace the "old" widget with the "new" one.

        It is assumed that "new" is already a child of this element.
        '''
        self.children.remove(new)
        old_index = self.children.index(old)
        old.delete()
        self.children.insert(old_index, new)
        if hasattr(self, 'layout'):
            self.layout.layout()

    def clear(self):
        for child in list(self.children): child.delete()
        self.children = []

    def delete(self):
        gui = self.getGUI()
        # clear modality?
        if self.is_modal: gui.setModal(None)
        gui.dispatch_event(self, 'on_delete')
        self.parent.children.remove(self)
        gui.unregisterID(self)
        self.clear()

