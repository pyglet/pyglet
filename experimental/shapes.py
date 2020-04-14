import math

from pyglet.gl import GL_TRIANGLES, GL_TRIANGLE_FAN, GL_BLEND, GL_COLOR_BUFFER_BIT, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA
from pyglet.gl import glPushAttrib, glPopAttrib, glBlendFunc, glEnable
from pyglet.graphics import Group, Batch


class ShapeGroup(Group):
    """Shared Shape rendering Group."""

    def __init__(self, blend_src, blend_dest, parent=None):
        """Create a Shape group.

        The group is created internally. Usually you do not
        need to explicitly create it.

        :Parameters:
            `blend_src` : int
                OpenGL blend source mode; for example,
                ``GL_SRC_ALPHA``.
            `blend_dest` : int
                OpenGL blend destination mode; for example,
                ``GL_ONE_MINUS_SRC_ALPHA``.
            `parent` : `~pyglet.graphics.Group`
                Optional parent group.
        """
        super().__init__(parent)
        self.blend_src = blend_src
        self.blend_dest = blend_dest

    def set_state(self):
        glPushAttrib(GL_COLOR_BUFFER_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self):
        glPopAttrib()

    def __eq__(self, other):
        return (other.__class__ is self.__class__ and
                self.parent is other.parent and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self):
        return hash((id(self.parent), self.blend_src, self.blend_dest))


class _Shape:
    _rgb = (255, 255, 255)
    _opacity = 255
    _visible = True
    _x = 0
    _y = 0
    _anchor_x = 0
    _anchor_y = 0
    _batch = None
    _vertex_list = None

    def _update_position(self):
        raise NotImplementedError

    def _update_color(self):
        raise NotImplementedError

    def draw(self):
        self._vertex_list.draw(GL_TRIANGLES)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self._update_position()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self._update_position()

    @property
    def position(self):
        return self._x, self._y

    @position.setter
    def position(self, values):
        self._x, self._y = values
        self._update_position()

    @property
    def anchor_x(self):
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, value):
        self._anchor_x = value
        self._update_position()

    @property
    def anchor_y(self):
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, value):
        self._anchor_y = value
        self._update_position()

    @property
    def anchor_position(self):
        return self._anchor_x, self._anchor_y

    @anchor_position.setter
    def anchor_position(self, values):
        self._anchor_x, self._anchor_y = values
        self._update_position()

    @property
    def color(self):
        """Shape color.

        This property sets the color of the Shape's color.

        The color is specified as an RGB tuple of integers '(red, green, blue)'.
        Each color component must be in the range 0 (dark) to 255 (saturated).

        :type: (int, int, int)
        """
        return self._rgb

    @color.setter
    def color(self, values):
        self._rgb = list(map(int, values))
        self._update_color()

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self._update_color()

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value
        self._update_position()


class Rectangle(_Shape):
    def __init__(self, x, y, width, height, color=(255, 255, 255), batch=None, group=None):
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._rotation = 0
        self._rgb = color

        self._batch = batch or Batch()
        self._group = ShapeGroup(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, group)
        self._vertex_list = self._batch.add(6, GL_TRIANGLES, self._group, 'v2f', 'c4B')
        self._update_position()
        self._update_color()

    def _update_position(self):
        if not self._visible:
            vertices = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        elif self._rotation:
            x1 = -self._anchor_x
            y1 = -self._anchor_y
            x2 = x1 + self._width
            y2 = y1 + self._height
            x = self._x
            y = self._y

            r = -math.radians(self._rotation)
            cr = math.cos(r)
            sr = math.sin(r)
            ax = x1 * cr - y1 * sr + x
            ay = x1 * sr + y1 * cr + y
            bx = x2 * cr - y1 * sr + x
            by = x2 * sr + y1 * cr + y
            cx = x2 * cr - y2 * sr + x
            cy = x2 * sr + y2 * cr + y
            dx = x1 * cr - y2 * sr + x
            dy = x1 * sr + y2 * cr + y
            vertices = (ax, ay, bx, by, cx, cy, ax, ay, cx, cy, dx, dy)
        else:
            x1 = self._x - self._anchor_x
            y1 = self._y - self._anchor_y
            x2 = x1 + self._width
            y2 = y1 + self._height
            vertices = (x1, y1, x2, y1, x2, y2, x1, y1, x2, y2, x1, y2)

        self._vertex_list.vertices[:] = vertices

    def _update_color(self):
        self._vertex_list.colors[:] = [*self._rgb, int(self._opacity)] * 6

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self._update_position()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = value
        self._update_position()

    @property
    def rotation(self):
        """Clockwise rotation of the Rectangle, in degrees.

        The Rectangle will be rotated about its (anchor_x, anchor_y)
        position.

        :type: float
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation
        self._update_position()


class Circle(_Shape):
    def __init__(self, x, y, radius, segments=25, color=(255, 255, 255), batch=None, group=None):
        self._x = x
        self._y = y
        self._radius = radius
        self._segments = segments
        self._rgb = color

        self._batch = batch or Batch()
        self._group = ShapeGroup(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, group)

        self._vertex_list = self._batch.add(self._segments*3, GL_TRIANGLES, self._group, 'v2f', 'c4B')
        self._update_position()
        self._update_color()

    def _update_position(self):
        if not self._visible:
            vertices = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        else:
            x = self._x + self._anchor_x
            y = self._y + self._anchor_y
            r = self._radius
            tau_segs = math.pi * 2 / self._segments

            # Calcuate the outer points of the circle:
            points = [(x + (r * math.cos(i * tau_segs)),
                       y + (r * math.sin(i * tau_segs))) for i in range(self._segments)]

            # Create a list of trianges from the points:
            vertices = []
            for i, point in enumerate(points):
                triangle = x, y, *points[i-1], *point
                vertices.extend(triangle)

        self._vertex_list.vertices[:] = vertices

    def _update_color(self):
        self._vertex_list.colors[:] = [*self._rgb, int(self._opacity)] * self._segments * 3
