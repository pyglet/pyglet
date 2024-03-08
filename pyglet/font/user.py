from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Protocol, List

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
    from pyglet.image import ImageData
    from pyglet.font.base import Glyph


class UserDefinedGlyphRenderer(base.GlyphRenderer):
    def __init__(self, font: UserDefinedFontBase):
        super().__init__(font)
        self._font = font

    def render(self, image_data: ImageData):
        if self._font._scaling:
            image_original = Image.frombytes('RGBA', (image_data.width, image_data.height),
                                             image_data.get_image_data().get_data('RGBA'))
            scale_ratio = self._font.size / self._font._base_size
            image_resized = image_original.resize((int(image_data.width * scale_ratio),
                                                   int(image_data.height * scale_ratio)), Resampling.NEAREST)
            new_image = pyglet.image.ImageData(image_resized.width, image_resized.height,
                                               'RGBA', image_resized.tobytes())
            glyph = self._font.create_glyph(new_image)
            glyph.set_bearings(-self._font.descent, 0, image_resized.width)
        else:
            glyph = self._font.create_glyph(image_data)
            glyph.set_bearings(-self._font.descent, 0, image_data.width)
        return glyph


class UserDefinedFontBase(base.Font):
    glyph_renderer_class = UserDefinedGlyphRenderer

    def __init__(
            self, name: str, default_char: str, size: int, ascent: Optional[int] = None, descent: Optional[int] = None,
            bold: bool = False, italic: bool = False, stretch: bool = False, dpi: int = 96,
            locale: Optional[str] = None,
    ):
        super().__init__()
        self._name = name
        self.default_char = default_char
        self.ascent = ascent
        self.descent = descent
        self.size = size
        self.bold = bold
        self.italic = italic
        self.stretch = stretch
        self.dpi = dpi
        self.locale = locale

        self._base_size = 0
        self._scaling = False

    @property
    def name(self) -> str:
        return self._name

    def enable_scaling(self, base_size: int):
        if not SCALING_ENABLED:
            raise Exception("PIL is not installed. User Font Scaling requires PIL.")

        self._base_size = base_size
        self._scaling = True


class UserDefinedFontException(Exception):
    pass


class DictLikeObject(Protocol):
    def get(self, char: str) -> Optional[ImageData]:
        pass


class UserDefinedMappingFont(UserDefinedFontBase):
    """The default UserDefinedFont, it can take mappings of characters to ImageData to make a User defined font."""

    def __init__(
            self, name: str, default_char: str, size: int, mappings: DictLikeObject,
            ascent: Optional[int] = None, descent: Optional[int] = None, bold: bool = False, italic: bool = False,
            stretch: bool = False, dpi: int = 96, locale: Optional[str] = None,

    ):
        """Create a custom font using the mapping dict.

        :Parameters:
            `name` : str
                Name of the font.
            `default_char` : str
                If a character in a string is not found in the font,
                it will use this as fallback.
            `size` : int
                Font size.
            `mappings` : DictLikeObject
                A dict or dict-like object with a get function.
                The get function must take a string character, and output ImageData if found.
                It also must return None if no character is found.
            `ascent` : int
                Maximum ascent above the baseline, in pixels. If None, the image height is used.
            `descent` : int
                Maximum descent below the baseline, in pixels. Usually negative.
        """
        self.mappings = mappings
        default_image = self.mappings.get(default_char)
        if not default_image:
            raise UserDefinedFontException(f"Default character '{default_char}' must exist within your mappings.")

        if ascent is None or descent is None:
            if ascent is None:
                ascent = default_image.height
            if descent is None:
                descent = 0

        super().__init__(name, default_char, size, ascent, descent, bold, italic, stretch, dpi, locale)

    def enable_scaling(self, base_size: int) -> None:
        super().enable_scaling(base_size)
        glyphs = self.get_glyphs(self.default_char)
        self.ascent = glyphs[0].height
        self.descent = 0

    def get_glyphs(self, text: str) -> List[Glyph]:
        """Create and return a list of Glyphs for `text`.

        If any characters do not have a known glyph representation in this
        font, a substitution will be made with the default_char.

        :Parameters:
            `text` : str or unicode
                Text to render.

        :rtype: list of `Glyph`
        """
        glyph_renderer = None
        glyphs = []  # glyphs that are committed.
        for c in base.get_grapheme_clusters(text):
            # Get the glyph for 'c'.  Hide tabs (Windows and Linux render
            # boxes)
            if c == '\t':
                c = ' '
            if c not in self.glyphs:
                if not glyph_renderer:
                    glyph_renderer = self.glyph_renderer_class(self)

                image_data = self.mappings.get(c)
                if not image_data:
                    c = self.default_char
                else:
                    self.glyphs[c] = glyph_renderer.render(image_data)
            glyphs.append(self.glyphs[c])
        return glyphs


def get_scaled_user_font(font_base: UserDefinedMappingFont, size: int):
    """This function will return a new font that can scale it's size based off the original base font."""
    new_font = UserDefinedMappingFont(font_base.name, font_base.default_char, size, font_base.mappings,
                                      font_base.ascent, font_base.descent, font_base.bold, font_base.italic,
                                      font_base.stretch, font_base.dpi, font_base.locale)

    new_font.enable_scaling(font_base.size)
    return new_font


__all__ = (
    "UserDefinedFontBase",
    "UserDefinedFontException",
    "UserDefinedMappingFont",
    "get_scaled_user_font"
)
