from typing import Callable, Optional

import pyglet
from pyglet.font import base
from pyglet.font.user import UserDefinedFontException


class UserSearchTextureGlyphRenderer(base.GlyphRenderer):
    def __init__(self, font: 'UserDefinedSearchTextureFont'):
        self._font = font
        self._font.glyphs[self._font._default_char] = self.render(self._font._default_char)
        super().__init__(font)

    def render(self, text: str):
        image_data = self._font.search_texture(
            text, size=self._font.size, bold=self._font.bold,
            italic=self._font.italic, stretch=self._font.stretch
        )
        glyph = self._font.create_glyph(image_data)
        glyph.set_bearings(-self._font.descent, 0, image_data.width)
        return glyph


class UserDefinedSearchTextureFont(base.Font):
    """A basic UserDefinedFont, it takes a function search_texture to
    get ImageData of a character.
    """

    glyph_renderer_class = UserSearchTextureGlyphRenderer

    def __init__(
        self, default_char: str, name: str, ascent: float, descent: float,
        size: float, bold: bool = False, italic: bool = False, stretch: bool = False,
        dpi: int = None,locale: str = None,
        search_texture: Callable[..., Optional[pyglet.image.ImageData]] = None
    ):
        """Create a custom font.

        The search_texture function should be defined like::

            def search_texture(
                char, size=12, bold=False, italic=False,
                stretch=False, dpi=96
            ):
                ...
        """
        super().__init__()
        self._name = name
        self.search_texture = search_texture
        if self.search_texture is None:
            raise UserDefinedFontException("A search_texture function must be provided.")

        self._default_char = default_char
        if (
            self.search_texture(
                default_char, size=size, bold=bold,
                italic=italic, stretch=stretch, dpi=dpi
            )
            is None
        ):
            raise UserDefinedFontException(
                "The search_texture function must return an ImageData "
                f"for default character '{default_char}'."
            )

        if ascent is None or descent is None:
            image = self.search_texture(default_char)
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
                if (
                    self.search_texture(
                        c, size=self.size, bold=self.bold, italic=self.italic,
                        stretch=self.stretch, dpi=self.dpi
                    )
                    is None
                ):
                    c = self._default_char
                else:
                    self.glyphs[c] = glyph_renderer.render(c)
            glyphs.append(self.glyphs[c])
        return glyphs


__all__ = ("UserSearchTextureGlyphRenderer", "UserDefinedSearchTextureFont")
