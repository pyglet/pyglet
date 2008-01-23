import operator

from pyglet import gl, event

import spryte
import tilemap

class View(object):
    '''Render a flat view of a scene2d.Scene.

    Attributes:

        scene           -- a scene2d.Scene instance
        allow_oob       -- indicates whether the viewport will allow
                           viewing of out-of-bounds tile positions (ie.
                           for which there is no tile image). If set to
                           False then the map will not scroll to attempt
                           to display oob tiles.
        fx, fy | focus  -- pixel point to center in the viewport, subject
                           to OOB checks
    '''
    def __init__(self, x, y, width, height, allow_oob=False,
            fx=0, fy=0, layers=None, near=-50, far=50):
        super(View, self).__init__()
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.near, self.far = near, far
        self.allow_oob = allow_oob
        self.fx, self.fy = fx, fy
        if layers is None:
            self.layers = []
        else:
            self.layers = layers
            for layer in layers:
                if not hasattr(layer, 'z'): layer.z = 0
            self.layers.sort(key=operator.attrgetter('z'))

    def on_resize(self, width, height):
        self.width, self.height = width, height
        return event.EVENT_UNHANDLED

    @classmethod
    def for_window(cls, window, **kw):
        '''Create a view which is the same dimensions as the supplied
        window.'''
        return cls(0, 0, window.width, window.height, **kw)

    def __repr__(self):
        return '<%s object at 0x%x focus=(%d,%d) oob=%s>'%(
            self.__class__.__name__, id(self), self.fx, self.fy,
            self.allow_oob)

    #
    # QUERY INTERFACE
    #
    def translate_position(self, x, y):
        '''Translate the on-screen pixel position to a scene pixel
        position.'''
        fx, fy = self._determine_focus()
        ox, oy = self.width/2-fx, self.height/2-fy
        return (int(x - ox), int(y - oy))

    def get(self, x, y):
        ''' Pick whatever is on the top at the position x, y. '''
        r = []

        for layer in self.layers:
            cell = layer.get(x, y)
            if cell:
                r.append(cell)

        return r

    def add_layer(self, layer, z):
        layer.z = z
        self.layers.append(layer)

    def remove_layer(self, layer):
        self.layers.remove(layer)

    def get_layer(self, z):
        '''Get a layer for the specified Z depth, adding it if necessary.
        '''
        for layer in self.layers:
            if layer.z == z:
                break
        else:
            layer = spryte.SpriteBatch()
            layer.z = z
            self.layers.append(layer)
            self.layers.sort(key=operator.attrgetter('z'))
        return layer

    def add_sprite(self, im, x, y, z=0, klass=spryte.Sprite, **kw):
        layer = self.get_layer(z)
        return klass(im, x, y, batch=layer, **kw)

    def add_map(self, im, cells, z=0, **kw):
        map = tilemap.Map.from_imagegrid(im, cells, **kw)
        map.z = z
        self.layers.append(map)
        self.layers.sort(key=operator.attrgetter('z'))
        return map

    def cell_at(self, x, y):
        ' query for a map cell at given screen pixel position '
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
            # XXX isinstance Map instead?
            if hasattr(layer, 'pixel_width'):
                bounded.append(layer)
        if not bounded:
            return (fx, fy)

        # figure the bounds min/max
        m = bounded[0]
        b_min_x = m.x
        b_min_y = m.y
        b_max_x = m.x + m.pixel_width
        b_max_y = m.y + m.pixel_height
        for m in bounded[1:]:
            b_min_x = min(b_min_x, m.x)
            b_min_y = min(b_min_y, m.y)
            b_max_x = min(b_max_x, m.x + m.pixel_width)
            b_max_y = min(b_max_y, m.y + m.pixel_height)

        # figure the view min/max based on focus
        w2 = self.width/2
        h2 = self.height/2

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


    def set_focus(self, value):
        self.fx, self.fy = value
    focus = property(lambda self: (self.fx, self.fy), set_focus)


    def draw(self):
        # set up projection
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glViewport(self.x, self.y, self.width, self.height)
        gl.glOrtho(0, self.width, 0, self.height, self.near, self.far)
        gl.glMatrixMode(gl.GL_MODELVIEW)

        fx, fy = self._determine_focus()

        w2 = self.width/2
        h2 = self.height/2
        x1, y1 = fx - w2, fy - h2
        x2, y2 = fx + w2, fy + h2

        gl.glPushMatrix()
        gl.glTranslatef(self.width/2-fx, self.height/2-fy, 0)
        for layer in self.layers:
            if hasattr(layer, 'x'):
                translate = layer.x or layer.y
            else:
                translate = False
            if translate:
                gl.glPushMatrix()
                gl.glTranslatef(layer.x, layer.y, 0)
            layer.draw()
            if translate:
                gl.glPopMatrix()
        gl.glPopMatrix()
 
