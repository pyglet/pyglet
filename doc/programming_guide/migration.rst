.. _migration:

Migrating from pyglet 1.5
=========================

pyglet 2.0 migrates the internals to OpenGL 3.3+, wheras previous releases
used legacy OpenGL 2.0 contexts. While much has changed internally, the general
API remains the same. This means that if your program does not use much OpenGL
directly, migrating to pyglet 2.0 will be fairly easy. If your program *does*
make heavy use of OpenGL, then all of the caveats that go with modernizing an
OpenGL program will apply.

In addition to changes, pyglet 2.0 also includes quite a few nice improvments.
For games, user input has been improved with a new Controller API. This is a
modern alternative to the Joystick API, specifically for game controllers.
Internally, a lot of work has been done to improve the platform abstractions.
A new :mod:`pyglet.math` module has also been added, which provides built-in
support for common Vector and Matrix types.

pyglet 2.0 should be just as easy to use, but will allow more flexibility due
to the highly programmable nature of modern OpenGL.


General Changes
---------------
If your program only uses pyglet's high level classes (Sprites, Text, Shapes),
then very little needs to be done. The most prominent changes are described
in the following sections.

Sprites
^^^^^^^
Sprites now have a `z` position, in addition to `x` and `y`. This can be useful
for some sorting techniques, or even for advanced uses like positioning 2D
sprites on a 3D background. If you are using the `Sprite.position` property,
make sure to account for the additional `z` value::

    sprx, spry, sprz = my_sprite.position
    my_sprite.position = 10, 10, 0


Window Projection
^^^^^^^^^^^^^^^^^


Application Event Loop
^^^^^^^^^^^^^^^^^^^^^^

app.run (fps)


Graphics module
---------------


(See :ref:`guide_graphics`)