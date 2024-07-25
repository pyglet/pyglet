"""2D shapes.

This module provides classes for a variety of simplistic 2D shapes,
such as Rectangles, Circles, and Lines. These shapes are made
internally from OpenGL primitives, and provide excellent performance
when drawn as part of a :py:class:`~pyglet.graphics.Batch`.
Convenience methods are provided for positioning, changing color, opacity,
and rotation.
The Python ``in`` operator can be used to check whether a point is inside a shape.
(This is approximated with some shapes, such as Star).

If the shapes in this module don't suit your needs, you have two
options:

.. list-table::
   :header-rows: 1

   * - Your Goals
     - Best Approach

   * - Simple shapes like those here
     - Subclass :py:class:`ShapeBase`

   * - Complex & optimized shapes
     - See :ref:`guide_graphics` to learn about
       the low-level graphics API.


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


.. note:: Some Shapes, such as :py:class:`.Line` and :py:class:`.Triangle`,
          have multiple coordinates.

          These shapes treat their :py:attr:`~ShapeBase.position` as their
          primary coordinate. Changing it or its components (the
          :py:attr:`~ShapeBase.x` or :py:attr:`~ShapeBase.y` properties)
          also moves all secondary coordinates by the same offset from
          the previous :py:attr:`~ShapeBase.position` value. This allows
          you to move these shapes without distorting them.


.. versionadded:: 1.5.4
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Sequence, Tuple, Union

import pyglet
from pyglet.extlibs import earcut
from pyglet.gl import GL_BLEND, GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA, GL_TRIANGLES, glBlendFunc, glDisable, glEnable
from pyglet.graphics import Batch, Group
from pyglet.math import Vec2

if TYPE_CHECKING:
    from pyglet.graphics.shader import ShaderProgram

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


def get_default_shader() -> ShaderProgram:
    return pyglet.gl.current_context.create_program((vertex_source, 'vertex'),
                                                    (fragment_source, 'fragment'))


def _rotate_point(center: tuple[float, float], point: tuple[float, float], angle: float) -> tuple[float, float]:
    prev_angle = math.atan2(point[1] - center[1], point[0] - center[0])
    now_angle = prev_angle + angle
    r = math.dist(point, center)
    return center[0] + r * math.cos(now_angle), center[1] + r * math.sin(now_angle)


def _point_in_polygon(polygon: Sequence[tuple[float, float]], point: tuple[float, float]) -> bool:
    """Use raycasting to determine if a point is inside a polygon.

    This function is an example implementation available under MIT License at:
    https://www.algorithms-and-technologies.com/point_in_polygon/python
    """
    odd = False
    i = 0
    j = len(polygon) - 1
    while i < len(polygon) - 1:
        i = i + 1
        if ((polygon[i][1] > point[1]) != (polygon[j][1] > point[1])) and (
                point[0]
                < (
                        (polygon[j][0] - polygon[i][0]) * (point[1] - polygon[i][1])
                        / (polygon[j][1] - polygon[i][1])
                )
                + polygon[i][0]
        ):
            odd = not odd
        j = i
    return odd


def _get_segment(p0: tuple[float, float] | list[float], p1: tuple[float, float] | list[float],
                 p2: tuple[float, float] | list[float], p3: tuple[float, float] | list[float],
                 thickness: float = 1.0, prev_miter: Vec2 | None = None, prev_scale: Vec2 | None = None) -> tuple[
    Vec2, Vec2, float, float, float, float, float, float, float, float, float, float, float, float]:
    """Computes a line segment between the points p1 and p2.

    If points p0 or p3 are supplied then the segment p1->p2 will have the correct "miter" angle
    for each end respectively.  This returns computed miter and scale values which can be supplied
    to the next call of the method for a minor performance improvement.  If they are not supplied
    then they will be computed.

    Args:
        p0:
            The "previous" point for the segment p1->p2 which is used to compute the "miter"
            angle of the start of the segment.  If None is supplied then the start of the line
            is 90 degrees to the segment p1->p2.
        p1:
            The origin of the segment p1->p2.
        p2:
            The end of the segment p1->p2
        p3:
            The "following" point for the segment p1->p2 which is used to compute the "miter"
            angle to the end of the segment.  If None is supplied then the end of the line is
            90 degrees to the segment p1->p2.
        thickness:
            Thickness of the miter.
        prev_miter:
            The miter value to be used.
        prev_scale:
            The scale value to be used.
    """
    v_np1p2 = Vec2(p2[0] - p1[0], p2[1] - p1[1]).normalize()
    v_normal = Vec2(-v_np1p2.y, v_np1p2.x)

    # Prep the miter vectors to the normal vector in case it is only one segment
    v_miter2 = v_normal
    scale1 = scale2 = thickness / 2.0

    # miter1 is either already computed or the normal
    v_miter1 = v_normal
    if prev_miter and prev_scale:
        v_miter1 = prev_miter
        scale1 = prev_scale
    elif p0:
        # Compute the miter joint vector for the start of the segment
        v_np0p1 = Vec2(p1[0] - p0[0], p1[1] - p0[1]).normalize()
        v_normal_p0p1 = Vec2(-v_np0p1.y, v_np0p1.x)
        # Add the 2 normal vectors and normalize to get miter vector
        v_miter1 = Vec2(v_normal_p0p1.x + v_normal.x, v_normal_p0p1.y + v_normal.y).normalize()
        scale1 = scale1 / math.sin(math.acos(v_np1p2.dot(v_miter1)))

    if p3:
        # Compute the miter joint vector for the end of the segment
        v_np2p3 = Vec2(p3[0] - p2[0], p3[1] - p2[1]).normalize()
        v_normal_p2p3 = Vec2(-v_np2p3.y, v_np2p3.x)
        # Add the 2 normal vectors and normalize to get miter vector
        v_miter2 = Vec2(v_normal_p2p3.x + v_normal.x, v_normal_p2p3.y + v_normal.y).normalize()
        scale2 = scale2 / math.sin(math.acos(v_np2p3.dot(v_miter2)))

    # Quick fix for preventing the scaling factors from getting out of hand
    # with extreme angles.
    scale1 = min(scale1, 2.0 * thickness)
    scale2 = min(scale2, 2.0 * thickness)

    # Make these tuples instead of Vec2 because accessing
    # members of Vec2 is suprisingly slow
    miter1_scaled_p = (v_miter1.x * scale1, v_miter1.y * scale1)
    miter2_scaled_p = (v_miter2.x * scale2, v_miter2.y * scale2)

    v1 = (p1[0] + miter1_scaled_p[0], p1[1] + miter1_scaled_p[1])
    v2 = (p2[0] + miter2_scaled_p[0], p2[1] + miter2_scaled_p[1])
    v3 = (p1[0] - miter1_scaled_p[0], p1[1] - miter1_scaled_p[1])
    v4 = (p2[0] + miter2_scaled_p[0], p2[1] + miter2_scaled_p[1])
    v5 = (p2[0] - miter2_scaled_p[0], p2[1] - miter2_scaled_p[1])
    v6 = (p1[0] - miter1_scaled_p[0], p1[1] - miter1_scaled_p[1])

    return v_miter2, scale2, v1[0], v1[1], v2[0], v2[1], v3[0], v3[1], v4[0], v4[1], v5[0], v5[1], v6[0], v6[1]


class _ShapeGroup(Group):
    """Shared Shape rendering Group.

    The group is automatically coalesced with other shape groups
    sharing the same parent group and blend parameters.
    """

    def __init__(self, blend_src: int, blend_dest: int, program: ShaderProgram, parent: Group | None = None) -> None:
        """Create a Shape group.

        The group is created internally. Usually you do not
        need to explicitly create it.

        Args:
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            program:
                The ShaderProgram to use.
            parent:
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

    def __eq__(self, other: Group | _ShapeGroup) -> None:
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
    you can write your own custom subclass of ``ShapeBase`` by using
    the provided shapes as reference.
    """

    # _rgba and any class attribute set to None is untyped because
    # doing so doesn't require None-handling from some type checkers.
    _rgba = (255, 255, 255, 255)
    _rotation: float = 0.0
    _visible: bool = True
    _x: float = 0.0
    _y: float = 0.0
    _anchor_x: float = 0.0
    _anchor_y: float = 0.0
    _batch: Batch | None = None
    _group: _ShapeGroup | Group | None = None
    _num_verts: int = 0
    _user_group: Group | None = None
    _vertex_list = None
    _draw_mode: int = GL_TRIANGLES
    group_class: Group = _ShapeGroup

    def __init__(self,
                 vertex_count: int,
                 blend_src: int = GL_SRC_ALPHA,
                 blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
                 batch: Batch | None = None,
                 group: Group | None = None,
                 program: ShaderProgram | None = None,
                 ) -> None:
        """Initialize attributes that all Shape object's require.

        Args:
            vertex_count:
                The amount of vertices this Shape object has.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch object.
            group:
                Optional group object.
            program:
                Optional ShaderProgram object.
        """
        self._num_verts = vertex_count
        self._blend_src = blend_src
        self._blend_dest = blend_dest
        self._batch = batch
        self._user_group = group
        self._program = program or get_default_shader()
        self._group = self.get_shape_group()
        self._create_vertex_list()

    def __del__(self) -> None:
        if self._vertex_list is not None:
            self._vertex_list.delete()
            self._vertex_list = None

    def __contains__(self, point: tuple[float, float]) -> bool:
        """Test whether a point is inside a shape."""
        raise NotImplementedError(f"The `in` operator is not supported for {self.__class__.__name__}")

    def get_shape_group(self) -> _ShapeGroup | Group:
        """Creates and returns a group to be used to render the shap[e.

        This is used internally to create a consolidated group for rendering.

        .. note:: This is for advanced usage. This is a group automatically created internally as a child of ``group``,
                  and does not need to be modified unless the parameters of your custom group changes.

        .. versionadded:: 2.0.16
        """
        return self.group_class(self._blend_src, self._blend_dest, self._program, self._user_group)

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
        raise NotImplementedError('_create_vertex_list must be defined in order to use group or batch properties')

    @abstractmethod
    def _update_vertices(self) -> None:
        """Generate up-to-date vertex positions & send them to the GPU.

        This method must set the contents of `self._vertex_list.vertices`
        using a list or tuple that contains the new vertex coordinates for
        each vertex in the shape. See the `ShapeBase` subclasses in this
        module for examples of how to do this.
        """
        raise NotImplementedError("_update_vertices must be defined for every ShapeBase subclass")

    @property
    def blend_mode(self) -> tuple[int, int]:
        """The current blend mode applied to this shape.

        .. note:: Changing this can be an expensive operation as it involves a group creation and transfer.
        """
        return self._blend_src, self._blend_dest

    @blend_mode.setter
    def blend_mode(self, modes: tuple[int, int]) -> None:
        src, dst = modes
        if src == self._blend_src and dst == self._blend_dest:
            return

        self._blend_src = src
        self._blend_dest = dst

        self._group = self.get_shape_group()
        if self._batch is not None:
            self._batch.migrate(self._vertex_list, self._draw_mode, self._group, self._batch)
        else:
            self._vertex_list.delete()
            self._create_vertex_list()

    @property
    def program(self) -> ShaderProgram:
        """The current shader program.

        .. note:: Changing this can be an expensive operation as it involves a group creation and transfer.
        """
        return self._program

    @program.setter
    def program(self, program: ShaderProgram) -> None:
        if self._program == program:
            return
        self._program = program
        self._group = self.get_shape_group()

        if (self._batch and
                self._batch.update_shader(self._vertex_list, GL_TRIANGLES, self._group, program)):
            # Exit early if changing domain is not needed.
            return

        # Recreate vertex list.
        self._vertex_list.delete()
        self._create_vertex_list()

    @property
    def rotation(self) -> float:
        """Get/set the shape's clockwise rotation in degrees.

        All shapes rotate around their :attr:`.anchor_position`.
        For most shapes, this defaults to both:

        * The shape's first vertex of the shape
        * The lower left corner

        Shapes with a ``radius`` property rotate around the
        point the radius is measured from. This will be either
        their center or the center of the circle they're cut from:

        These shapes rotate around their center:

        * :py:class:`.Circle`
        * :py:class:`.Ellipse`
        * :py:class:`.Star`

        These shapes rotate around the point of their angles:

        * :py:class:`.Arc`
        * :py:class:`.Sector`

        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: float) -> None:
        self._rotation = rotation
        self._vertex_list.rotation[:] = (rotation,) * self._num_verts

    def draw(self) -> None:
        """Debug method to draw a single shape at its current position.

        .. warning:: Avoid this inefficient method for everyday use!

                     Regular drawing should add shapes to a :py:class:`Batch`
                     and call its :py:meth:`~Batch.draw` method.

        """
        self._group.set_state_recursive()
        self._vertex_list.draw(self._draw_mode)
        self._group.unset_state_recursive()

    def delete(self) -> None:
        """Force immediate removal of the shape from video memory.

        You should usually call this whenever you no longer need the shape.
        Otherwise, Python may call the finalizer of the shape instance only
        some time after the shape has fallen out of scope, and the shape's video
        memory will not be freed until the finalizer is eventually called by
        garbage collection.

        Implementing manual garbage collection may satisfy the same concern
        without using the current method, but is a very advanced technique.
        """
        if self._vertex_list is not None:
            self._vertex_list.delete()
            self._vertex_list = None

    @property
    def x(self) -> float:
        """Get/set the X coordinate of the shape's :py:attr:`.position`.

        #. To update both :py:attr:`.x` and :py:attr:`.y`, use
           :attr:`.position` instead.
        #. Shapes may vary slightly in how they use :py:attr:`.position`

        See :py:attr:`.position` to learn more.
        """
        return self._x

    @x.setter
    def x(self, value: float) -> None:
        self._x = value
        self._update_translation()

    @property
    def y(self) -> float:
        """Get/set the Y coordinate of the shape's :py:attr:`.position`.

        This property has the following pitfalls:

        #. To update both :py:attr:`.x` and :py:attr:`.y`, use
           :py:attr:`.position` instead.
        #. Shapes may vary slightly in how they use :py:attr:`.position`

        See :attr:`.position` to learn more.
        """
        return self._y

    @y.setter
    def y(self, value: float) -> None:
        self._y = value
        self._update_translation()

    @property
    def position(self) -> tuple[float, float]:
        """Get/set the ``(x, y)`` coordinates of the shape.

        .. tip:: This is more efficient than setting :py:attr:`.x`
                 and :py:attr:`.y` separately!

        All shapes default to rotating around their position. However,
        the way they do so varies.

        Shapes with a ``radius`` property will use this as their
        center:

        * :py:class:`.Circle`
        * :py:class:`.Ellipse`
        * :py:class:`.Arc`
        * :py:class:`.Sector`
        * :py:class:`.Star`

        Others default to using it as their lower left corner.
        """
        return self._x, self._y

    @position.setter
    def position(self, values: tuple[float, float]) -> None:
        self._x, self._y = values
        self._update_translation()

    @property
    def anchor_x(self) -> float:
        """Get/set the X coordinate of the anchor point.

        If you need to set both this and :py:attr:`.anchor_x`, use
        :py:attr:`.anchor_position` instead.
        """
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, value: float) -> None:
        self._anchor_x = value
        self._update_vertices()

    @property
    def anchor_y(self) -> float:
        """Get/set the Y coordinate of the anchor point.

        If you need to set both this and :py:attr:`.anchor_x`, use
        :py:attr:`.anchor_position` instead.
        """
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, value: float) -> None:
        self._anchor_y = value
        self._update_vertices()

    @property
    def anchor_position(self) -> tuple[float, float]:
        """Get/set the anchor's ``(x, y)`` offset from :py:attr:`.position`.

        This defines the point a shape rotates around. By default, it is
        ``(0.0, 0.0)``. However:

        * Its behavior may vary between shape classes.
        * On many shapes, you can set the anchor or its components
          (:py:attr:`.anchor_x` and :attr:`.anchor_y`) to custom values.

        Since all anchor updates recalculate a shape's vertices on the
        CPU, this property is faster than updating :py:attr:`.anchor_x` and
        :py:attr:`.anchor_y` separately.
        """
        return self._anchor_x, self._anchor_y

    @anchor_position.setter
    def anchor_position(self, values: tuple[float, float]) -> None:
        self._anchor_x, self._anchor_y = values
        self._update_vertices()

    @property
    def color(self) -> tuple[int, int, int, int]:
        """Get/set the shape's color.

        The color may set to:

        * An RGBA tuple of integers ``(red, green, blue, alpha)``
        * An RGB tuple of integers ``(red, green, blue)``

        If an RGB color is set, the current alpha will be preserved.
        Otherwise, the new alpha value will be used for the shape. Each
        color component must be in the range 0 (dark) to 255 (saturated).
        """
        return self._rgba

    @color.setter
    def color(
            self,
            values: tuple[int, int, int, int] | tuple[int, int, int],
    ) -> None:
        r, g, b, *a = values

        if a:
            self._rgba = r, g, b, a[0]
        else:
            self._rgba = r, g, b, self._rgba[3]

        self._update_color()

    @property
    def opacity(self) -> int:
        """Get/set the blend opacity of the shape.

        .. tip:: To toggle visibility on/off, :py:attr:`.visible` may be
                 more efficient!

        Opacity is implemented as the alpha component of a shape's
        :py:attr:`.color`. When part of a group with a default blend
        mode of ``(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)``, opacities
        below ``255`` draw with fractional opacity over the background:

        .. list-table:: Example Values & Effects
           :header-rows: 1

           * - Opacity
             - Effect

           * - ``255`` (Default)
             - Shape is fully opaque

           * - ``128``
             - Shape looks translucent

           * - ``0``
             - Invisible

        """
        return self._rgba[3]

    @opacity.setter
    def opacity(self, value: int) -> None:
        self._rgba = (*self._rgba[:3], value)
        self._update_color()

    @property
    def visible(self) -> bool:
        """Get/set whether the shape will be drawn at all.

        For absolute showing / hiding, this is
        """
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value
        self._update_vertices()

    @property
    def group(self) -> Group:
        """Get/set the shape's :class:`Group`.

        You can migrate a shape from one group to another by setting
        this property. Note that it can be an expensive (slow) operation.

        If :py:attr:`.batch` isn't ``None``, setting this property will
        also trigger a batch migration.
        """
        return self._user_group

    @group.setter
    def group(self, group: Group) -> None:
        if self._user_group == group:
            return
        self._user_group = group
        self._group = self.get_shape_group()
        if self._batch:
            self._batch.migrate(self._vertex_list, self._draw_mode, self._group, self._batch)

    @property
    def batch(self) -> Batch | None:
        """Get/set the :py:class:`Batch` for this shape.

        .. warning:: Setting this to ``None`` currently breaks things!

                     Known issues include :py:attr:`.group` breaking.

        You can migrate a shape from one batch to another by setting
        this property, but it can be an expensive (slow) operation.
        """
        return self._batch

    @batch.setter
    def batch(self, batch: Batch | None) -> None:
        if self._batch == batch:
            return

        if batch is not None and self._batch is not None:
            self._batch.migrate(self._vertex_list, self._draw_mode, self._group, batch)
            self._batch = batch
        else:
            self._vertex_list.delete()
            self._batch = batch
            self._create_vertex_list()


class Arc(ShapeBase):

    def __init__(
            self,
            x: float, y: float,
            radius: float,
            segments: int | None = None,
            angle: float = math.tau,
            start_angle: float = 0.0,
            closed: bool = False,
            thickness: float = 1.0,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create an Arc.

        The Arc's anchor point (x, y) defaults to its center.

        Args:
            x:
                X coordinate of the circle.
            y:
                Y coordinate of the circle.
            radius:
                The desired radius.
            segments:
                You can optionally specify how many distinct line segments
                the arc should be made from. If not specified it will be
                automatically calculated using the formula:
                ``max(14, int(radius / 1.25))``.
            angle:
                The angle of the arc, in radians. Defaults to tau (pi * 2),
                which is a full circle.
            start_angle:
                The start angle of the arc, in radians. Defaults to 0.
            closed:
                If ``True``, the ends of the arc will be connected with a line.
                defaults to ``False``.
            thickness:
                The desired thickness or width of the line used for the arc.
            color:
                The RGB or RGBA color of the arc, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        self._x = x
        self._y = y
        self._radius = radius
        self._segments = segments or max(14, int(radius / 1.25))

        # handle both 3 and 4 byte colors
        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        self._thickness = thickness
        self._angle = angle
        self._start_angle = start_angle
        # Only set closed if the angle isn't tau
        self._closed = closed if abs(math.tau - self._angle) > 1e-9 else False
        self._rotation = 0

        super().__init__(
            # Each segment is now 6 vertices long
            self._segments * 6 + (6 if self._closed else 0),
            blend_src, blend_dest, batch, group, program,
        )

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts

        x = -self._anchor_x
        y = -self._anchor_y
        r = self._radius
        tau_segs = self._angle / self._segments
        start_angle = self._start_angle - math.radians(self._rotation)

        # Calculate the outer points of the arc:
        points = [(x + (r * math.cos((i * tau_segs) + start_angle)),
                   y + (r * math.sin((i * tau_segs) + start_angle))) for i in range(self._segments + 1)]

        # Create a list of quads from the points
        vertices = []
        prev_miter = None
        prev_scale = None
        for i in range(len(points) - 1):
            prev_point = None
            next_point = None
            if i > 0:
                prev_point = points[i - 1]
            elif self._closed:
                prev_point = points[-1]
            elif abs(self._angle - math.tau) <= 1e-9:
                prev_point = points[-2]

            if i + 2 < len(points):
                next_point = points[i + 2]
            elif self._closed:
                next_point = points[0]
            elif abs(self._angle - math.tau) <= 1e-9:
                next_point = points[1]

            prev_miter, prev_scale, *segment = _get_segment(prev_point, points[i], points[i + 1], next_point,
                                                            self._thickness, prev_miter, prev_scale)
            vertices.extend(segment)

        if self._closed:
            prev_point = None
            next_point = None
            if len(points) > 2:
                prev_point = points[-2]
                next_point = points[1]
            prev_miter, prev_scale, *segment = _get_segment(prev_point, points[-1], points[0], next_point,
                                                            self._thickness, prev_miter, prev_scale)
            vertices.extend(segment)

        return vertices

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def radius(self) -> float:
        """Get/set the radius of the arc."""
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        self._radius = value
        self._update_vertices()

    @property
    def thickness(self) -> float:
        """Get/set the thickness of the Arc."""
        return self._thickness

    @thickness.setter
    def thickness(self, thickness: float) -> None:
        self._thickness = thickness
        self._update_vertices()

    @property
    def angle(self) -> float:
        """Get/set the angle of the arc in radians."""
        return self._angle

    @angle.setter
    def angle(self, value: float) -> None:
        self._angle = value
        self._update_vertices()

    @property
    def start_angle(self) -> float:
        """Get/set the start angle of the arc in radians."""
        return self._start_angle

    @start_angle.setter
    def start_angle(self, angle: float) -> None:
        self._start_angle = angle
        self._update_vertices()


class BezierCurve(ShapeBase):

    def __init__(
            self,
            *points: tuple[float, float],
            t: float = 1.0,
            segments: int = 100,
            thickness: int = 1.0,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create a Bézier curve.

        The curve's anchor point (x, y) defaults to its first control point.

        Args:
            points:
                Control points of the curve. Points can be specified as multiple
                lists or tuples of point pairs. Ex. (0,0), (2,3), (1,9)
            t:
                Draw `100*t` percent of the curve. 0.5 means the curve
                is half drawn and 1.0 means draw the whole curve.
            segments:
                You can optionally specify how many line segments the
                curve should be made from.
            thickness:
                The desired thickness or width of the line used for the curve.
            color:
                The RGB or RGBA color of the curve, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        self._points = list(points)
        self._x, self._y = self._points[0]
        self._t = t
        self._segments = segments
        self._thickness = thickness
        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        super().__init__(
            self._segments * 6,
            blend_src, blend_dest, batch, group, program,
        )

    def _make_curve(self, t: float) -> list[float]:
        n = len(self._points) - 1
        p = [0, 0]
        for i in range(n + 1):
            m = math.comb(n, i) * (1 - t) ** (n - i) * t ** i
            p[0] += m * self._points[i][0]
            p[1] += m * self._points[i][1]
        return p

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts

        x = -self._anchor_x - self._x
        y = -self._anchor_y - self._y

        # Calculate the points of the curve:
        points = [(x + self._make_curve(self._t * t / self._segments)[0],
                   y + self._make_curve(self._t * t / self._segments)[1]) for t in range(self._segments + 1)]
        trans_x, trans_y = points[0]
        trans_x += self._anchor_x
        trans_y += self._anchor_y
        coords = [[x - trans_x, y - trans_y] for x, y in points]

        # Create a list of doubled-up points from the points:
        vertices = []
        prev_miter = None
        prev_scale = None
        for i in range(len(coords) - 1):
            prev_point = None
            next_point = None
            if i > 0:
                prev_point = points[i - 1]

            if i + 2 < len(points):
                next_point = points[i + 2]

            prev_miter, prev_scale, *segment = _get_segment(prev_point, points[i], points[i + 1], next_point,
                                                            self._thickness, prev_miter, prev_scale)
            vertices.extend(segment)

        return vertices

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def points(self) -> list[tuple[float, float]]:
        """Get/set the control points of the Bézier curve."""
        return self._points

    @points.setter
    def points(self, value: list[tuple[float, float]]) -> None:
        self._points = value
        self._update_vertices()

    @property
    def t(self) -> float:
        """Get/set the t in ``100*t`` percent of the curve to draw."""
        return self._t

    @t.setter
    def t(self, value: float) -> None:
        self._t = value
        self._update_vertices()

    @property
    def thickness(self) -> float:
        """Get/set the line thickness for the Bézier curve."""
        return self._thickness

    @thickness.setter
    def thickness(self, thickness: float) -> None:
        self._thickness = thickness
        self._update_vertices()


class Circle(ShapeBase):

    def __init__(
            self,
            x: float, y: float,
            radius: float,
            segments: int | None = None,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create a circle.

        The circle's anchor point (x, y) defaults to the center of the circle.

        Args:
            x:
                X coordinate of the circle.
            y:
                Y coordinate of the circle.
            radius:
                The desired radius.
            segments:
                You can optionally specify how many distinct triangles
                the circle should be made from. If not specified it will
                be automatically calculated using the formula:
                `max(14, int(radius / 1.25))`.
            color:
                The RGB or RGBA color of the circle, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        self._x = x
        self._y = y
        self._radius = radius
        self._segments = segments or max(14, int(radius / 1.25))
        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        super().__init__(
            self._segments * 3,
            blend_src, blend_dest, batch, group, program,
        )

    def __contains__(self, point: tuple[float, float]) -> bool:
        assert len(point) == 2
        return math.dist((self._x - self._anchor_x, self._y - self._anchor_y), point) < self._radius

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._program.vertex_list(
            self._segments * 3, self._draw_mode, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts

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

        return vertices

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def radius(self) -> float:
        """Gets/set radius of the circle."""
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        self._radius = value
        self._update_vertices()


class Ellipse(ShapeBase):

    def __init__(
            self,
            x: float, y: float,
            a: float, b: float,
            segments: int | None = None,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create an ellipse.

        The ellipse's anchor point ``(x, y)`` defaults to the center of
        the ellipse.

        Args:
            x:
                X coordinate of the ellipse.
            y:
                Y coordinate of the ellipse.
            a:
                Semi-major axes of the ellipse.
            b:
                Semi-minor axes of the ellipse.
            segments:
                You can optionally specify how many distinct line segments
                the ellipse should be made from. If not specified it will be
                automatically calculated using the formula:
                ``int(max(a, b) / 1.25)``.
            color:
                The RGB or RGBA color of the ellipse, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
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
        self._segments = segments or int(max(a, b) / 1.25)

        super().__init__(
            self._segments * 3,
            blend_src, blend_dest, batch, group, program,
        )

    def __contains__(self, point: tuple[float, float]) -> bool:
        assert len(point) == 2
        point = _rotate_point((self._x, self._y), point, math.radians(self._rotation))
        # Since directly testing whether a point is inside an ellipse is more
        # complicated, it is more convenient to transform it into a circle.
        point = (self._b / self._a * point[0], point[1])
        shape_center = (self._b / self._a * (self._x - self._anchor_x), self._y - self._anchor_y)
        return math.dist(shape_center, point) < self._b

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._program.vertex_list(
            self._segments * 3, self._draw_mode, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts

        x = -self._anchor_x
        y = -self._anchor_y
        tau_segs = math.pi * 2 / self._segments

        # Calculate the points of the ellipse by formula:
        points = [(x + self._a * math.cos(i * tau_segs),
                   y + self._b * math.sin(i * tau_segs)) for i in range(self._segments)]

        # Create a list of triangles from the points:
        vertices = []
        for i, point in enumerate(points):
            triangle = x, y, *points[i - 1], *point
            vertices.extend(triangle)

        return vertices

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def a(self) -> float:
        """Get/set the semi-major axes of the ellipse."""
        return self._a

    @a.setter
    def a(self, value: float) -> None:
        self._a = value
        self._update_vertices()

    @property
    def b(self) -> float:
        """Get/set the semi-minor axes of the ellipse."""
        return self._b

    @b.setter
    def b(self, value: float) -> None:
        self._b = value
        self._update_vertices()


class Sector(ShapeBase):

    def __init__(
            self,
            x: float, y: float,
            radius: float,
            segments: int | None = None,
            angle: float = math.tau,
            start_angle: float = 0.0,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create a Sector of a circle.

        By default, ``(x, y)`` is used as:
        * The sector's anchor point
        * The center of the circle the sector is cut from

        Args:
            x:
                X coordinate of the sector.
            y:
                Y coordinate of the sector.
            radius:
                The desired radius.
            segments:
                You can optionally specify how many distinct triangles
                the sector should be made from. If not specified it will
                be automatically calculated using the formula:
                `max(14, int(radius / 1.25))`.
            angle:
                The angle of the sector, in radians. Defaults to tau (pi * 2),
                which is a full circle.
            start_angle:
                The start angle of the sector, in radians. Defaults to 0.
            color:
                The RGB or RGBA color of the circle, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        self._x = x
        self._y = y
        self._radius = radius
        self._segments = segments or max(14, int(radius / 1.25))

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        self._angle = angle
        self._start_angle = start_angle
        self._rotation = 0

        super().__init__(
            self._segments * 3,
            blend_src, blend_dest, batch, group, program,
        )

    def __contains__(self, point: tuple[float, float]) -> bool:
        assert len(point) == 2
        point = _rotate_point((self._x, self._y), point, math.radians(self._rotation))
        angle = math.atan2(point[1] - self._y + self._anchor_y, point[0] - self._x + self._anchor_x)
        if angle < 0:
            angle += 2 * math.pi
        if self._start_angle < angle < self._start_angle + self._angle:
            return math.dist((self._x - self._anchor_x, self._y - self._anchor_y), point) < self._radius
        return False

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts

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

        return vertices

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def angle(self) -> float:
        """Get/set the angle of the sector in radians."""
        return self._angle

    @angle.setter
    def angle(self, value: float) -> None:
        self._angle = value
        self._update_vertices()

    @property
    def start_angle(self) -> float:
        """Get/set the start angle of the sector in radians."""
        return self._start_angle

    @start_angle.setter
    def start_angle(self, angle: float) -> None:
        self._start_angle = angle
        self._update_vertices()

    @property
    def radius(self) -> float:
        """Get/set the radius of the sector.

        By default, this is in screen pixels. Your drawing / GL settings
        may alter how this is drawn.
        """
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        self._radius = value
        self._update_vertices()


class Line(ShapeBase):

    def __init__(
            self,
            x: float, y: float, x2: float, y2: float,
            width: float = 1.0,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ):
        """Create a line.

        The line's anchor point defaults to the center of the line's
        width on the X axis, and the Y axis.

        Args:
            x:
                The first X coordinate of the line.
            y:
                The first Y coordinate of the line.
            x2:
                The second X coordinate of the line.
            y2:
                The second Y coordinate of the line.
            width:
                The desired width of the line.
            color:
                The RGB or RGBA color of the line, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        self._x = x
        self._y = y
        self._x2 = x2
        self._y2 = y2

        self._width = width
        self._rotation = 0

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        super().__init__(6,blend_src, blend_dest, batch, group, program)

    def __contains__(self, point: tuple[float, float]) -> bool:
        assert len(point) == 2
        vec_ab = Vec2(self._x2 - self._x, self._y2 - self._y)
        vec_ba = Vec2(self._x - self._x2, self._y - self._y2)
        vec_ap = Vec2(point[0] - self._x - self._anchor_x, point[1] - self._y + self._anchor_y)
        vec_bp = Vec2(point[0] - self._x2 - self._anchor_x, point[1] - self._y2 + self._anchor_y)
        if vec_ab.dot(vec_ap) * vec_ba.dot(vec_bp) < 0:
            return False

        a, b = point[0] + self._anchor_x, point[1] - self._anchor_y
        x1, y1, x2, y2 = self._x, self._y, self._x2, self._y2
        # The following is the expansion of the determinant of a 3x3 matrix
        # used to calculate the area of a triangle.
        double_area = abs(a * y1 + b * x2 + x1 * y2 - x2 * y1 - a * y2 - b * x1)
        h = double_area / math.dist((self._x, self._y), (self._x2, self._y2))
        return h < self._width / 2

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._program.vertex_list(
            6, self._draw_mode, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts

        x1 = 0
        y1 = -self._width / 2
        x2 = x1 + math.hypot(self._y2 - self._y, self._x2 - self._x)
        y2 = y1 + self._width

        r = math.atan2(self._y2 - self._y, self._x2 - self._x)
        cr = math.cos(r)
        sr = math.sin(r)
        anchor_x = self._anchor_x
        anchor_y = self._anchor_y
        ax = x1 * cr - y1 * sr - anchor_x
        ay = x1 * sr + y1 * cr - anchor_y
        bx = x2 * cr - y1 * sr - anchor_x
        by = x2 * sr + y1 * cr - anchor_y
        cx = x2 * cr - y2 * sr - anchor_x
        cy = x2 * sr + y2 * cr - anchor_y
        dx = x1 * cr - y2 * sr - anchor_x
        dy = x1 * sr + y2 * cr - anchor_y

        return ax, ay, bx, by, cx, cy, ax, ay, cx, cy, dx, dy

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def width(self) -> float:
        """Get/set the line's thickness."""
        return self._width

    @width.setter
    def width(self, width: float) -> None:
        self._width = width
        self._update_vertices()

    @property
    def x2(self) -> float:
        """Get/set the 2nd X coordinate of the line."""
        return self._x2

    @x2.setter
    def x2(self, value: float) -> None:
        self._x2 = value
        self._update_vertices()

    @property
    def y2(self) -> float:
        """Get/set the 2nd Y coordinate of the line."""
        return self._y2

    @y2.setter
    def y2(self, value: float) -> None:
        self._y2 = value
        self._update_vertices()


class Rectangle(ShapeBase):

    def __init__(
            self,
            x: float, y: float,
            width: float, height: float,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ):
        """Create a rectangle or square.

        The rectangle's anchor point defaults to the ``(x, y)``
        coordinates, which are at the bottom left.

        Args:
            x:
                The X coordinate of the rectangle.
            y:
                The Y coordinate of the rectangle.
            width:
                The width of the rectangle.
            height:
                The height of the rectangle.
            color:
                The RGB or RGBA color of the circle, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._rotation = 0

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        super().__init__(6, blend_src, blend_dest, batch, group, program)

    def __contains__(self, point: tuple[float, float]) -> bool:
        assert len(point) == 2
        point = _rotate_point((self._x, self._y), point, math.radians(self._rotation))
        x, y = self._x - self._anchor_x, self._y - self._anchor_y
        return x < point[0] < x + self._width and y < point[1] < y + self._height

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._program.vertex_list(
            6, self._draw_mode, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts
        else:
            x1 = -self._anchor_x
            y1 = -self._anchor_y
            x2 = x1 + self._width
            y2 = y1 + self._height

            return x1, y1, x2, y1, x2, y2, x1, y1, x2, y2, x1, y2

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def width(self) -> float:
        """Get/set width of the rectangle.

        The new left and right of the rectangle will be set relative to
        its :py:attr:`.anchor_x` value.
        """
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        self._width = value
        self._update_vertices()

    @property
    def height(self) -> float:
        """Get/set the height of the rectangle.

        The bottom and top of the rectangle will be positioned relative
        to its :py:attr:`.anchor_y` value.
        """
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        self._height = value
        self._update_vertices()


class BorderedRectangle(ShapeBase):

    def __init__(
            self,
            x: float, y: float, width: float, height: float,
            border: float = 1.0,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255),
            border_color: tuple[int, int, int, int] | tuple[int, int, int] = (100, 100, 100),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ):
        """Create a bordered rectangle.

        The rectangle's anchor point defaults to the ``(x, y)`` coordinates,
        which are at the bottom left.

        Args:
            x:
                The X coordinate of the rectangle.
            y:
                The Y coordinate of the rectangle.
            width:
                The width of the rectangle.
            height:
                The height of the rectangle.
            border:
                The thickness of the border.
            color:
                The RGB or RGBA fill color of the rectangle, specified
                as a tuple of 3 or 4 ints in the range of 0-255. RGB
                colors will be treated as having an opacity of 255.
            border_color:
                The RGB or RGBA fill color of the border, specified
                as a tuple of 3 or 4 ints in the range of 0-255. RGB
                colors will be treated as having an opacity of 255.

                The alpha values must match if you pass RGBA values to
                both this argument and `border_color`. If they do not,
                a `ValueError` will be raised informing you of the
                ambiguity.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._rotation = 0
        self._border = border

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

        super().__init__(8, blend_src, blend_dest, batch, group, program)

    def __contains__(self, point: tuple[float, float]) -> bool:
        assert len(point) == 2
        point = _rotate_point((self._x, self._y), point, math.radians(self._rotation))
        x, y = self._x - self._anchor_x, self._y - self._anchor_y
        return x < point[0] < x + self._width and y < point[1] < y + self._height

    def _create_vertex_list(self) -> None:
        indices = [0, 1, 2, 0, 2, 3, 0, 4, 3, 4, 7, 3, 0, 1, 5, 0, 5, 4, 1, 2, 5, 5, 2, 6, 6, 2, 3, 6, 3, 7]
        self._vertex_list = self._program.vertex_list_indexed(
            8, self._draw_mode, indices, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * 4 + self._border_rgba * 4),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _update_color(self) -> None:
        self._vertex_list.colors[:] = self._rgba * 4 + self._border_rgba * 4

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts

        bx1 = -self._anchor_x
        by1 = -self._anchor_y
        bx2 = bx1 + self._width
        by2 = by1 + self._height
        b = self._border
        ix1 = bx1 + b
        iy1 = by1 + b
        ix2 = bx2 - b
        iy2 = by2 - b

        return (ix1, iy1, ix2, iy1, ix2, iy2, ix1, iy2,
                bx1, by1, bx2, by1, bx2, by2, bx1, by2)

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def border(self) -> float:
        """The border thickness of the bordered rectangle.

        This extends inward from the edge of the rectangle toward the
        center.
        """
        return self._border

    @border.setter
    def border(self, thickness: float) -> None:
        self._border = thickness
        self._update_vertices()

    @property
    def width(self) -> float:
        """Get/set width of the bordered rectangle.

        The new left and right of the rectangle will be set relative to
        its :py:attr:`.anchor_x` value.
        """
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        self._width = value
        self._update_vertices()

    @property
    def height(self) -> float:
        """Get/set the height of the bordered rectangle.

        The bottom and top of the rectangle will be positioned relative
        to its :py:attr:`.anchor_y` value.
        """
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        self._height = value
        self._update_vertices()

    @property
    def border_color(self) -> tuple[int, int, int, int]:
        """Get/set the bordered rectangle's border color.

        To set the color of the interior fill, see :py:attr:`.color`.

        You can set the border color to either of the following:

        * An RGBA tuple of integers ``(red, green, blue, alpha)``
        * An RGB tuple of integers ``(red, green, blue)``

        Setting the alpha on this property will change the alpha of
        the entire shape, including both the fill and the border.

        Each color component must be in the range 0 (dark) to 255 (saturated).
        """
        return self._border_rgba

    @border_color.setter
    def border_color(
            self,
            values: tuple[int, int, int, int] | tuple[int, int, int],
    ) -> None:
        r, g, b, *a = values

        if a:
            alpha = a[0]
        else:
            alpha = self._rgba[3]

        self._border_rgba = r, g, b, alpha
        self._rgba = *self._rgba[:3], alpha

        self._update_color()

    @property
    def color(self) -> tuple[int, int, int, int] | tuple[int, int, int]:
        """Get/set the bordered rectangle's interior fill color.

        To set the color of the border outline, see
        :py:attr:`.border_color`.

        The color may be specified as either of the following:

        * An RGBA tuple of integers ``(red, green, blue, alpha)``
        * An RGB tuple of integers ``(red, green, blue)``

        Setting the alpha through this property will change the alpha
        of the entire shape, including both the fill and the border.

        Each color component must be in the range 0 (dark) to 255
        (saturated).
        """
        return self._rgba

    @color.setter
    def color(
            self,
            values: tuple[int, int, int, int] | tuple[int, int, int],
    ) -> None:
        r, g, b, *a = values

        if a:
            alpha = a[0]
        else:
            alpha = self._rgba[3]

        self._rgba = r, g, b, alpha
        self._border_rgba = *self._border_rgba[:3], alpha
        self._update_color()


class Box(ShapeBase):

    def __init__(
            self,
            x: float, y: float,
            width: float, height: float,
            thickness: float = 1.0,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create an unfilled rectangular shape, with optional thickness.

        The box's anchor point defaults to the ``(x, y)`` coordinates,
        which are placed at the bottom left.
        Changing the thickness of the box will extend the walls inward;
        the outward dimensions will not be affected.

        Args:
            x:
                The X coordinate of the box.
            y:
                The Y coordinate of the box.
            width:
                The width of the box.
            height:
                The height of the box.
            thickness:
                The thickness of the lines that make up the box.
            color:
                The RGB or RGBA color of the box, specified as a tuple
                of 3 or 4 ints in the range of 0-255. RGB colors will
                be treated as having an opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._thickness = thickness

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        super().__init__(8, blend_src, blend_dest, batch, group, program)

    def __contains__(self, point: tuple[float, float]) -> bool:
        assert len(point) == 2
        point = _rotate_point((self._x, self._y), point, math.radians(self._rotation))
        x, y = self._x - self._anchor_x, self._y - self._anchor_y
        return x < point[0] < x + self._width and y < point[1] < y + self._height

    def _create_vertex_list(self) -> None:
        #   3        6
        #     2    7
        #     1    4
        #   0        5
        indices = [0, 1, 2, 0, 2, 3, 0, 5, 4, 0, 4, 1, 4, 5, 6, 4, 6, 7, 2, 7, 6, 2, 6, 3]
        self._vertex_list = self._program.vertex_list_indexed(
            self._num_verts, self._draw_mode, indices, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _update_color(self):
        self._vertex_list.colors[:] = self._rgba * self._num_verts

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts

        t = self._thickness
        left = -self._anchor_x
        bottom = -self._anchor_y
        right = left + self._width
        top = bottom + self._height

        x1 = left
        x2 = left + t
        x3 = right - t
        x4 = right
        y1 = bottom
        y2 = bottom + t
        y3 = top - t
        y4 = top
        #     |  0   |   1   |   2   |   3   |   4   |   5   |   6   |   7   |
        return x1, y1, x2, y2, x2, y3, x1, y4, x3, y2, x4, y1, x4, y4, x3, y3

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def width(self) -> float:
        """Get/set the width of the box.

        Setting the width will position the left and right sides
        relative to the box's :py:attr:`.anchor_x` value.
        """
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        self._width = value
        self._update_vertices()

    @property
    def height(self) -> float:
        """Get/set the height of the Box.

        Setting the height will set the bottom and top relative to the
        box's :py:attr:`.anchor_y` value.
        """
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        self._height = float(value)
        self._update_vertices()

    @property
    def thickness(self) -> float:
        """Get/set the line thickness of the Box."""
        return self._thickness

    @thickness.setter
    def thickness(self, thickness: float) -> None:
        self._thickness = thickness
        self._update_vertices()


_RadiusT = Union[float, Tuple[float, float]]


class RoundedRectangle(pyglet.shapes.ShapeBase):

    def __init__(
            self,
            x: float, y: float,
            width: float, height: float,
            radius: _RadiusT | tuple[_RadiusT, _RadiusT, _RadiusT, _RadiusT],
            segments: int | tuple[int, int, int, int] | None = None,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create a rectangle with rounded corners.

        The rectangle's anchor point defaults to the ``(x, y)``
        coordinates, which are at the bottom left.

        Args:
            x:
                The X coordinate of the rectangle.
            y:
                The Y coordinate of the rectangle.
            width:
                The width of the rectangle.
            height:
                The height of the rectangle.
            radius:
                One or four values to specify the radii used for the rounded corners.
                If one value is given, all corners will use the same value. If four values
                are given, it will specify the radii used for the rounded corners clockwise:
                bottom-left, top-left, top-right, bottom-right. A value can be either a single
                float, or a tuple of two floats to specify different x,y dimensions.
            segments:
                You can optionally specify how many distinct triangles each rounded corner
                should be made from. This can be one int for all corners, or a tuple of
                four ints for each corner, specified clockwise: bottom-left, top-left,
                top-right, bottom-right. If no value is specified, it will automatically
                calculated using the formula: ``max(14, int(radius / 1.25))``.
            color:
                The RGB or RGBA color of the rectangle, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._set_radius(radius)
        self._set_segments(segments)
        self._rotation = 0

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        super().__init__(
            (sum(self._segments) + 4) * 3,
            blend_src, blend_dest, batch, group, program,
        )

    def _set_radius(self, radius: _RadiusT | tuple[_RadiusT, _RadiusT, _RadiusT, _RadiusT]) -> None:
        if isinstance(radius, (int, float)):
            self._radius = ((radius, radius),) * 4
        elif len(radius) == 2:
            self._radius = (radius,) * 4
        else:
            assert len(radius) == 4
            self._radius = []
            for value in radius:
                if isinstance(value, (int, float)):
                    self._radius.append((value, value))
                else:
                    assert len(value) == 2
                    self._radius.append(value)

    def _set_segments(self, segments: int | tuple[int, int, int, int] | None) -> None:
        if segments is None:
            self._segments = tuple(int(max(a, b) / 1.25) for a, b in self._radius)
        elif isinstance(segments, int):
            self._segments = (segments,) * 4
        else:
            assert len(segments) == 4
            self._segments = segments

    def __contains__(self, point: tuple[float, float]) -> bool:
        assert len(point) == 2
        point = _rotate_point((self._x, self._y), point, math.radians(self._rotation))
        x, y = self._x - self._anchor_x, self._y - self._anchor_y
        return x < point[0] < x + self._width and y < point[1] < y + self._height

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts

        x = -self._anchor_x
        y = -self._anchor_y

        points = []
        # arc_x, arc_y, start_angle
        arc_positions = [
            # bottom-left
            (x + self._radius[0][0],
             y + self._radius[0][1], math.pi * 3 / 2),
            # top-left
            (x + self._radius[1][0],
             y + self._height - self._radius[1][1], math.pi),
            # top-right
            (x + self._width - self._radius[2][0],
             y + self._height - self._radius[2][1], math.pi / 2),
            # bottom-right
            (x + self._width - self._radius[3][0],
             y + self._radius[3][1], 0),
        ]

        for (rx, ry), (arc_x, arc_y, arc_start), segments in zip(self._radius, arc_positions, self._segments):
            tau_segs = -math.pi / 2 / segments
            points.extend([(arc_x + rx * math.cos(i * tau_segs + arc_start),
                            arc_y + ry * math.sin(i * tau_segs + arc_start)) for i in range(segments + 1)])

        center_x = self._width / 2
        center_y = self._height / 2
        vertices = []
        for i, point in enumerate(points):
            triangle = center_x, center_y, *points[i - 1], *point
            vertices.extend(triangle)

        return vertices

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def width(self) -> float:
        """Get/set width of the rectangle.

        The new left and right of the rectangle will be set relative to
        its :py:attr:`.anchor_x` value.
        """
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        self._width = value
        self._update_vertices()

    @property
    def height(self) -> float:
        """Get/set the height of the rectangle.

        The bottom and top of the rectangle will be positioned relative
        to its :py:attr:`.anchor_y` value.
        """
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        self._height = value
        self._update_vertices()

    @property
    def radius(self) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]:
        return self._radius

    @radius.setter
    def radius(self, value: _RadiusT | tuple[_RadiusT, _RadiusT, _RadiusT, _RadiusT]) -> None:
        self._set_radius(value)
        self._update_vertices()


class Triangle(ShapeBase):
    def __init__(
            self,
            x: float, y: float,
            x2: float, y2: float,
            x3: float, y3: float,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create a triangle.

        The triangle's anchor point defaults to the first vertex point.

        Args:
            x:
                The first X coordinate of the triangle.
            y:
                The first Y coordinate of the triangle.
            x2:
                The second X coordinate of the triangle.
            y2:
                The second Y coordinate of the triangle.
            x3:
                The third X coordinate of the triangle.
            y3:
                The third Y coordinate of the triangle.
            color:
                The RGB or RGBA color of the triangle, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        self._x = x
        self._y = y
        self._x2 = x2
        self._y2 = y2
        self._x3 = x3
        self._y3 = y3
        self._rotation = 0

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        super().__init__(3, blend_src, blend_dest, batch, group, program)

    def __contains__(self, point: tuple[float, float]) -> bool:
        assert len(point) == 2
        return _point_in_polygon(
            [(self._x, self._y), (self._x2, self._y2), (self._x3, self._y3), (self._x, self._y)],
            point)

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._program.vertex_list(
            3, self._draw_mode, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts
        else:
            x1 = -self._anchor_x
            y1 = -self._anchor_y
            x2 = self._x2 + x1 - self._x
            y2 = self._y2 + y1 - self._y
            x3 = self._x3 + x1 - self._x
            y3 = self._y3 + y1 - self._y
            return x1, y1, x2, y2, x3, y3

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def x2(self) -> float:
        """Get/set the X coordinate of the triangle's 2nd vertex."""
        return self._x + self._x2

    @x2.setter
    def x2(self, value: float) -> None:
        self._x2 = value
        self._update_vertices()

    @property
    def y2(self) -> float:
        """Get/set the Y coordinate of the triangle's 2nd vertex."""
        return self._y + self._y2

    @y2.setter
    def y2(self, value: float) -> None:
        self._y2 = value
        self._update_vertices()

    @property
    def x3(self) -> float:
        """Get/set the X coordinate of the triangle's 3rd vertex."""
        return self._x + self._x3

    @x3.setter
    def x3(self, value: float) -> None:
        self._x3 = value
        self._update_vertices()

    @property
    def y3(self) -> float:
        """Get/set the Y value of the triangle's 3rd vertex."""
        return self._y + self._y3

    @y3.setter
    def y3(self, value: float) -> None:
        self._y3 = value
        self._update_vertices()


class Star(ShapeBase):
    def __init__(
            self,
            x: float, y: float,
            outer_radius: float,
            inner_radius: float,
            num_spikes: int,
            rotation: float = 0.0,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create a star.

        The star's anchor point ``(x, y)`` defaults to the on-screen
        center of the star.

        Args:
            x:
                The X coordinate of the star.
            y:
                The Y coordinate of the star.
            outer_radius:
                The desired outer radius of the star.
            inner_radius:
                The desired inner radius of the star.
            num_spikes:
                The desired number of spikes of the star.
            rotation:
                The rotation of the star in degrees. A rotation of 0 degrees
                will result in one spike lining up with the X axis in
                positive direction.
            color:
                The RGB or RGBA color of the star, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        self._x = x
        self._y = y
        self._outer_radius = outer_radius
        self._inner_radius = inner_radius
        self._num_spikes = num_spikes
        self._rotation = rotation

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        super().__init__(
            num_spikes * 6,
            blend_src, blend_dest, batch, group, program,
        )

    def __contains__(self, point: tuple[float, float]) -> bool:
        assert len(point) == 2
        point = _rotate_point((self._x, self._y), point, math.radians(self._rotation))
        center = (self._x - self._anchor_x, self._y - self._anchor_y)
        radius = (self._outer_radius + self._inner_radius) / 2
        return math.dist(center, point) < radius

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * self._num_verts),
            rotation=('f', (self._rotation,) * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts

        x = -self._anchor_x
        y = -self._anchor_y
        r_i = self._inner_radius
        r_o = self._outer_radius

        # get angle covered by each line (= half a spike)
        d_theta = math.pi / self._num_spikes

        # calculate alternating points on outer and outer circles
        points = []
        for i in range(self._num_spikes):
            points.append((x + (r_o * math.cos(2 * i * d_theta)),
                           y + (r_o * math.sin(2 * i * d_theta))))
            points.append((x + (r_i * math.cos((2 * i + 1) * d_theta)),
                           y + (r_i * math.sin((2 * i + 1) * d_theta))))

        # create a list of doubled-up points from the points
        vertices = []
        for i, point in enumerate(points):
            triangle = x, y, *points[i - 1], *point
            vertices.extend(triangle)

        return vertices

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def outer_radius(self) -> float:
        """Get/set outer radius of the star."""
        return self._outer_radius

    @outer_radius.setter
    def outer_radius(self, value: float) -> None:
        self._outer_radius = value
        self._update_vertices()

    @property
    def inner_radius(self) -> float:
        """Get/set the inner radius of the star."""
        return self._inner_radius

    @inner_radius.setter
    def inner_radius(self, value: float) -> None:
        self._inner_radius = value
        self._update_vertices()

    @property
    def num_spikes(self) -> int:
        """Number of spikes of the star."""
        return self._num_spikes

    @num_spikes.setter
    def num_spikes(self, value: int) -> None:
        self._num_spikes = value
        self._update_vertices()


class Polygon(ShapeBase):
    def __init__(
            self,
            *coordinates: tuple[float, float] | Sequence[float],
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create a polygon.

        The polygon's anchor point defaults to the first vertex point.

        Args:
            coordinates:
                The coordinates for each point in the polygon. Each one
                must be able to unpack to a pair of float-like X and Y
                values.
            color:
                The RGB or RGBA color of the polygon, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        # len(self._coordinates) = the number of vertices and sides in the shape.
        self._rotation = 0
        self._coordinates = list(coordinates)
        self._x, self._y = self._coordinates[0]

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255
        super().__init__(
            len(self._coordinates),
            blend_src, blend_dest, batch, group, program,
        )

    def __contains__(self, point: tuple[float, float]) -> bool:
        assert len(point) == 2
        point = _rotate_point(self._coordinates[0], point, math.radians(self._rotation))
        return _point_in_polygon(self._coordinates + [self._coordinates[0]], point)

    def _create_vertex_list(self) -> None:
        vertices = self._get_vertices()
        self._vertex_list = self._program.vertex_list_indexed(
            self._num_verts, self._draw_mode,
            earcut.earcut(vertices),
            self._batch, self._group,
            position=('f', vertices),
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts

        # Adjust all coordinates by the anchor.
        trans_x, trans_y = self._coordinates[0]
        trans_x += self._anchor_x
        trans_y += self._anchor_y
        coords = [[x - trans_x, y - trans_y] for x, y in self._coordinates]

        # Return the flattened coords.
        return earcut.flatten([coords])["vertices"]

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()


class MultiLine(ShapeBase):

    def __init__(
            self,
            *coordinates: tuple[float, float] | Sequence[float],
            closed: bool = False,
            thickness: float = 1.0,
            color: tuple[int, int, int, int] = (255, 255, 255, 255),
            blend_src: int = GL_SRC_ALPHA,
            blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
            batch: Batch | None = None,
            group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create multiple connected lines from a series of coordinates.

        The shape's anchor point defaults to the first vertex point.

        Args:
            coordinates:
                The coordinates for each point in the shape. Each must
                unpack like a tuple consisting of an X and Y float-like
                value.
            closed:
                Set this to ``True`` to add a line connecting the first
                and last points. The default is ``False``
            thickness:
                The desired thickness or width used for the line segments.
            color:
                The RGB or RGBA color of the shape, specified as a
                tuple of 3 or 4 ints in the range of 0-255. RGB colors
                will be treated as having an opacity of 255.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the shape to.
            group:
                Optional parent group of the shape.
            program:
                Optional shader program of the shape.
        """
        # len(self._coordinates) = the number of vertices in the shape.
        self._thickness = thickness
        self._closed = closed
        self._rotation = 0
        self._coordinates = list(coordinates)
        if closed:
            # connect final point with first
            self._coordinates.append(self._coordinates[0])
        self._x, self._y = self._coordinates[0]

        r, g, b, *a = color
        self._rgba = r, g, b, a[0] if a else 255

        super().__init__(
            (len(self._coordinates) - 1) * 6,
            blend_src, blend_dest, batch, group, program,
        )

    def _create_vertex_list(self) -> None:
        self._vertex_list = self._program.vertex_list(
            self._num_verts, self._draw_mode, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * self._num_verts),
            translation=('f', (self._x, self._y) * self._num_verts))

    def _get_vertices(self) -> Sequence[float]:
        if not self._visible:
            return (0, 0) * self._num_verts

        trans_x, trans_y = self._coordinates[0]
        trans_x += self._anchor_x
        trans_y += self._anchor_y
        coords: list[list[float]] = [[x - trans_x, y - trans_y] for x, y in self._coordinates]

        # Create a list of triangles from segments between 2 points:
        triangles = []
        prev_miter = None
        prev_scale = None
        for i in range(len(coords) - 1):
            prev_point: list[float] | None = None
            next_point: list[float] | None = None
            if i > 0:
                prev_point = coords[i - 1]

            if i + 2 < len(coords):
                next_point = coords[i + 2]

            prev_miter, prev_scale, *segment = _get_segment(prev_point, coords[i], coords[i + 1], next_point,
                                                            self._thickness, prev_miter, prev_scale)
            triangles.extend(segment)

        return triangles

    def _update_vertices(self) -> None:
        self._vertex_list.position[:] = self._get_vertices()

    @property
    def thickness(self) -> float:
        """Get/set the line thickness of the multi-line."""
        return self._thickness

    @thickness.setter
    def thickness(self, thickness: float) -> None:
        self._thickness = thickness
        self._update_vertices()


__all__ = ('Arc', 'Box', 'BezierCurve', 'Circle', 'Ellipse', 'Line', 'MultiLine', 'Rectangle',
           'BorderedRectangle', 'Triangle', 'Star', 'Polygon', 'Sector', 'ShapeBase')
