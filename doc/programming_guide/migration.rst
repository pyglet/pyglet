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
use :py:class:`~pyglet.graphics.TextureGrid`. This behaves the same way as :py:class:`~pyglet.image.ImageGrid`, but
for textures. This will allow you to use an already existing texture, such as one loaded from an atlas.


Separation of Media Players
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The former ``pyglet.media.Player` class has been split into two dedicated classes: :py:class:`~pyglet.media.AudioPlayer`
and :py:class:`~pyglet.media.VideoPlayer`. This separation makes the API clearer by distinguishing pure audio playback
from video playback, which requires GPU-accelerated rendering and integration with the graphics system.

Video playback has always needed FFmpeg integration, but did not need it for more common audio playback. The new
:py:class:`~pyglet.media.VideoPlayer` will enforce a check for FFmpeg to make sure it is loaded.

By decoupling these responsibilities, pyglet can provide more focused, maintainable implementations
while avoiding unnecessary dependencies for applications that only need audio or only need video.


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

If your application still needs this behavior, it can still be done by creating your own hidden window, as shown below::

    shadow_window = pyglet.window.Window(1, 1, visible=False)


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

We have added many built in and common states to pyglet to make Groups easier to define and use. This also reduces the
need for you to use direct API related calls (such as OpenGL).

This change should only affect you if you utilize any sort of custom groups in your code.

You will notice in the above example there is no longer a ``set_state`` or ``unset_state`` method on the Group itself;
These methods have have been moved into the ``State`` object. Refer to the rendering guide section: "Creating a custom
state" to learn the new way to do this.

