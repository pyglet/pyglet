#!/usr/bin/env python

'''
View code for displaying 2d scenes of maps and sprites
======================================================

---------------
Getting Started
---------------

Creating a simple scene and displaying it:

    >>> import pyglet.window
    >>> import scene2d
    >>> m = scene2d.RectMap(32, 32, cells=gen_rect_map([[0]*4]*4, 32, 32)
    >>> w = pyglet.window.Window(width=m.pxw, height=m.pxh)
    >>> v = scene2d.FlatView.from_window(s, w, layers=[m])
    >>> v.debug((0,0))
    >>> w.flip()

------------------
Events and Picking
------------------

The following are examples of attaching event handlers to Views::

    @event(view)
    def on_mouse_enter(objects, x, y):
        """ The mouse is hovering at map pixel position (x,y) over the
            indicated objects (cells or sprites)."""
           
    @event(view)
    def on_mouse_leave(objects):
        ' The mouse has stopped hovering over the indicated objects.'
               
    @event(view)
    def on_mouse_press(objects, x, y, button, modifiers):
        ' The mouse has been clicked on the indicated objects. '

The filters available in scene2d.events module may be used to
limit the cells or sprites for which events are generated.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import operator

from pyglet.event import EventDispatcher, EVENT_UNHANDLED
from scene2d.camera import FlatCamera
from scene2d.drawable import draw_many
from scene2d.map import Map
from scene2d.sprite import SpriteLayer
from pyglet.gl import *

class View(EventDispatcher):

    def get(self, x, y):
        ''' Pick whatever is on the top at the pixel position x, y. '''
        raise NotImplemented()

    def tile_at(self, (x, y)):
        ' query for tile at given screen pixel position '
        raise NotImplemented()
 
    def sprite_at(self, (x, y)):
        ' query for sprite at given screen pixel position '
        raise NotImplemented()

EVENT_MOUSE_DRAG = View.register_event_type('on_mouse_drag')
EVENT_MOUSE_PRESS = View.register_event_type('on_mouse_press')
EVENT_MOUSE_RELEASE = View.register_event_type('on_mouse_release')
EVENT_MOUSE_ENTER = View.register_event_type('on_mouse_enter')
EVENT_MOUSE_LEAVE = View.register_event_type('on_mouse_leave')

class FlatView(View):
    '''Render a flat view of a scene2d.Scene.

    Attributes:

        scene           -- a scene2d.Scene instance
        camera          -- a scene2d.FlatCamera instance
        allow_oob       -- indicates whether the viewport will allow
                           viewing of out-of-bounds tile positions (ie.
                           for which there is no tile image). If set to
                           False then the map will not scroll to attempt
                           to display oob tiles.
        fx, fy          -- pixel point to center in the viewport, subject
                           to OOB checks
    '''
    def __init__(self, x, y, width, height, allow_oob=False,
            fx=0, fy=0, layers=None, sprites=None):
        super(View, self).__init__()
        self.camera = FlatCamera(x, y, width, height)
        self.allow_oob = allow_oob
        self.fx, self.fy = fx, fy
        if layers is None:
            self.layers = []
        else:
            self.layers = layers
        if sprites is None:
            self.sprites = []
        else:
            self.sprites = sprites

    @classmethod
    def from_window(cls, window, **kw):
        '''Create a view which is the same dimensions as the supplied
        window.'''
        return cls(0, 0, window.width, window.height, **kw)

    def __repr__(self):
        return '<%s object at 0x%x focus=(%d,%d) oob=%s>'%(
            self.__class__.__name__, id(self), self.fx, self.fy,
            self.allow_oob)

    #
    # EVENT HANDLING
    #
    _mouse_in_objs = set()
    def dispatch_event(self, x, y, event_type, *args):
        ''' if a handler has a limit attached then use that to filter objs
        '''

        # now fire the handler
        for frame in self._event_stack:
            handler = frame.get(event_type, None)
            if not handler: continue

            # XXX don't do this for every handler?
            objs = []

            # maps to pass to the handler
            if hasattr(handler, 'map_filters') and \
                    handler.map_filters is not None:
                for mf in handler.map_filters:
                    l = []
                    for map in mf.maps:
                        cell = map.get(x, y)
                        if cell:
                            l.append(cell)
                    objs.extend((map.z, mf(l)))
            else:
                for layer in self.layers:
                    if not isinstance(layer, Map): continue
                    cell = layer.get(x, y)
                    if cell:
                        objs.append((layer.z, cell))

            # sprites to pass to the handler
            if hasattr(handler, 'sprite_filters') and \
                    handler.sprite_filters is not None:
                for sf in handler.sprite_filters:
                    l = []
                    for sprite in sf.sprites:
                        if sprite.contains(x, y):
                            l.append((sprite.z, sprite))
                    objs.extend(sf(l))
            else:
                for layer in self.layers:
                    if not isinstance(layer, SpriteLayer): continue
                    for sprite in layer.sprites:
                        if sprite.contains(x, y):
                            objs.append((layer.z, sprite))
                for sprite in self.sprites:
                    if sprite.contains(x, y):
                        # un-layered sprites are at depth 0
                        objs.append((0, sprite))

            # sort by depth
            objs.sort()
            l = [obj for o, obj in objs]

            # highest to lowest
            l.reverse()

            # now gen events
            if event_type is EVENT_MOUSE_ENTER:
                active = set(l)
                l = active - self._mouse_in_objs
                if not l: continue
                self._mouse_in_objs = self._mouse_in_objs | l
                l = list(l)
            elif event_type is EVENT_MOUSE_LEAVE:
                active = set(l)
                l = self._mouse_in_objs - active
                if not l: continue
                self._mouse_in_objs = self._mouse_in_objs - l
                l = list(l)
            else:
                if not l: continue

            ret = handler(l, *args)

            if ret != EVENT_UNHANDLED:
                break
        return None

    def on_mouse_press(self, x, y, button, modifiers):
        x, y = self.translate_position(x, y)
        self.dispatch_event(x, y, EVENT_MOUSE_PRESS, x, y, button, modifiers)
        return EVENT_UNHANDLED

    def on_mouse_release(self, x, y, button, modifiers):
        x, y = self.translate_position(x, y)
        self.dispatch_event(x, y, EVENT_MOUSE_RELEASE, x, y, button, modifiers)
        return EVENT_UNHANDLED

    def on_mouse_motion(self, x, y, dx, dy):
        x, y = self.translate_position(x, y)
        self.dispatch_event(x, y, EVENT_MOUSE_LEAVE)
        self.dispatch_event(x, y, EVENT_MOUSE_ENTER)
        return EVENT_UNHANDLED

    def on_mouse_enter(self, x, y):
        x, y = self.translate_position(x, y)
        self.dispatch_event(x, y, EVENT_MOUSE_ENTER)
        return EVENT_UNHANDLED

    def on_mouse_leave(self, x, y):
        x, y = self.translate_position(x, y)
        self.dispatch_event(x, y, EVENT_MOUSE_LEAVE)
        return EVENT_UNHANDLED

    #
    # QUERY INTERFACE
    #
    def translate_position(self, x, y):
        '''Translate the on-screen pixel position to a scene pixel
        position.'''
        fx, fy = self._determine_focus()
        ox, oy = self.camera.width/2-fx, self.camera.height/2-fy
        return (int(x - ox), int(y - oy))

    def get(self, x, y):
        ''' Pick whatever is on the top at the position x, y. '''
        r = []

        for sprite in self.sprites:
            if sprite.contains(x, y):
                r.append(sprite)

        self.layers.sort(key=operator.attrgetter('z'))
        for layer in self.layers:
            cell = layer.get(x, y)
            if cell:
                r.append(cell)

        return r

    def tile_at(self, x, y):
        ' query for tile at given screen pixel position '
        raise NotImplemented()
 
    def sprite_at(self, x, y):
        ' query for sprite at given screen pixel position '
        raise NotImplemented()

    #
    # FOCUS ADJUSTMENT
    #
    def _determine_focus(self):
        '''Determine the focal point of the view based on foxus (fx, fy),
        allow_oob and maps.

        Note that this method does not actually change the focus attributes
        fx and fy.
        '''
        # enforce int-only positioning of focus
        fx = int(self.fx)
        fy = int(self.fy)

        
        if self.allow_oob: return (fx, fy)

        # check that any layer has bounds
        bounded = []
        for layer in self.layers:
            if hasattr(layer, 'pxw'):
                bounded.append(layer)
        if not bounded:
            return (fx, fy)


        # figure the bounds min/max
        m = bounded[0]
        b_min_x = m.x
        b_min_y = m.y
        b_max_x = m.x + m.pxw
        b_max_y = m.y + m.pxh
        for m in bounded[1:]:
            b_min_x = min(b_min_x, m.x)
            b_min_y = min(b_min_y, m.y)
            b_max_x = min(b_max_x, m.x + m.pxw)
            b_max_y = min(b_max_y, m.y + m.pxh)

        # figure the view min/max based on focus
        w2 = self.camera.width/2
        h2 = self.camera.height/2

        v_min_x = fx - w2
        v_min_y = fy - h2
        x_moved = y_moved = False
        if v_min_x < b_min_x:
            fx += b_min_x - v_min_x
            x_moved = True
        if v_min_y < b_min_y:
            fy += b_min_y - v_min_y
            y_moved = True

        v_max_x = fx + w2
        v_max_y = fy + h2
        if not x_moved and v_max_x > b_max_x:
            fx -= v_max_x - b_max_x
        if not y_moved and v_max_y > b_max_y:
            fy -= v_max_y - b_max_y

        return map(int, (fx, fy))


    #
    # RENDERING
    #
    def clear(self, colour=None, is_window=True):
        '''Clear the view.

        If colour is None then the current glColor (is_window == False)
        or glClearColor (is_window == True) is used.

        If the view is not the whole window then you should pass
        is_window=False otherwise the whole window will be cleared.
        '''
        if is_window:
            if colour is not None:
                glClearColor(*colour)
            glClear(GL_COLOR_BUFFER_BIT)
        else:
            if colour is not None:
                glColor(*colour)
            glBegin(GL_QUADS)
            glVertex2f(0, 0)
            glVertex2f(0, self.camera.height)
            glVertex2f(self.camera.width, self.camera.height)
            glVertex2f(self.camera.width, 0)
            glEnd()


    def draw(self):
        '''Draw the view centered (or closest, depending on allow_oob)
        on position which is (x, y). '''
        self.camera.project()

        # sort by depth
        self.layers.sort(key=operator.attrgetter('z'))

        # determine the focus point
        fx, fy = self._determine_focus()

        w2 = self.camera.width/2
        h2 = self.camera.height/2
        x1, y1 = fx - w2, fy - h2
        x2, y2 = fx + w2, fy + h2

        # now draw
        glPushMatrix()
        glTranslatef(self.camera.width/2-fx, self.camera.height/2-fy, 0)

        for layer in self.layers:
            if hasattr(layer, 'x'):
                translate = layer.x or layer.y or layer.z
            else:
                translate = False
            if translate:
                glPushMatrix()
                glTranslatef(layer.x, layer.y, layer.z)
            draw_many(layer.get_in_region(x1, y1, x2, y2))
            if translate:
                glPopMatrix()

        if self.sprites:
            draw_many(self.sprites)

        glPopMatrix()
 

class ViewScrollHandler(object):
    '''Scroll the view in response to the mouse scroll wheel.
    '''
    def __init__(self, view):
        self.view = view

    def on_mouse_scroll(self, x, y, dx, dy):
        fx, fy = self.view._determine_focus()
        self.view.fx = fx + dx * 30
        self.view.fy = fy + dy * 30

