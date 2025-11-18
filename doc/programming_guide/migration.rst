.. _migration:

Migrating to pyglet 3.x
=======================
This page will help you upgrade your project from pyglet 2.x to pyglet 3.0.

There are significant changes to pyglet 3.0 that have breaking API changes,
including:

* Refactored location of GL libraries
* Removal of image.blit
* Separation of Audio and Video media Players
* Changes to Groups
* Resource image loading

Many of these changes are to clear up ambiguity and future proof the library going forward.

To report a missing change or a bug, please use `GitHub Issues`_ or
another :ref:`contributor communication <contributor-communication>`
channel.

.. _GitHub Issues: https://github.com/pyglet/pyglet/issues

.. _migration-options:


pyglet.gl reorganization
^^^^^^^^^^^^^^^^^^^^^^^^
To support multiple backends and a more flexible rendering architecture, the `pyglet.gl`
module has been reorganized under `pyglet.graphics.api.gl`. If you used OpenGL directly, you will need to update
these imports.

With the new backend agnostic changes, this should no longer be needed unless you are directly interacting
with OpenGL. We understand people still may use Pyglet just for OpenGL usage, so this capability will still be
possible.


Image changes and removal of image.blit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Many classes have been moved out of the ``pyglet.image`` to ``pyglet.graphics.texture``. These changes
were done because it blurred the distinction between CPU-side image representations and GPU-side
rendering operations. ``ImageData`` is intended to represent raw pixel data stored in system CPU memory,
while ``Texture``s represent GPU usage and drawing. Keeping everything in the same module and the constant
cross-usage of both led to ambiguous behavior and inconsistent expectations.

With those changes in mind, ``ImageData.blit`` has also been removed, as this is no longer consistent with
that separation.

Instead to draw an image, create a Sprite (or Texture) from it and draw it directly or batch it instead:

.. code-block:: python

    batch = pyglet.graphics.Batch()
    sprite = pyglet.sprite.Sprite(image, batch=batch)
    batch.draw()


**Resource image loading**

:py:meth:`~pyglet.resource.image` previously loaded an image into a texture atlas. However, this was not properly
named as it did not actually return a `~pyglet.image.ImageData` instance in the same way `~pyglet.image.load` does.
With the decisions explained in the previous section, this has also been changed.

Going forward, migrate your code to instead use :py:meth:`~pyglet.resource.texture` as it will give the previous
behavior of loading into a texture atlas.

.. note:: While using :py:meth:`~pyglet.resource.image` will still work, you may experience significant performance penalties
in doing so. Please update your functions to this new usage.

**Image grids**

The function `pyglet.image.ImageGrid.get_texture_sequence` has been removed. This is no longer recommended,
as it created it's own texture, further reducing performance. Going forward, it is best to
use ``pyglet.graphics.TextureGrid``. This behaves the same way as ``ImageGrid``, but for textures. This
will allow you to use an existing texture, such as loaded from an atlas.


Separation of Media Player
^^^^^^^^^^^^^^^^^^^^^^^^^^
The former `pyglet.media.Player` class has been split into two dedicated classes: `pyglet.media.AudioPlayer`
and `pyglet.media.VideoPlayer`. This separation makes the API clearer by distinguishing pure audio playback
from video playback, which requires GPU-accelerated rendering and integration with the graphics system.

Video playback has always needed FFmpeg integration, but did not need it for more common audio playback. The new
`pyglet.media.VideoPlayer` will enforce a check for FFmpeg to make sure it is loaded.

By decoupling these responsibilities, pyglet can provide more focused, maintainable implementations
while avoiding unnecessary dependencies for applications that only need audio or only need video.


Loading resources before Window creation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In previous versions of Pyglet, a "shadow window" with its own context was something enabled by
default. This created a hidden 1x1 window that had it's own context that could be shared with other
windows. This allowed users to load resources and access OpenGL before the "real" window was made
visible.

This caused problems in certain hardware, and certain configurations. For example, sometimes
you could ask for an OpenGL ES context, but because of the shadow window, the driver would upgrade it
to a full context. Some drivers are also more strict when it comes to sharing behavior.

This functionality has been removed to increase compatibility between backends. This should only affect
you if you attempt to load resources before a Window is created. If you want the previous behavior, it
can still be done. You would create your own window before as shown below::

    shadow_window = pyglet.window.Window(1, 1, visible=False)

This will mimic the previous behavior.

pyglet.graphics.Group changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
One of the most significant changes will be with Groups. There were three driving reasons

1) To make groups easier to use: This was a common pitfall for users creating their own groups.
2) To better support multiple backends: Less need for direct backend (GL) calls for users.
3) To optimize the draw list for better performance.: Now that groups are state aware, we can remove
duplicate function calls.

To better understand Groups, please visit the rendering section here: <add link> as the next section will have an
assumed knowledge of Groups.

Starting with Pyglet 3.0, the new `pyglet.graphics.State` object has been added.

A Group is a collection of states, and with this new object, it will help by giving a clearer perspective on
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

We have added many built in and common states to Pyglet to make Groups easier to use.

This change should only affect you if you utilize any sort of custom groups in your code.

You will notice in the above example there is no longer a `set_state` or `unset_state` on the Group itself, these have
have been moved into the `State` object.

Refer to the rendering guide section: Creating a custom state. on the new way to do this.

