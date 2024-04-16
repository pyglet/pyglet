"""Abstract classes used by pyglet.font implementations.

These classes should not be constructed directly.  Instead, use the functions
in `pyglet.font` to obtain platform-specific instances.  You can use these
classes as a documented interface to the concrete classes.
"""
from __future__ import annotations

import abc
import unicodedata
from typing import BinaryIO, ClassVar

from pyglet import image
from pyglet.gl import GL_LINEAR, GL_RGBA, GL_TEXTURE_2D

_other_grapheme_extend = list(map(chr, [0x09be, 0x09d7, 0x0be3, 0x0b57, 0x0bbe, 0x0bd7, 0x0cc2,
                                        0x0cd5, 0x0cd6, 0x0d3e, 0x0d57, 0x0dcf, 0x0ddf, 0x200c,
                                        0x200d, 0xff9e, 0xff9f]))  # skip codepoints above U+10000
_logical_order_exception = list(map(chr, list(range(0xe40, 0xe45)) + list(range(0xec0, 0xec4))))

_grapheme_extend = lambda c, cc: cc in ("Me", "Mn") or c in _other_grapheme_extend

_CR = "\u000d"
_LF = "\u000a"
_control = lambda c, cc: cc in ("ZI", "Zp", "Cc", "Cf") and c not in list(map(chr, [0x000d, 0x000a, 0x200c, 0x200d]))
_extend = lambda c, cc: _grapheme_extend(c, cc) or \
                        c in list(map(chr, [0xe30, 0xe32, 0xe33, 0xe45, 0xeb0, 0xeb2, 0xeb3]))
_prepend = lambda c, cc: c in _logical_order_exception  # noqa: ARG005
_spacing_mark = lambda c, cc: cc == "Mc" and c not in _other_grapheme_extend


def grapheme_break(left: str, right: str) -> bool:  # noqa: D103
    # GB1
    if left is None:
        return True

    # GB2 not required, see end of get_grapheme_clusters

    # GB3
    if left == _CR and right == _LF:
        return False

    left_cc = unicodedata.category(left)

    # GB4
    if _control(left, left_cc):
        return True

    right_cc = unicodedata.category(right)

    # GB5
    if _control(right, right_cc):
        return True

    # GB6, GB7, GB8 not implemented

    # GB9
    if _extend(right, right_cc):
        return False

    # GB9a
    if _spacing_mark(right, right_cc):
        return False

    # GB9b
    if _prepend(left, left_cc):
        return False

    # GB10
    return True


def get_grapheme_clusters(text: str) -> list[str]:
    """Implements Table 2 of UAX #29: Grapheme Cluster Boundaries.

    Does not currently implement Hangul syllable rules.

    Args:
        text: unicode
            String to cluster.

    Returns:
         List of Unicode grapheme clusters.
    """
    clusters = []
    cluster = ""
    left = None
    for right in text:
        if cluster and grapheme_break(left, right):
            clusters.append(cluster)
            cluster = ""
        elif cluster:
            # Add a zero-width space to keep len(clusters) == len(text)
            clusters.append("\u200b")
        cluster += right
        left = right

    # GB2
    if cluster:
        clusters.append(cluster)
    return clusters


class Glyph(image.TextureRegion):
    """A single glyph located within a larger texture.

    Glyphs are drawn most efficiently using the higher level APIs.
    """
    baseline: int = 0
    lsb: int = 0
    advance: int = 0

    #: :The vertices of this glyph, with (0,0) originating at the left-side bearing at the baseline.
    vertices: tuple[int, int, int, int] = (0, 0, 0, 0)

    #: :If a glyph is colored by the font renderer, such as an emoji, it may be treated differently by pyglet.
    colored = False

    def set_bearings(self, baseline: int, left_side_bearing: int, advance: int, x_offset: int = 0,
                     y_offset: int = 0) -> None:
        """Set metrics for this glyph.

        Args:
            baseline:
                Distance from the bottom of the glyph to its baseline. Typically negative.
            left_side_bearing:
                Distance to add to the left edge of the glyph.
            advance:
                Distance to move the horizontal advance to the next glyph, in pixels.
            x_offset:
                Distance to move the glyph horizontally from its default position.
            y_offset:
                Distance to move the glyph vertically from its default position.
        """
        self.baseline = baseline
        self.lsb = left_side_bearing
        self.advance = advance

        self.vertices = (
            left_side_bearing + x_offset,
            -baseline + y_offset,
            left_side_bearing + self.width + x_offset,
            -baseline + self.height + y_offset)


class GlyphTexture(image.Texture):
    """A texture containing a glyph."""
    region_class = Glyph


class GlyphTextureAtlas(image.atlas.TextureAtlas):
    """A texture atlas containing many glyphs."""
    texture_class = GlyphTexture

    def __init__(self, width: int = 2048, height: int = 2048, fmt: int = GL_RGBA, min_filter: int = GL_LINEAR,  # noqa: D107
                 mag_filter: int = GL_LINEAR) -> None:
        super().__init__(width, height)
        self.texture = self.texture_class.create(width, height, GL_TEXTURE_2D, fmt, min_filter, mag_filter, fmt=fmt)
        self.allocator = image.atlas.Allocator(width, height)

    def add(self, img: image.AbstractImage, border: int = 0) -> Glyph:
        return super().add(img, border)


class GlyphTextureBin(image.atlas.TextureBin):
    """Same as a TextureBin but allows you to specify filter of Glyphs."""

    def add(self, img: image.AbstractImage, fmt: int = GL_RGBA, min_filter: int = GL_LINEAR,
            mag_filter: int = GL_LINEAR, border: int = 0) -> Glyph:
        for atlas in list(self.atlases):
            try:
                return atlas.add(img, border)
            except image.atlas.AllocatorException:  # noqa: PERF203
                # Remove atlases that are no longer useful (so that their textures
                # can later be freed if the images inside them get collected).
                if img.width < 64 and img.height < 64:
                    self.atlases.remove(atlas)

        atlas = GlyphTextureAtlas(self.texture_width, self.texture_height, fmt, min_filter, mag_filter)
        self.atlases.append(atlas)
        return atlas.add(img, border)


class GlyphRenderer(abc.ABC):
    """Abstract class for creating glyph images."""

    @abc.abstractmethod
    def __init__(self, font: Font) -> None:
        """Initialize the glyph renderer.

        Args:
            font: The :py:class:`~pyglet.font.base.Font` object to be rendered.
        """

    @abc.abstractmethod
    def render(self, text: str) -> Glyph:
        """Render the string of text into an image.

        Args:
            text: The initial string to be rendered, typically one character.

        Returns:
             A Glyph with the proper metrics for that specific character.
        """


class FontException(Exception):  # noqa: N818
    """Generic exception related to errors from the font module.  Typically, from invalid font data."""


class Font:
    """Abstract font class able to produce glyphs.

    To construct a font, use :py:func:`pyglet.font.load`, which will instantiate the
    platform-specific font class.

    Internally, this class is used by the platform classes to manage the set
    of textures into which glyphs are written.

    Attributes:
        texture_width:
            Default Texture width to use if ``optimize_glyph`` is False.
        texture_height:
            Default Texture height to use if ``optimize_glyph`` is False.
        optimize_fit:
            Determines max texture size by the ``glyph_fit`` attribute. If False, ``texture_width`` and
            ``texture_height`` are used.
        glyph_fit:
            Standard keyboard characters amount to around ~100 alphanumeric characters. This value is used to
             pre-calculate how many glyphs can be saved into a single texture atlas. Increase this if you plan to
             support more than this standard scenario. Performance is increased the less textures are used. However,
             it does consume more video memory.
        texture_internalformat:
            Determines how textures are stored in internal format. By default, ``GL_RGBA``.
        texture_min_filter:
            The default minification filter for glyph textures. By default, ``GL_LINEAR``. Can be changed to
            ``GL_NEAREST`` to prevent aliasing with pixelated fonts.
        texture_mag_filter:
            The default magnification filter for glyph textures. By default, ``GL_LINEAR``. Can be changed to
            ``GL_NEAREST`` to prevent aliasing with pixelated fonts.
    """
    #: :meta private:
    glyphs: dict[str, Glyph]

    texture_width: int = 512
    texture_height: int = 512

    optimize_fit: int = True
    glyph_fit: int = 100

    texture_internalformat: int = GL_RGBA
    texture_min_filter: int = GL_LINEAR
    texture_mag_filter: int = GL_LINEAR

    # These should also be set by subclass when known
    ascent: int = 0
    descent: int = 0

    #: :meta private:
    # The default glyph renderer class. Should not be overridden by users, only other renderer variations.
    glyph_renderer_class: ClassVar[type[GlyphRenderer]] = GlyphRenderer

    #: :meta private:
    # The default type of texture bins. Should not be overridden by users.
    texture_class: ClassVar[type[GlyphTextureBin]] = GlyphTextureBin

    def __init__(self) -> None:
        """Initialize a font that can be used with Pyglet."""
        self.texture_bin = None
        self.glyphs = {}

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the Family Name of the font as a string."""

    @classmethod
    def add_font_data(cls: type[Font], data: BinaryIO) -> None:
        """Add font data to the font loader.

        This is a class method and affects all fonts loaded.  Data must be
        some byte string of data, for example, the contents of a TrueType font
        file.  Subclasses can override this method to add the font data into
        the font registry.

        There is no way to instantiate a font given the data directly, you
        must use :py:func:`pyglet.font.load` specifying the font name.
        """

    @classmethod
    def have_font(cls: type[Font], name: str) -> bool:
        """Determine if a font with the given name is installed.

        Args:
            name:
                Name of a font to search for.
        """
        return True

    def create_glyph(self, img: image.AbstractImage, fmt: int | None = None) -> Glyph:
        """Create a glyph using the given image.

        This is used internally by `Font` subclasses to add glyph data
        to the font.  Glyphs are packed within large textures maintained by the
        `Font` instance.  This method inserts the image into a texture atlas managed by the font.

        Applications should not use this method directly.

        Args:
            img:
                The image to write to the font texture.
            fmt:
                Override for the format and internalformat of the atlas texture. None will use default.
        """
        if self.texture_bin is None:
            if self.optimize_fit:
                self.texture_width, self.texture_height = self._get_optimal_atlas_size(img)
            self.texture_bin = GlyphTextureBin(self.texture_width, self.texture_height)

        return self.texture_bin.add(
            img, fmt or self.texture_internalformat, self.texture_min_filter, self.texture_mag_filter, border=1)

    def _get_optimal_atlas_size(self, image_data: image.AbstractImage) -> tuple[int, int]:
        """Retrieves the optimal atlas size to fit ``image_data`` with ``glyph_fit`` number of glyphs."""
        # A texture glyph sheet should be able to handle all standard keyboard characters in one sheet.
        # 26 Alpha upper, 26 lower, 10 numbers, 33 symbols, space = around 96 characters. (Glyph Fit)
        aw, ah = self.texture_width, self.texture_height

        atlas_size: tuple[int, int] | None = None

        # Just a fast check to get the smallest atlas size possible to fit.
        i = 0
        while not atlas_size:
            fit = ((aw - (image_data.width + 2)) // (image_data.width + 2) + 1) * (
                    (ah - (image_data.height + 2)) // (image_data.height + 2) + 1)

            if fit >= self.glyph_fit:
                atlas_size = (aw, ah)

            if i % 2:
                aw *= 2
            else:
                ah *= 2

            i += 1

        return atlas_size

    def get_glyphs(self, text: str) -> list[Glyph]:
        """Create and return a list of Glyphs for `text`.

        If any characters do not have a known glyph representation in this
        font, a substitution will be made.

        Args:
            text:
                Text to render.
        """
        glyph_renderer = None
        glyphs = []  # glyphs that are committed.
        for c in get_grapheme_clusters(str(text)):
            # Get the glyph for 'c'.  Hide tabs (Windows and Linux render
            # boxes)
            if c == "\t":
                c = " "  # noqa: PLW2901
            if c not in self.glyphs:
                if not glyph_renderer:
                    glyph_renderer = self.glyph_renderer_class(self)
                self.glyphs[c] = glyph_renderer.render(c)
            glyphs.append(self.glyphs[c])
        return glyphs

    def get_glyphs_for_width(self, text: str, width: int) -> list[Glyph]:
        """Return a list of glyphs for ``text`` that fit within the given width.

        If the entire text is larger than 'width', as much as possible will be
        used while breaking after a space or zero-width space character.  If a
        newline is encountered in text, only text up to that newline will be
        used.  If no break opportunities (newlines or spaces) occur within
        `width`, the text up to the first break opportunity will be used (this
        will exceed `width`).  If there are no break opportunities, the entire
        text will be used.

        You can assume that each character of the text is represented by
        exactly one glyph; so the amount of text "used up" can be determined
        by examining the length of the returned glyph list.

        Args:
            text:
                Text to render.
            width:
                Maximum width of returned glyphs.
        """
        glyph_renderer = None
        glyph_buffer = []  # next glyphs to be added, as soon as a BP is found
        glyphs = []  # glyphs that are committed.
        for c in text:
            if c == "\n":
                glyphs += glyph_buffer
                break

            # Get the glyph for 'c'
            if c not in self.glyphs:
                if not glyph_renderer:
                    glyph_renderer = self.glyph_renderer_class(self)
                self.glyphs[c] = glyph_renderer.render(c)
            glyph = self.glyphs[c]

            # Add to holding buffer and measure
            glyph_buffer.append(glyph)
            width -= glyph.advance

            # If over width and have some committed glyphs, finish.
            if width <= 0 < len(glyphs):
                break

            # If a valid breakpoint, commit holding buffer
            if c in "\u0020\u200b":
                glyphs += glyph_buffer
                glyph_buffer = []

        # If nothing was committed, commit everything (no breakpoints found).
        if len(glyphs) == 0:
            glyphs = glyph_buffer

        return glyphs

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.name}')"
