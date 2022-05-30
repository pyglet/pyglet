.. _guide_math:

Matrix and Vector Math
======================

Modern OpenGL depends on matrixes for projection and translation, among
other things. To provide out-of-the-box functionality, pyglet includes it's own
`math` module. This module contains the common 4x4 and 3x3 Matrix types,
as well as several Vector types. These are:

* ``pyglet.math.Mat3``
* ``pyglet.math.Mat4``
* ``pyglet.math.Vec2``
* ``pyglet.math.Vec3``
* ``pyglet.math.Vec4``

These objects support most common Matrix and Vector operations, in addition
to helper methods for rotating, scaling, and transforming. See the
:py:mod:`~pyglet.math` module for more information.

.. note:: For performance, all Matrix and Vector objects are subclasses of
    the `tuple` type. They are therefore immutable - all operations return
    a **new** object; they are not updated in-place.

Creating a Matrix
-----------------
A Matrix can be created with no arguments, or by passing a tuple or list
of `float`::

    my_matrix = Mat4()
    # or
    my_matrix = Mat4([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1])

If no arguments are given, an "identity" matrix will be created by default.
(1.0 on main diagonal).


Matrix Multiplication
---------------------

Matrix classes in pyglet use the Python `matmul` (`@`) operator for matrix
multiplication. For clarity, the `star` operator (`*`) will not work. For example::

    new_matrix = rotation @ translation


Helper Methods
--------------
A common operation in OpenGL is creating a 2D or 3D projection. The `Mat4`
module includes a handle method for this task. It's similar to what you will
find in general OpenGL math libraries::

    # Orthographic (2D) projection matrix:
    projection = Mat4.orthogonal_projection(0, width, 0, height, -255, 255)

    # Perspective (3D) projection matrix:
    projection = Mat4.perspective_projection(aspect_ratio, z_near=0.1, z_far=255)

For setting a 3D projection on the current OpenGL context, pyglet Windows have
a `projection` property. For example::

    window.projection = Mat4.perspective_projection(aspect_ratio, z_near=0.1, z_far=255)

By default, pyglet automatically sets a 2D projection whenever a Window is resized.
A useful pattern is to override the default on_resize event to set a 3D projection::

    @window.event
    def on_resize(width, height):
        # window.viewport = (0, 0, *window.get_framebuffer_size())
        window.projection = Mat4.perspective_projection(window.aspect_ratio, z_near=0.1, z_far=255)
        return pyglet.event.EVENT_HANDLED

