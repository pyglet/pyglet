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
        self.height = height or window.height
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

    def setModal(self, element):
        '''The element will capture all input.

        setModal(None) to clear.
        '''
        if element is None:
            for child in self.children:
                child.is_enabled = True
        else:
            found = False
            for child in self.children:
                if child is not element:
                    child.is_enabled = False
                else:
                    found = True
            assert found, '%r not found in gui children'%(element,)

    def dump(self, s=''):
        print s + str(self)
        for child in self.children: child.dump(s+' ')

    def delete(self):
        for child in self.children: child.delete()
        self.children = []

    # XXX alter to be registerElement
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
    def getByID(self, id):
        for child in self.children:
            match = child.getByID(id)
            if match is not None: return match
        raise KeyError, id

    def addChild(self, child):
        self.children.append(child)
        self.registerID(child)
    def deleteChild(self, child):
        child.delete()
        self.children.remove(child)

    def focusNextElement(self, direction=1):
        '''Move the focus on to the next element.
        '''
        if not self._focus_order: return
        N = len(self._focus_order)
        if self.focused_element is None:
            if direction == 1: i = 0
            else: i = N-1
        else:
            try:
                i = self._focus_order.index(self.focused_element.id) + direction
            except ValueError:
                # element not in the focus order list
                i = 0
            if i < 0: i = N-1
            if i >= N: i = 0
        j = i
        while 1:
            element = self._by_id[self._focus_order[i]]
            if element.isEnabled() and self.isVisible():
                self.setFocus(element)
                return
            i += direction
            if i < 0: i = N-1
            if i >= N: i = 0
            if i == j: return       # no focusable element found

    # Element API terminators
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

    def draw(self):
        '''Render all the elements on display.'''
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_DEPTH_TEST)

        view_clip = None #self.rect
        for element in self.children:
            if element is self.debug_display: continue
            element.draw(view_clip)

        if self.debug:

            # render the debugging displays
            self.debug_display.draw()

            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_BLEND)
            for o, (x, y, z, w, h) in self.getRects(view_clip):
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

        glPopAttrib()

