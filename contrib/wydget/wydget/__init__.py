'''wydget is a graphical user interface (GUI) toolkit for pyglet.

This module allows applications to create a user interface comprised of
widgets and attach event handling to those widgets.

GUIs are managed by the top-level GUI class::
 
    from pyglet.window import Window
    from wydget import GUI
    window = Window(100, 100)
    gui = GUI(window)
    window.push_handlers(gui)

You may then add components to the GUI by importing them from the
`wydget.widgets` package::

    from wydget.widgets import TextButton
    b = TextButton(gui, 'Press me!')

To handle click events on the button, create a handler::

    @gui.select(b)
    def on_click(button, *args):
        print 'I was pressed!'

Finally, use a standard pyglet event loop to have the GUI run, and invoke
``gui.draw()`` to render the GUI. The GUI will render to an area the
dimensions of the window and at z = 0::

    while not window.has_exit:
        window.dispatch_events()
        window.clear()
        gui.draw()
        window.flip()
'''

import sys
from xml.etree import ElementTree

from pyglet.gl import *
from pyglet import media

import style
import event
import loadxml
import widgets

class GUI(event.GUIEventDispatcher):
    '''GUI oganisation and event handling.
    '''
    id = '-gui'
    name = 'gui'
    classes = ()
    parent = None

    def __init__(self, window, x=0, y=0, z=0, width=None, height=None):
        super(GUI, self).__init__()
        self.window = window
        self.style = style.Style()

        # element.Element stuff
        self.x, self.y, self.z = x, y, z
        self.width = width or window.width
        self.width_spec = width
        self.height = height or window.height
        self.height_spec = height
        self.children = []

        # map Element.id to Element
        self._by_id = {}

        # list Element.ids in the order they're registered for tabbing
        self._focus_order = []

        self.debug_display = None
        self.debug = '--debug' in sys.argv
        if self.debug:
            self.debug_display = widgets.Label(self, 'dummy',
                bgcolor="white", padding=1, width=self.width)

    def __repr__(self):
        return '<%s at (%s, %s, %s) (%sx%s)>'%(self.__class__.__name__,
            self.x, self.y, self.z, self.width, self.height)

    @classmethod
    def fromXML(cls, window, file, **kw):
        '''Load a GUI from the file or filename.

        See `doc/xml-format.txt` for more information.
        '''
        gui = cls(window, **kw)
        loadxml.load_xml(gui, file)
        return gui

    def dump(self, s=''):
        print s + str(self)
        for child in self.children: child.dump(s+' ')


    # clipboard support
    clipboard_element = None
    def setSelection(self, element):
        '''The element has some data that may interact with the clipboard.
        '''
        if self.clipboard_element not in (element, None):
            self.clipboard_element.clearSelection()
        self.clipboard_element = element

    def clearSelection(self, element):
        '''The element doesn't want to interact with the clipboard any
        longer.
        '''
        # might already have been bumped for another
        if self.clipboard_element is element:
            self.clipoard_element = None


    # Management by Element ID
    # XXX remove "ID" from API?
    def registerID(self, element):
        if element.id in self._by_id:
            raise KeyError, 'ID %r already exists as %r (trying to add %r)'%(
                element.id, self._by_id[element.id], element)
        self._by_id[element.id] = element
        if element.is_focusable:
            self._focus_order.append(element.id)
        self.setDirty()
    def unregisterID(self, element):
        del self._by_id[element.id]
        if self.focused_element is element:
            self.focused_element = None
        if element.is_focusable:
            self._focus_order.remove(element.id)
        self.setDirty()
    def hasID(self, id):
        return id in self._by_id
    def getByID(self, id):
        return self._by_id[id]


    # rendering / hit detection
    _rects = None
    def setDirty(self):
        '''Indicate that one or more of the gui's children have changed
        geometry and a new set of child rects is needed.
        '''
        self._rects = None

    def getRects(self, exclude=None):
        '''Get the rects for all the children to draw & interact with.

        Prune the tree at "exclude" if provided.
        '''
        if self._rects is not None and exclude is None:
            return self._rects

        rects = []
        clip = self.rect
        for element in self.children:
            if element is exclude: continue
            rects.extend(element.getRects(clip, exclude))
        rects.sort(lambda a,b: cmp(a[1][2], b[1][2]))
        if exclude is None:
            self._rects = rects
        return rects

    def determineHit(self, x, y, exclude=None):
        '''Determine which element is at the absolute (x, y) position.

        "exclude" allows us to ignore a single element (eg. an element
        under the cursor being dragged - we wish to know which element is
        under *that)
        '''
        for o, (ox, oy, oz, sx, sy, clip) in reversed(self.getRects(exclude)):
            ox += clip.x
            oy += clip.y
            if x < ox or y < oy: continue
            if x > ox + clip.width: continue
            if y > oy + clip.height: continue
            return o
        return None

    def draw(self):
        '''Render all the elements on display.'''
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_DEPTH_TEST)

        # get the rects and sort by Z (yay for stable sort!)
        rects = self.getRects()

        # draw
        oz = 0
        for element, (x, y, z, sx, sy, c) in rects:
            if element is self.debug_display:
                continue
            element.draw(x, y, z, sx, sy, c)

        if self.debug:
            # render the debugging displays

            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_BLEND)
            for o, (x, y, z, sx, sy, c) in rects:
                w, h = c.width, c.height
                x += c.x
                y += c.y
                glColor4f(1, 0, 0, .1)
                glRectf(x, y, x+w, y+h)
                glColor4f(1, 1, 1, .1)
                glBegin(GL_LINE_LOOP)
                glVertex2f(x, y)
                glVertex2f(x+w, y)
                glVertex2f(x+w, y+h)
                glVertex2f(x, y+h)
                glEnd()

                if o.view_clip:
                    v = o.view_clip
                    glColor4f(0, 0, 1, .1)
                    glRectf(x+v.x, y+v.y, x+v.x+v.width, y+v.y+v.height)

            glDisable(GL_BLEND)
            self.debug_display.draw(0, 0, 0, 1, 1, util.Rect(0, 0,
                self.width, self.debug_display.height))

        glPopAttrib()


    # Element API (mostly terminators)
    def getStyle(self): return self.style
    def getGUI(self): return self
    def isEnabled(self): return True
    def isVisible(self): return True

    def getParent(self, selector):
        if selector == self.name: return self
        return None

    def calculateAbsoluteCoords(self, x, y):
        return (x + self.x, y + self.y)

    def calculateRelativeCoords(self, x, y):
        return (x - self.x, y - self.y)
    
    def layoutDimensionsChanged(self, layout):
        pass

    def get_rect(self):
        return util.Rect(0, 0, self.width, self.height)
    rect = property(get_rect)
    inner_rect = property(get_rect)

    def addChild(self, child):
        self.children.append(child)
        self.registerID(child)

    def delete(self):
        for child in self.children: child.delete()
        self.children = []

