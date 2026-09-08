.. _migration:

Migrating from pyglet 2.1 to pyglet 3.0
=======================================
This page will help you upgrade your project from pyglet 2.x to pyglet 3.0.


.. contents::
    :depth: 3

Introduction
^^^^^^^^^^^^

A major focus for pyglet 3.0 has been clearing up ambiguity in the APIs, and working towards future proofing
the library. You should find that the vast majority of the high-level API (sprites, text, audio) is mostly
the same as before, but much of the lower level and internal modules have changed. We hope that this page
will make upgrading to pyglet v3.0 relatively straight-forward.

Some of the major changes include::

* Refactored location of graphics libraries (OpenGL).
* Removal of image.blit, and some other legacy patterns.
* Separation of Audio and Video media Players.
* Changes to Groups, including how custom Groups are made.
* Built-in 2D and 3D cameras with managed shader state.
* Resource image loading improvements.
* Clearer separation of raw ImageData and Textures.


The sections below should hopefully cover all of the changes that you will need to migrate a project. If you
find any missing changes or bugs, please use `GitHub Issues`_ or
another :ref:`contributor communication <contributor-communication>`
channel to let us know about it.

.. _GitHub Issues: https://github.com/pyglet/pyglet/issues

.. _migration-options:


pyglet.gl reorganization
^^^^^^^^^^^^^^^^^^^^^^^^
Historically pyglet has been based on OpenGL, and much of the internal APIs were tightly intertwined.
With version 3.0, to support multiple backends and a more flexible rendering architecture, the graphics backend
is now decoupled from the high-level APIs. The `pyglet.gl` module has therefore been reorganized under
``pyglet.graphics.api.gl``. If you used OpenGL directly, you will need to update these imports.
However, with the new backend agnostic changes, this should no longer be needed unless you are directly interacting
with OpenGL. We understand people still may use pyglet just for OpenGL usage, so this capability will still be
possible. Due to changes in groups (see below), you may no longer need direct OpenGL calls in many cases.

Enum-based graphics constants
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Many GL constants that were previously passed around in higher-level APIs
now have pyglet-owned enums under :py:mod:`pyglet.enums`. This keeps the API
backend-agnostic and avoids relying on raw ``GL_*`` values in user code.

Common migrations:

* Geometry modes:

  ``pyglet.gl.GL_TRIANGLES`` -> ``pyglet.enums.GeometryMode.TRIANGLES``

* Texture filtering:

  ``pyglet.gl.GL_NEAREST`` -> ``pyglet.enums.TextureFilter.NEAREST``
  ``pyglet.gl.GL_LINEAR`` -> ``pyglet.enums.TextureFilter.LINEAR``

* Framebuffer attachments:

  ``pyglet.gl.GL_COLOR_ATTACHMENT0`` -> ``pyglet.enums.FramebufferAttachment.COLOR0``
  ``pyglet.gl.GL_DEPTH_ATTACHMENT`` -> ``pyglet.enums.FramebufferAttachment.DEPTH``

* Blend factors:

  ``pyglet.gl.GL_SRC_ALPHA`` -> ``pyglet.enums.BlendFactor.SRC_ALPHA``
  ``pyglet.gl.GL_ONE_MINUS_SRC_ALPHA`` -> ``pyglet.enums.BlendFactor.ONE_MINUS_SRC_ALPHA``

If you still use raw OpenGL calls directly, you can continue to use ``GL_*``
constants from ``pyglet.graphics.api.gl``. But for pyglet's high-level APIs
and new rendering helpers, refer to the enums.


Shader vertex formats
^^^^^^^^^^^^^^^^^^^^^
Vertex-list creation no longer accepts ``(format, values)`` tuples. Configure
non-default vertex-buffer storage formats on a ShaderProgram view before creating
vertex lists instead. For example, replace::

    program.vertex_list(3, GeometryMode.TRIANGLES, colors=('Bn', colors))

with::

    byte_colors = program.get_attribute_view(colors='Bn')
    byte_colors.vertex_list(3, GeometryMode.TRIANGLES, colors=colors)

This is especially useful for normalized color attributes: the ``"Bn"`` format
stores colors as unsigned bytes and normalizes them for a ``vec4`` shader input.
The built-in Sprite and Label classes use this normalized-byte color layout by
default. If a custom shader is supplied to a Sprite, Label, or related helper,
request the matching view explicitly::

    shader = shader.get_attribute_view(colors="Bn")
    sprite = pyglet.sprite.Sprite(image, program=shader)

Otherwise the uploaded ``0``--``255`` color values may be consumed as
unnormalized floats and clamp to ``1.0``, producing solid white output.

Instance attribute divisors are also configured once on the program. Replace::

    program.vertex_list_instanced(3, GeometryMode.TRIANGLES,
                                  instance_attributes={'translation': 1},
                                  translation=translations)

with::

    program.set_instance_attributes(translation=1)
    program.vertex_list_instanced(3, GeometryMode.TRIANGLES,
                                  translation=translations)

Use ``program.get_attribute_view(...)`` when one linked shader program needs
multiple vertex formats. It returns an interned
:class:`~pyglet.graphics.shader.ShaderProgramView`, which can be used anywhere
a ShaderProgram is accepted. Equivalent configurations return the same view::

    byte_colors = program.get_attribute_view(colors='Bn')
    float_colors = program.get_attribute_view(colors='f')

To keep a different divisor configuration alongside the program's default,
configure it on a view::

    instanced_byte_colors = byte_colors.set_instance_attributes(colors=1)


Image changes and removal of image.blit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Many classes have been moved out of the ``pyglet.image`` to ``pyglet.graphics.texture``. These changes
were done because the distinction between CPU-side image representations and GPU-side rendering operations
was somewhat blurred until now. ``ImageData`` is intended to represent raw pixel data stored in system CPU memory,
while ``Texture`` objects represent data stored on the GPU. Keeping everything in the same module led to ambiguous
behavior and inconsistent expectations.

With those changes in mind, ``ImageData.blit`` has also been removed, as this is no longer consistent with
that separation.

Instead, to draw an image, create a py:class:`~pyglet.sprite.Sprite` and construct it with either a ``Texture`` or
``ImageData``.

.. note:: It is still recommended to use batching when creating objects such as sprites, as it produces large
          performance gains. See :ref:`guide_graphics`

Additionally, ``ImageData.get_data`` and ``ImageData.set_data`` have been removed after being deprecated. Use
``ImageData.get_bytes`` and ``ImageData.set_bytes`` instead (the same applies to ``ImageDataRegion``).

Removed image buffer APIs
-------------------------
The legacy ``pyglet.image`` buffer API has been removed.

The following names have been removed:

* ``pyglet.image.BufferManager``
* ``pyglet.image.get_buffer_manager``
* ``pyglet.image.BufferImage``
* ``pyglet.image.ColorBufferImage``
* ``pyglet.image.DepthBufferImage``
* ``pyglet.image.BufferImageMask``

For explicit framebuffer objects, use
:py:class:`pyglet.graphics.framebuffer.Framebuffer`.

For screenshots, replace this pattern::

    pyglet.image.get_buffer_manager().get_color_buffer().save('screenshot.png')

With::

    pyglet.graphics.framebuffer.get_screenshot().save("screenshot.png")


Resource Image and Texture Loading
----------------------------------
:py:meth:`~pyglet.resource.image` previously loaded an image into a texture atlas. However, this was not named
consistently in the same way :py:meth:`~pyglet.image.load` was, causing confusion. The latter returned
:py:class:`~pyglet.image.ImageData` instances while the :py:meth:`~pyglet.resource.image` returned a ``Texture``. With the
decisions explained in the previous section, the behavior of this function has been changed.

With these changes being needed, the :py:meth:`~pyglet.resource.texture` was also updated to correct this ambiguity. In
previous versions  _only_ returned a standalone ``Texture`` instance - there was no automatic texture atlas support.
With v3.0, :py:meth:`~pyglet.resource.texture` now supports automatically adding to an atlas, mimicking how
:py:meth:`~pyglet.resource.image` previously behaved.

.. note:: You can still opt to get a standalone ``Texture`` by passing the ``atlas=False`` argument, if you wish.

In summary, going forward, migrate your code to instead use :py:meth:`~pyglet.resource.texture` as it will give the
previous behavior of loading into a texture atlas.

.. note:: While using :py:meth:`~pyglet.resource.image` will still work, you may experience significant performance
          penalties in doing so. Please update your functions to this new usage.

Image Grids
-----------
The function `pyglet.image.ImageGrid.get_texture_sequence` has been removed. This is no longer recommended,
as it created it's own texture, further reducing performance. Going forward, it is best to
use :py:class:`~pyglet.graphics.texture.TextureGrid`. This behaves the same way as :py:class:`~pyglet.image.ImageGrid`, but
for textures. This will allow you to use an already existing texture, such as one loaded from an atlas.


Separation of Media Players
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The former ``pyglet.media.Player`` class has been split into two dedicated classes: :py:class:`~pyglet.media.AudioPlayer`
and :py:class:`~pyglet.media.VideoPlayer`. This separation makes the API clearer by distinguishing pure audio playback
from video playback, which requires GPU-accelerated rendering and integration with the graphics system.

Video playback has always needed FFmpeg integration, but did not need it for more common audio playback. The new
:py:class:`~pyglet.media.VideoPlayer` will enforce a check for FFmpeg to make sure it is loaded.

By decoupling these responsibilities, pyglet can provide more focused, maintainable implementations
while avoiding unnecessary dependencies for applications that only need audio or only need video.

Media Loading
-------------
Along with the split to the media players, media loading functions have also been split into explicit audio/video calls.

Here are the following API changes:

* ``pyglet.media.load`` -> ``pyglet.media.load_audio`` or ``pyglet.media.load_video``
* ``pyglet.resource.media`` -> ``pyglet.resource.audio`` or ``pyglet.resource.video``

The behavior and signature has been kept the same.

Loading resources before Window creation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In previous versions of pyglet, a "shadow window" with its own context was something enabled by
default. This created a hidden 1x1 window that had it's own context that could be shared with other
windows. This allowed users to load resources and access OpenGL functions before the "real" window was made
visible.

This caused problems in certain hardware and certain configurations. For example, sometimes
you could ask for an OpenGL ES context, but because of the shadow window, the driver would upgrade it
to a full context. Some drivers are also more strict when it comes to sharing behavior. Many downstream
libraries that depend on pyglet have long disabled the "shadow window" to work around such issues. Due to these many
factors, we have opted to remove this going forward. This will increase compatibility between backends, while reducing
the amount of driver related bugs and exceptions.

This change should only affect you if you attempt to load resources before a Window is created.

If your application needs to load resources before showing its window, the simplest approach is to
create the *actual* window hidden, load the resources while its context is current, then show that
same window.::

    window = pyglet.window.Window(800, 600, visible=False)
    window.switch_to()
    batch = pyglet.graphics.Batch()
    # Load textures and create other resources here.
    window.set_visible(True)

Alternatively, a hidden window can still be used as a shadow context for assets that OpenGL permits
contexts to share, such as textures, buffers, shaders, and programs. Passing its context when
creating the visible window creates a new context in the same sharing group; it does not make both
windows use one context. Explicitly switch to the visible window before creating context-local
objects such as :class:`~pyglet.graphics.Batch` data and vertex array objects (VAOs).::

    shadow_window = pyglet.window.Window(1, 1, visible=False)
    shadow_window.switch_to()
    texture = pyglet.resource.texture("player.png")  # A shareable resource.

    actual_window = pyglet.window.Window(800, 600, context=shadow_window.context)
    actual_window.switch_to()
    batch = pyglet.graphics.Batch()  # Bound to actual_window's context.

VAOs are not shared between OpenGL contexts. A batch created while ``shadow_window`` is current
therefore cannot safely be drawn through ``actual_window``, even though the two contexts share
textures and other shareable resources. The same separation applies to other context-local OpenGL
objects.


Migrating custom cameras
^^^^^^^^^^^^^^^^^^^^^^^^
pyglet 2.x did not provide a public camera component, so applications commonly implemented one by
constructing projection and view matrices, assigning ``window.projection`` or ``window.view``, and
restoring those matrices around each draw. Older camera examples followed similar patterns. In
pyglet 3.0, use the cameras in :py:mod:`pyglet.window.camera` instead. Every window has a default
:py:class:`~pyglet.window.camera.Camera2D` available as
:py:attr:`~pyglet.window.Window.camera`, and additional 2D or 3D cameras can be created for world,
UI, split-screen, minimap, and render-pass views.

This is more than a convenience wrapper around matrix calculations. A camera owns the per-camera
matrix state and applies it at the correct point in a draw, preventing one view or render pass from
overwriting data still needed by another. Managing that storage directly can overwrite data that the
GPU is still reading, introduce synchronization stalls, or leave a later batch using the wrong matrices.
Applications should therefore select a camera for a draw rather than manually managing the matrix state
around it. See :ref:`guide_camera` for the shader integration and other camera implementation details.

For example, a typical custom 2D camera previously changed global window matrices around a batch
draw::

    # Typical pyglet 2.x application pattern:
    camera.apply(window)
    world_batch.draw()
    camera.reset(window)
    ui_batch.draw()

Replace that matrix/state management with a :class:`~pyglet.window.camera.Camera2D` and select it
for the batch draw::

    from pyglet.window.camera import Camera2D

    world_camera = Camera2D(
        window,
        scroll_speed=400.0,
        min_zoom=0.25,
        max_zoom=4.0,
    )
    world_camera.position = (camera_x, camera_y)
    world_camera.zoom = zoom

    @window.event
    def on_draw():
        window.clear()
        with world_batch.draw_with_options() as options:
            options.camera = world_camera
        ui_batch.draw()  # Uses window.camera by default.

If world and UI objects share one batch, attach cameras to groups instead::

    world_group = pyglet.graphics.Group(order=0)
    world_group.set_camera(world_camera)

    ui_group = pyglet.graphics.Group(order=1)
    ui_group.set_camera(window.camera)

    world_sprite = pyglet.sprite.Sprite(image, batch=batch, group=world_group)
    ui_label = pyglet.text.Label("Score: 0", batch=batch, group=ui_group)

Camera views can be created with ``camera.create_view()`` for parallax layers, nested transforms, minimaps, and
independent viewports without manually swapping global matrices.

Simple existing code that assigns :py:attr:`~pyglet.window.Window.projection`,
:py:attr:`~pyglet.window.Window.view`, or :py:attr:`~pyglet.window.Window.viewport` remains valid.
These properties now proxy the root view of ``window.camera``. They are useful when an application
must preserve custom matrices. Prefer camera position, zoom, orientation, viewport, and view APIs
whenever possible so matrix storage is committed at the correct point in the draw operation. See
:ref:`guide_camera` for camera views, coordinate conversion, scoped drawing, viewport, and scissor
examples.

pyglet.graphics.Group changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
One of the most significant changes will be with Groups. There were three driving reasons:

1) To make groups easier to use: This was a common pitfall for users creating their own groups.
2) To better support multiple backends: Less need for direct backend (GL) calls for users.
3) To optimize the draw list for better performance: Now that groups are state aware, we can remove
   duplicate function calls.

To better understand Groups, please visit the rendering section here: (see :ref:`guide_graphics`) as the next section
will have an assumed knowledge of Groups.

Starting with Pyglet 3.0, the new ``pyglet.graphics.State`` object has been added.
Since a Group is a collection of states, this new object will help by giving a clearer perspective on
how a Group works and how states are applied.

Previously to apply a state, your group might look like this::

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
            glBindTexture(GL_TEXTURE_2D, self.texture.handle)

        def unset_state(self):
            # not required

        def __eq__(self, other):
            return (self.__class__ is other.__class__ and
                    self.texture.key == other.texture.key and
                    self.texture.target == other.texture.target and
                    self.parent == other.parent)

        def __hash__(self):
            return hash((self.texture.key, self.texture.target))

That same group with Pyglet 3.0 look like this::

    class TextureGroup(pyglet.graphics.Group):
        def __init__(self, texture):
            self.set_texture(texture, binding=0)

    group = TextureGroup(texture)

Or just as valid::

    class TextureGroup(pyglet.graphics.Group):
        ...

    group = TextureGroup()
    group.set_texture(texture)

We have added many built in and common states to pyglet to make Groups easier to define and use. This also reduces the
need for you to use direct API related calls (such as OpenGL).

This change should only affect you if you utilize any sort of custom groups in your code.

You will notice in the above example there is no longer a ``set_state`` or ``unset_state`` method on the Group itself;
These methods have have been moved into the ``State`` object. Refer to the rendering guide section: "Creating a custom
state" to learn the new way to do this.

Other notable API changes
^^^^^^^^^^^^^^^^^^^^^^^^^
Additional changes not covered above:

* ``pyglet.config`` and ``pyglet.window.Window(config=...)``:
  The old ``pyglet.gl.Config`` flow was replaced by ``pyglet.config.Config``.
  Configure backend-specific options on ``config.opengl``, ``config.gl2``,
  ``config.gles2``, ``config.gles3``, or ``config.webgl``. You can pass one
  ``Config`` or multiple ``Config`` objects (in priority order) to
  ``Window(config=...)``. See :ref:`guide_window-config`.

* ``pyglet.graphics.Texture``:
  ``Texture.blit_into`` was renamed to ``Texture.upload`` and
  ``Texture.get_image_data`` was renamed to ``Texture.fetch`` to better reflect that these involve GPU requests.

* Graphics resource identities:
  Backend-created resources such as textures, buffers, shaders, shader programs,
  framebuffers, renderbuffers, and vertex arrays now separate their backend
  ``handle`` from their stable pyglet ``key``. Use ``resource.handle`` when
  passing a resource to a backend API, and ``resource.key`` for equality,
  hashing, batching, or cache keys. The read-only ``resource.id`` alias is
  deprecated; replace it with ``handle``.

* Fonts and text:
  ``pyglet.font.manager`` now supports custom font-name callbacks,
  ``pyglet.font.get_custom_font_names`` was added, and ``pyglet.font.FontGroup``
  allows grouped font fallbacks. ``Label.font_name`` now returns the resolved
  font family name, not the style string passed in. The Windows-only
  ``pyglet.options.dw_legacy_naming`` option was removed; use the
  cross-platform ``pyglet.options.font_name_compatibility`` option instead.

* ``pyglet.window``:
  ``Window.set_mouse_visible`` was renamed to
  ``Window.set_mouse_cursor_visible``, and ``Window.set_mouse_platform_visible``
  was renamed to ``Window.set_mouse_cursor_platform_visible``.
  ``MouseCursor.gl_drawable`` was renamed to ``MouseCursor.api_drawable``.

* ``pyglet.input``:
  Controllers now dispatch separate events for left/right sticks and
  left/right triggers.

* ``pyglet.window``:
  As mentioned above in the shadow window section. The ``context`` keyword argument in Pyglet window
  creation has been changed take an existing context. This context will share resources with the
  newly created window.
