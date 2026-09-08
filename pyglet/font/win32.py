# Windows Vista: need to call SetProcessDPIAware?  May affect GDI+ calls as well as font.
from __future__ import annotations

import ctypes
import math
import warnings
from typing import TYPE_CHECKING, ClassVar, Sequence

import pyglet
import pyglet.image
from pyglet.enums import Stretch, Style, Weight
from pyglet.font import FontManager, base
from pyglet.image.codecs.gdiplus import BitmapData, ImageLockModeRead, PixelFormat32bppARGB, Rect, gdiplus
from pyglet.libs.win32 import _gdi32 as gdi32
from pyglet.libs.win32 import _user32 as user32
from pyglet.libs.win32.constants import (
    ANTIALIASED_QUALITY,
    FW_BLACK,
    FW_BOLD,
    FW_DEMIBOLD,
    FW_EXTRABOLD,
    FW_EXTRALIGHT,
    FW_HEAVY,
    FW_LIGHT,
    FW_MEDIUM,
    FW_NORMAL,
    FW_REGULAR,
    FW_SEMIBOLD,
    FW_THIN,
    FW_ULTRABOLD,
    FW_ULTRALIGHT,
)
from pyglet.libs.win32.context_managers import device_context
from pyglet.libs.win32.types import ABC, BYTE, LOGFONTW, SIZE, TEXTMETRIC

if TYPE_CHECKING:
    from pyglet.font.base import Glyph



DriverStringOptionsCmapLookup = 1
DriverStringOptionsRealizedAdvance = 4
TextRenderingHintSingleBitPerPixelGridFit = 1
TextRenderingHintAntiAlias = 4
TextRenderingHintAntiAliasGridFit = 3


FontStyleBold = 1
FontStyleItalic = 2
UnitPixel = 2

StringFormatFlagsDirectionRightToLeft = 0x00000001
StringFormatFlagsDirectionVertical = 0x00000002
StringFormatFlagsNoFitBlackBox = 0x00000004
StringFormatFlagsDisplayFormatControl = 0x00000020
StringFormatFlagsNoFontFallback = 0x00000400
StringFormatFlagsMeasureTrailingSpaces = 0x00000800
StringFormatFlagsNoWrap = 0x00001000
StringFormatFlagsLineLimit = 0x00002000
StringFormatFlagsNoClip = 0x00004000

FontFamilyNotFound = 14
GGI_MARK_NONEXISTING_GLYPHS = 0x0001


_debug_font = pyglet.options.debug_font

_font_weights = {
    True: FW_BOLD,
    False: FW_NORMAL,
    None: FW_NORMAL,
    "thin": FW_THIN,
    "extralight": FW_EXTRALIGHT,
    "ultralight": FW_ULTRALIGHT,
    "light": FW_LIGHT,
    "normal": FW_NORMAL,
    "regular": FW_REGULAR,
    "medium": FW_MEDIUM,
    "demibold": FW_DEMIBOLD,
    "semibold": FW_SEMIBOLD,
    "bold": FW_BOLD,
    "extrabold": FW_EXTRABOLD,
    "ultrabold": FW_ULTRABOLD,
    "black": FW_BLACK,
    "heavy": FW_HEAVY,
}


class Rectf(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("width", ctypes.c_float),
        ("height", ctypes.c_float),
    ]


_text_quality = {
    True: TextRenderingHintAntiAliasGridFit,
    False: TextRenderingHintSingleBitPerPixelGridFit,
}

class GDIPlusGlyphRenderer(base.GlyphRenderer):

    def __init__(self, font: GDIPlusFont) -> None:
        self._bitmap = None
        self._graphics = None
        self._brush = None
        self._matrix = None
        self._dc = None
        self._bitmap_rect = None
        super().__init__(font)
        self.font = font

        # Pessimistically round up width and height to 4 byte alignment
        width = font.max_glyph_width
        height = font.ascent - font.descent
        width = (width | 0x3) + 1
        height = (height | 0x3) + 1
        self._create_bitmap(width, height)

        gdi32.SelectObject(self._dc, self.font.hfont)

    def __del__(self) -> None:
        try:
            self._dispose_bitmap()
            if self._dc:
                user32.ReleaseDC(0, self._dc)
        except Exception:  # noqa: S110, BLE001
            pass

    def _dispose_bitmap(self) -> None:
        if self._matrix:
            gdiplus.GdipDeleteMatrix(self._matrix)
            self._matrix = None
        if self._brush:
            gdiplus.GdipDeleteBrush(self._brush)
            self._brush = None
        if self._graphics:
            gdiplus.GdipDeleteGraphics(self._graphics)
            self._graphics = None
        if self._bitmap:
            gdiplus.GdipDisposeImage(self._bitmap)
            self._bitmap = None

    def _create_bitmap(self, width: int, height: int) -> None:
        self._dispose_bitmap()

        self._data = (BYTE * (4 * width * height))()
        self._bitmap = ctypes.c_void_p()
        self._format = PixelFormat32bppARGB
        gdiplus.GdipCreateBitmapFromScan0(width, height, width * 4,
            self._format, self._data, ctypes.byref(self._bitmap))

        self._graphics = ctypes.c_void_p()
        gdiplus.GdipGetImageGraphicsContext(self._bitmap,
            ctypes.byref(self._graphics))
        gdiplus.GdipSetPageUnit(self._graphics, UnitPixel)

        if not self._dc:
            self._dc = user32.GetDC(0)
        gdi32.SelectObject(self._dc, self.font.hfont)

        gdiplus.GdipSetTextRenderingHint(self._graphics,
            _text_quality[pyglet.options.text_antialiasing])

        self._brush = ctypes.c_void_p()
        gdiplus.GdipCreateSolidFill(0xffffffff, ctypes.byref(self._brush))

        self._matrix = ctypes.c_void_p()
        gdiplus.GdipCreateMatrix(ctypes.byref(self._matrix))

        self._flags = (DriverStringOptionsCmapLookup |
                       DriverStringOptionsRealizedAdvance)

        self._rect = Rect(0, 0, width, height)

        self._bitmap_width = width
        self._bitmap_height = height

    def _ensure_bitmap_size(self, width: int, height: int) -> None:
        if width <= self._bitmap_width and height <= self._bitmap_height:
            return

        width = max(width, self._bitmap_width)
        height = max(height, self._bitmap_height)
        width = (width | 0x3) + 1
        height = (height | 0x3) + 1
        self._create_bitmap(width, height)

    def _get_bitmap_data(self, width: int, height: int) -> pyglet.image.ImageData:
        bitmap_data = BitmapData()
        gdiplus.GdipBitmapLockBits(
            self._bitmap,
            ctypes.byref(self._rect), ImageLockModeRead, self._format,
            ctypes.byref(bitmap_data))

        buffer = ctypes.create_string_buffer(bitmap_data.Stride * bitmap_data.Height)
        ctypes.memmove(buffer, bitmap_data.Scan0, len(buffer))
        gdiplus.GdipBitmapUnlockBits(self._bitmap, ctypes.byref(bitmap_data))

        return pyglet.image.ImageData(width, height, "BGRA", buffer, -bitmap_data.Stride)

    def render(self, text: str) -> Glyph:
        ch = ctypes.create_unicode_buffer(text)
        len_ch = len(ch) - 1

        # Layout rectangle; not clipped against so not terribly important.
        width = 10000
        height = self._bitmap_height
        rect = Rectf(0, self._bitmap_height
                        - self.font.ascent + self.font.descent,
                     width, height)

        # Set up GenericTypographic with 1 character measure range
        generic = ctypes.c_void_p()
        gdiplus.GdipStringFormatGetGenericTypographic(ctypes.byref(generic))
        fmt = ctypes.c_void_p()
        gdiplus.GdipCloneStringFormat(generic, ctypes.byref(fmt))
        gdiplus.GdipDeleteStringFormat(generic)

        # --- Measure advance

        # XXX HACK HACK HACK
        # Windows GDI+ is a filthy broken toy.  No way to measure the bounding
        # box of a string, or to obtain LSB.  What a joke.
        #
        # For historical note, GDI cannot be used because it cannot composite
        # into a bitmap with alpha.
        #
        # It looks like MS have abandoned GDI and GDI+ and are finally
        # supporting accurate text measurement with alpha composition in .NET
        # 2.0 (WinForms) via the TextRenderer class; this has no C interface
        # though, so we're entirely screwed.
        #
        # So anyway, we first try to get the width with GdipMeasureString.
        # Then if it's a TrueType font, we use GetCharABCWidthsW to get the
        # correct LSB. If it's a negative LSB, we move the layoutRect `rect`
        # to the right so that the whole glyph is rendered on the surface.
        # For positive LSB, we let the renderer render the correct white
        # space and we don't pass the LSB info to the Glyph.set_bearings

        bbox = Rectf()
        flags = (StringFormatFlagsMeasureTrailingSpaces |
                 StringFormatFlagsNoClip |
                 StringFormatFlagsNoFitBlackBox)
        gdiplus.GdipSetStringFormatFlags(fmt, flags)
        gdiplus.GdipMeasureString(self._graphics,
                                  ch,
                                  len_ch,
                                  self.font._gdipfont,
                                  ctypes.byref(rect),
                                  fmt,
                                  ctypes.byref(bbox),
                                  None,
                                  None)

        # We only care about the advance from this whole thing.
        advance = int(math.ceil(bbox.width))

        # GDI functions only work for a single character so we transform
        # grapheme \r\n into \r
        if text == "\r\n":
            text = "\r"

        # XXX END HACK HACK HACK

        abc = ABC()
        width = 0
        lsb = 0
        ttf_font = True
        # Use GDI to get code points for the text passed. This is almost always 1.
        # For special unicode characters it may be comprised of 2+ codepoints. Get the width/lsb of each.
        # Function only works on TTF fonts.
        for codepoint in [ord(c) for c in text]:
            if gdi32.GetCharABCWidthsW(self._dc, codepoint, codepoint, ctypes.byref(abc)):
                lsb += abc.abcA
                width += abc.abcB

                if lsb < 0:
                    # Negative LSB: we shift the layout rect to the right
                    # Otherwise we will cut the left part of the glyph
                    rect.x = -lsb
                    width -= lsb
                else:
                    width += lsb
            else:
                ttf_font = False
                break

        # Almost always a TTF font. Haven't seen a modern font that GetCharABCWidthsW fails on.
        # For safety, just use the advance as the width.
        if not ttf_font:
            width = advance

            # This hack bumps up the width if the font is italic;
            # this compensates for some common fonts.  It's also a stupid
            # waste of texture memory.
            if self.font.style:
                width += width // 2
                # Do not enlarge more than the _rect width.
                width = min(width, self._rect.Width)

        # ABC queries operate on BMP characters and can report the default
        # glyph for supplementary-plane text. The GDI+ measurement covers the
        # complete UTF-16 grapheme and prevents those glyphs from being cropped.
        width = max(1, width, math.ceil(bbox.width))
        self._ensure_bitmap_size(width, height)

        # Draw character to bitmap
        gdiplus.GdipGraphicsClear(self._graphics, 0x00000000)
        gdiplus.GdipDrawString(self._graphics,
                               ch,
                               len_ch,
                               self.font._gdipfont,
                               ctypes.byref(rect),
                               fmt,
                               self._brush)

        gdiplus.GdipFlush(self._graphics, 1)
        gdiplus.GdipDeleteStringFormat(fmt)

        image = self._get_bitmap_data(width, height)

        glyph = self.font.create_glyph(image)
        # Only pass negative LSB info
        lsb = min(lsb, 0)
        glyph.set_bearings(-self.font.descent, lsb, advance)
        return glyph

class Win32Font(base.Font):
    glyph_renderer_class = GDIPlusGlyphRenderer

    def __init__(
            self,
            name: str, size: float,
            weight: Weight | str = Weight.NORMAL,
            style: Style | str = Style.NORMAL,
            stretch: Stretch | str = Stretch.NORMAL,
            dpi: int | None = None,
    ) -> None:
        dpi = dpi or 96
        super().__init__(name, size, weight, style, stretch, dpi)

        italic = style != "normal"

        self.logfont = self.get_logfont(name, size, weight, italic, dpi)
        self.hfont = gdi32.CreateFontIndirectW(ctypes.byref(self.logfont))

        # Create a dummy DC for coordinate mapping
        with device_context(None) as dc:
            metrics = TEXTMETRIC()
            gdi32.SelectObject(dc, self.hfont)
            gdi32.GetTextMetricsA(dc, ctypes.byref(metrics))
            self.ascent = metrics.tmAscent
            self.descent = -metrics.tmDescent
            self.max_glyph_width = metrics.tmMaxCharWidth

    @staticmethod
    def get_logfont(
            name: str,
            size: float,
            weight: Weight | str | int | bool,
            italic: bool,
            dpi: int | None = None,
    ) -> LOGFONTW:
        """Get a raw Win32 :py:class:`.LOGFONTW` struct for the given arguments.

        Args:
            name: The name of the font
            size: The font size in points
            weight: Font weight name or numeric GDI font weight.
            italic: Whether to request the font as italic
            dpi: The screen dpi

        Returns:
            LOGFONTW: a ctypes binding of a Win32 LOGFONTW struct
        """

        dpi = dpi or 96
        logfont = LOGFONTW()
        logfont.lfHeight = -int(size * dpi / 72)
        if isinstance(weight, int) and not isinstance(weight, bool):
            logfont.lfWeight = weight
        else:
            logfont.lfWeight = _font_weights.get(weight, FW_NORMAL)
        logfont.lfItalic = italic
        logfont.lfFaceName = name
        logfont.lfQuality = ANTIALIASED_QUALITY

        return logfont

    def get_text_size(self, text: str) -> tuple[int, int]:
        """Return the unshaped dimensions of a text string."""
        size = SIZE()
        text_buffer = ctypes.create_unicode_buffer(text)
        with device_context(None) as dc:
            previous_font = gdi32.SelectObject(dc, self.hfont)
            try:
                if not gdi32.GetTextExtentPoint32W(dc, text_buffer, len(text_buffer) - 1, ctypes.byref(size)):
                    raise ctypes.WinError()
            finally:
                gdi32.SelectObject(dc, previous_font)
        return size.cx, size.cy

    def has_character(self, character: str) -> bool:
        super().has_character(character)

        glyph_index = ctypes.c_ushort()
        with device_context(None) as dc:
            previous_font = gdi32.SelectObject(dc, self.hfont)
            try:
                result = gdi32.GetGlyphIndicesW(
                    dc, character, 1, ctypes.byref(glyph_index), GGI_MARK_NONEXISTING_GLYPHS,
                )
            finally:
                gdi32.SelectObject(dc, previous_font)
        # GDI_ERROR (0xffffffff) signals a failed query. With
        # GGI_MARK_NONEXISTING_GLYPHS, 0xffff marks a character that has no
        # glyph in the selected face rather than returning its default glyph.
        return result != 0xffffffff and glyph_index.value != 0xffff


def _get_font_families(font_collection: ctypes.c_void_p) -> Sequence[ctypes.c_void_p]:
    num_count = ctypes.c_int()
    gdiplus.GdipGetFontCollectionFamilyCount(
        font_collection, ctypes.byref(num_count))
    gpfamilies = (ctypes.c_void_p * num_count.value)()
    numFound = ctypes.c_int()
    gdiplus.GdipGetFontCollectionFamilyList(
        font_collection, num_count, gpfamilies, ctypes.byref(numFound))

    return gpfamilies

def _get_font_family_names(font_collection: ctypes.c_void_p) -> set[str]:
    names = set()
    font_name = ctypes.create_unicode_buffer(32)
    for gpfamily in _get_font_families(font_collection):
        gdiplus.GdipGetFamilyName(gpfamily, font_name, "\0")
        names.add(font_name.value)

    return names

def _font_exists_in_collection(font_collection: ctypes.c_void_p, name: str) -> bool:
    font_name = ctypes.create_unicode_buffer(32)
    for gpfamily in _get_font_families(font_collection):
        gdiplus.GdipGetFamilyName(gpfamily, font_name, "\0")
        if font_name.value == name:
            return True

    return False


class GDIPlusFont(Win32Font):
    glyph_renderer_class: ClassVar[type[base.GlyphRenderer]] = GDIPlusGlyphRenderer

    _private_collection: ctypes.c_void_p | None = None
    _system_collection: ctypes.c_void_p | None = None

    _default_name = "Arial"

    def __init__(self, name: str, size: float, weight: Weight | str = Weight.NORMAL,
                 style: Style | str = Style.NORMAL, stretch: Stretch | str = Stretch.NORMAL,
                 dpi: int | None = None) -> None:
        self.hfont = None
        self._gdipfont = None

        if not name:
            name = self._default_name

        if stretch != "normal":
            warnings.warn("The current font render does not support the stretch argument.")

        super().__init__(name, size, weight, style, stretch, dpi)

        self._name = name

        family = ctypes.c_void_p()

        # GDI will add @ in front of a localized font for some Asian languages. However, GDI will also not find it
        # based on that name (???). Here we remove it before checking font collections.
        if name[0] == "@":
            name = name[1:]
            self._name = name

        name = ctypes.c_wchar_p(name)

        # Look in private collection first:
        if self._private_collection:
            gdiplus.GdipCreateFontFamilyFromName(name, self._private_collection, ctypes.byref(family))

        # Then in system collection:
        if not family:
            if _debug_font:
                print(f"Warning: Font '{name}' was not found. Defaulting to: {self._default_name}") 

            gdiplus.GdipCreateFontFamilyFromName(name, None, ctypes.byref(family))

        # Nothing found, use default font.
        if not family:
            self._name = self._default_name
            gdiplus.GdipCreateFontFamilyFromName(ctypes.c_wchar_p(self._name), None, ctypes.byref(family))

        # Keep the GDI+ rasterizer and the GDI metrics on the exact same
        # LOGFONT. This also preserves weights other than normal/bold.
        if self._name != self.logfont.lfFaceName:
            gdi32.DeleteObject(self.hfont)
            self.logfont = self.get_logfont(self._name, size, weight, style != "normal", self.dpi)
            self.hfont = gdi32.CreateFontIndirectW(ctypes.byref(self.logfont))

        self._gdipfont = ctypes.c_void_p()
        with device_context(None) as dc:
            status = gdiplus.GdipCreateFontFromLogfontW(
                dc,
                ctypes.byref(self.logfont),
                ctypes.byref(self._gdipfont),
            )
        if status != 0:
            gdip_style = 0
            if self.logfont.lfWeight >= FW_BOLD:
                gdip_style |= FontStyleBold
            if self.logfont.lfItalic:
                gdip_style |= FontStyleItalic
            status = gdiplus.GdipCreateFont(
                family,
                ctypes.c_float(self.pixel_size),
                gdip_style,
                UnitPixel,
                ctypes.byref(self._gdipfont),
            )
        gdiplus.GdipDeleteFontFamily(family)
        if status != 0:
            msg = f"GDI+ could not create font '{self._name}' from LOGFONT (status {status})."
            raise base.FontException(msg)

    @property
    def name(self) -> str:
        return self._name

    def __del__(self) -> None:
        try:
            if self.hfont:
                gdi32.DeleteObject(self.hfont)
            if self._gdipfont:
                gdiplus.GdipDeleteFont(self._gdipfont)
        except Exception:  # noqa: S110, BLE001
            pass

    @classmethod
    def add_font_data(cls: type[GDIPlusFont], data: bytes, manager: FontManager) -> None:
        numfonts = ctypes.c_uint32()
        _handle = gdi32.AddFontMemResourceEx(data, len(data), 0, ctypes.byref(numfonts))

        # None means a null handle was returned, ie something went wrong
        if _handle is None:
            raise ctypes.WinError()

        if not cls._private_collection:
            _loaded_families = set()
            cls._private_collection = ctypes.c_void_p()
            gdiplus.GdipNewPrivateFontCollection(ctypes.byref(cls._private_collection))
        else:
            _loaded_families = _get_font_family_names(cls._private_collection)

        gdiplus.GdipPrivateAddMemoryFont(cls._private_collection, data, len(data))

        current_families = _get_font_family_names(cls._private_collection)

        new_font = current_families - _loaded_families
        if len(new_font) > 0:
            font_name = list(new_font)[0]
            manager._add_loaded_font({(font_name, "normal", "normal", "normal")})

        # Loaded a variant?


    @classmethod
    def have_font(cls: type[GDIPlusFont], name: str) -> bool:
        # Enumerate the private collection fonts first, as those are most likely to be used.
        if cls._private_collection and _font_exists_in_collection(cls._private_collection, name):
            return True

        # Instead of enumerating all fonts on the system, as there can potentially be thousands, attempt to create
        # the font family with the name. If it does not error (0), then it exists in the system.
        family = ctypes.c_void_p()
        status = gdiplus.GdipCreateFontFamilyFromName(name, None, ctypes.byref(family))
        if status == 0:
            # Delete temp family to prevent leak.
            gdiplus.GdipDeleteFontFamily(family)
            return True

        return False
