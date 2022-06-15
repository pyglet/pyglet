.. _guide_graphics:

Graphics
========

At the lowest level, pyglet uses OpenGL to draw graphics in program windows.
The OpenGL interface is exposed via the :py:mod:`pyglet.gl` module
(see :ref:`guide_gl`).

For new users, however, using the OpenGL interface directly can be daunting.
The :py:mod:`pyglet.graphics` module provides high level abstractions that
use vertex arrays and vertex buffer objects internally to deliver high
performance. For advanced users, these abstractions can still help to avoid
a lot of the OpenGL boilerplate code that would otherwise be necessary to write
yourself.

pyglet's rendering abstractions cosist of three major components:
"VertexDomains", "VertexLists", and "ShaderPrograms". These will be explained
in more detail in the following sections, but a rough overview is as follows:

* ShaderPrograms are at the highest level, and are simple abstractions over
  standard OpenGL Shader Programs. pyglet does full attribute and uniform
  introspection, and provides methods for automatically generating buffers
  that match the attribute formats.
* VertexDomains at at the lowest level, and users will generally not need to
  interact with them directly. They maintain ownership of raw OpenGL vertex
  array buffers, that match a specific collection of vertex attributes.
  Buffers are resized automatically as needed. Access to these buffers is
  usually not done directly, but instead through the use of VertexLists.
* VertexLists sit in-between The VertexDomains and the ShaderPrograms. They
  provide a simple "view" into a portion of a VertexDomain's buffers. A
  ShaderProgram is able to generate VertexLists directly.

In summary, the process is as follows:

1. User creates a ShaderProgram. Vertex attribute metadata is introspected
   automatically.
2. User creates a new VertexList with the `ShaderProgram.vertex_list(...)` method.
   Users do not need to worry about creating the internal buffers themselves.
3. When the VertexList is created in step 2, pyglet automatically matches the
   ShaderProgram's attributes to an appropriate VertexDomain. (If no existing
   domain is available, a new one is created). A VertexList is generated from
   the matching VertexDomain, and returned.


Working with Shaders
--------------------

Drawing anything in modern OpenGL requires a Shader Program. Working with
Shader resources directly can be tedious, so the :py:mod:`pyglet.graphics.shader`
module provides simplified (but robust) abstractions.

See the `OpenGL Programming SDK`_ for more information on Shaders and the
OpenGL Shader Language (GLSL).

Creating a Shader Program
^^^^^^^^^^^^^^^^^^^^^^^^^

To create a Shader Program, first prepare the GLSL source as Python strings.
This can be loaded from disk, or simply defined inside of your project. Here
is simplistic Vertex and Fragment source::

    vertex_source = """#version 150 core
        in vec2 position;
        in vec4 colors;
        out vec4 vertex_colors;

        uniform mat4 projection;

        void main()
        {
            gl_Position = projection * vec4(position, 0.0, 1.0);
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

The source strings are then used to create `Shader` objects, which are
then linked together in a `ShaderProgram`. Shader objects are automatically
detached after linking the ShaderProgram, so they can be discarded
afterwards (or used again in other ShaderPrograms)::

    from pyglet.graphics.shader import Shader, ShaderProgram

    vert_shader = Shader(vertex_source, 'vertex')
    frag_shader = Shader(fragment_source, 'fragment')
    program = ShaderProgram(vert_shader, frag_shader)

ShaderPrograms internally introspect on creation. There are several properties
that can be queried to inspect the varios vertex attributes, uniforms, and uniform
blocks that are available::

    >>> for attribute in program.attributes.items():
    ...     print(attribute)
    ...
    ('position', {'type': 35664, 'size': 1, 'location': 0, 'count': 2, 'format': 'f'})
    ('colors', {'type': 35666, 'size': 1, 'location': 1, 'count': 4, 'format': 'f'})

    >>> for uniform in program.uniforms.items():
    ...     print(uniform)
    ...
    ('projection', Uniform('projection', location=0, length=16, count=1))


.. note:: Most OpenGL drivers will optimize shaders during compilation. If an
          attribute or a uniform is not being used, it will often be optimized out.

Creating Vertex Lists
^^^^^^^^^^^^^^^^^^^^^

Once you have a ShaderProgram, you need vertex data to render. As an easier alternative
to manually creating and managing vertex buffers, pyglet provides a high level
:py:class:`~pyglet.graphics.vertexdomain.VertexList` object. VertexLists are abstractions
over OpenGL buffers, with properties for easily accessing the arrays of attribute data.

The ShaderProgram provides the following two methods:
:py:meth:`~pyglet.graphics.shader.ShaderProgram.vertex_list`
and
:py:meth:`~pyglet.graphics.shader.ShaderProgram.vertex_list_indexed`

At a minimum, you must provide a `count` and `mode` when creating a VertexList.
The `count` is simply the number of vertices you wish to create. The `mode` is
the OpenGL primitive type. A ``group`` and ``batch`` parameters are also accepted
(described below).

The mode should be passed using one of the following constants:

* ``pyglet.gl.GL_POINTS``
* ``pyglet.gl.GL_LINES``
* ``pyglet.gl.GL_LINE_STRIP``
* ``pyglet.gl.GL_TRIANGLES``
* ``pyglet.gl.GL_TRIANGLE_STRIP``
* ``pyglet.gl.GL_QUADS``
* ``pyglet.gl.GL_QUAD_STRIP``

When using ``GL_LINE_STRIP``, ``GL_TRIANGLE_STRIP`` or ``GL_QUAD_STRIP`` care
must be taken to insert degenerate vertices at the beginning and end of each
vertex list.  For example, given the vertex list::

    A, B, C, D

the correct vertex list to provide the vertex list is::

    A, A, B, C, D, D

.. note:: Because of the way the high level API renders multiple primitives with
          shared state, ``GL_POLYGON``, ``GL_LINE_LOOP`` and ``GL_TRIANGLE_FAN``
          cannot be used --- the results are undefined.

Create a VertexList with three vertices, without initial data::

    vlist = program.vertex_list(3, pyglet.gl.GL_TRIANGLES)

From examining the ShaderProgram.attributes above, we know `position` and `colors`
attributes are available. The underlying arrays can be accessed directly::

    >>> vlist.position
    <pyglet.graphics.vertexattribute.c_float_Array_6 object at 0x7f6d3a30b1c0>
    >>> vlist.colors
    <pyglet.graphics.vertexattribute.c_float_Array_12 object at 0x7f6d3a30b0c0>
    >>>
    >>> vlist.position[:]
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    >>>
    >>> vlist.colors[:]
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

The `position` data is a float array with 6 elements. This attribute is a `vec2`
in the shader. Looking at the attribute metadata above, we can confirm that
`count=2`. Since the VertexList was created with 3 vertices, the length of the array
is simply 3 * 2 = 6.  Likewise, the `colors` attribute is defined as a `vec4` in the
shader, so it's simply 3 * 4 = 12.

This VertexList was created without any initial data, but it can be set (or updated)
on the property by passing a list or tuple of the correct length. For example::

    vlist.position = (100, 300, 200, 250, 200, 350)
    # or slightly faster to update in-place:
    vlist.position[:] = (100, 300, 200, 250, 200, 350)

The default data format is single precision floats, but it is possible to specify a
format using a "format string". This is passed on creation as a Python keyword
argument. The following formats are available:

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


For example, if you would like to pass the `position` data as a signed int, you
can pass the "i" format string as a Python keyword argument::

    vlist = program.vertex_list(3, pyglet.gl.GL_TRIANGLES, position='i')

By appending ``"n"`` to the format string, you can also specify that the passed
data should be "normalized" to the range ``[0, 1]``. The value is used as-is if
the data type is floating-point. If the data type is byte, short or int, the value
is divided by the maximum value representable by that type.  For example, unsigned
bytes are divided by 255 to get the normalised value.

A common case is to use normalized unsigned bytes for the color data. Simply
pass "Bn" as the format::

    vlist = program.vertex_list(3, pyglet.gl.GL_TRIANGLES, colors='Bn')


Passing Initial Data
~~~~~~~~~~~~~~~~~~~~

Rather than setting the data *after* creation of a VertexList, you can also
easily pass initial arrays of data on creation. You do this by passing the format
and the data as a tuple, using a keyword argument as above. To set the position
and color data on creation::

    vlist = program.vertex_list(3, pyglet.gl.GL_TRIANGLES,
                                position=('f', (200, 400, 300, 350, 300, 450)),
                                colors=('Bn', (255, 0, 0, 255,  0, 255, 0, 255,  75, 75, 255, 255),)


Indexed Rendering
~~~~~~~~~~~~~~~~~

Vertices can also be drawn out of order and more than once by using the
indexed rendering. This requires a list of integers giving the indices into
the vertex data. You also use the
:py:meth:`~pyglet.graphics.shader.ShaderProgram.vertex_list_indexed` method
instead of :py:meth:`~pyglet.graphics.shader.ShaderProgram.vertex_list`. The
API is almost identical, except for the required index list.

The following example creates four vertices, and provides their positional data.
By passing an index list of [0, 1, 2, 0, 2, 3], we creates two adjacent triangles,
and the shared vertices are reused::

    vlist = program.vertex_list_indexed(4, pyglet.gl.GL_TRIANGLES,
        [0, 1, 2, 0, 2, 3],
        position=('i', (100, 100,  150, 100,  150, 150,  100, 150)),
    )

Note that the first argument gives the number of vertices in the data, not the
number of indices (which is implicit on the length of the index list given in
the third argument).

Resource Management
~~~~~~~~~~~~~~~~~~~

VertexLists reference data that is stored on the GPU, but they do not own
any data themselves. For this reason, it's not strictly necessary to keep a
reference to a VertexList after creating it. If you wish to delete the data
from the GPU, however, it can only be done with the `VertexList.delete()`
method. Likewise, you can only update a VertexList's vertex data if you have
kept a reference to it. For that reason, you should keep a reference to any
objects that you might want to modify or delete from your scene after creation.

.. _guide_batched-rendering:

Batched rendering
-----------------

For optimal OpenGL performance, you should render as many vertex lists as
possible in a single ``draw`` call.  Internally, pyglet uses
:py:class:`~pyglet.graphics.vertexdomain.VertexDomain` and
:py:class:`~pyglet.graphics.vertexdomain.IndexedVertexDomain` to keep VertexLists
that share the same attribute formats in adjacent areas of memory.
The entire domain of vertex lists can then be drawn at once, without calling
:py:meth:`~pyglet.graphics.vertexdomain.VertexList.draw` on each individual
list.

It is quite difficult and tedious to write an application that manages vertex
domains itself, though.  In addition to maintaining a vertex domain for each
ShaderProgram and set of attribute formats, domains must also be separated by
primitive mode and required OpenGL state.

The :py:class:`~pyglet.graphics.Batch` class implements this functionality,
grouping related vertex lists together and sorting by OpenGL state
automatically. A batch is created with no arguments::

    batch = pyglet.graphics.Batch()

To use a Batch, you simply pass it as a (keyword) argument when creating
any of pyglet's high level objects. For example::

    vlist = program.vertex_list(3, pyglet.gl.GL_TRIANGLES, batch=batch)
    sprite = pyglet.sprite.Sprite(img, x, y, batch=batch)

To draw all objects contained in the batch at once::

    batch.draw()

For batches containing many objects, this gives a significant performance
improvement over drawing individually. It's generally recommended to always
use Batches.

Setting the OpenGL state
^^^^^^^^^^^^^^^^^^^^^^^^

Before drawing in OpenGL, it's necessary to set certain state. You might need
to activate a ShaderProgram, or bind a Texture. For example, to enable and bind
a texture requires the following before drawing::

    from pyglet.gl import *
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(texture.target, texture.id)

With a :py:class:`~pyglet.graphics.Group` these state changes can be
encapsulated and associated with the vertex lists they affect.
Subclass :py:class:`~pyglet.graphics.Group` and override the `Group.set_state`
and `Group.unset_state` methods to perform the required state changes::

    class CustomGroup(pyglet.graphics.Group):
        def __init__(self, texture, shaderprogram):
            super().__init__()
            self.texture = texture
            self.program = shaderprogram

        def set_state(self):
            self.program.use()
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(self.texture.target, self.texture.id)

        def unset_state(self):
            self.program.stop()

An instance of this group can now be attached to vertex lists::

    custom_group = CustomGroup()
    vertex_list = program.vertex_list(2, pyglet.gl.GL_POINTS, batch, custom_group,
        position=('i', (10, 15, 30, 35)),
        colors=('Bn', (0, 0, 255, 0, 255, 0))
    )

The :py:class:`~pyglet.graphics.Batch` ensures that the appropriate
``set_state`` and ``unset_state`` methods are called before and after
the vertex lists that use them.

hierarchical state
^^^^^^^^^^^^^^^^^^

Groups have a `parent` attribute that allows them to be implicitly organised
in a tree structure.  If groups **B** and **C** have parent **A**, then the
order of ``set_state`` and ``unset_state`` calls for vertex lists in a batch
will be::

    A.set_state()

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
            glActiveTexture(GL_TEXTURE0)

        def unset_state(self):
            # not necessary


    texture_enable_group = TextureEnableGroup()


    class TextureBindGroup(pyglet.graphics.Group):
        def __init__(self, texture):
            super().__init__(parent=texture_enable_group)
            assert texture.target = GL_TEXTURE_2D
            self.texture = texture

        def set_state(self):
            glBindTexture(GL_TEXTURE_2D, self.texture.id)

        def unset_state(self):
            # not required

        def __eq__(self, other):
            return (self.__class__ is other.__class__ and
                    self.texture.id == other.texture.id and
                    self.texture.target == other.texture.target and
                    self.parent == other.parent)

        def __hash__(self):
            return hash((self.texture.id, self.texture.target))

    program.vertex_list_indexed(4, GL_TRIANGLES, indices, batch, TextureBindGroup(texture1))
    program.vertex_list_indexed(4, GL_TRIANGLES, indices, batch, TextureBindGroup(texture2))
    program.vertex_list_indexed(4, GL_TRIANGLES, indices, batch, TextureBindGroup(texture1))


.. note:: The ``__eq__`` method on the group allows the :py:class:`~pyglet.graphics.Batch`
          to automatically merge the two identical ``TextureBindGroup`` instances.
          For optimal performance, always take care to ensure your custom Groups have
          correct ``__eq__`` and ``__hash__`` methods defined.

drawing order
^^^^^^^^^^^^^

:py:class:`~pyglet.graphics.vertexdomain.VertexDomain` does not attempt
to keep vertex lists in any particular order. So, any vertex lists sharing
the same primitive mode, attribute formats and group will be drawn in an
arbitrary order.  However, :py:class:`~pyglet.graphics.Group` objects do
have an `order` parameter that allows `:py:class:`~pyglet.graphics.Batch`
to sort objects sharing the same parent. In summary, inside of a Batch:

1. Groups are sorted by their parent (if any). (Parent Groups may also be ordered).
2. Groups are sorted by their `order` attribute. There is one draw call per order level.

A common use pattern is to create several Groups for each level in your scene.
For instance, a "background" group that is drawn before the "foreground" group::

    background = pyglet.graphics.Group(0)
    foreground = pyglet.graphics.Group(1)

    pyglet.sprite.Sprite(image, batch=batch, group=background)
    pyglet.sprite.Sprite(image, batch=batch, group=foreground)

By combining hierarchical groups with ordered groups it is possible to
describe an entire scene within a single :py:class:`~pyglet.graphics.Batch`,
which then renders it as efficiently as possible.

visibility
^^^^^^^^^^

Groups have a boolean `visible` property. By setting this to `False`, any
objects in that Group will no longer be rendered. A common use case is to
create a parent Group specifically for this purpose, often when combined
with custom ordering (as described above). For example, you might create
a "HUD" Group, which is ordered to draw in front of everything else. The
"HUD" Group's visibility can then easily be toggled.


Batches and groups in other modules
-----------------------------------

The :py:class:`~pyglet.sprite.Sprite`, :py:class:`~pyglet.text.Label`,
:py:class:`~pyglet.text.layout.TextLayout`, and other default classes all
accept ``batch`` and ``group`` parameters in their constructors. This allows
you to add any of these higher-level pyglet drawables into arbitrary places in
your rendering code.

For example, multiple sprites can be grouped into a single batch and then
drawn at once, instead of calling ``Sprite.draw()`` on each one individually::

    batch = pyglet.graphics.Batch()
    sprites = [pyglet.sprite.Sprite(image, batch=batch) for i in range(100)]

    batch.draw()

The ``group`` parameter can be used to set the drawing order (and hence which
objects overlap others) within a single batch, as described on the previous page.

In general you should batch all drawing objects into as few batches as
possible, and use groups to manage the draw order and other OpenGL state
changes for optimal performance.

If you are creating your own drawable
classes, consider adding ``batch`` and ``group`` parameters in a similar way.

.. _OpenGL Programming SDK: http://www.opengl.org/sdk
