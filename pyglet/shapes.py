"""2D shapes.

This module provides classes for a variety of simplistic 2D shapes,
such as Rectangles, Circles, and Lines. These shapes are made
internally from OpenGL primitives, and provide excellent performance
when drawn as part of a :py:class:`~pyglet.graphics.Batch`.
Convenience methods are provided for positioning, changing color
and opacity, and rotation (where applicable). To create more
complex shapes than what is provided here, the lower level
graphics API is more appropriate.
See the :ref:`guide_graphics` for more details.

A simple example of drawing shapes::

    import pyglet
    from pyglet import shapes

    window = pyglet.window.Window(960, 540)
    batch = pyglet.graphics.Batch()

    circle = shapes.Circle(700, 150, 100, color=(50, 225, 30), batch=batch)
    square = shapes.Rectangle(200, 200, 200, 200, color=(55, 55, 255), batch=batch)
    rectangle = shapes.Rectangle(250, 300, 400, 200, color=(255, 22, 20), batch=batch)
    rectangle.opacity = 128
    rectangle.rotation = 33
    line = shapes.Line(100, 100, 100, 200, width=19, batch=batch)
    line2 = shapes.Line(150, 150, 444, 111, width=4, color=(200, 20, 20), batch=batch)
    star = shapes.Star(800, 400, 60, 40, num_spikes=20, color=(255, 255, 0), batch=batch)

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    pyglet.app.run()


.. note:: Some Shapes, such as Lines and Triangles, have multiple coordinates.
          If you update the x, y coordinate, this will also affect the secondary
          coordinates. This allows you to move the shape without affecting it's
          overall dimensions.

.. versionadded:: 1.5.4
"""

import math

from abc import ABC, abstractmethod
from __future__ import annotations

import pyglet

from pyglet.gl import GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA
from pyglet.gl import GL_TRIANGLES, GL_LINES, GL_BLEND
from pyglet.gl import glBlendFunc, glEnable, glDisable
from pyglet.graphics import Batch, Group


vertex_source = """#version 150 core
    in vec2 position;
    in vec2 translation;
    in vec4 colors;
    in float rotation;


    out vec4 vertex_colors;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    mat4 m_rotation = mat4(1.0);
    mat4 m_translate = mat4(1.0);

    void main()
    {
        m_translate[3][0] = translation.x;
        m_translate[3][1] = translation.y;
        m_rotation[0][0] =  cos(-radians(rotation));
        m_rotation[0][1] =  sin(-radians(rotation));
        m_rotation[1][0] = -sin(-radians(rotation));
        m_rotation[1][1] =  cos(-radians(rotation));

        gl_Position = window.projection * window.view * m_translate * m_rotation * vec4(position, 0.0, 1.0);
        vertex_colors = colors;
    }
"""

fragment_source = """#version 150 core
    in vec4 vertex_colors;
    out vec4 final_color;

    void main()
    {
        final_color = vertex_colors;
    }
"""


def get_default_shader():
    try:
        return pyglet.gl.current_context.pyglet_shapes_default_shader
    except AttributeError:
        _default_vert_shader = pyglet.graphics.shader.Shader(vertex_source, 'vertex')
        _default_frag_shader = pyglet.graphics.shader.Shader(fragment_source, 'fragment')
        default_shader_program = pyglet.graphics.shader.ShaderProgram(_default_vert_shader, _default_frag_shader)
        pyglet.gl.current_context.pyglet_shapes_default_shader = default_shader_program
        return default_shader_program


class _ShapeGroup(Group):
    """Shared Shape rendering Group.

    The group is automatically coalesced with other shape groups
    sharing the same parent group and blend parameters.
    """

    def __init__(self, blend_src, blend_dest, program, parent=None) -> None:
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
            `program` : `~pyglet.graphics.shader.ShaderProgram`
                The ShaderProgram to use.
            `parent` : `~pyglet.graphics.Group`
                Optional parent group.
        """
        super().__init__(parent=parent)
        self.program = program
        self.blend_src = blend_src
        self.blend_dest = blend_dest

    def set_state(self) -> None:
        self.program.bind()
        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self) -> None:
        glDisable(GL_BLEND)
        self.program.unbind()

    def __eq__(self, other) -> bool:
        return (other.__class__ is self.__class__ and
                self.program == other.program and
                self.parent == other.parent and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self) -> int:
        return hash((self.program, self.parent, self.blend_src, self.blend_dest))


class ShapeBase(ABC):
    """Base class for all shape objects.

    A number of default shapes are provided in this module. Curves are
    approximated using multiple vertices.

    If you need shapes or functionality not provided in this module,
    you can write your own custom subclass of `ShapeBase` by using
    the provided shapes as reference.
    """

    _rgba = (255, 255, 255, 255)
    _visible = True
    _x = 0
    _y = 0
    _anchor_x = 0
    _anchor_y = 0
    _batch = None
    _group = None
    _num_verts = 0
    _vertex_list = None
    _draw_mode = GL_TRIANGLES
    group_class = _ShapeGroup

    def __del__(self):
        if self._vertex_list is not None:
            self._vertex_list.delete()

    def _update_color(self) -> None:
        """Send the new colors for each vertex to the GPU.

        This method must set the contents of `self._vertex_list.colors`
        using a list or tuple that contains the RGBA color components
        for each vertex in the shape. This is usually done by repeating
        `self._rgba` for each vertex.
        """
        self._vertex_list.colors[:] = self._rgba * self._num_verts

    def _update_translation(self) -> None:
        self._vertex_list.translation[:] = (self._x, self._y) * self._num_verts

    def _create_vertex_list(self) -> None:
        """Build internal vertex list.

        This method must create a vertex list and assign it to
        `self._vertex_list`. It is advisable to use it
        during `__init__` and to then update the vertices accordingly
        with `self._update_vertices`.

        While it is not mandatory to implement it, some properties (
        namely `batch` and `group`) rely on this method to properly
        recreate the vertex list.
        """
        raise NotImplementedError('_create_vertex_list must be defined in '
                                  'order to use group or batch properties')

    @abstractmethod
    def _update_vertices(self) -> None:
        """
        Generate up-to-date vertex positions & send them to the GPU.

        This method must set the contents of `self._vertex_list.vertices`
        using a list or tuple that contains the new vertex coordinates for
        each vertex in the shape. See the `ShapeBase` subclasses in this
        module for examples of how to do this.
        """
        raise NotImplementedError("_update_vertices must be defined"
                                  "for every ShapeBase subclass")

    def draw(self) -> None:
        """Draw the shape at its current position.

        Using this method is not recommended. Instead, add the
        shape to a `pyglet.graphics.Batch` for efficient rendering.
        """
        self._group.set_state_recursive()
        self._vertex_list.draw(self._draw_mode)
        self._group.unset_state_recursive()

    def delete(self) -> None:
        """Force immediate removal of the shape from video memory.

        It is recommended to call this whenever you delete a shape,
        as the Python garbage collector will not necessarily call the
        finalizer as soon as the sprite falls out of scope.
        """
        self._vertex_list.delete()
        self._vertex_list = None

    @property
    def x(self) -> Union[int, float]:
        """X coordinate of the shape.

        :type: int or float
        """
        return self._x

    @x.setter
    def x(self, value: Union[int, float]) -> None:
        self._x = value
        self._update_translation()

    @property
    def y(self) -> Union[int, float]:
        """Y coordinate of the shape.

        :type: int or float
        """
        return self._y

    @y.setter
    def y(self, value: Union[int, float]):
        self._y = value
        self._update_translation()

    @property
    def position(self) -> tuple:
        """The (x, y) coordinates of the shape, as a tuple.

        :Parameters:
            `x` : int or float
                X coordinate of the sprite.
            `y` : int or float
                Y coordinate of the sprite.
        """
        return self._x, self._y

    @position.setter
    def position(self, values:tuple) -> None:
        self._x, self._y = values
        self._update_translation()

    @property
    def anchor_x(self) -> Union[int, float]:
        """
        The X coordinate of the anchor point

        :rtype: int or float
        """
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, value: Union[int, float]):
        """Set the X coordinate of the anchor point"""
        self._anchor_x = value
        self._update_vertices()

    @property
    def anchor_y(self) -> Union[int, float]:
        """
        The Y coordinate of the anchor point

        :rtype: int or float
        """
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, value: Union[int, float]):
        """Set the Y coordinate of the anchor point"""
        self._anchor_y = value
        self._update_vertices()

    @property
    def anchor_position(self) -> tuple:
        """
        The (x, y) coordinates of the anchor point, as a tuple.

        :Parameters:
            `x` : int or float
                X coordinate of the anchor point.
            `y` : int or float
                Y coordinate of the anchor point.
        """
        return self._anchor_x, self._anchor_y

    @anchor_position.setter
    def anchor_position(self, values: tuple) -> None:
        self._anchor_x, self._anchor_y = values
        self._update_vertices()

    @property
    def color(self) -> tuple(int, int, int):
        """The shape color.

        This property sets the color of the shape.

        The color is specified as an RGB tuple of integers '(red, green, blue)'.
        Each color component must be in the range 0 (dark) to 255 (saturated).

        :type: (int, int, int)
        """
        return self._rgba

    @color.setter
    def color(self, values: tuple(int, int, int)) -> None:
        r, g, b, *a = values

        if a:
            self._rgba = r, g, b, a[0]
        else:
            self._rgba = r, g, b, self._rgba[3]

        self._update_color()

    @property
    def opacity(self) -> int:
        """
        Blend opacity.

        This property sets the alpha component of the color of the shape.
        With the default blend mode (see the constructor), this allows the
        shape to be drawn with fractional opacity, blending with the
        background.

        An opacity of 255 (the default) has no effect.  An opacity of 128
        will make the shape appear translucent.

        :type: int
        """
        return self._rgba[3]

    @opacity.setter
    def opacity(self, value: int) -> None:
        self._rgba = (*self._rgba[:3], value)
        self._update_color()

    @property
    def visible(self) -> bool:
        """True if the shape will be drawn.

        :type: bool
        """
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value
        self._update_vertices()

    @property
    def group(self) -> Group:
        """User assigned :class:`Group` object."""
        return self._group.parent

    @group.setter
    def group(self, group: Group) -> None:
        """Set the Group"""
        if self._group.parent == group:
            return
        self._group = self.group_class(self._group.blend_src,
                                  self._group.blend_dest,
                                  self._group.program,
                                  group)
        self._batch.migrate(self._vertex_list, self._draw_mode, self._group,
                            self._batch)

    @property
    def batch(self) -> Batch:
        """User assigned :class:`Batch` object."""
        return self._batch

    @batch.setter
    def batch(self, batch: Batch) -> Batch:
        """Set the Batch"""
        if self._batch == batch:
            return

        if batch is not None and self._batch is not None:
            self._batch.migrate(self._vertex_list, self._draw_mode, self._group, batch)
            self._batch = batch
        else:
            self._vertex_list.delete()
            self._batch = batch
            self._create_vertex_list()
            self._update_vertices()


class Arc(ShapeBase):
    _draw_mode = GL_LINES

    def __init__(self, x, y, radius, segments=None, angle=math.tau, start_angle=0,
                 closed=False, color=(255, 255, 255, 255), batch=None, group=None) -> None:
        """
        Create an Arc.

        The Arc's anchor point (x, y) defaults to its center.

        :Parameters:
            `x` : float
                X coordinate of the circle.
            `y` : float
                Y coordinate of the circle.
            `radius` : float
                The desired radius.
            `segments` : int
                You can optionally specify how many distinct line segments
                the arc should be made from. If not specified it will be
                automatically calculated using the formula:
                `max(14, int(radius / 1.25))`.
            `angle` : float
                The angle of the arc, in radians. Defaults to tau (pi * 2),
                which is a full circle.
            `start_angle` : float
                The start angle of the arc, in radians. Defaults to 0.
            `closed` : bool
                If True, the ends of the arc will be connected with a line.
                defaults to False.
            `color` : (int, int, int, int)
                The RGB or RGBA color of the arc, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having opacity of 255.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the circle to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the circle.
        """
        self._x = x
        self._y = y
        self._radius = radius
        self._segments = segments or max(14, int(radius / 1.25))
        self._num_verts = self._segments * 2 + (2 if closed else 0)

        # handle both 3 and 4 byte colors
        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        self._angle = angle
        self._start_angle = start_angle
        self._closed = closed
        self._rotation = 0

        self._batch = batch or Batch()
        program = get_default_shader()
        self._group = self.group_class(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, program, group)

        self._create_vertex_list()
        self._update_vertices()

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._group.program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _update_vertices(self) -> None:
        if not self._visible:
            vertices = (0,) * (self._segments + 1) * 4
        else:
            x = -self._anchor_x
            y = -self._anchor_y
            r = self._radius
            tau_segs = self._angle / self._segments
            start_angle = self._start_angle - math.radians(self._rotation)

            # Calculate the outer points of the arc:
            points = [(x + (r * math.cos((i * tau_segs) + start_angle)),
                       y + (r * math.sin((i * tau_segs) + start_angle))) for i in range(self._segments + 1)]

            # Create a list of doubled-up points from the points:
            vertices = []
            for i in range(len(points) - 1):
                line_points = *points[i], *points[i + 1]
                vertices.extend(line_points)

            if self._closed:
                chord_points = *points[-1], *points[0]
                vertices.extend(chord_points)

        self._vertex_list.position[:] = vertices

    @property
    def rotation(self) -> float:
        """Clockwise rotation of the arc, in degrees.

        The arc will be rotated about its (anchor_x, anchor_y)
        position.

        :rtype: float
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation) -> None:
        self._rotation = rotation
        self._vertex_list.rotation[:] = (rotation,) * self._num_verts

    @property
    def angle(self) -> float:
        """The angle of the arc.

        :type: float
        """
        return self._angle

    @angle.setter
    def angle(self, value) -> None:
        self._angle = value
        self._update_vertices()

    @property
    def start_angle(self) -> float:
        """The start angle of the arc.

        :rtype: float
        """
        return self._start_angle

    @start_angle.setter
    def start_angle(self, angle: float) -> None:
        self._start_angle = angle
        self._update_vertices()

    def draw(self) -> None:
        """Draw the shape at its current position.

        Using this method is not recommended. Instead, add the
        shape to a `pyglet.graphics.Batch` for efficient rendering.
        """
        self._vertex_list.draw(self._draw_mode)


class BezierCurve(ShapeBase):
    _draw_mode = GL_LINES

    def __init__(self, *points: [[int, int]], t: float=1.0, segments: int=100, color: tuple=(255, 255, 255, 255), batch: Batch=None, group: Group=None) -> None:
        """Create a Bézier curve.

        The curve's anchor point (x, y) defaults to its first control point.

        :Parameters:
            `points` : List[[int, int]]
                Control points of the curve.
            `t` : float
                Draw `100*t` percent of the curve. 0.5 means the curve
                is half drawn and 1.0 means draw the whole curve.
            `segments` : int
                You can optionally specify how many line segments the
                curve should be made from.
            `color` : (int, int, int, int)
                The RGB or RGBA color of the curve, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the curve to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the curve.
        """
        self._points = list(points)
        self._t = t
        self._segments = segments
        self._num_verts = self._segments * 2
        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        program = get_default_shader()
        self._batch = batch or Batch()
        self._group = self.group_class(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, program, group)

        self._create_vertex_list()
        self._update_vertices()

    def _make_curve(self, t) -> [int, int]:
        n = len(self._points) - 1
        p = [0, 0]
        for i in range(n + 1):
            m = math.comb(n, i) * (1 - t) ** (n - i) * t ** i
            p[0] += m * self._points[i][0]
            p[1] += m * self._points[i][1]
        return p

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._group.program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._points[0]) * self._num_verts))

    def _update_vertices(self) -> None:
        if not self._visible:
            vertices = (0,) * self._segments * 4
        else:
            x = -self._anchor_x
            y = -self._anchor_y

            # Calculate the points of the curve:
            points = [(x + self._make_curve(self._t * t / self._segments)[0],
                       y + self._make_curve(self._t * t / self._segments)[1]) for t in range(self._segments + 1)]
            trans_x, trans_y = points[0]
            trans_x += self._anchor_x
            trans_y += self._anchor_y
            coords = [[x - trans_x, y - trans_y] for x, y in points]

            # Create a list of doubled-up points from the points:
            vertices = []
            for i in range(len(coords) - 1):
                line_points = *coords[i], *coords[i + 1]
                vertices.extend(line_points)

        self._vertex_list.position[:] = vertices

    @property
    def points(self) -> [[int, int]]:
        """Control points of the curve.

        :rtype: List[[int, int]]
        """
        return self._points

    @points.setter
    def points(self, value: [[int, int]]) -> None:
        self._points = value
        self._update_vertices()

    @property
    def t(self) -> float:
        """Draw `100*t` percent of the curve.

        :rtype: float
        """
        return self._t

    @t.setter
    def t(self, value: float) -> None:
        self._t = value
        self._update_vertices()


class Circle(ShapeBase):
    def __init__(self, x: float, y: float, radius: float, segments: int=None, color: tuple=(255, 255, 255, 255),
                 batch: Batch=None, group: Group=None) -> None:
        """Create a circle.

        The circle's anchor point (x, y) defaults to the center of the circle.

        :Parameters:
            `x` : float
                X coordinate of the circle.
            `y` : float
                Y coordinate of the circle.
            `radius` : float
                The desired radius.
            `segments` : int
                You can optionally specify how many distinct triangles
                the circle should be made from. If not specified it will
                be automatically calculated using the formula:
                `max(14, int(radius / 1.25))`.
            `color` : (int, int, int, int)
                The RGB or RGBA color of the circle, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the circle to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the circle.
        """
        self._x = x
        self._y = y
        self._radius = radius
        self._segments = segments or max(14, int(radius / 1.25))
        self._num_verts = self._segments * 3
        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        program = get_default_shader()
        self._batch = batch or Batch()
        self._group = self.group_class(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, program, group)

        self._create_vertex_list()
        self._update_vertices()

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._group.program.vertex_list(
            self._segments*3, self._draw_mode, self._batch, self._group,
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _update_vertices(self) -> None:
        if not self._visible:
            vertices = (0,) * self._segments * 6
        else:
            x = -self._anchor_x
            y = -self._anchor_y
            r = self._radius
            tau_segs = math.pi * 2 / self._segments

            # Calculate the outer points of the circle:
            points = [(x + (r * math.cos(i * tau_segs)),
                       y + (r * math.sin(i * tau_segs))) for i in range(self._segments)]

            # Create a list of triangles from the points:
            vertices = []
            for i, point in enumerate(points):
                triangle = x, y, *points[i - 1], *point
                vertices.extend(triangle)

        self._vertex_list.position[:] = vertices

    @property
    def radius(self) -> float:
        """The radius of the circle.

        :rtype: float
        """
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        self._radius = value
        self._update_vertices()


class Ellipse(ShapeBase):
    _draw_mode = GL_LINES

    def __init__(self, x: float, y: float, a: float, b: float, color: tuple=(255, 255, 255, 255),
                 batch: Batch=None, group: Group=None) -> None:
        """Create an ellipse.

        The ellipse's anchor point (x, y) defaults to the center of the ellipse.

        :Parameters:
            `x` : float
                X coordinate of the ellipse.
            `y` : float
                Y coordinate of the ellipse.
            `a` : float
                Semi-major axes of the ellipse.
            `b`: float
                Semi-minor axes of the ellipse.
            `color` : (int, int, int, int)
                The RGB or RGBA color of the ellipse, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the circle to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the circle.
        """
        self._x = x
        self._y = y
        self._a = a
        self._b = b

        # Break with conventions in other _Shape constructors
        # because a & b are used as meaningful variable names.
        color_r, color_g, color_b, *color_a = color
        self._rgba = color_r, color_g, color_b, color_a[0] if color_a else 255

        self._rotation = 0
        self._segments = int(max(a, b) / 1.25)
        self._num_verts = self._segments * 2

        program = get_default_shader()
        self._batch = batch or Batch()
        self._group = self.group_class(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, program, group)

        self._create_vertex_list()
        self._update_vertices()

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._group.program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _update_vertices(self) -> None:
        if not self._visible:
            vertices = (0,) * self._num_verts * 4
        else:
            x = -self._anchor_x
            y = -self._anchor_y
            tau_segs = math.pi * 2 / self._segments

            # Calculate the points of the ellipse by formula:
            points = [(x + self._a * math.cos(i * tau_segs),
                       y + self._b * math.sin(i * tau_segs)) for i in range(self._segments + 1)]

            # Create a list of lines from the points:
            vertices = []
            for i in range(len(points) - 1):
                line_points = *points[i], *points[i + 1]
                vertices.extend(line_points)

        self._vertex_list.position[:] = vertices

    @property
    def a(self) -> float:
        """The semi-major axes of the ellipse.

        :rtype: float
        """
        return self._a

    @a.setter
    def a(self, value: float) -> None:
        self._a = value
        self._update_vertices()

    @property
    def b(self) -> float:
        """The semi-minor axes of the ellipse.

        :rtype: float
        """
        return self._b

    @b.setter
    def b(self, value: float) -> None:
        self._b = value
        self._update_vertices()

    @property
    def rotation(self) -> float:
        """Clockwise rotation of the arc, in degrees.

        The arc will be rotated about its (anchor_x, anchor_y)
        position.

        :rtype: float
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: float) -> None:
        self._rotation = rotation
        self._vertex_list.rotation[:] = (rotation,) * self._num_verts


class Sector(ShapeBase):
    def __init__(self, x: float, y: float, radius: float, segments: int=None, angle: float=math.tau, start_angle: float=0,
                 color: tuple=(255, 255, 255, 255), batch: Batch=None, group: Group=None) -> None:
        """Create a Sector of a circle.

                The sector's anchor point (x, y) defaults to the center of the circle.

                :Parameters:
                    `x` : float
                        X coordinate of the sector.
                    `y` : float
                        Y coordinate of the sector.
                    `radius` : float
                        The desired radius.
                    `segments` : int
                        You can optionally specify how many distinct triangles
                        the sector should be made from. If not specified it will
                        be automatically calculated using the formula:
                        `max(14, int(radius / 1.25))`.
                    `angle` : float
                        The angle of the sector, in radians. Defaults to tau (pi * 2),
                        which is a full circle.
                    `start_angle` : float
                        The start angle of the sector, in radians. Defaults to 0.
                    `color` : (int, int, int, int)
                        The RGB or RGBA color of the circle, specified as a
                        tuple of 3 or 4 ints in the range of 0-255. RGB colors
                        will be treated as having an opacity of 255.
                    `batch` : `~pyglet.graphics.Batch`
                        Optional batch to add the sector to.
                    `group` : `~pyglet.graphics.Group`
                        Optional parent group of the sector.
                """
        self._x = x
        self._y = y
        self._radius = radius
        self._segments = segments or max(14, int(radius / 1.25))
        self._num_verts = self._segments * 3

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        self._angle = angle
        self._start_angle = start_angle
        self._rotation = 0

        program = get_default_shader()
        self._batch = batch or Batch()
        self._group = self.group_class(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, program, group)

        self._create_vertex_list()
        self._update_vertices()

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._group.program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _update_vertices(self) -> None:
        if not self._visible:
            vertices = (0,) * self._segments * 6
        else:
            x = -self._anchor_x
            y = -self._anchor_y
            r = self._radius
            tau_segs = self._angle / self._segments
            start_angle = self._start_angle - math.radians(self._rotation)

            # Calculate the outer points of the sector.
            points = [(x + (r * math.cos((i * tau_segs) + start_angle)),
                       y + (r * math.sin((i * tau_segs) + start_angle))) for i in range(self._segments + 1)]

            # Create a list of triangles from the points
            vertices = []
            for i, point in enumerate(points[1:], start=1):
                triangle = x, y, *points[i - 1], *point
                vertices.extend(triangle)

        self._vertex_list.position[:] = vertices

    @property
    def angle(self) -> float:
        """The angle of the sector.

        :rtype: float
        """
        return self._angle

    @angle.setter
    def angle(self, value: float) -> None:
        self._angle = value
        self._update_vertices()

    @property
    def start_angle(self) -> float:
        """The start angle of the sector.

        :type: float
        """
        return self._start_angle

    @start_angle.setter
    def start_angle(self, angle: float) -> None:
        self._start_angle = angle
        self._update_vertices()

    @property
    def radius(self) -> None:
        """The radius of the sector.

        :rtype: float
        """
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        self._radius = value
        self._update_vertices()

    @property
    def rotation(self) -> float:
        """Clockwise rotation of the sector, in degrees.

        The sector will be rotated about its (anchor_x, anchor_y)
        position.

        :rtype: float
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: float) -> None:
        self._rotation = rotation
        self._vertex_list.rotation[:] = (rotation,) * self._num_verts


class Line(ShapeBase):
    def __init__(self, x: float, y: float, x2: float, y2: float, width: int=1, color: tuple=(255, 255, 255, 255),
                 batch: Batch=None, group: Group=None) -> None:
        """Create a line.

        The line's anchor point defaults to the center of the line's
        width on the X axis, and the Y axis.

        :Parameters:
            `x` : float
                The first X coordinate of the line.
            `y` : float
                The first Y coordinate of the line.
            `x2` : float
                The second X coordinate of the line.
            `y2` : float
                The second Y coordinate of the line.
            `width` : float
                The desired width of the line.
            `color` : (int, int, int, int)
                The RGB or RGBA color of the line, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the line to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the line.
        """
        self._x = x
        self._y = y
        self._x2 = x2
        self._y2 = y2

        self._width = width
        self._rotation = math.degrees(math.atan2(y2 - y, x2 - x))
        self._num_verts = 6

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        program = get_default_shader()
        self._batch = batch or Batch()
        self._group = self.group_class(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, program, group)

        self._create_vertex_list()
        self._update_vertices()

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._group.program.vertex_list(
            6, self._draw_mode, self._batch, self._group,
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _update_vertices(self) -> None:
        if not self._visible:
            self._vertex_list.position[:] = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        else:
            x1 = -self._anchor_x
            y1 = self._anchor_y - self._width / 2
            x2 = x1 + math.hypot(self._y2 - self._y, self._x2 - self._x)
            y2 = y1 + self._width

            r = math.atan2(self._y2 - self._y, self._x2 - self._x)
            cr = math.cos(r)
            sr = math.sin(r)
            ax = x1 * cr - y1 * sr
            ay = x1 * sr + y1 * cr
            bx = x2 * cr - y1 * sr
            by = x2 * sr + y1 * cr
            cx = x2 * cr - y2 * sr
            cy = x2 * sr + y2 * cr
            dx = x1 * cr - y2 * sr
            dy = x1 * sr + y2 * cr

            self._vertex_list.position[:] = (ax, ay,  bx, by,  cx, cy, ax, ay,  cx, cy,  dx, dy)

    @property
    def x2(self) -> Union[int, float]:
        """Second X coordinate of the shape.

        :rtype: int or float
        """
        return self._x2

    @x2.setter
    def x2(self, value: Union[int, float]) -> None:
        self._x2 = value
        self._update_vertices()

    @property
    def y2(self) -> Union[int, float]:
        """Second Y coordinate of the shape.

        :rtype: int or float
        """
        return self._y2

    @y2.setter
    def y2(self, value: Union[int, float]) -> None:
        self._y2 = value
        self._update_vertices()


class Rectangle(ShapeBase):
    def __init__(self, x: float, y: float, width: float, height: float, color: tuple=(255, 255, 255, 255),
                 batch: Batch=None, group: Group=None) -> None:
        """Create a rectangle or square.

        The rectangle's anchor point defaults to the (x, y) coordinates,
        which are at the bottom left.

        :Parameters:
            `x` : float
                The X coordinate of the rectangle.
            `y` : float
                The Y coordinate of the rectangle.
            `width` : float
                The width of the rectangle.
            `height` : float
                The height of the rectangle.
            `color` : (int, int, int, int)
                The RGB or RGBA color of the circle, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the rectangle to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the rectangle.
        """
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._rotation = 0
        self._num_verts = 6

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        program = get_default_shader()
        self._batch = batch or Batch()
        self._group = self.group_class(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, program, group)

        self._create_vertex_list()
        self._update_vertices()

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._group.program.vertex_list(
            6, self._draw_mode, self._batch, self._group,
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _update_vertices(self) -> None:
        if not self._visible:
            self._vertex_list.position[:] = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        else:
            x1 = -self._anchor_x
            y1 = -self._anchor_y
            x2 = x1 + self._width
            y2 = y1 + self._height

            self._vertex_list.position[:] = x1, y1, x2, y1, x2, y2, x1, y1, x2, y2, x1, y2

    @property
    def width(self) -> float:
        """The width of the rectangle.

        :rtype: float
        """
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        self._width = value
        self._update_vertices()

    @property
    def height(self) -> None:
        """The height of the rectangle.

        :rtype: float
        """
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        self._height = value
        self._update_vertices()

    @property
    def rotation(self) -> None:
        """Clockwise rotation of the rectangle, in degrees.

        The Rectangle will be rotated about its (anchor_x, anchor_y)
        position.

        :rtype: float
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: float) -> None:
        self._rotation = rotation
        self._vertex_list.rotation[:] = (rotation,) * self._num_verts


class BorderedRectangle(ShapeBase):
    def __init__(self, x: float, y: float, width: float, height: float, border: float=1, color: tuple=(255, 255, 255),
                 border_color: tuple=(100, 100, 100), batch: Batch=None, group: Group=None) -> None:
        """Create a rectangle or square.

        The rectangle's anchor point defaults to the (x, y) coordinates,
        which are at the bottom left.

        :Parameters:
            `x` : float
                The X coordinate of the rectangle.
            `y` : float
                The Y coordinate of the rectangle.
            `width` : float
                The width of the rectangle.
            `height` : float
                The height of the rectangle.
            `border` : float
                The thickness of the border.
            `color` : (int, int, int, int)
                The RGB or RGBA fill color of the rectangle, specified
                as a tuple of 3 or 4 ints in the range of 0-255. RGB
                colors will be treated as having an opacity of 255.
            `border_color` : (int, int, int, int)
                The RGB or RGBA fill color of the rectangle, specified
                as a tuple of 3 or 4 ints in the range of 0-255. RGB
                colors will be treated as having an opacity of 255.

                The alpha values must match if you pass RGBA values to
                both this argument and `border_color`. If they do not,
                a `ValueError` will be raised informing you of the
                ambiguity.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the rectangle to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the rectangle.
        """
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._rotation = 0
        self._border = border
        self._num_verts = 8

        fill_r, fill_g, fill_b, *fill_a = color
        border_r, border_g, border_b, *border_a = border_color

        # Start with a default alpha value of 255.
        alpha = 255
        # Raise Exception if we have conflicting alpha values
        if fill_a and border_a and fill_a[0] != border_a[0]:
            raise ValueError("When color and border_color are both RGBA values,"
                             "they must both have the same opacity")

        # Choose a value to use if there is no conflict
        elif fill_a:
            alpha = fill_a[0]
        elif border_a:
            alpha = border_a[0]

        # Although the shape is only allowed one opacity, the alpha is
        # stored twice to keep other code concise and reduce cpu usage
        # from stitching together sequences.
        self._rgba = fill_r, fill_g, fill_b, alpha
        self._border_rgba = border_r, border_g, border_b, alpha

        program = get_default_shader()
        self._batch = batch or Batch()
        self._group = self.group_class(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, program, group)

        self._create_vertex_list()
        self._update_vertices()

    def _create_vertex_list(self) -> None:
        indices = [0, 1, 2, 0, 2, 3, 0, 4, 3, 4, 7, 3, 0, 1, 5, 0, 5, 4, 1, 2, 5, 5, 2, 6, 6, 2, 3, 6, 3, 7]
        self._vertex_list = self._group.program.vertex_list_indexed(
            8, self._draw_mode, indices, self._batch, self._group,
            colors=('Bn', self._rgba * 4 + self._border_rgba * 4),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _update_color(self) -> None:
        self._vertex_list.colors[:] = self._rgba * 4 + self._border_rgba * 4

    def _update_vertices(self) -> None:
        if not self._visible:
            self._vertex_list.position[:] = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        else:
            bx1 = -self._anchor_x
            by1 = -self._anchor_y
            bx2 = bx1 + self._width
            by2 = by1 + self._height
            b = self._border
            ix1 = bx1 + b
            iy1 = by1 + b
            ix2 = bx2 - b
            iy2 = by2 - b

            self._vertex_list.position[:] = (ix1, iy1, ix2, iy1, ix2, iy2, ix1, iy2,
                                             bx1, by1, bx2, by1, bx2, by2, bx1, by2)

    @property
    def width(self) -> float:
        """The width of the rectangle.

        :rtype: float
        """
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        self._width = value
        self._update_vertices()

    @property
    def height(self) -> float:
        """The height of the rectangle.

        :rtype: float
        """
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        self._height = value
        self._update_vertices()

    @property
    def rotation(self) -> float:
        """Clockwise rotation of the rectangle, in degrees.

        The Rectangle will be rotated about its (anchor_x, anchor_y)
        position.

        :rtype: float
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: float) -> None:
        self._rotation = rotation
        self._vertex_list.rotation[:] = (rotation,) * self._num_verts

    @property
    def border_color(self) -> (int, int, int, int):
        """The rectangle's border color.

        This property sets the color of the border of a bordered rectangle.

        The color is specified as an RGB tuple of integers '(red, green, blue)'
        or an RGBA tuple of integers '(red, green, blue, alpha)`. Setting the
        alpha on this property will change the alpha of the entire shape,
        including both the fill and the border.

        Each color component must be in the range 0 (dark) to 255 (saturated).

        :rtype: (int, int, int, int)
        """
        return self._border_rgba

    @border_color.setter
    def border_color(self, values: (int, int, int, int)) -> None:
        r, g, b, *a = values

        if a:
            alpha = a[0]
        else:
            alpha = self._rgba[3]

        self._border_rgba = r, g, b, alpha
        self._rgba = *self._rgba[:3], alpha

        self._update_color()

    @property
    def color(self) -> (int, int, int, int):
        """The rectangle's fill color.

        This property sets the color of the inside of a bordered rectangle.

        The color is specified as an RGB tuple of integers '(red, green, blue)'
        or an RGBA tuple of integers '(red, green, blue, alpha)`. Setting the
        alpha on this property will change the alpha of the entire shape,
        including both the fill and the border.

        Each color component must be in the range 0 (dark) to 255 (saturated).

        :type: (int, int, int, int)
        """
        return self._rgba

    @color.setter
    def color(self, values: (int, int, int, int)) -> None:
        r, g, b, *a = values

        if a:
            alpha = a[0]
        else:
            alpha = self._rgba[3]

        self._rgba = r, g, b, alpha
        self._border_rgba = *self._border_rgba[:3], alpha
        self._update_color()


class Triangle(ShapeBase):
    def __init__(self, x: float, y: float, x2: float, y2: float, x3: float, y3: float, color: tuple=(255, 255, 255, 255),
                 batch: Batch=None, group: Group=None) -> None:
        """Create a triangle.

        The triangle's anchor point defaults to the first vertex point.

        :Parameters:
            `x` : float
                The first X coordinate of the triangle.
            `y` : float
                The first Y coordinate of the triangle.
            `x2` : float
                The second X coordinate of the triangle.
            `y2` : float
                The second Y coordinate of the triangle.
            `x3` : float
                The third X coordinate of the triangle.
            `y3` : float
                The third Y coordinate of the triangle.
            `color` : (int, int, int, int)
                The RGB or RGBA color of the triangle, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the triangle to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the triangle.
        """
        self._x = x
        self._y = y
        self._x2 = x2
        self._y2 = y2
        self._x3 = x3
        self._y3 = y3
        self._rotation = 0
        self._num_verts = 3

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        program = get_default_shader()
        self._batch = batch or Batch()
        self._group = self.group_class(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, program, group)

        self._create_vertex_list()
        self._update_vertices()

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._group.program.vertex_list(
            3, self._draw_mode, self._batch, self._group,
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _update_vertices(self) -> None:
        if not self._visible:
            self._vertex_list.position[:] = (0, 0, 0, 0, 0, 0)
        else:
            x1 = -self._anchor_x
            y1 = -self._anchor_y
            x2 = self._x2 + x1 - self._x
            y2 = self._y2 + y1 - self._y
            x3 = self._x3 + x1 - self._x
            y3 = self._y3 + y1 - self._y
            self._vertex_list.position[:] = (x1, y1, x2, y2, x3, y3)

    @property
    def x2(self) -> Union[int, float]:
        """Second X coordinate of the shape.

        :type: int or float
        """
        return self._x + self._x2

    @x2.setter
    def x2(self, value: Union[int, float]) -> None:
        self._x2 = value
        self._update_vertices()

    @property
    def y2(self) -> Union[int, float]:
        """Second Y coordinate of the shape.

        :type: int or float
        """
        return self._y + self._y2

    @y2.setter
    def y2(self, value: Union[int, float]) -> None:
        self._y2 = value
        self._update_vertices()

    @property
    def x3(self) -> Union[int, float]:
        """Third X coordinate of the shape.

        :type: int or float
        """
        return self._x + self._x3

    @x3.setter
    def x3(self, value: Union[int, float]) -> None:
        self._x3 = value
        self._update_vertices()

    @property
    def y3(self) -> Union[int, float]:
        """Third Y coordinate of the shape.

        :type: int or float
        """
        return self._y + self._y3

    @y3.setter
    def y3(self, value: Union[int, float]) -> None:
        self._y3 = value
        self._update_vertices()


class Star(ShapeBase):
    def __init__(self, x: float, y: float, outer_radius: float, inner_radius: float, num_spikes: float, rotation: float=0,
                 color: tuple=(255, 255, 255, 255), batch: Batch=None, group: Group=None) -> None:
        """Create a star.

        The star's anchor point (x, y) defaults to the center of the star.

        :Parameters:
            `x` : float
                The X coordinate of the star.
            `y` : float
                The Y coordinate of the star.
            `outer_radius` : float
                The desired outer radius of the star.
            `inner_radius` : float
                The desired inner radius of the star.
            `num_spikes` : float
                The desired number of spikes of the star.
            `rotation` : float
                The rotation of the star in degrees. A rotation of 0 degrees
                will result in one spike lining up with the X axis in
                positive direction.
            `color` : (int, int, int)
                The RGB or RGBA color of the star, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the star to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the star.
        """
        self._x = x
        self._y = y
        self._outer_radius = outer_radius
        self._inner_radius = inner_radius
        self._num_spikes = num_spikes
        self._num_verts = num_spikes * 6
        self._rotation = rotation

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        program = get_default_shader()
        self._batch = batch or Batch()
        self._group = self.group_class(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, program, group)

        self._create_vertex_list()
        self._update_vertices()

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._group.program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            colors=('Bn', self._rgba * self._num_verts),
            rotation=('f', (self._rotation,) * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _update_vertices(self) -> None:
        if not self._visible:
            vertices = (0, 0) * self._num_spikes * 6
        else:
            x = -self._anchor_x
            y = -self._anchor_y
            r_i = self._inner_radius
            r_o = self._outer_radius

            # get angle covered by each line (= half a spike)
            d_theta = math.pi / self._num_spikes

            # calculate alternating points on outer and outer circles
            points = []
            for i in range(self._num_spikes):
                points.append((x + (r_o * math.cos(2*i * d_theta)),
                               y + (r_o * math.sin(2*i * d_theta))))
                points.append((x + (r_i * math.cos((2*i+1) * d_theta)),
                               y + (r_i * math.sin((2*i+1) * d_theta))))

            # create a list of doubled-up points from the points
            vertices = []
            for i, point in enumerate(points):
                triangle = x, y, *points[i - 1], *point
                vertices.extend(triangle)

        self._vertex_list.position[:] = vertices

    @property
    def outer_radius(self) -> float:
        """The outer radius of the star."""
        return self._outer_radius

    @outer_radius.setter
    def outer_radius(self, value: float) -> None:
        self._outer_radius = value
        self._update_vertices()

    @property
    def inner_radius(self) -> float:
        """The inner radius of the star."""
        return self._inner_radius

    @inner_radius.setter
    def inner_radius(self, value: float) -> None:
        self._inner_radius = value
        self._update_vertices()

    @property
    def num_spikes(self) -> float:
        """Number of spikes of the star."""
        return self._num_spikes

    @num_spikes.setter
    def num_spikes(self, value: float) -> None:
        self._num_spikes = value
        self._update_vertices()

    @property
    def rotation(self) -> float:
        """Rotation of the star, in degrees.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: float) -> None:
        self._rotation = rotation
        self._vertex_list.rotation[:] = (rotation,) * self._num_verts


class Polygon(ShapeBase):
    def __init__(self, *coordinates: [[int, int]], color: tuple=(255, 255, 255, 255), batch: Batch=None, group: Group=None) -> None:
        """Create a convex polygon.

        The polygon's anchor point defaults to the first vertex point.

        :Parameters:
            `coordinates` : List[[int, int]]
                The coordinates for each point in the polygon.
            `color` : (int, int, int)
                The RGB or RGBA color of the polygon, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the polygon to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the polygon.
        """

        # len(self._coordinates) = the number of vertices and sides in the shape.
        self._rotation = 0
        self._coordinates = list(coordinates)
        self._num_verts = (len(self._coordinates) - 2) * 3

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        program = get_default_shader()
        self._batch = batch or Batch()
        self._group = self.group_class(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, program, group)

        self._create_vertex_list()
        self._update_vertices()

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._group.program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._coordinates[0]) * self._num_verts))

    def _update_vertices(self) -> None:
        if not self._visible:
            self._vertex_list.position[:] = tuple([0] * ((len(self._coordinates) - 2) * 6))
        else:
            # Adjust all coordinates by the anchor.
            trans_x, trans_y = self._coordinates[0]
            trans_x += self._anchor_x
            trans_y += self._anchor_y
            coords = [[x - trans_x, y - trans_y] for x, y in self._coordinates]

            # Triangulate the convex polygon.
            triangles = []
            for n in range(len(coords) - 2):
                triangles += [coords[0], coords[n + 1], coords[n + 2]]

            # Flattening the list before setting vertices to it.
            self._vertex_list.position[:] = tuple(value for coordinate in triangles for value in coordinate)

    @property
    def rotation(self) -> float:
        """
        Clockwise rotation of the polygon, in degrees.

        The Polygon will be rotated about its (anchor_x, anchor_y)
        position.

        :rtype: float
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: float) -> None:
        """
        Change the clockwise rotation of the polygon, in degrees.

        The Polygon will be rotated about its (anchor_x, anchor_y)
        position.

        :rtype: NoneType
        """
        self._rotation = rotation
        self._vertex_list.rotation[:] = (rotation,) * self._num_verts


__all__ = 'Arc', 'BezierCurve', 'Circle', 'Ellipse', 'Line', 'Rectangle', 'BorderedRectangle', 'Triangle', 'Star', 'Polygon', 'Sector'
