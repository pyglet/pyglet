"""This module defines the usage and creation of user defined fonts in Pyglet.

Previously, pyglet only supported font renderers that are built into the operating system, such as
``FreeType``, ``DirectWrite``, or ``Quartz``. However, there are situations in which a user may not want or need all the
features a font can provide. They just need to put characters in a particular order without the hassle of exporting
into a separate file.

The :py:class:`~pyglet.font.user.UserDefinedMappingFont` is provided for most use cases, which will allow you to
make an internal font that can be used where a ``font_name`` is required to identify a font.

A user defined font is also identified by its name. The name you choose should be unique to ensure it will not conflict
with a system font. For example, do not use `Arial`, as that will collide with Windows systems.

With :py:class:`~pyglet.font.user.UserDefinedMappingFont` you can pass a mapping of characters that point to your
:py:class:`~pyglet.image.ImageData`.

.. code-block:: python

    mappings={'c': my_image_data, 'b': my_image_data, 'a': my_image_data}

For more custom behavior, a dict-like object can be used, such as a class.

.. code-block:: python

    class MyCustomMapping:
        def get(self, char: str) -> ImageData | None:
            # return ImageData if a character is found.
            # return None if no character is found

    mappings = MyCustomMapping()

Once your font is created, you also must register it within pyglet to use it. This can be done through the
 :py:func:`~pyglet.font.add_user_font` function.

When you register a user defined font, only those parameters will used to identify the font. If you have a font, but
want to have a ``italic`` enabled version. You must make a new instance of your font, but with the ``italic``
parameter set as ``True``. Same applies to the ``size`` parameter. The ``weight`` parameter can also be provided as
a string.

Scaling
=======
By default, user font's will not be scaled. In most use cases, you have a single font at a specific size that you
want to use.

There are cases where a user may want to scale their font to be used at any size. We provide the following function:
:py:func:`~pyglet.font.user.get_scaled_user_font`. By providing the user defined font instance, and a new size, you will
get back a new font instance that is scaled to the new size. This new instance must also be registered the same way as
the base font.

When specifying the ``size`` parameter, that value is used to determine the ratio of scaling between the new size. So
if your base font is a size of 12, creating a scaled version at size 24 will be double the size of the base.

.. warning::

    The ``PIL`` library is a required dependency to use the scaling functionality.

.. versionadded:: 2.0.15
"""
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Protocol

import pyglet
from pyglet.font import base

SCALING_ENABLED = False
try:
    from PIL import Image
    from PIL.Image import Resampling

    SCALING_ENABLED = True
except ImportError:
    pass

if TYPE_CHECKING:
    from pyglet.font.base import Glyph, GlyphPosition
    from pyglet.image import ImageData


class UserDefinedGlyphRenderer(base.GlyphRenderer):
    def __init__(self, font: UserDefinedFontBase) -> None:
        super().__init__(font)
        self._font = font

    def render(self, image_data: ImageData) -> Glyph:
        if self._font._scaling:  # noqa: SLF001
            image_original = Image.frombytes("RGBA", (image_data.width, image_data.height),
                                             image_data.get_image_data().get_data("RGBA"))
            scale_ratio = self._font.size / self._font._base_size
            image_resized = image_original.resize((int(image_data.width * scale_ratio),
                                                   int(image_data.height * scale_ratio)), Resampling.NEAREST)
            new_image = pyglet.image.ImageData(image_resized.width, image_resized.height,
                                               "RGBA", image_resized.tobytes())
            glyph = self._font.create_glyph(new_image)
            glyph.set_bearings(-self._font.descent, 0, image_resized.width)
        else:
            glyph = self._font.create_glyph(image_data)
            glyph.set_bearings(-self._font.descent, 0, image_data.width)
        return glyph


class UserDefinedFontBase(base.Font):
    """Used as a base for all user defined fonts.

    .. versionadded:: 2.0.15
    """
    glyph_renderer_class: ClassVar[type[base.GlyphRenderer]] = UserDefinedGlyphRenderer

    def __init__(
            self, name: str, default_char: str, size: int, ascent: int | None = None, descent: int | None = None,
            weight: str = "normal", italic: bool = False, stretch: bool = False, dpi: int = 96, locale: str | None = None,
    ) -> None:
        """Initialize a user defined font.

        Args:
            name:
                Name of the font. Used to identify the font. Must be unique to ensure it does not
                collide with any system fonts.
            default_char:
                If a character in a string is not found in the font, it will use this as fallback.
            size:
                Font size, usually in pixels.
            ascent:
                Maximum ascent above the baseline, in pixels. If None, the image height is used.
            descent:
                Maximum descent below the baseline, in pixels. Usually negative.
            weight:
                The font weight, as a string. Defaults to "normal".
            italic:
                If True, this font will be used when ``italic`` is enabled for the font name.
            stretch:
                If True, this font will be used when ``stretch`` is enabled for the font name.
            dpi:
                The assumed resolution of the display device, for the purposes of determining the pixel size of the
                font. Use a default of 96 for standard sizing.
            locale:
                Used to specify the locale of this font.
        """
        super().__init__()
        self._name = name
        self.default_char = default_char
        self.ascent = ascent
        self.descent = descent
        self.size = size
        self.weight = weight
        self.italic = italic
        self.stretch = stretch
        self.dpi = dpi
        self.locale = locale

        self._base_size = 0
        self._scaling = False

    @property
    def name(self) -> str:
        return self._name

    def enable_scaling(self, base_size: int) -> None:
        if not SCALING_ENABLED:
            msg = "PIL is not installed. User Font Scaling requires PIL."
            raise ImportError(msg)

        self._base_size = base_size
        self._scaling = True

    def _initialize_renderer(self) -> None:
        """Initialize the glyph renderer and cache it on the Font.

        This way renderers for fonts that have been loaded but not used will not have unnecessary loaders.
        """
        if not self._glyph_renderer:
            self._glyph_renderer = self.glyph_renderer_class(self)

class UserDefinedFontException(Exception):  # noqa: N818
    """An exception related to user font creation."""


class DictLikeObject(Protocol):
    def get(self, char: str) -> ImageData | None:
        pass


class UserDefinedMappingFont(UserDefinedFontBase):
    """The class allows the creation of user defined fonts from a set of mappings.

    .. versionadded:: 2.0.15
    """
    _glyph_renderer: UserDefinedGlyphRenderer

    def __init__(self, name: str, default_char: str, size: int, mappings: DictLikeObject,
            ascent: int | None = None, descent: int | None = None, weight: str = "normal", italic: bool = False,
            stretch: bool = False, dpi: int = 96, locale: str | None = None) -> None:
        """Initialize the default parameters of your font.

        Args:
            name:
                Name of the font. Must be unique to ensure it does not collide with any system fonts.
            default_char:
                If a character in a string is not found in the font, it will use this as fallback.
            size:
                Font size. Should be in pixels. This value will affect scaling if enabled.
            mappings:
                A dict or dict-like object with a ``get`` function.
                The ``get`` function must take a string character, and output :py:class:`~pyglet.image.ImageData` if
                found. It also must return ``None`` if no character is found.
            ascent:
                Maximum ascent above the baseline, in pixels. If None, the image height is used.
            descent:
                Maximum descent below the baseline, in pixels. Usually negative.
            weight:
                The font weight, as a string. Defaults to "normal".
            italic:
                If ``True``, this font will be used when ``italic`` is enabled for the font name.
            stretch:
                If ``True``, this font will be used when ``stretch`` is enabled for the font name.
            dpi:
                The assumed resolution of the display device, for the purposes of determining the pixel size of the
                font. Use a default of 96 for standard sizing.
            locale:
                Used to specify the locale of this font.
        """
        self.mappings = mappings
        default_image = self.mappings.get(default_char)
        if not default_image:
            msg = f"Default character '{default_char}' must exist within your mappings."
            raise UserDefinedFontException(msg)

        if ascent is None or descent is None:
            if ascent is None:
                ascent = default_image.height
            if descent is None:
                descent = 0

        super().__init__(name, default_char, size, ascent, descent, weight, italic, stretch, dpi, locale)

    def enable_scaling(self, base_size: int) -> None:
        """Enables scaling the font size.

        Args:
            base_size:
                The base size is used to calculate the ratio between new sizes and the original.
        """
        super().enable_scaling(base_size)
        glyphs, offsets = self.get_glyphs(self.default_char)
        self.ascent = glyphs[0].height
        self.descent = 0

    def get_glyphs(self, text: str) -> tuple[list[Glyph], list[GlyphPosition]]:
        """Create and return a list of Glyphs for `text`.

        If any characters do not have a known glyph representation in this font, a substitution will be made with
        the ``default_char``.
        """
        self._initialize_renderer()
        offsets = []
        glyphs = []  # glyphs that are committed.
        for c in base.get_grapheme_clusters(text):
            # Get the glyph for 'c'.  Hide tabs (Windows and Linux render
            # boxes)
            if c == "\t":
                c = " "
            if c not in self.glyphs:
                image_data = self.mappings.get(c)
                if not image_data:
                    c = self.default_char
                else:
                    self.glyphs[c] = self._glyph_renderer.render(image_data)
            glyphs.append(self.glyphs[c])
            offsets.append(base.GlyphPosition(0, 0, 0, 0))
        return glyphs, offsets


def get_scaled_user_font(font_base: UserDefinedMappingFont, size: int) -> UserDefinedMappingFont:
    """This function will return a new font instance which can scale it's size based off the original base font.

    .. note:: The scaling functionality requires the PIL library to be installed.

    .. versionadded:: 2.0.15

    Args:
        font_base:
            The base font object to create a new size from.
        size:
            The new font size. This will be scaled based on the ratio between the base size and the new size.
    """
    new_font = UserDefinedMappingFont(font_base.name, font_base.default_char, size, font_base.mappings,
                                      font_base.ascent, font_base.descent, font_base.weight, font_base.italic,
                                      font_base.stretch, font_base.dpi, font_base.locale)

    new_font.enable_scaling(font_base.size)
    return new_font


__all__ = (
    "UserDefinedFontBase",
    "UserDefinedFontException",
    "UserDefinedMappingFont",
    "get_scaled_user_font",
)
