.. _guide_graphics:

Graphics
========

At the lowest level, pyglet uses OpenGL to draw graphics in program windows.
The OpenGL interface is exposed via the :py:mod:`pyglet.gl` module
(see :ref:`guide_gl`).

Using the OpenGL interface directly, however, can be difficult to do
efficiently. The :py:mod:`pyglet.graphics` module provides a simpler means
for drawing graphics that uses vertex arrays and vertex buffer objects
internally to deliver better performance.

Drawing primitives
------------------

The :py:mod:`pyglet.graphics` module draws the OpenGL primitive objects by
a mode denoted by the constants

* ``pyglet.gl.GL_POINTS``
* ``pyglet.gl.GL_LINES``
* ``pyglet.gl.GL_LINE_LOOP``
* ``pyglet.gl.GL_LINE_STRIP``
* ``pyglet.gl.GL_TRIANGLES``
* ``pyglet.gl.GL_TRIANGLE_STRIP``
* ``pyglet.gl.GL_TRIANGLE_FAN``
* ``pyglet.gl.GL_QUADS``
* ``pyglet.gl.GL_QUAD_STRIP``
* ``pyglet.gl.GL_POLYGON``

See the `OpenGL Programming Guide <http://www.glprogramming.com/red/>`_ for a
description of each of mode.

Each primitive is made up of one or more vertices.  Each vertex is specified
with either 2, 3 or 4 components (for 2D, 3D, or non-homogeneous coordinates).
The data type of each component can be either int or float.

Use :py:func:`pyglet.graphics.draw` to directly draw a primitive.
The following example draws two points at coordinates (10, 15) and (30, 35)::

    pyglet.graphics.draw(2, pyglet.gl.GL_POINTS,
        ('v2i', (10, 15, 30, 35))
    )

The first and second arguments to the function give the number of vertices to
draw and the primitive mode, respectively.  The third argument is a "data
item", and gives the actual vertex data.

However, because of the way the graphics API renders multiple primitives with
shared state, ``GL_POLYGON``, ``GL_LINE_LOOP`` and ``GL_TRIANGLE_FAN`` cannot
be used --- the results are undefined.

Alternatively, the ``NV_primitive_restart`` extension can be used if it is
present.  This also permits use of ``GL_POLYGON``, ``GL_LINE_LOOP`` and
``GL_TRIANGLE_FAN``.   Unfortunately the extension is not provided by older
video drivers, and requires indexed vertex lists.

Because vertex data can be supplied in several forms, a "format string" is
required.  In this case, the format string is ``"v2i"``, meaning the vertex
position data has two components (2D) and int type.

The following example has the same effect as the previous one, but uses
floating point data and 3 components per vertex::

    pyglet.graphics.draw(2, pyglet.gl.GL_POINTS,
        ('v3f', (10.0, 15.0, 0.0, 30.0, 35.0, 0.0))
    )

Vertices can also be drawn out of order and more than once by using the
:py:func:`pyglet.graphics.draw_indexed` function.  This requires a list of
integers giving the indices into the vertex data.  The following example
draws the same two points as above, but indexes the vertices (sequentially)::

    pyglet.graphics.draw_indexed(2, pyglet.gl.GL_POINTS,
        [0, 1],
        ('v2i', (10, 15, 30, 35))
    )

This second example is more typical; two adjacent triangles are drawn, and the
shared vertices are reused with indexing::

    pyglet.graphics.draw_indexed(4, pyglet.gl.GL_TRIANGLES,
        [0, 1, 2, 0, 2, 3],
        ('v2i', (100, 100,
                 150, 100,
                 150, 150,
                 100, 150))
    )

Note that the first argument gives the number of vertices in the data, not the
number of indices (which is implicit on the length of the index list given in
the third argument).

When using ``GL_LINE_STRIP``, ``GL_TRIANGLE_STRIP`` or ``GL_QUAD_STRIP`` care
must be taken to insert degenerate vertices at the beginning and end of each
vertex list.  For example, given the vertex list::

    A, B, C, D

the correct vertex list to provide the vertex list is::

    A, A, B, C, D, D


Vertex attributes
-----------------

Besides the required vertex position, vertices can have several other numeric
attributes.  Each is specified in the format string with a letter, the number
of components and the data type.

Each of the attributes is described in the table below with the set of valid
format strings written as a regular expression (for example, ``"v[234][if]"``
means ``"v2f"``, ``"v3i"``, ``"v4f"``, etc. are all valid formats).

Some attributes have a "recommended" format string, which is the most efficient
form for the video driver as it requires less conversion.

    .. list-table::
        :header-rows: 1

        * - Attribute
          - Formats
          - Recommended
        * - Vertex position
          - ``"v[234][sifd]"``
          - ``"v[234]f"``
        * - Color
          - ``"c[34][bBsSiIfd]"``
          - ``"c[34]B"``
        * - Edge flag
          - ``"e1[bB]"``
          -
        * - Fog coordinate
          - ``"f[1234][bBsSiIfd]"``
          -
        * - Normal
          - ``"n3[bsifd]"``
          - ``"n3f"``
        * - Secondary color
          - ``"s[34][bBsSiIfd]"``
          - ``"s[34]B"``
        * - Texture coordinate
          - ``"[0-31]?t[234][sifd]"``
          - ``"[0-31]?t[234]f"``
        * - Generic attribute
          - ``"[0-15]g(n)?[1234][bBsSiIfd]"``
          -

The possible data types that can be specified in the format string are
described below.

    .. list-table::
        :header-rows: 1

        * - Format
          - Type
          - Python type
        * - ``"b"``
          - Signed byte
          - int
        * - ``"B"``
          - Unsigned byte
          - int
        * - ``"s"``
          - Signed short
          - int
        * - ``"S"``
          - Unsigned short
          - int
        * - ``"i"``
          - Signed int
          - int
        * - ``"I"``
          - Unsigned int
          - int
        * - ``"f"``
          - Single precision float
          - float
        * - ``"d"``
          - Double precision float
          - float

The following attributes are normalised to the range ``[0, 1]``.  The value is
used as-is if the data type is floating-point.  If the data type is byte,
short or int, the value is divided by the maximum value representable by that
type.  For example, unsigned bytes are divided by 255 to get the normalised
value.

* Color
* Secondary color
* Generic attributes with the ``"n"`` format given.

Texture coordinate attributes may optionally be preceded by a texture unit
number.  If unspecified, texture unit 0 (``GL_TEXTURE0``) is implied.  It is
the application's responsibility to ensure that the OpenGL version is adequate
and that the specified texture unit is within the maximum allowed by the
implementation.

Up to 16 generic attributes can be specified per vertex, and can be used by
shader programs for any purpose (they are ignored in the fixed-function
pipeline).  For the other attributes, consult the OpenGL programming guide for
details on their effects.

When using the `pyglet.graphics.draw` and related functions, attribute data is
specified alongside the vertex position data.  The following example
reproduces the two points from the previous page, except that the first point
is blue and the second green::

    pyglet.graphics.draw(2, pyglet.gl.GL_POINTS,
        ('v2i', (10, 15, 30, 35)),
        ('c3B', (0, 0, 255, 0, 255, 0))
    )

It is an error to provide more than one set of data for any attribute, or to
mismatch the size of the initial data with the number of vertices specified in
the first argument.

Vertex lists
------------

There is a significant overhead in using :py:func:`pyglet.graphics.draw` and
:py:func:`pyglet.graphics.draw_indexed` due to pyglet interpreting and
formatting the vertex data for the video device.  Usually the data drawn in
each frame (of an animation) is identical or very similar to the previous
frame, so this overhead is unnecessarily repeated.

A :py:class:`~pyglet.graphics.vertexdomain.VertexList` is a list of vertices
and their attributes, stored in an efficient manner that's suitable for
direct upload to the video card. On newer video cards (supporting
OpenGL 1.5 or later) the data is actually stored in video memory.

Create a :py:class:`~pyglet.graphics.vertexdomain.VertexList` for a set of
attributes and initial data with :py:func:`pyglet.graphics.vertex_list`.
The following example creates a vertex list with the two coloured points
used in the previous page::

    vertex_list = pyglet.graphics.vertex_list(2,
        ('v2i', (10, 15, 30, 35)),
        ('c3B', (0, 0, 255, 0, 255, 0))
    )

To draw the vertex list, call its :py:meth:`~pyglet.graphics.vertexdomain.VertexList.draw` method::

    vertex_list.draw(pyglet.gl.GL_POINTS)

Note that the primitive mode is given to the draw method, not the vertex list
constructor.  Otherwise the :py:func:`pyglet.graphics.vertex_list` function
takes the same arguments as :py:class:`pyglet.graphics.draw`, including
any number of vertex attributes.

Because vertex lists can reside in video memory, it is necessary to call the
`delete` method to release video resources if the vertex list isn't going to
be used any more (there's no need to do this if you're just exiting the
process).

Updating vertex data
^^^^^^^^^^^^^^^^^^^^

The data in a vertex list can be modified.  Each vertex attribute (including
the vertex position) appears as an attribute on the
:py:class:`~pyglet.graphics.vertexdomain.VertexList` object.
The attribute names are given in the following table.

    .. list-table::
        :header-rows: 1

        * - Vertex attribute
          - Object attribute
        * - Vertex position
          - ``vertices``
        * - Color
          - ``colors``
        * - Edge flag
          - ``edge_flags``
        * - Fog coordinate
          - ``fog_coords``
        * - Normal
          - ``normals``
        * - Secondary color
          - ``secondary_colors``
        * - Texture coordinate
          - ``tex_coords`` [#multitex]_
        * - Generic attribute
          - *Inaccessible*

In the following example, the vertex positions of the vertex list are updated
by replacing the ``vertices`` attribute::

    vertex_list.vertices = [20, 25, 40, 45]

The attributes can also be selectively updated in-place::

    vertex_list.vertices[:2] = [30, 35]

Similarly, the color attribute of the vertex can be updated::

    vertex_list.colors[:3] = [255, 0, 0]

For large vertex lists, updating only the modified vertices can have a
perfomance benefit, especially on newer graphics cards.

Attempting to set the attribute list to a different size will cause an error
(not necessarily immediately, either).  To resize the vertex list, call
`VertexList.resize` with the new vertex count.  Be sure to fill in any
newly uninitialised data after resizing the vertex list.

Since vertex lists are mutable, you may not necessarily want to initialise
them with any particular data.  You can specify just the format string in
place of the ``(format, data)`` tuple in the data arguments `vertex_list`
function.  The following example creates a vertex list of 1024 vertices with
positional, color, texture coordinate and normal attributes::

    vertex_list = pyglet.graphics.vertex_list(1024, 'v3f', 'c4B', 't2f', 'n3f')

Data usage
^^^^^^^^^^

By default, pyglet assumes vertex data will be updated less often than it is
drawn, but more often than just during initialisation.  You can override
this assumption for each attribute by affixing a usage specification
onto the end of the format string, detailed in the following table:

    .. list-table::
        :header-rows: 1

        * - Usage
          - Description
        * - ``"/static"``
          - Data is never or rarely modified after initialisation
        * - ``"/dynamic"``
          - Data is occasionally modified (default)
        * - ``"/stream"``
          - Data is updated every frame

In the following example a vertex list is created in which the positional data
is expected to change every frame, but the color data is expected to remain
relatively constant::

    vertex_list = pyglet.graphics.vertex_list(1024, 'v3f/stream', 'c4B/static')

The usage specification affects how pyglet lays out vertex data in memory,
whether or not it's stored on the video card, and is used as a hint to OpenGL.
Specifying a usage does not affect what operations are possible with a vertex
list (a ``static`` attribute can still be modified), and may only have
performance benefits on some hardware.

Indexed vertex lists
^^^^^^^^^^^^^^^^^^^^

:py:class:`~pyglet.graphics.vertexdomain.IndexedVertexList` performs the same
role as :py:class:`~pyglet.graphics.vertexdomain.VertexList`, but for indexed
vertices.  Use :py:func:`pyglet.graphics.vertex_list_indexed` to construct an
indexed vertex list, and update the
:py:class:`~pyglet.graphics.vertexdomain.IndexedVertexList.indices` sequence to
change the indices.

.. [#multitex] Only texture coordinates for texture unit 0 are accessible
    through this attribute.

.. _guide_batched-rendering:

Batched rendering
-----------------

For optimal OpenGL performance, you should render as many vertex lists as
possible in a single ``draw`` call.  Internally, pyglet uses
:py:class:`~pyglet.graphics.vertexdomain.VertexDomain` and
:py:class:`~pyglet.graphics.vertexdomain.IndexedVertexDomain` to keep vertex
lists that share the same attribute formats in adjacent areas of memory.
The entire domain of vertex lists can then be drawn at once, without calling
:py:meth:`~pyglet.graphics.vertexdomain.VertexList.draw` on each individual
list.

It is quite difficult and tedious to write an application that manages vertex
domains itself, though.  In addition to maintaining a vertex domain for each
set of attribute formats, domains must also be separated by primitive mode and
required OpenGL state.

The :py:class:`~pyglet.graphics.Batch` class implements this functionality,
grouping related vertex lists together and sorting by OpenGL state
automatically. A batch is created with no arguments::

    batch = pyglet.graphics.Batch()

Vertex lists can now be created with the :py:meth:`~pyglet.graphics.Batch.add`
and :py:meth:`~pyglet.graphics.Batch.add_indexed` methods instead of
:py:func:`pyglet.graphics.vertex_list` and
:py:func:`pyglet.graphics.vertex_list_indexed` functions.  Unlike the module
functions, these methods accept a ``mode`` parameter (the primitive mode)
and a ``group`` parameter (described below).

The two coloured points from previous pages can be added to a batch as a
single vertex list with::

    vertex_list = batch.add(2, pyglet.gl.GL_POINTS, None,
        ('v2i', (10, 15, 30, 35)),
        ('c3B', (0, 0, 255, 0, 255, 0))
    )

The resulting `vertex_list` can be modified as described in the previous
section.  However, instead of calling ``VertexList.draw`` to draw it, call
``Batch.draw()`` to draw all vertex lists contained in the batch at once::

    batch.draw()

For batches containing many vertex lists this gives a significant performance
improvement over drawing individual vertex lists.

To remove a vertex list from a batch, call ``VertexList.delete()``. If you
don't need to modify or delete vertex lists after adding them to the batch,
you can simply ignore the return value of the
:py:meth:`~pyglet.graphics.Batch.add` and
:py:meth:`~pyglet.graphics.Batch.add_indexed` methods.

Setting the OpenGL state
^^^^^^^^^^^^^^^^^^^^^^^^

In order to achieve many effects in OpenGL one or more global state parameters
must be set.  For example, to enable and bind a texture requires::

    from pyglet.gl import *
    glEnable(texture.target)
    glBindTexture(texture.target, texture.id)

before drawing vertex lists, and then::

    glDisable(texture.target)

afterwards to avoid interfering with later drawing commands.

With a :py:class:`~pyglet.graphics.Group` these state changes can be
encapsulated and associated with the vertex lists they affect.
Subclass :py:class:`~pyglet.graphics.Group` and override the `Group.set_state`
and `Group.unset_state` methods to perform the required state changes::

    class CustomGroup(pyglet.graphics.Group):
        def set_state(self):
            glEnable(texture.target)
            glBindTexture(texture.target, texture.id)

        def unset_state(self):
            glDisable(texture.target)

An instance of this group can now be attached to vertex lists in the batch::

    custom_group = CustomGroup()
    vertex_list = batch.add(2, pyglet.gl.GL_POINTS, custom_group,
        ('v2i', (10, 15, 30, 35)),
        ('c3B', (0, 0, 255, 0, 255, 0))
    )

The :py:class:`~pyglet.graphics.Batch` ensures that the appropriate
``set_state`` and ``unset_state`` methods are called before and after
the vertex lists that use them.

Hierarchical state
^^^^^^^^^^^^^^^^^^

Groups have a `parent` attribute that allows them to be implicitly organised
in a tree structure.  If groups **B** and **C** have parent **A**, then the
order of ``set_state`` and ``unset_state`` calls for vertex lists in a batch
will be::

    A.set_state()
    # Draw A vertices
    B.set_state()
    # Draw B vertices
    B.unset_state()
    C.set_state()
    # Draw C vertices
    C.unset_state()
    A.unset_state()

This is useful to group state changes into as few calls as possible.  For
example, if you have a number of vertex lists that all need texturing enabled,
but have different bound textures, you could enable and disable texturing in
the parent group and bind each texture in the child groups.  The following
example demonstrates this::

    class TextureEnableGroup(pyglet.graphics.Group):
        def set_state(self):
            glEnable(GL_TEXTURE_2D)

        def unset_state(self):
            glDisable(GL_TEXTURE_2D)

    texture_enable_group = TextureEnableGroup()

    class TextureBindGroup(pyglet.graphics.Group):
        def __init__(self, texture):
            super(TextureBindGroup, self).__init__(parent=texture_enable_group)
            assert texture.target = GL_TEXTURE_2D
            self.texture = texture

        def set_state(self):
            glBindTexture(GL_TEXTURE_2D, self.texture.id)

        # No unset_state method required.

        def __eq__(self, other):
            return (self.__class__ is other.__class__ and
                    self.texture.id == other.texture.id and
                    self.texture.target == other.texture.target and
                    self.parent == other.parent)

        def __hash__(self):
            return hash((self.texture.id, self.texture.target))

    batch.add(4, GL_QUADS, TextureBindGroup(texture1), 'v2f', 't2f')
    batch.add(4, GL_QUADS, TextureBindGroup(texture2), 'v2f', 't2f')
    batch.add(4, GL_QUADS, TextureBindGroup(texture1), 'v2f', 't2f')

Note the use of an ``__eq__`` method on the group to allow
:py:class:`~pyglet.graphics.Batch` to merge the two ``TextureBindGroup``
identical instances.

Sorting vertex lists
^^^^^^^^^^^^^^^^^^^^

:py:class:`~pyglet.graphics.vertexdomain.VertexDomain` does not attempt
to keep vertex lists in any particular order. So, any vertex lists sharing
the same primitive mode, attribute formats and group will be drawn in an
arbitrary order.  However, :py:class:`~pyglet.graphics.Batch` will sort
:py:class:`~pyglet.graphics.Group` objects sharing the same parent by
their ``__cmp__`` method.  This allows groups to be ordered.

The :py:class:`~pyglet.graphics.OrderedGroup` class is a convenience
group that does not set any OpenGL state, but is parameterised by an
integer giving its draw order.  In the following example a number of
vertex lists are grouped into a "background" group that is drawn before
the vertex lists in the "foreground" group::

    background = pyglet.graphics.OrderedGroup(0)
    foreground = pyglet.graphics.OrderedGroup(1)

    batch.add(4, GL_QUADS, foreground, 'v2f')
    batch.add(4, GL_QUADS, background, 'v2f')
    batch.add(4, GL_QUADS, foreground, 'v2f')
    batch.add(4, GL_QUADS, background, 'v2f', 'c4B')

By combining hierarchical groups with ordered groups it is possible to
describe an entire scene within a single :py:class:`~pyglet.graphics.Batch`,
which then renders it as efficiently as possible.

Batches and groups in other modules
-----------------------------------

The :py:class:`~pyglet.sprite.Sprite`, :py:class:`~pyglet.text.Label` and
:py:class:`~pyglet.text.layout.TextLayout` classes all accept ``batch`` and
``group`` parameters in their constructors.  This allows you to add any of
these higher-level pyglet drawables into arbitrary places in your rendering
code.

For example, multiple sprites can be grouped into a single batch and then
drawn at once, instead of calling ``Sprite.draw()`` on each one individually::

    batch = pyglet.graphics.Batch()
    sprites = [pyglet.sprite.Sprite(image, batch=batch) for i in range(100)]

    batch.draw()

The ``group`` parameter can be used to set the drawing order (and hence which
objects overlap others) within a single batch, as described  on the previous
page.

In general you should batch all drawing objects into as few batches as
possible, and use groups to manage the draw order and other OpenGL state
changes for optimal performance.   If you are creating your own drawable
classes, consider adding ``batch`` and ``group`` parameters in a similar way.


Shader program details
----------------------

* VAOs are generated at the Batch level.
* Groups are used to segregate shader programs. Group set/unset state_calls
  are used to activate and deactivate these programs.
* Only one texture unit (GL_TEXTURE0) is currently being used by the image module,.
  and therefore textures.

