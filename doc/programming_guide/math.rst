.. _guide_math:

Matrix and Vector Math
======================

Modern OpenGL depends on matrixes for projection, translation, and
other things. To provide out-of-the-box functionality, pyglet's `math` module
includes the necessary Matrix and Vector types to cover most use cases:

* ``pyglet.math.Vec2``
* ``pyglet.math.Vec3``
* ``pyglet.math.Vec4``
* ``pyglet.math.Mat3``
* ``pyglet.math.Mat4``

These types support most common Matrix and Vector operations, including
rotating, scaling, and transforming. See the :py:mod:`~pyglet.math` module
for full API documentation.

.. note:: For performance, Matrix types are subclasses of the `tuple` type.
    They are therefore immutable - all operations return a **new** object;
    they are not updated in-place.

Creating a Matrix
-----------------
A Matrix can be created with no arguments, or by passing a tuple or list
of `float`::

    my_matrix = Mat4()
    # or
    my_matrix = Mat4([1.0, 0.0, 0.0, 0.0,
                      0.0, 1.0, 0.0, 0.0,
                      0.0, 0.0, 1.0, 0.0,
                      0.0, 0.0, 0.0, 1.0])

If no arguments are given, an "identity" matrix will be created by default.
(1.0 on the main diagonal).


Matrix Multiplication
---------------------

Matrix classes in pyglet use the modern Python `matmul` (`@`) operator for
matrix multiplication. The `star` operator (`*`) is not allowed. For example::

    new_matrix = rotation_matrix @ translation_matrix


Helper Methods
--------------
A common operation in OpenGL is creating a 2D or 3D projection matrix. The `Mat4`
module includes a helper method for this task. The arguments should be similar to what
you will find in popular OpenGL math libraries::

    # Orthographic (2D) projection matrix:
    projection = Mat4.orthogonal_projection(0, width, 0, height, z_near=-255, z_far=255)

    # Perspective (3D) projection matrix:
    projection = Mat4.perspective_projection(aspect_ratio, z_near=0.1, z_far=255)

For setting a 3D projection on the current OpenGL context, pyglet Windows have
a `projection` property. For example::

    my_matrix = Mat4.perspective_projection(aspect_ratio, z_near=0.1, z_far=255)
    window.projection = my_matrix

By default, pyglet automatically sets a 2D projection whenever a Window is resized.
If you plan to set your own 3D or 2D projection matrix, a useful pattern is to override
the default on_resize event handler::

    @window.event
    def on_resize(width, height):
        # window.viewport = (0, 0, *window.get_framebuffer_size())
        window.projection = Mat4.perspective_projection(window.aspect_ratio, z_near=0.1, z_far=255)
        return pyglet.event.EVENT_HANDLED   # Don't call the default handler

