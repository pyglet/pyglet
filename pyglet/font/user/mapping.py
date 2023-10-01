from __future__ import annotations
from typing import Dict

from pyglet.font import base
from pyglet.font.user import UserDefinedFontBase, UserDefinedFontException
from pyglet.image import ImageData


class UserMappingGlyphRenderer(base.GlyphRenderer):
    def __init__(self, font: UserDefinedMappingFont):
        self._font = font
        self._font.glyphs[self._font.default_char] = self.render(self._font.default_char)
        super().__init__(font)

    def render(self, text: str):
        image_data = self._font.mappings[text]
        glyph = self._font.create_glyph(image_data)
        glyph.set_bearings(-self._font.descent, 0, image_data.width)
        return glyph


class UserDefinedMappingFont(UserDefinedFontBase):
    """A basic UserDefinedFont, it takes a mappings of ImageData."""

    glyph_renderer_class = UserMappingGlyphRenderer

    def __init__(
        self, name: str, default_char: str, size: int, ascent: int = None,
        descent: int = None, bold: bool = False, italic: bool = False,
        stretch: bool = False, dpi: int = 96, locale: str = None,
        mappings: Dict[str, ImageData]={}
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
            `ascent` : int
                Maximum ascent above the baseline, in pixels.
            `descent` : int
                Maximum descent below the baseline, in pixels. Usually negative.
            `mappings` : dict
                A dict likes ``{character: ImageData}``.
        """
        self.mappings = mappings
        if default_char not in self.mappings:
            raise UserDefinedFontException(
                f"Default character '{default_char}' must exist within your mappings."
            )
        if ascent is None or descent is None:
            image = list(mappings.values())[0]
            if ascent is None:
                ascent = image.height
            if descent is None:
                descent = 0
        super().__init__(
                name, default_char, size, ascent, descent,
                bold, italic, stretch, dpi, locale
            )

    def get_glyphs(self, text: str):
        """Create and return a list of Glyphs for `text`.

        If any characters do not have a known glyph representation in this
        font, a substitution will be made.

        :Parameters:
            `text` : str or unicode
                Text to render.

        :rtype: list of `Glyph`
        """
        glyph_renderer = None
        glyphs = []  # glyphs that are committed.
        for c in base.get_grapheme_clusters(str(text)):
            # Get the glyph for 'c'.  Hide tabs (Windows and Linux render
            # boxes)
            if c == '\t':
                c = ' '
            if c not in self.glyphs:
                if not glyph_renderer:
                    glyph_renderer = self.glyph_renderer_class(self)
                if c not in self.mappings:
                    c = self.default_char
                else:
                    self.glyphs[c] = glyph_renderer.render(c)
            glyphs.append(self.glyphs[c])
        return glyphs


__all__ = ("UserMappingGlyphRenderer", "UserDefinedMappingFont")
