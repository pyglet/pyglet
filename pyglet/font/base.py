"""Abstract classes used by pyglet.font implementations.

These classes should not be constructed directly.  Instead, use the functions
in `pyglet.font` to obtain platform-specific instances.  You can use these
classes as a documented interface to the concrete classes.
"""

import unicodedata

from pyglet.gl import *
from pyglet import image

_other_grapheme_extend = list(map(chr, [0x09be, 0x09d7, 0x0be3, 0x0b57, 0x0bbe, 0x0bd7, 0x0cc2,
                                        0x0cd5, 0x0cd6, 0x0d3e, 0x0d57, 0x0dcf, 0x0ddf, 0x200c,
                                        0x200d, 0xff9e, 0xff9f]))  # skip codepoints above U+10000
_logical_order_exception = list(map(chr, list(range(0xe40, 0xe45)) + list(range(0xec0, 0xec4))))

_grapheme_extend = lambda c, cc: cc in ('Me', 'Mn') or c in _other_grapheme_extend

_CR = u'\u000d'
_LF = u'\u000a'
_control = lambda c, cc: cc in ('ZI', 'Zp', 'Cc', 'Cf') and not \
    c in list(map(chr, [0x000d, 0x000a, 0x200c, 0x200d]))
_extend = lambda c, cc: _grapheme_extend(c, cc) or \
                        c in list(map(chr, [0xe30, 0xe32, 0xe33, 0xe45, 0xeb0, 0xeb2, 0xeb3]))
_prepend = lambda c, cc: c in _logical_order_exception
_spacing_mark = lambda c, cc: cc == 'Mc' and c not in _other_grapheme_extend


def grapheme_break(left, right):
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


def get_grapheme_clusters(text):
    """Implements Table 2 of UAX #29: Grapheme Cluster Boundaries.

    Does not currently implement Hangul syllable rules.
    
    :Parameters:
        `text` : unicode
            String to cluster.

    .. versionadded:: 1.1.2

    :rtype: List of `unicode`
    :return: List of Unicode grapheme clusters
    """
    clusters = []
    cluster = ''
    left = None
    for right in text:
        if cluster and grapheme_break(left, right):
            clusters.append(cluster)
            cluster = ''
        elif cluster:
            # Add a zero-width space to keep len(clusters) == len(text)
            clusters.append(u'\u200b')
        cluster += right
        left = right

    # GB2
    if cluster:
        clusters.append(cluster)
    return clusters


class Glyph(image.TextureRegion):
    """A single glyph located within a larger texture.

    Glyphs are drawn most efficiently using the higher level APIs, for example
    `GlyphString`.

    :Ivariables:
        `advance` : int
            The horizontal advance of this glyph, in pixels.
        `vertices` : (int, int, int, int)
            The vertices of this glyph, with (0,0) originating at the
            left-side bearing at the baseline.
        `colored` : bool
            If a glyph is colored by the font renderer, such as an emoji, it may
            be treated differently by pyglet. For example, being omitted from text color shaders.

    """
    baseline = 0
    lsb = 0
    advance = 0
    vertices = (0, 0, 0, 0)
    colored = False

    def set_bearings(self, baseline, left_side_bearing, advance, x_offset=0, y_offset=0):
        """Set metrics for this glyph.

        :Parameters:
            `baseline` : int
                Distance from the bottom of the glyph to its baseline;
                typically negative.
            `left_side_bearing` : int
                Distance to add to the left edge of the glyph.
            `advance` : int
                Distance to move the horizontal advance to the next glyph.
            `offset_x` : int
                Distance to move the glyph horizontally from its default position.
            `offset_y` : int
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

    def get_kerning_pair(self, right_glyph):
        """Not implemented.
        """
        return 0


class GlyphTexture(image.Texture):
    region_class = Glyph


class GlyphTextureAtlas(image.atlas.TextureAtlas):
    """A texture atlas containing glyphs."""
    texture_class = GlyphTexture

    def __init__(self, width=2048, height=2048, fmt=GL_RGBA, min_filter=GL_LINEAR, mag_filter=GL_LINEAR):
        self.texture = self.texture_class.create(width, height, GL_TEXTURE_2D, fmt, min_filter, mag_filter, fmt=fmt)
        self.allocator = image.atlas.Allocator(width, height)


class GlyphTextureBin(image.atlas.TextureBin):
    """Same as a TextureBin but allows you to specify filter of Glyphs."""

    def add(self, img, fmt=GL_RGBA, min_filter=GL_LINEAR, mag_filter=GL_LINEAR, border=0):
        for atlas in list(self.atlases):
            try:
                return atlas.add(img, border)
            except image.atlas.AllocatorException:
                # Remove atlases that are no longer useful (so that their textures
                # can later be freed if the images inside them get collected).
                if img.width < 64 and img.height < 64:
                    self.atlases.remove(atlas)

        atlas = GlyphTextureAtlas(self.texture_width, self.texture_height, fmt, min_filter, mag_filter)
        self.atlases.append(atlas)
        return atlas.add(img, border)


class GlyphRenderer:
    """Abstract class for creating glyph images.
    """

    def __init__(self, font):
        pass

    def render(self, text):
        raise NotImplementedError('Subclass must override')


class FontException(Exception):
    """Generic exception related to errors from the font module.  Typically
    these relate to invalid font data."""
    pass


class Font:
    """Abstract font class able to produce glyphs.

    To construct a font, use :py:func:`pyglet.font.load`, which will instantiate the
    platform-specific font class.

    Internally, this class is used by the platform classes to manage the set
    of textures into which glyphs are written.

    :Ivariables:
        `ascent` : int
            Maximum ascent above the baseline, in pixels.
        `descent` : int
            Maximum descent below the baseline, in pixels. Usually negative.
    """
    texture_width = 512
    texture_height = 512

    optimize_fit = True
    glyph_fit = 100

    texture_internalformat = GL_RGBA
    texture_min_filter = GL_LINEAR
    texture_mag_filter = GL_LINEAR

    # These should also be set by subclass when known
    ascent = 0
    descent = 0

    glyph_renderer_class = GlyphRenderer
    texture_class = GlyphTextureBin

    def __init__(self):
        self.texture_bin = None
        self.glyphs = {}

    @property
    def name(self):
        """Return the Family Name of the font as a string."""
        raise NotImplementedError

    @classmethod
    def add_font_data(cls, data):
        """Add font data to the font loader.

        This is a class method and affects all fonts loaded.  Data must be
        some byte string of data, for example, the contents of a TrueType font
        file.  Subclasses can override this method to add the font data into
        the font registry.

        There is no way to instantiate a font given the data directly, you
        must use :py:func:`pyglet.font.load` specifying the font name.
        """
        pass

    @classmethod
    def have_font(cls, name):
        """Determine if a font with the given name is installed.

        :Parameters:
            `name` : str
                Name of a font to search for

        :rtype: bool
        """
        return True

    def create_glyph(self, image, fmt=None):
        """Create a glyph using the given image.

        This is used internally by `Font` subclasses to add glyph data
        to the font.  Glyphs are packed within large textures maintained by
        `Font`.  This method inserts the image into a font texture and returns
        a glyph reference; it is up to the subclass to add metadata to the
        glyph.

        Applications should not use this method directly.

        :Parameters:
            `image` : `pyglet.image.AbstractImage`
                The image to write to the font texture.
            `fmt` : `int`
                Override for the format and internalformat of the atlas texture

        :rtype: `Glyph`
        """
        if self.texture_bin is None:
            if self.optimize_fit:
                self.texture_width, self.texture_height = self._get_optimal_atlas_size(image)
            self.texture_bin = GlyphTextureBin(self.texture_width, self.texture_height)

        glyph = self.texture_bin.add(
            image, fmt or self.texture_internalformat, self.texture_min_filter, self.texture_mag_filter, border=1)

        return glyph

    def _get_optimal_atlas_size(self, image_data):
        """Return the smallest size of atlas that can fit around 100 glyphs based on the image_data provided."""
        # A texture glyph sheet should be able to handle all standard keyboard characters in one sheet.
        # 26 Alpha upper, 26 lower, 10 numbers, 33 symbols, space = around 96 characters. (Glyph Fit)
        aw, ah = self.texture_width, self.texture_height

        atlas_size = None

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
        for c in get_grapheme_clusters(str(text)):
            # Get the glyph for 'c'.  Hide tabs (Windows and Linux render
            # boxes)
            if c == '\t':
                c = ' '
            if c not in self.glyphs:
                if not glyph_renderer:
                    glyph_renderer = self.glyph_renderer_class(self)
                self.glyphs[c] = glyph_renderer.render(c)
            glyphs.append(self.glyphs[c])
        return glyphs

    def get_glyphs_for_width(self, text, width):
        """Return a list of glyphs for `text` that fit within the given width.
        
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

        :Parameters:
            `text` : str or unicode
                Text to render.
            `width` : int
                Maximum width of returned glyphs.
        
        :rtype: list of `Glyph`

        :see: `GlyphString`
        """
        glyph_renderer = None
        glyph_buffer = []  # next glyphs to be added, as soon as a BP is found
        glyphs = []  # glyphs that are committed.
        for c in text:
            if c == '\n':
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
            if c in u'\u0020\u200b':
                glyphs += glyph_buffer
                glyph_buffer = []

        # If nothing was committed, commit everything (no breakpoints found).
        if len(glyphs) == 0:
            glyphs = glyph_buffer

        return glyphs

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.name}')"
