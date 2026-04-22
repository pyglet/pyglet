Textures and Rendering
======================

This page covers GPU-side imaging in pyglet 3.0: drawing images, working with
textures, texture atlases, and framebuffers.

Texture classes moved from ``pyglet.image`` to ``pyglet.graphics.texture`` in
pyglet 3.0. Use :py:class:`~pyglet.graphics.texture.Texture` and related classes
for GPU resources, and keep :py:mod:`pyglet.image` for CPU-side image
data (see :doc:`image`).

Drawing images
--------------

For most users, the :py:class:`~pyglet.sprite.Sprite` class is the best way to
draw an image.

.. note::
    ``image.blit`` no longer exists in pyglet 3.0. Use sprites for drawing.

Example::

    import pyglet

    window = pyglet.window.Window(800, 600)
    image = pyglet.image.load("kitten.png")
    sprite = pyglet.sprite.Sprite(image, x=100, y=80)

    @window.event
    def on_draw():
        window.clear()
        sprite.draw()

    pyglet.app.run()

Sprites can be created from either :py:class:`~pyglet.image.ImageData`,
:py:class:`~pyglet.image.animation.Animation`, or an existing texture object.

Batched sprites
^^^^^^^^^^^^^^^

If you need to draw many sprites, use a :py:class:`~pyglet.graphics.draw.Batch`:

::

    batch = pyglet.graphics.Batch()
    sprites = [pyglet.sprite.Sprite(image, batch=batch) for _ in range(100)]

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

When using batches, draw order can be controlled with
:py:class:`~pyglet.graphics.draw.Group` objects:

::

    batch = pyglet.graphics.Batch()
    background = pyglet.graphics.Group(order=0)
    foreground = pyglet.graphics.Group(order=1)

    pyglet.sprite.Sprite(image, batch=batch, group=background)
    pyglet.sprite.Sprite(image, batch=batch, group=foreground)

To reduce texture switches, prefer atlased textures (for example via
:py:meth:`~pyglet.resource.texture`) or use explicit texture bins/atlases as
described below.

Converting images and textures
------------------------------

CPU image objects can be uploaded to the GPU with
:py:meth:`~pyglet.image.ImageData.get_texture`::

    img = pyglet.image.load('kitten.png')
    texture = img.get_texture()

If you need finer control over texture creation (for example filtering,
address mode, texture type, or internal format settings), use
``Texture.create_from_image(...)`` instead of ``get_texture()``.

Reading texture pixels back to CPU memory can be done with
``Texture.fetch()``::

    image_data = texture.fetch()

These readbacks can be expensive, especially if done every frame.

Writing into textures
---------------------

To write CPU image data into an existing texture, use ``Texture.upload(...)``.
This method was previously named ``blit_into``.

::

    image_data = pyglet.image.load('overlay.png').get_image_data()
    texture = pyglet.graphics.Texture.create(512, 512)
    texture.upload(image_data, x=0, y=0, z=0)

Texture uploads replace texel data in the target region. They do not perform
alpha blending with existing texels. Blending only applies when drawing
geometry/sprites with blend state enabled.
For render-based updates, see :ref:`guide_drawing-into-a-texture`.

Image sequences and atlases
---------------------------

Sometimes a single source image is used to hold many sub-images (for example,
sprite sheets). pyglet provides helpers for this workflow.

.. _guide_texture-grids:

Texture grids
^^^^^^^^^^^^^

You can define the CPU-side grid first with :py:class:`~pyglet.image.ImageGrid`
(see :ref:`guide_image-grids` in :doc:`image`). Then convert it to a
GPU-side :py:class:`~pyglet.graphics.texture.TextureGrid` for efficient
rendering:

::

    explosion = pyglet.image.load('explosion.png')
    explosion_grid = pyglet.image.ImageGrid(explosion, 1, 8)
    explosion_tex_grid = pyglet.graphics.TextureGrid.from_image_grid(explosion_grid)

    first_frame = explosion_tex_grid[0]

:py:class:`~pyglet.graphics.texture.TextureGrid` can also be created directly
with the same grid arguments as :py:class:`~pyglet.image.ImageGrid`
(``rows``, ``columns``, optional ``item_width``/``item_height``, and padding),
but with a texture as the first argument:

::

    texture = explosion.get_texture()
    explosion_tex_grid = pyglet.graphics.TextureGrid(texture, 1, 8)

``pyglet.graphics.TextureGrid`` is the same class alias exposed as
:py:class:`~pyglet.graphics.texture.TextureGrid`.

:py:class:`~pyglet.graphics.texture.TextureGrid` items are
:py:class:`~pyglet.graphics.texture.TextureRegion` objects.

.. _guide_texture-bins-and-atlases:

Texture bins and atlases
^^^^^^^^^^^^^^^^^^^^^^^^

A :py:class:`~pyglet.graphics.atlas.TextureAtlas` is a large texture that packs
many smaller images. A :py:class:`~pyglet.graphics.atlas.TextureBin` manages
multiple atlases as needed.

::

    images = [
        pyglet.image.load('img1.png'),
        pyglet.image.load('img2.png'),
    ]

    bin = pyglet.graphics.atlas.TextureBin()
    regions = [bin.add(image) for image in images]

The result of ``TextureBin.add`` is typically a
``TextureRegion``.


3D textures
^^^^^^^^^^^

You can create a :py:class:`~pyglet.graphics.texture.Texture3D` from a sequence
of images or from an
:py:class:`~pyglet.image.ImageGrid` (see :ref:`guide_image-grids`)::

    explosion_3d = pyglet.graphics.texture.Texture3D.create_for_image_grid(explosion_grid)

Slicing a :py:class:`~pyglet.graphics.texture.Texture3D` returns
:py:class:`~pyglet.graphics.texture.TextureRegion` objects for layers.

Framebuffers
------------

For explicit framebuffer objects, use ``Framebuffer`` and ``Renderbuffer`` in
:py:mod:`pyglet.graphics.framebuffer`.

::

    import pyglet
    from pyglet.enums import TextureFilter, FramebufferAttachment, ComponentFormat
    from pyglet.graphics import Texture, Renderbuffer, Framebuffer

    window = pyglet.window.Window()

    color_buffer = Texture.create(width, height, filters=TextureFilter.NEAREST)
    depth_buffer = Renderbuffer(window.context, width, height,
                                component_format=ComponentFormat.D, bit_size=24)

    framebuffer = Framebuffer(context=window.context)
    framebuffer.attach_texture(color_buffer, attachment=FramebufferAttachment.COLOR0)
    framebuffer.attach_renderbuffer(depth_buffer, attachment=FramebufferAttachment.DEPTH)

    framebuffer.bind()

.. _guide_drawing-into-a-texture:

Drawing into a texture
^^^^^^^^^^^^^^^^^^^^^^

Use a framebuffer with a texture attachment when you want to render *into* a
texture (for post-processing, compositing, dynamic texture generation, etc.).

::

    import pyglet
    from pyglet.enums import FramebufferAttachment, TextureFilter

    window = pyglet.window.Window(800, 600)

    source_image = pyglet.image.load('source.png')
    source_sprite = pyglet.sprite.Sprite(source_image, x=100, y=120)

    target_texture = pyglet.graphics.Texture.create(
        800, 600, filters=TextureFilter.NEAREST
    )
    framebuffer = pyglet.graphics.Framebuffer(context=window.context)
    framebuffer.attach_texture(target_texture, attachment=FramebufferAttachment.COLOR0)

    # This sprite displays the texture we rendered into:
    result_sprite = pyglet.sprite.Sprite(target_texture, x=0, y=0)

    @window.event
    def on_draw():
        # Pass 1: render into texture:
        framebuffer.bind()
        window.clear()
        source_sprite.draw()
        framebuffer.unbind()

        # Pass 2: render texture to window:
        window.clear()
        result_sprite.draw()

    pyglet.app.run()

This is different from ``Texture.upload(...)``: framebuffer rendering runs the
normal draw pipeline (shaders, blending, draw order), while ``upload`` is a
direct texel data replacement.

To capture the default framebuffer to an image:

::

    from pyglet.graphics.framebuffer import get_screenshot

    screenshot = get_screenshot()
    screenshot.save('screenshot.png')

OpenGL texture access
---------------------

This section assumes familiarity with texture mapping in OpenGL (for example,
chapter 9 of the `OpenGL Programming Guide`_).

To create a texture from image data:

::

    kitten = pyglet.image.load('kitten.jpg')
    texture = kitten.get_texture()

A :py:class:`~pyglet.graphics.texture.Texture` has a ``target`` and ``id``:

::

    from pyglet.graphics.api.gl import *
    glBindTexture(texture.target, texture.id)

.. _OpenGL Programming Guide: http://www.opengl-redbook.com/

Texture filtering
^^^^^^^^^^^^^^^^^

By default, all textures are created with smooth (:py:data:`~pyglet.enums.TextureFilter.LINEAR`)
filtering.

To use a different filter for a specific texture, pass the filtering constant(s)
to ``Texture.create`` via the ``filter`` arguments or
``Texture.create_from_image``.


Pixel art
"""""""""

To enable nearest-neighbor filtering for retro-style games, set the
corresponding variables of :py:class:`pyglet.graphics.texture.Texture` to
:py:data:`~pyglet.enums.TextureFilter.NEAREST`:

.. code-block:: python

   from pyglet.enums import TextureFilter
   pyglet.graphics.Texture.default_filters = (TextureFilter.NEAREST, TextureFilter.NEAREST)

Afterward, all textures pyglet creates will default
to nearest-neighbor sampling.

