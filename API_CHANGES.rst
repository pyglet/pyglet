Pyglet 3.0
==========
Large overhaul of the graphics systems, as it will now support different graphics backends or no backend.

pyglet.options
--------------
*Added*: ``pyglet.options.backend``: Can now specify a specific graphics backend to target, or no backend if you wish to use
Pyglet for windowing.

pyglet.graphics
---------------
*Changed*: Created backend agnostic API setups to support multiple backends. See pyglet.enums.
*Changed*: Now has a global graphics core object that manages the multiple contexts.
*Added*: Ability kwargs to target specific contexts for Pyglet objects if using multiple contexts.

pyglet.font
-----------
*Added*: ``pyglet.font.manager``. Allows a callback to determine the font name and properties of a custom loaded font. Refer to documentation.


pyglet.text
-----------
*Changed*: ``Label.font_name`` will return the actual name of the font object, not the style name passed.

pyglet.image
------------
Module was stripped down to CPU related image operations. All GPU related operations moved to pyglet.graphics.texture.
*Moved*: Texture, TextureRegion, Texture3D, TextureArray, TextureArrayRegion, TextureGrid to pyglet.graphics.texture to
create a separation of CPU ImageData from GPU Texture.
*Removed*: ImageData.blit, use a Sprite or vertex list.
*Removed*: TileableTexture as it has no use without a blit.

pyglet.graphics.texture
-----------------------
*Changed*: ``Texture.blit_into`` renamed to ``Texture.upload`` to better specify that it's uploading and replacing data, not drawing an image.
*Changed*: ``Texture.get_image_data` renamed to ``Texture.fetch`` to better specify that it's pulling pixel data from the GPU texture, and not an ``ImageData`` instance it may have been created with.


pyglet.graphics.group
---------------------
*Changed*: Groups now set their state by set of connector ``pyglet.graphics.state`` objects. This allows for better
optimization and optimized to operate the same between multiple backends.
