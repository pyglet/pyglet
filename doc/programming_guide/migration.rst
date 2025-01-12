.. _migration:

Migrating from pyglet 2.0
=========================
This page helps projects upgrade from pyglet 2.0.

Several improvements required small breaking changes in pyglet
2.1. These include improvements to:

* Usability in text and other areas
* Type checking and annotations
* Code quality and organization

If your project stops working after upgrading, this page
will help you start updating. To report a missing change
or a bug, please use `GitHub Issues`_ or reach out via one
of the :ref:`contributor communication <contributor-communication>`
channels.

.. _GitHub Issues: https://github.com/pyglet/pyglet/issues


Setting pyglet Options
----------------------

The :py:attr:`pyglet.options` attribute now uses a dedicated class with new features.

The Options Object
^^^^^^^^^^^^^^^^^^
The :py:attr:`pyglet.options` attribute now uses a :py:class:`pyglet.Options` class.

Although it is now a :py:func:`dataclass <dataclasses.dataclass>` instead of a
:py:class:`dict`, it supports both of the following access approaches:

* attribute style (:py:attr:`pyglet.debug_gl <pyglet.Options.debug_gl>`)
* subscript / :py:class:`dict` style (``pyglet.options['debug_gl']``)


Window "HiDPI" support
^^^^^^^^^^^^^^^^^^^^^^
The v2.1 release now provides a lot more control over how modern 'HiDPI' displays
are treated. This includes "retina" displays, or any display that has a non-100%
zoom or scale (such as 4K displays). This is exposed as new pyglet option. Please
see the following to learn more:

* :py:attr:`pyglet.options.dpi_scaling <pyglet.Options.dpi_scaling>`
* :py:attr:`pyglet.Options`


Labels & Text Layouts
---------------------

Argument Consistency
^^^^^^^^^^^^^^^^^^^^

The positional arguments for creating :py:class:`pyglet.text` layouts
and labels now all *start* with similar argument orders. This helps
you:

* switch between labels and layouts
* create custom subclasses

The order *after* the initial arguments may differ. Please see any
relevant API documentation to learn more.

Layout Arguments
""""""""""""""""
All :py:mod:`pyglet.text.layout` types now *start* with the same positional
argument order::

    TextLayout(document, x, y, z, width, height, anchor_x, anchor_y, rotation, ...)
    ScrollableTextLayout(document, x, y, z, width, height, anchor_x, anchor_y, rotation, ...)
    IncrementalTextLayout(document, x, y, z, width, height, anchor_x, anchor_y, rotation, ...)

These types all take a concrete instance of an
:py:class:`~pyglet.text.layout.AbstractDocument` subclass as their
first argument. Subsequent arguments may differ.

Please see the following to learn more:

* :py:class:`pyglet.text.layout.TextLayout`
* :py:class:`pyglet.text.layout.ScrollableTextLayout`
* :py:class:`pyglet.text.layout.IncrementalTextLayout`

Label Arguments
"""""""""""""""
The label classes now also share similar early argument orders.

Only :py:class:`~pyglet.text.DocumentLabel` is identical to layouts in
its initial arguments. The others both take a string ``text`` argument
as their first argument::

    DocumentLabel(document, x, y, z, width, height, anchor_x, anchor_y, rotation, ...)
    Label(text, x, y, z, width, height, anchor_x, anchor_y, rotation, ...)
    HTMLLabel(text, x, y, z, width, height, anchor_x, anchor_y, rotation, ...)

As with layouts, the subsequent arguments may vary. Please see the following
to learn more:

* :py:class:`pyglet.text.DocumentLabel`
* :py:class:`pyglet.text.Label`
* :py:class:`pyglet.text.HTMLLabel`


Replace Bold With Weight
^^^^^^^^^^^^^^^^^^^^^^^^

The string ``weight`` argument is more flexible than the ``bold`` argument it replaces.

The ``weight`` argument now allows you too choose a desired font weight from
those your specific font and rendering back-end support. For known cross-platform
``weight`` strings, please see :py:class:`pyglet.text.Weight`.

* The names and values mimic OpenType and CSS (``"bold"``, ``"thin"``, ``"extrabold"``, etc)
* Some rendering back-ends *may* support more names than listed there

Shapes
------
For consistency with the rest of the library, it was decided to represent
all angles in degrees instead of radians. Previously we had a mix of both,
which lead to some confusion. Using degrees also makes the API consistent
with Sprites and other rotatable objects, which have long used degrees.

The arguments for :py:class:`~pyglet.shapes.Line` have changed slightly.
Instead of "width", we now use "thickness". This matches with other shapes
that are made up of line segments. For example the :py:class:`~pyglet.shapes.Box`
shape, which already uses "width" (and height) to mean it's overall size.
Going forward, any shape that is made up of lines should use `thickness`
for the thickness/width of those lines.

.. _migration-controllers:

Controllers
-----------
The Controller interface has been changed slightly. Analog sticks and dpad
events now dispatch :py:class:`~pyglet.math.Vec2`, instead of individual float
or boolean values. This can potentially save a few lines of code, and gives
easy access to several helper methods found on the Vec classes. For instance,
where you had to do this in the past::

    @controller.event
    def on_dpad_motion(controller, dpleft, dpright, dpup, dpdown):
        if dpleft:
            # move left
        if dpright:
            # move right
        if dpright and dpdown:
            # move diagonal, but have to normalize the values by yourself

You now get a Vec2 instead of booleans that can be used directly::

    @controller.event
    def on_dpad_motion(controller, vector):
        player_position += vector * PLAYER_SPEED
        # Easily normalize for diagonal values:
        player_position += vector.normalize() * PLAYER_SPEED

This should be more efficient in most cases. If you want to access the values
as booleans for a quick workaround when migrating, you can do something like this::

    dpleft, dpright, dpup, dpdown = vector.x < 0, vector.x > 0, vector.y > 0, vector.y < 0


Vectors can also be useful for analog sticks, because it gives an easy way to
calculate dead-zones using :py:meth:`~pyglet.math.Vec2.length`. For example::

    @controller.event
    def on_stick_motion(controller, name, vector):
        if vector.length() <= DEADZONE:
            return
        elif name == "leftstick":
            # Do something with the 2D vector
        elif name == "rightstick":
            # Do something with the 2D vector

Normalization of vectors can also be useful for some analog sticks. When dealing
with Controllers that have non-circular gates, the The absolute values of their
combined x and y axis can sometimes exceed ``1.0``. Vector normalization can ensure
that the maximum value stays within range. For example::

            vector = min(vector, vector.normalize())

You can also directly access the individual :py:attr:`~pyglet.math.Vec2.x` and
:py:attr:`~pyglet.math.Vec2.y` attributes or unpack a vector:

.. code-block:: python

   # Direct access
   x = vector2.x
   y = vector2.y

   # Unpacking-style access
   x, y = vector2

Please see the following to learn more about vectors in pyglet 2.1:

* The :ref:`migration-math` section of this page
* :py:class:`pyglet.math.Vec2`

Gui
---

Widget Event Dispatching
^^^^^^^^^^^^^^^^^^^^^^^^
All widget events now dispatch the widget instance itself as the first argument.

This is similar to how Controller/Joystick events are implemented. It allows
handler functions re-used across multiple widgets to determine which specific
widget dispatched an event.

Button Argument Names
^^^^^^^^^^^^^^^^^^^^^

The :py:class:`~pyglet.gui.widgets.ToggleButton` and :py:class:`~pyglet.gui.widgets.PushButton`
widgets now use ``pressed`` and ``unpressed`` for their image arguments.

.. _migration-math:

Math
----
The :py:mod:`~pyglet.math` module includes a number of performance and
usability changes.

Immutable Vectors and Matrices
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All :py:mod:`~pyglet.math` datatypes are now :py:class:`typing.NamedTuple`
subclasses. This provides multiple benefits:

* More consistent creation syntax
* Vectors and matrices are now hashable

  * They can be :py:class:`dict` keys or :py:class:`set` members
  * Combine with ``/``, ``//``, :py:func:`round` or :py:func:`math.floor` for easy spatial hashing

* Cleaner controller code (see :ref:`migration-controllers`)

.. important:: The mypy typechecker is incompatible with :py:mod:`pyglet.math`.

               When typechecking, it is a good idea to:

               1. exclude :py:mod:`pyglet.math` from mypy checks
               2. use pyright instead (pylance in VS Code)


Matrix Creation Syntax
^^^^^^^^^^^^^^^^^^^^^^

:py:class:`~pyglet.math.Mat3` and :py:mod:`pyglet.math.Mat4` now accept arguments
directly instead of an iterable.

If you create your matrices via the helper methods, nothing changes. If you
create matrices directly, pyglet 2.1 allows more efficient code:

.. code-block:: python

    # pyglet 2.1 requires passing the elements directly
    my_mat4 = pyglet.math.Mat4(1, 2, 3, 4, 5, ...)

    # pyglet 2.0 required an intermediate iterable like a list
    my_mat4 = pyglet.math.Mat4([1, 2, 3, 4, 5, ...])

If your pre-existing code has an ``intermediate_iterable``, you can use
``*`` unpacking as a quick fix:

.. code-block:: python

    # Use * unpacking to unpack the pre-allocated intermediate_iterable
    my_mat4 = pyglet.math.Mat4(*intermediate_iterable)


Models
------
The :py:mod:`~pyglet.model` module has seen some changes. This is an undocumented
WIP module for pyglet 2.0, and it remains so pyglet 2.1. That said, it's in a more
usable state now. The first change is that :py:meth:`~pyglet.model.load` now returns
a ``Scene`` object instead of a ``Model`` object. The Scene is a new, "pure data"
intermediate representation of a 3D scene, that closely mimics the layout of the glTF
format. The :py:meth:`~pyglet.model.Scene.create_models` method can be used to create
``Model`` instances from the Scene, but the Scene data can also be manually iterated
over for more advanced use cases.

Canvas module
-------------
The ``pyglet.canvas`` module has been renamed to ``pyglet.display``. The "canvas"
concept was a work-in-progress in legacy pyglet, and was never fully fleshed out.
It appears to have been meant to allow arbitrary renderable areas, but this type
of functionality can now be easily accomplished with Framebuffers. The name ``display``
is a more accurate representation of what the code in the module actually relates to.
The usage is the same, with just the name change::

    my_display = pyglet.canvas.get_display()     # old pyglet 2.0
    my_display = pyglet.display.get_display()    # new pyglet 2.1

