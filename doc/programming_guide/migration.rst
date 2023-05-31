.. _migration:

Migrating from pyglet 1.5
=========================

pyglet 2.0 includes a number of breaking changes, so some effort may be needed
to upgrade your application or game. Primarily, pyglet 2.0 is now built
around modern OpenGL (3.3+), wheras previous releases used legacy OpenGL 2.0
contexts. While much has changed internally, the user facing APIs remain
mostly the same. This means that if your program does not use much OpenGL
directly, migrating to pyglet 2.0 will be fairly easy. If your program *does*
make heavy use of OpenGL, then all of the caveats that go with modernizing an
OpenGL program will apply.

In addition to changes, pyglet 2.0 also includes quite a few nice improvements.
For games, user input has been improved with a new Controller API. This is a
modern compliment to the Joystick API, specifically for game controllers.
Internally, a lot of work has been done to improve the platform abstractions.
A new :mod:`pyglet.math` module has also been added, which provides built-in
support for common Vector and Matrix types.

pyglet 2.0 should be just as easy to use, but will allow more flexibility due
to the highly programmable nature of modern OpenGL.

If you maintain a project that relies on pyglet, and are unable to update right
away, you may want to pin your pyglet version (in requirements.txt or setup.py)::

    pyglet<2


General Changes
---------------
If your program only uses pyglet's high level objects (Sprites, Text, Shapes),
then very little needs to be done. The most prominent changes are described
in the following sections.

Sprites and Labels
^^^^^^^^^^^^^^^^^^
Sprites and Labels now have a `z` position, in addition to `x` and `y`. This
can be useful for some sorting techniques, or even for advanced uses like
positioning 2D sprites on a 3D background. If you are using `position` property,
make sure to account for the additional `z` value (leave it at 0 if unneeded)::

    sprx, spry, sprz = my_sprite.position
    my_sprite.position = 10, 10, 0


Groups
^^^^^^
`OrderedGroup` has been removed. Instead, all Groups now have an `order`
parameter. You can mimic the behavior by creating a Group instance with
order parameter::

    from pyglet.graphics import Group

    bg_group = Group(order=0)
    fg_group = Group(order=1)


Window Projection and Cameras
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Windows now have `projection` and `view` properties, which are 4x4 matrixes.
These two matrixes are used internally to determine the final screen projection.
In pyglet 1.X, you may have used OpenGL commands like `glOrtho`, `glTranslate`,
etc. to manipulate the "Camera". Or, if working with the OpenGL matrixes
directly, commands such as `glMatrixMode`, `glPushMatrix`, `glPopMatrix`, etc.
to manipulate the matrixes. In pyglet 2.0+, you can simply set the matrixes
directly on the Window.

For example:
If you want to set a perspective (3D) projection instead of the default
orthographic (2D) projection, simply set the `Window.projection` matrix.
If you want to scroll the viewport, simply set the `Window.view` matrix.

The new :py:mod:`~pyglet.math` module is available to assist in creating
and manipulating matrixes, so basic operations can be performed without
deep mathematical knowledge.

Here are some very simplistic examples on the new usages.

.. list-table:: Pyglet 1.5 -> 2.0 Chart
   :header-rows: 1

   * - 
     - 1.5 Code
     - 2.0 Code
   * - Translation
     -  .. code-block::
     
           glTranslatef(x, y, z)

     -  .. code-block::
     
           window.view = window.view.translate((x, y, z))
           
   * - Scaling
     -  .. code-block::
     
           glScalef(zoom, zoom, 1)
           
     -  .. code-block::
     
           window.view = window.view.scale((zoom, zoom, 1))
           
        
   * - Orthogonal Projection
     -  .. code-block::
          
           gl.glMatrixMode(gl.GL_PROJECTION)
           gl.glLoadIdentity()
           gl.glOrtho(0, width, 0, height, -255, 255)
           gl.glMatrixMode(gl.GL_MODELVIEW)

     -  .. code-block::
           
           from pyglet.math import Mat4
           window.projection = Mat4.orthogonal_projection(
               0, width, 0, height, -255, 255
           )
           
   * - GL_QUADS
     -  .. code-block::
          
           vertex_list = batch.add(4, GL_QUADS, group, vertex_format,
                ('c4B', (255,255,255,255) * 4),
                ('t3f', texture.tex_coords))
                
     -  .. code-block::
          
               vertex_list = program.vertex_list_indexed(
                4, GL_TRIANGLES, [0, 1, 2, 0, 2, 3], batch, group,
                colors=('Bn', (255, 255, 255, 255) * 4),
                tex_coords=('f', texture.tex_coords))


Application Event Loop
^^^^^^^^^^^^^^^^^^^^^^
In previous releases, the Window was redrawn (and the `Window.on_draw()` event
dispatched) whenever any scheduled function was called, or event dispatched.
This often lead to unpredictability and potentially unstable frame rates. In
pyglet 2.0, a new `interval` argument has been added to `pyglet.app.run`.
Windows will now always be redrawn at this interval. It defaults to 60fps (1/60),
but can be set as desired::

    @mywindow.event
    def on_draw():
        # always called at 120fps

    pyglet.app.run(interval=1/120)


Graphics module
---------------
The largest user facing change in pyglet 2.0 is the :py:mod:`~pyglet.graphics`
module (also see :ref:`guide_graphics`). If you were using this module to
draw simple shapes and OpenGL primitives, the :py:mod:`~pyglet.shapes`
module may be able to fill that need. If your needs are more advanced, read on.

In legacy OpenGL, the fixed function pipeline had pre-defined vertex attributes.
(Vertex, Color, Normals, Texture Coordinates, etc.) Because these were all
predefined, it was possible to create a VertexList directly, or use `Batch.add(...)`
to define one.
In modern OpenGL, this is no longer the case. Due to its highly programmable nature,
nothing is pre-defined. Instead, the attribute names, sizes, etc. are all defined
in Shader Programs. Shaders can be as complex or simple as needed, only defining
the attributes that are necessary. For instance pyglet objects, such as Sprites and
Shapes, both have their own custom Shaders with attributes that suite them.

For the above reason, `Batch.add` and `Batch.add_indexed` have been removed.
Instead you start with a ShaderProgram, and use the `ShaderProgram.vertex_list`
or `ShaderProgram.vertex_list_indexed` methods. The resulting VertexLists
can still be Batched, but you pass in your Batch instance as an argument (the
same way as you would when creating a Sprite, or other object).

In legacy pyglet versions you would do something like this::

    vertex_list = batch.add(4, GL_TRIANGLES, group,
                            ('v3f', vertex_positions),
                            ('t3f', tex.tex_coords))


In pyglet 2+ you start with the ShaderProgram, and the syntax has changed slightly::

    vertex_list = shader_program.vertex_list(4, GL_TRIANGLES, batch, group,
                                             position=('f', vertex_positions),
                                             tex_coords=('f', tex.tex_coords))

Please see the :ref:`guide_graphics` section for more detailed information on the new
interface.
