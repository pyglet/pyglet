"""Abstract classes used by pyglet.font implementations.

These classes should not be constructed directly.  Instead, use the functions
in `pyglet.font` to obtain platform-specific instances.  You can use these
classes as a documented interface to the concrete classes.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, BinaryIO, ClassVar, TYPE_CHECKING

import unicodedata

from pyglet.enums import (
    TextureFilter,
    Weight,
    Stretch,
    Style,
)
from pyglet.graphics import atlas
from pyglet.graphics.texture import Texture, TextureRegion
from pyglet.image import ImageData

if TYPE_CHECKING:
    from pyglet.font import FontManager

_OTHER_GRAPHEME_EXTEND = {
    chr(x) for x in [0x09be, 0x09d7, 0x0be3, 0x0b57, 0x0bbe, 0x0bd7, 0x0cc2,
                     0x0cd5, 0x0cd6, 0x0d3e, 0x0d57, 0x0dcf, 0x0ddf, 0x200c,
                     0x200d, 0xff9e, 0xff9f]
}  # skip codepoints above U+10000
_LOGICAL_ORDER_EXCEPTION = {chr(x) for x in range(0xe40, 0xe45)} | {chr(x) for x in range(0xec0, 0xec4)}

_EXTEND_CHARS = {chr(x) for x in [0xe30, 0xe32, 0xe33, 0xe45, 0xeb0, 0xeb2, 0xeb3]}

_CR = "\u000d"
_LF = "\u000a"

_CATEGORY_EXTEND = {"Me", "Mn"}
_CATEGORY_CONTROL = {"ZI", "Zp", "Cc", "Cf"}
_CATEGORY_SPACING_MARK = {"Mc"}


def grapheme_break(left: str, left_cc: str, right: str, right_cc: str) -> bool:
    """Determines if there should be a break between characters."""
    # GB1
    if left is None:
        return True

    # GB2 not required, see end of get_grapheme_clusters

    # GB3: CR + LF do not break
    if left == _CR and right == _LF:
        return False

    # GB4: Break before Control characters
    if left_cc in _CATEGORY_CONTROL and left not in _OTHER_GRAPHEME_EXTEND:
        return True

    # GB5: Break after Control characters
    if right_cc in _CATEGORY_CONTROL and right not in _OTHER_GRAPHEME_EXTEND:
        return True

    # GB6, GB7, GB8 not implemented

    # GB9: Do not break before Extend characters
    if right_cc in _CATEGORY_EXTEND or right in _EXTEND_CHARS:
        return False

    # GB9a: Do not break before SpacingMark characters
    if right_cc == "Mc" and right not in _OTHER_GRAPHEME_EXTEND:
        return False

    # GB9b: Do not break after Prepend characters
    if left in _LOGICAL_ORDER_EXCEPTION:
        return False

    # GB999: Default to break
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
    cluster_chars = []
    left = None
    left_cc = None

    for right in text:
        right_cc = unicodedata.category(right)

        if cluster_chars and grapheme_break(left, left_cc, right, right_cc):
            clusters.append("".join(cluster_chars))
            cluster_chars.clear()

        cluster_chars.append(right)
        left = right
        left_cc = right_cc

    if cluster_chars:
        clusters.append("".join(cluster_chars))

    return clusters


#: :meta private:
@dataclass
class GlyphPosition:
    """Positioning offsets for a glyph."""
    __slots__ = ('x_advance', 'x_offset', 'y_advance', 'y_offset')
    x_advance: int  # How far the line advances AFTER drawing horizontal.
    y_advance: int  # How far the line advances AFTER drawing vertical.
    x_offset: int  # How much the current glyph moves on the X-axis when drawn. Does not advance.
    y_offset: int  # How much the current glyph moves on the Y-axis when drawn. Does not advance.


class Glyph(TextureRegion):
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

    def set_bearings(self, baseline: int, left_side_bearing: int, advance: int) -> None:
        """Set metrics for this glyph.

        Args:
            baseline:
                Distance from the bottom of the glyph to its baseline. Typically negative.
            left_side_bearing:
                Distance to add to the left edge of the glyph.
            advance:
                Distance to move the horizontal advance to the next glyph, in pixels.
        """
        self.baseline = baseline
        self.lsb = left_side_bearing
        self.advance = advance

        self.vertices = (
            left_side_bearing,
            -baseline,
            left_side_bearing + self.width,
            -baseline + self.height)


class GlyphTexture(Texture):
    """A texture containing a glyph."""
    region_class = Glyph


class GlyphTextureAtlas(atlas.TextureAtlas):
    """A texture atlas containing many glyphs."""
    texture_class = GlyphTexture

    def __init__(self, width: int = 2048, height: int = 2048, filters: TextureFilter = TextureFilter.LINEAR) -> None:
        super().__init__(width, height)
        self.texture = self.texture_class.create(width, height, filters=filters)
        self.allocator = atlas.Allocator(width, height)

    def add(self, img: ImageData, border: int = 0) -> Glyph:
        return super().add(img, border)


class GlyphTextureBin(atlas.TextureBin):
    """Same as a TextureBin but allows you to specify filter of Glyphs."""

    def add(self, img: ImageData, filters: TextureFilter, border: int = 0) -> Glyph:
        for glyph_atlas in list(self.atlases):
            try:
                return glyph_atlas.add(img, border)
            except atlas.AllocatorException:  # noqa: PERF203
                # Remove atlases that are no longer useful (so that their textures
                # can later be freed if the images inside them get collected).
                if img.width < 64 and img.height < 64:
                    self.atlases.remove(glyph_atlas)

        glyph_atlas = GlyphTextureAtlas(self.texture_width, self.texture_height, filters)
        self.atlases.append(glyph_atlas)
        return glyph_atlas.add(img, border)


class GlyphRenderer(abc.ABC):
    """Abstract class for creating glyph images."""

    @abc.abstractmethod
    def __init__(self, font: Font) -> None:
        """Initialize the glyph renderer.

        Args:
            font: The :py:class:`~pyglet.font.base.Font` object to be rendered.
        """
        self.font = font

    @abc.abstractmethod
    def render(self, text: str) -> Glyph:
        """Render the string of text into an image.

        Args:
            text: The initial string to be rendered, typically one character.

        Returns:
             A Glyph with the proper metrics for that specific character.
        """

    def create_zero_glyph(self) -> Glyph:
        """Zero glyph is a 1x1 image that has a -1 advance.

        This is to fill in for potential substitutions since font system requires 1 glyph per character in a string.
        """
        image_data = ImageData(1, 1, 'RGBA', bytes([0, 0, 0, 0]))
        glyph = self.font.create_glyph(image_data)
        glyph.set_bearings(-self.font.descent, 0, -1)
        return glyph

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
        default_descriptor:
            The default Texture description of the atlas and font.
    """
    #: :meta private:
    texture_bin: None | GlyphTextureBin

    #: :meta private:
    glyphs: dict[str | int | tuple[Any, int], Glyph]
    # Glyphs can be cached in various ways:
    # str: if no text shaping
    # int: glyph index, if no fallback behavior.
    # tuple: with a unique font identifier and glyph index

    texture_width: int = 512
    texture_height: int = 512

    optimize_fit: int = True
    glyph_fit: int = 100

    filters = TextureFilter.LINEAR

    # These should also be set by subclass when known
    ascent: int = 0
    descent: int = 0

    #: :meta private:
    # The default glyph renderer class. Should not be overridden by users, only other renderer variations.
    glyph_renderer_class: ClassVar[type[GlyphRenderer]] = GlyphRenderer

    #: :meta private:
    # The default type of texture bins. Should not be overridden by users.
    texture_class: ClassVar[type[GlyphTextureBin]] = GlyphTextureBin

    _glyph_renderer: GlyphRenderer | None
    _missing_glyph: Glyph | None
    _zero_glyph: Glyph | None

    # The size of the font in pixels.
    pixel_size: float

    def __init__(self, name: str, size: float, weight: str | Weight, style: str | Style, stretch: str | Stretch,
                 dpi: int | None) -> None:
        """Initialize a font that can be used with Pyglet.

        Args:
            name:
                Font family, for example, "Times New Roman".  If a list of names
                is provided, the first one matching a known font is used.  If no
                font can be matched to the name(s), a default font is used. The default font
                will be platform dependent.
            size:
                Size of the font, in points.  The returned font may be an exact
                match or the closest available.
            weight:
                If set, a specific weight variant is returned if one exists for the given font
                family and size. The weight is provided as a string. For example: "bold" or "light".
            style:
                If True, an italic variant is returned, if one exists for the given family and size. For some Font
                renderers, italics may have an "oblique" variation which can be specified as a string.
            stretch:
                If True, a stretch variant is returned, if one exists for the given family and size.  Currently only
                supported by Windows through the ``DirectWrite`` font renderer. For example, "condensed" or "expanded".
            dpi: int
                The assumed resolution of the display device, for the purposes of
                determining the pixel size of the font.  Defaults to 96.
        """
        self._name = name
        self.size = size
        self.weight = weight
        self.style = style
        self.stretch = stretch
        self.dpi = dpi

        # From DPI to DIP (Device Independent Pixels)
        self.pixel_size = (self.size * self.dpi) // 72

        self.texture_bin = None
        self.hb_resource =  None
        self._glyph_renderer = None

        # Represents a missing glyph.
        self._missing_glyph = None

        # Represents a zero width glyph.
        self._zero_glyph = None
        self.glyphs = {}

    def _initialize_renderer(self) -> None:
        """Initialize the glyph renderer and cache it on the Font.

        This way renderers for fonts that have been loaded but not used will not have unnecessary loaders.
        """
        if not self._glyph_renderer:
            self._glyph_renderer = self.glyph_renderer_class(self)
            self._missing_glyph = self._glyph_renderer.render(" ")
            self._zero_glyph = self._glyph_renderer.create_zero_glyph()

    @property
    def name(self) -> str:
        """Return the Family Name of the font as a string."""
        return self._name

    @classmethod
    @abc.abstractmethod
    def add_font_data(cls: type[Font], data: BinaryIO, manager: FontManager) -> None:
        """Add font data to the font loader.

        This is a class method and affects all fonts loaded.  Data must be
        some byte string of data, for example, the contents of a TrueType font
        file.  Subclasses can override this method to add the font data into
        the font registry.

        There is no way to instantiate a font given the data directly, you
        must use :py:func:`pyglet.font.load` specifying the font name.
        """

    @classmethod
    @abc.abstractmethod
    def have_font(cls: type[Font], name: str) -> bool:
        """Determine if a font with the given name is installed.

        Args:
            name:
                Name of a font to search for.
        """

    def create_glyph(self, img: ImageData) -> Glyph:
        """Create a glyph using the given image.

        This is used internally by `Font` subclasses to add glyph data
        to the font.  Glyphs are packed within large textures maintained by the
        `Font` instance.  This method inserts the image into a texture atlas managed by the font.

        Applications should not use this method directly.

        Args:
            img:
                The image to write to the font texture.
            descriptor:
                Override for the atlas texture's descriptor. None will use default.
        """
        if self.texture_bin is None:
            if self.optimize_fit:
                self.texture_width, self.texture_height = self._get_optimal_atlas_size(img)
            self.texture_bin = GlyphTextureBin(self.texture_width, self.texture_height)

        return self.texture_bin.add(img, self.filters, border=1)

    def _get_optimal_atlas_size(self, image_data: ImageData) -> tuple[int, int]:
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

    def get_glyphs(self, text: str, shaping: bool = False) -> tuple[list[Glyph], list[GlyphPosition]]:
        """Create and return a list of Glyphs for `text`.

        If any characters do not have a known glyph representation in this
        font, a substitution will be made.

        Args:
            text:
                Text to render.
            shaping:
                If the text will be shaped using the global option. If ``False``, no text shaping will occur and
                positioning will instead be based on glyph dimensions.
        """
        glyph_renderer = None

        glyphs = []  # glyphs that are committed.
        offsets = []
        for c in get_grapheme_clusters(str(text)):
            # Get the glyph for 'c'.  Hide tabs (Windows and Linux render boxes)
            if c == "\t":
                c = " "  # noqa: PLW2901
            if c not in self.glyphs:
                if not glyph_renderer:
                    glyph_renderer = self.glyph_renderer_class(self)
                self.glyphs[c] = glyph_renderer.render(c)
            glyphs.append(self.glyphs[c])
            offsets.append(GlyphPosition(0, 0, 0, 0))

        return glyphs, offsets

    @abc.abstractmethod
    def get_text_size(self, text: str) -> tuple[int, int]:
        """Return's an estimated width and height of text using glyph metrics without rendering..

        This does not take into account any shaping.
        """

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
        return f"{self.__class__.__name__}('name={self.name}, size={self.size})')"


# Font Table Mappings
_weight_class_to_weight = {
    100: Weight.THIN,
    200: Weight.EXTRALIGHT,  # Ultralight
    300: Weight.LIGHT,
    400: Weight.NORMAL,  # REGULAR
    500: Weight.MEDIUM,
    600: Weight.SEMIBOLD,  # DEMIBOLD
    700: Weight.BOLD,
    800: Weight.EXTRABOLD,  # ULTRABOLD
    900: Weight.BLACK,  # HEAVY
    950: Weight.EXTRABLACK,
}

_width_class_to_stretch = {
    1: Stretch.ULTRACONDENSED,
    2: Stretch.EXTRACONDENSED,
    3: Stretch.CONDENSED,
    4: Stretch.SEMICONDENSED,
    5: Stretch.NORMAL,
    6: Stretch.SEMIEXPANDED,
    7: Stretch.EXPANDED,
    8: Stretch.EXTRAEXPANDED,
    9: Stretch.ULTRAEXPANDED,
}
