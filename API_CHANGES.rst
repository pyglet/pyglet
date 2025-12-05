Pyglet 3.0
==========
Large overhaul of the graphics systems, as it will now support different graphics backends or no backend.


pyglet.config
-------------
*Added*: This module replaces ``pyglet.gl.Config``. To be used for specific backends such as ``pyglet.config.OpenGL``.

pyglet.enums
------------
*Added*: This module creates enums for various systems including graphical backends and fonts. (Fill in specifics later)

pyglet.options
--------------
*Added*: ``pyglet.options.backend``: Can now specify a specific graphics backend to target, or no backend if you wish to use
Pyglet for windowing.

*Removed*: ``pyglet.options.shadow_window``: The shadow window containing a graphical context has been removed.

*Removed*: `'real'`, `'scaled'` options from ``pyglet.options.dpi_scaling``. Defaults to `'platform'`.

*Added*: ``pyglet.options.optimize_states``: For debugging purposes if states are not behaving as they should. Report any issues that arise where disabling this fixes an issue.

pyglet.graphics
---------------
*Changed*: Created backend agnostic API setups to support multiple backends. See pyglet.enums.

*Changed*: Now has a global graphics core object that manages the multiple contexts.

*Added*: Batches can now accept a specific context and/or initial size argument.

*Added*: Ability kwargs to target specific contexts for Pyglet objects if using multiple contexts.


pyglet.font
-----------
*Added*: ``pyglet.font.manager``. Allows a callback to determine the font name and properties of a custom loaded font. Refer to documentation.

*Added*: ``pyglet.font.get_custom_font_names``. Allows retrieval of loaded custom font family names.

*Added*: ``pyglet.font.FontGroup``, allows setting up multiple fonts to act as one. See ``examples/text/font_groups.py``

pyglet.text
-----------
*Changed*: ``Label.font_name`` will return the actual name of the font object, not the style name passed.

pyglet.image
------------
Module was stripped down to CPU related image operations. All GPU related operations moved to pyglet.graphics.texture.

*Moved*: Texture, TextureRegion, Texture3D, TextureArray, TextureArrayRegion, TextureGrid, CompressedTexture to pyglet.graphics.texture to
create a separation of CPU ImageData from GPU Texture.

*Removed*: ImageData.blit, use a Sprite or vertex list.

*Removed*: TileableTexture as it has no use without a blit.

*Removed*: S3TC software decoder. No longer relevant or used as all hardware supports the decoding now.

*Added*: KTX2 format support for compressed images. Supports zlib supercompression and no-compression decoding. (Note: that zstandard supercompression requires the `zstandard` library.)

*Deprecated*: `pyglet.image.ImageGrid.get_texture_sequence`. Use `pyglet.graphics.TextureGrid.from_image_grid(image_grid)` instead.

pyglet.graphics.texture
-----------------------
*Changed*: ``Texture.blit_into`` renamed to ``Texture.upload`` to better specify that it's uploading and replacing data, not drawing an image.

*Changed*: ``Texture.get_image_data` renamed to ``Texture.fetch`` to better specify that it's pulling pixel data from the GPU texture, and not an ``ImageData`` instance it may have been created with.

*Added*: Support for instanced drawing. See example ``examples/graphics/instancing.py`` for usage.

*Added*: Support for BC1-7 modern compression formats.

*Added*: Support for legacy L and LA image formats to swizzle to the proper colors.

pyglet.media
------------
*Changed*: `Player` has now been split into `AudioPlayer` and `VideoPlayer`.

*Changed*: `VideoPlayer` now explicitly requires FFmpeg to be used.

pyglet.graphics.group
---------------------
*Changed*: Groups now set their state by set of connector ``pyglet.graphics.state`` objects. This allows for better
consolidation optimization, and for compatibility between multiple backends.

pyglet.window
-------------
*Changed*: Window.set_mouse_visible has been renamed to Window.set_mouse_cursor_visible, and Window.set_mouse_platform_visible has been renamed to Window.set_mouse_cursor_platform_visible.

*Added*: pyglet.window.dialog.FileOpenDialog and pyglet.window.dialog.FileSaveDialog to open OS file dialog windows.

pyglet.input
------------
*Changed* Controllers now dispatch separate events for left/right sticks, and left/right triggers.

other
-----
*Added*: Functionality for Pyglet browser implementations via WebGL and Pyodide. (Note that this is still experimental, and reliant on the Pyodide project. See the docs.)

*Added*: Functionality for Windows 11 to change the window frame to Dark Mode based on the new Dark/Light theme settings.