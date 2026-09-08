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

``fetch()`` is intended for image-oriented use. It returns unsigned-byte
:py:class:`~pyglet.image.ImageData` and does not convert floating-point or
integer textures. Use ``Texture.read_pixels()`` when typed values are needed::

    pixels = texture.read_pixels()
    float_values = memoryview(pixels.data).cast("f")

The returned :py:class:`~pyglet.graphics.texture.PixelData` contains tightly
packed raw bytes together with their component format and data type. Neither
method should generally be called every frame because GPU readback can be
expensive.

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

Use a texture render target when you want to render *into* a texture, for
example for post-processing, compositing, minimaps, or dynamic texture
generation.

.. warning::
    Render targets allocate GPU resources and drawing into them submits GPU
    work. Creating targets or generating many textures every frame can be slow.
    Reuse can reduce setup overhead, but it does not eliminate texture
    allocation or rendering costs.

Persistent render textures
""""""""""""""""""""""""""

:py:class:`~pyglet.graphics.framebuffer.RenderTexture` owns a fixed color
texture and the framebuffer and camera used to draw into it. It is useful when
the same texture is updated repeatedly::

    import pyglet

    window = pyglet.window.Window(800, 600)
    scene_batch = pyglet.graphics.Batch()

    target = pyglet.graphics.RenderTexture(512, 512)

    with target:
        scene_batch.draw()

    # Use the result like any other texture.
    result_sprite = pyglet.sprite.Sprite(target.texture)

Entering the target clears it and temporarily installs a camera and viewport
matching its dimensions. On exit, the previous framebuffer, camera, viewport,
and scissor state are restored.

Deleting the target releases its framebuffer, camera-related state, and
optional depth buffer, but retains the color texture by default::

    texture = target.texture
    target.delete()

    # The texture is still valid.
    result_sprite = pyglet.sprite.Sprite(texture)

    # Delete it explicitly when it is no longer needed.
    texture.delete()

Pass ``delete_texture=True`` to
:py:meth:`~pyglet.graphics.framebuffer.RenderTexture.delete` when the color
texture should be deleted with the target.

Generating independent textures efficiently
""""""""""""""""""""""""""""""""""""""""""""

Each output must have its own texture if several results need to remain valid,
but the framebuffer and camera do not need to be recreated for every output.
:py:class:`~pyglet.graphics.framebuffer.TextureRenderTarget` keeps that target
state and attaches a fresh texture for each render scope::

    target = pyglet.graphics.TextureRenderTarget()
    textures = []

    for batch, width, height in jobs:
        with target.render_to_texture(width, height) as texture:
            batch.draw()
        textures.append(texture)

    # This does not delete any successfully returned textures.
    target.delete()

    for texture in textures:
        texture.delete()

The reusable target updates its camera and viewport for each output size. If
depth buffering is enabled, a same-sized depth buffer is reused and is
recreated only when the dimensions change. If drawing raises an exception, the
incomplete output texture is deleted and the target remains reusable.

Only the framebuffer, camera, and compatible depth buffer are reused. Every
successful call still allocates and renders into a new GPU texture so that
previous results remain independent.

Text layouts accept a reusable target through
:py:meth:`~pyglet.text.layout.TextLayout.get_as_texture`::

    target = pyglet.graphics.TextureRenderTarget()
    textures = [label.get_as_texture(target) for label in labels]
    target.delete()

Without an argument, ``get_as_texture`` creates and deletes a temporary target,
which is convenient for a single conversion::

    texture = label.get_as_texture()

The returned textures are always caller-owned and must eventually be deleted.

.. note::
    Render targets follow the same context rules as other graphics resources.
    They do not switch windows automatically. In a multi-window application,
    call ``window.switch_to()`` before constructing or using a target belonging
    to that window.

Low-level framebuffer usage
"""""""""""""""""""""""""""

For direct control, create a framebuffer and attach textures and renderbuffers
manually.

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
    glBindTexture(texture.target, texture.handle)

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

