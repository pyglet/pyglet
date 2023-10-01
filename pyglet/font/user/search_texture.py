from __future__ import annotations
from typing import Callable, Optional

from pyglet.font import base
from pyglet.font.user import UserDefinedFontBase, UserDefinedFontException
from pyglet.image import ImageData


class UserSearchTextureGlyphRenderer(base.GlyphRenderer):
    def __init__(self, font: UserDefinedSearchTextureFont):
        self._font = font
        self._font.glyphs[self._font.default_char] = self.render(self._font.default_char)
        super().__init__(font)

    def render(self, text: str):
        image_data = self._font.search_texture(text, **self._font._kwargs)
        glyph = self._font.create_glyph(image_data)
        glyph.set_bearings(-self._font.descent, 0, image_data.width)
        return glyph


class UserDefinedSearchTextureFont(UserDefinedFontBase):
    """A basic UserDefinedFont, it takes a function search_texture to
    get ImageData of a character.
    """

    glyph_renderer_class = UserSearchTextureGlyphRenderer

    def __init__(
        self, name: str, default_char: str, size: int, ascent: int = None,
        descent: int = None, bold: bool = False, italic: bool = False,
        stretch: bool = False, dpi: int = 96,locale: str = None,
        search_texture: Callable[..., Optional[ImageData]] = None
    ):
        """Create a custom font.

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
            `search_texture` : function
                A function gets glyph of a character.

        The search_texture function should be defined like::

            def search_texture(
                char, size=12, bold=False, italic=False,
                stretch=False, dpi=96
            ):
                ...

        This function should return a :py:class:`pyglet.image.ImageData` object.
        If the glyph not found, ``None`` must be returned.
        """
        self.search_texture = search_texture
        if self.search_texture is None:
            raise UserDefinedFontException("A search_texture function must be provided.")
        self._kwargs = {"size": size, "bold": bold, "italic": italic, "stretch": stretch, "dpi": dpi}
        if self.search_texture(default_char, **self._kwargs)is None:
            raise UserDefinedFontException(
                "The search_texture function must return an ImageData "
                f"for default character '{default_char}'."
            )
        if ascent is None or descent is None:
            image = self.search_texture(default_char, **self._kwargs)
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
                if self.search_texture(c, **self._kwargs) is None:
                    c = self._default_char
                else:
                    self.glyphs[c] = glyph_renderer.render(c)
            glyphs.append(self.glyphs[c])
        return glyphs


__all__ = ("UserSearchTextureGlyphRenderer", "UserDefinedSearchTextureFont")
