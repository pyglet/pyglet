.. _guide_graphics:

Shaders and Rendering
=====================

At the lowest level, pyglet uses OpenGL to draw graphics in program windows.
The OpenGL interface is exposed via the :py:mod:`pyglet.gl` module
(see :ref:`guid

.. Note::
    If you intend to use OpenGL ES with pyglet on devices like the Raspberry
    Pi, please read the :ref:`programming-guide-opengles` section first.

For new users, however, using the OpenGL interface directly can be daunting.
The :py:mod:`pyglet.graphics` module provides high level abstractions that
use vertex arrays and vertex buffer objects internally to deliver high
performance. For advanced users, these abstractions can still help to avoid
a lot of the OpenGL boilerplate code that would otherwise be necessary to write
yourself.

pyglet's rendering abstractions consist of three major components:
"VertexDomains", "VertexLists", and ":py:class:`~pyglet.graphics.shader.ShaderProgram`". These will be explained
in more detail in the following sections, but a rough overview is as follows:

* :py:class:`~pyglet.graphics.shader.ShaderProgram` are at the highest level, and are simple abstractions over
  standard OpenGL Shader Programs. pyglet does full attribute and uniform
  introspection, and provides methods for automatically generating buffers
  that match the attribute formats.
* VertexDomains at at the lowest level, and users will generally not need to
  interact with them directly. They maintain ownership of raw OpenGL vertex
  array buffers, that match a specific collection of vertex attributes.
  Buffers are resized automatically as needed. Access to these buffers is
  usually not done directly, but instead through the use of VertexLists.
* VertexLists sit in-between the VertexDomains and the :py:class:`~pyglet.graphics.shader.ShaderProgram`. They
  provide a simple "view" into a portion of a VertexDomain's buffers. A
  :py:class:`~pyglet.graphics.shader.ShaderProgram` is able to generate VertexLists directly.

In summary, the process is as follows:

1. User creates a :py:class:`~pyglet.graphics.shader.ShaderProgram`. Vertex attribute metadata is introspected
   automatically.
2. User creates a new VertexList with the :py:meth:`~pyglet.graphics.shader.ShaderProgram.vertex_list` method.
   Users do not need to worry about creating the internal buffers themselves.
3. When the VertexList is created in step 2, pyglet automatically matches the
   :py:class:`~pyglet.graphics.shader.ShaderProgram`'s attributes to an appropriate VertexDomain. (If no existing
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

        uniform WindowBlock
        {
            mat4 projection;
            mat4 view;
        } window;

        void main()
        {
            gl_Position = window.projection * window.view * vec4(position, 0.0, 1.0);
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


.. note:: By default, pyglet includes and sets the ``WindowBlock`` uniform when the window is created. If you do not use
          the ``window.projection`` or ``window.view`` in your vertex shader, you will have to manage the projection
          yourself or your graphics may not display properly.

The source strings are then used to create :py:class:`~pyglet.graphics.shader.Shader` objects, which are
then linked together in a :py:class:`~pyglet.graphics.shader.ShaderProgram`. Shader objects are automatically
detached after linking the :py:class:`~pyglet.graphics.shader.ShaderProgram`, so they can be discarded
afterwards (or used again in other :py:class:`~pyglet.graphics.shader.ShaderProgram`)::

    from pyglet.graphics.shader import Shader, ShaderProgram

    vert_shader = Shader(vertex_source, 'vertex')
    frag_shader = Shader(fragment_source, 'fragment')
    program = ShaderProgram(vert_shader, frag_shader)

:py:class:`~pyglet.graphics.shader.ShaderProgram` internally introspects on creation. There are
several properties that can be queried to inspect the various vertex attributes, uniforms,
and uniform blocks that are available. For example, the `uniforms` and `attributes` properties
will return dictionaries showing the metadata for these objects::

    >>> for attribute in program.attributes.items():
    ...     print(attribute)
    ...
    ('position', {'type': 35664, 'size': 1, 'location': 0, 'count': 2, 'format': 'f'})
    ('colors', {'type': 35666, 'size': 1, 'location': 1, 'count': 4, 'format': 'f'})

    >>> for uniform in program.uniforms.items():
    ...     print(uniform)
    ...
    ('time', {'location': 2, 'length': 1, 'size': 1})


.. note::
    Most OpenGL drivers will optimize shaders during compilation. If an
    attribute or a uniform is not being used, it will often be optimized out.


Uniforms
^^^^^^^^

Uniforms are variables that can be modified after a :py:class:`~pyglet.graphics.shader.ShaderProgram` has been compiled
to change functionality during run time.

.. warning::

    When setting uniforms, the program must be binded at the time of setting. This restriction does not exist in
    OpenGL 4.1+, but if you plan to support older contexts (such as 3.3), this must be accounted for.

Uniforms can be accessed as a key on the :py:class:`~pyglet.graphics.shader.ShaderProgram`
itself. For example if your uniform in your shader is::

    uniform float time;

Then you can set (or get) the value using the uniform name as a key::

    program['time'] = delta_time


Uniform Blocks and Uniform Buffer Objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pyglet also introspects and makes Uniform Blocks (or Interface Blocks) available, including ways to manage and use Uniform Buffer Objects.

By default, Pyglet's ``projection`` and ``view`` matrix are both contained in the ``WindowBlock`` uniform block. Which looks like this in the vertex shader::

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

You can view what uniform blocks exist in a :py:class:`~pyglet.graphics.shader.ShaderProgram` using the `uniform_blocks`
property. This is a dictionary containing a Uniform Block name key to a :py:class:`~pyglet.graphics.shader.UniformBlock`
object value. In the above example, the name would be ``WindowBlock`` while the ``window`` instance identifier is used in the GLSL shader itself.

Normally with OpenGL, you would have to manually assign a global binding point value to each Uniform Block for each Shader Program, as they are created. With Pyglet, the global binding values and assignments are all taken care of internally.

Uniform Blocks can be a convenient way to update uniforms of multiple Shader Programs at once, as their data is shared. This allows you to access the same information from multiple Shader Programs without having to bind every program using it, just to modify the uniform values. This can be achieved through a :py:class:`~pyglet.graphics.shader.UniformBufferObject`.

To modify the uniforms in a :py:class:`~pyglet.graphics.shader.UniformBlock`, you must first create a
:py:class:`~pyglet.graphics.shader.UniformBufferObject` using the
:py:meth:`~pyglet.graphics.shader.UniformBlock.create_ubo` method.::

    ubo = program.uniform_blocks['WindowBlock'].create_ubo()

The :py:class:`~pyglet.graphics.shader.UniformBufferObject` can then be used as a context manager for easy
access to update its uniforms::

        with ubo as window_block:
            window_block.projection[:] = new_matrix

You can also create multiple :py:class:`~pyglet.graphics.shader.UniformBufferObject` instances if you need to swap between different sets of data. Calling :py:meth:`~pyglet.graphics.shader.UniformBufferObject.bind` will bind the buffers data to the associated binding point.

There may come a point where you don't want a specific :py:class:`~pyglet.graphics.shader.ShaderProgram`, or a group of them, to use the same uniform data set as the rest of your shaders. At this point, you will have to modify the binding point of those Uniform Blocks to one that is unused. This can be done through :py:meth:`~pyglet.graphics.shader.UniformBlock.set_binding`. Once the binding has been set, you will have to create a new :py:class:`~pyglet.graphics.shader.UniformBufferObject` using the :py:meth:`~pyglet.graphics.shader.UniformBlock.create_ubo` method again and supply it with your new data set.

.. warning:: When assigning custom binding points through py:meth:`~pyglet.graphics.shader.UniformBlock.set_binding`, it is recommended to use an unassigned binding point, as unexpected behavior may occur. A warning will be output if such a collision occurs.

             The maximum binding point value is determined by the hardware. This can be retrieved by calling :py:func:`~pyglet.graphics.shader.get_maximum_binding_count`. It is recommended to use a number
             higher than the amount of Uniform Blocks in your application to prevent collisions.

.. note:: Binding point 0 cannot be set, as it is used internally for ``WindowBlock``.


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

When using ``GL_LINE_STRIP`` and ``GL_TRIANGLE_STRIP``, care must be taken to
insert degenerate vertices at the beginning and end of each vertex list.
For example, given the vertex list::

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
    <pyglet.graphics.shader.c_float_Array_6 object at 0x7f6d3a30b1c0>
    >>> vlist.colors
    <pyglet.graphics.shader.c_float_Array_12 object at 0x7f6d3a30b0c0>
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
to activate a :py:class:`~pyglet.graphics.shader.ShaderProgram`, or bind a Texture. For example, to enable and bind
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

Shader state
^^^^^^^^^^^^
:py:class:`~pyglet.graphics.shader.ShaderProgram` can be binded (:py:meth:`~pyglet.graphics.shader.ShaderProgram.use`)
and unbinded (:py:meth:`~pyglet.graphics.shader.ShaderProgram.stop`) manually. As a convenience method, it can also act
as a context manager that handles the binding and unbinding process automatically. This may be useful if you want to
ensure the state of a :py:class:`~pyglet.graphics.shader.ShaderProgram` is active during some edge case scenarios while
also being more Pythonic.

For example::

    with shaderprogram as my_shader:
        my_shader.my_uniform = 1.0


Hierarchical state
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

Drawing order
^^^^^^^^^^^^^

:py:class:`~pyglet.graphics.vertexdomain.VertexDomain` does not attempt
to keep vertex lists in any particular order. So, any vertex lists sharing
the same primitive mode, attribute formats and group will be drawn in an
arbitrary order.  However, :py:class:`~pyglet.graphics.Group` objects do
have an ``order`` parameter that allows :py:class:`~pyglet.graphics.Batch`
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

Visibility
^^^^^^^^^^

Groups have a boolean ``visible`` property. By setting this to ``False``, any
objects in that :py:class:`~pyglet.graphics.Group` will no longer be rendered. A common use case is to
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
