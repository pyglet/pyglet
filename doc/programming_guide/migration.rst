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
To support multiple (and future backends) and a more flexible rendering architecture, the `pyglet.gl`
module has been reorganized under `pyglet.graphics.api.gl`. If you used OpenGL directly, you will need to update
these imports.

With the new backend agnostic changes, this should no longer be needed unless you are directly interacting
with OpenGL. We understand people still may use Pyglet just for OpenGL usage, so this capability will still be
possible.

Resource image loading
^^^^^^^^^^^^^^^^^^^^^^
:py:meth:`~pyglet.resource.image` previously loaded an image into a texture atlas. However, this was not properly
named as it did not actually return a `~pyglet.image.ImageData` instance in the same way `~pyglet.image.load` does.

Furthermore, this also complicated the concept to users that an "image" and "texture" were effectively the
same thing when they are not. To clarify simply, an `~pyglet.image.ImageData` instance is a representation of the
image data on the CPU side, while a `~pyglet.graphics.Texture` is a representation of image data on the GPU side.

Going forward, migrate your code to instead use :py:meth:`~pyglet.resource.texture` as it will give the previous
behavior of loading into a texture atlas.

While using :py:meth:`~pyglet.resource.image` will still work, you will have significant performance penalties
in doing so. Please update your functions to this new usage.

Separation of Media Player
^^^^^^^^^^^^^^^^^^^^^^^^^^
The former `pyglet.media.Player` class has been split into two dedicated classes: `pyglet.media.AudioPlayer`
and `pyglet.media.VideoPlayer`. This separation makes the API clearer by distinguishing pure audio playback
from video playback, which requires GPU-accelerated rendering and integration with the graphics system.

Video playback has always needed FFmpeg integration, but did not need it for more common audio playback. The new
`pyglet.media.VideoPlayer` will enforce a check for FFmpeg to make sure it is loaded.

By decoupling these responsibilities, pyglet can provide more focused, maintainable implementations
while avoiding unnecessary dependencies for applications that only need audio or only need video.


pyglet.graphics.Group changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
One of the most significant changes will be with Groups. There were three driving reasons
1) To make groups easier to use: This was a common pitfall for users creating their own groups.
2) To better support multiple backends: Less need for direct GL calls.
3) To optimize the draw list for better performance.

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

This change should only affect you, if you utilize any sort of custom groups in your code.

You will notice in the above example there is no longer a `set_state` or `unset_state` on the Group itself, these have
have been moved into the `State` object.

Refer to the rendering guide section: Creating a custom state. on the new way to do this.

