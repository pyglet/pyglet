from typing import Dict

import pyglet
from pyglet.font import base
from pyglet.font.user import UserDefinedFontException


class UserMappingGlyphRenderer(base.GlyphRenderer):
    def __init__(self, font: 'UserDefinedMappingFont'):
        self._font = font
        self._font.glyphs[self._font.default_char] = self.render(self._font.default_char)
        super().__init__(font)

    def render(self, text: str):
        image_data = self._font.mappings[text]
        glyph = self._font.create_glyph(image_data)
        glyph.set_bearings(-self._font.descent, 0, image_data.width)
        return glyph


class UserDefinedMappingFont(base.Font):
    """A basic UserDefinedFont, it takes a mappings of ImageData."""

    glyph_renderer_class = UserMappingGlyphRenderer

    def __init__(
        self, default_char: str, name: str, ascent: float, descent: float,
        size: float, bold: bool = False, italic: bool = False, stretch: bool = False,
        dpi: int = None, locale: str = None,
        mappings: Dict[str, pyglet.image.ImageData]={}
    ):
        """Create a custom font using the mapping dict."""
        super().__init__()
        self._name = name
        self.mappings: Dict[str, pyglet.image.ImageData] = mappings

        if default_char not in self.mappings:
            raise UserDefinedFontException(
                f"Default character '{default_char}' must exist within your mappings."
            )
        self.default_char = default_char

        if ascent is None or descent is None:
            image = list(mappings.values())[0]
            if ascent is None:
                ascent = image.height
            if descent is None:
                descent = 0
        self.ascent = ascent
        self.descent = descent

        self.bold = bold
        self.italic = italic
        self.stretch = stretch
        self.dpi = dpi
        self.size = size
        self.locale = locale

    @property
    def name(self):
        return self._name

    def get_glyphs(self, text):
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
