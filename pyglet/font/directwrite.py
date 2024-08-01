from __future__ import annotations

import copy
import math
import os
import pathlib
import platform
from ctypes import (
    HRESULT,
    POINTER,
    Array,
    Structure,
    byref,
    c_int,
    c_int16,
    c_int32,
    c_ubyte,
    c_uint8,
    c_uint16,
    c_uint32,
    c_uint64,
    c_void_p,
    c_wchar,
    c_wchar_p,
    cast,
    create_unicode_buffer,
    pointer,
    sizeof,
    windll,
)
from ctypes.wintypes import BOOL, FLOAT, HDC, UINT, WCHAR
from typing import TYPE_CHECKING, BinaryIO, NoReturn

import pyglet
from pyglet.font import base
from pyglet.image import ImageData
from pyglet.image.codecs.wic import GUID_WICPixelFormat32bppPBGRA, IWICBitmap, WICDecoder
from pyglet.libs.win32 import LOGFONTW, c_void, com
from pyglet.libs.win32 import _kernel32 as kernel32
from pyglet.libs.win32.constants import (
    LOCALE_NAME_MAX_LENGTH,
    WINDOWS_8_1_OR_GREATER,
    WINDOWS_10_CREATORS_UPDATE_OR_GREATER,
)
from pyglet.util import debug_print

if TYPE_CHECKING:
    from pyglet.font.base import Glyph

try:
    dwrite = "dwrite"

    # System32 and SysWOW64 folders are opposite perception in Windows x64.
    # System32 = x64 dll's | SysWOW64 = x86 dlls
    # By default ctypes only seems to look in system32 regardless of Python architecture, which has x64 dlls.
    if platform.architecture()[0] == "32bit":
        if platform.machine().endswith("64"):  # Machine is 64 bit, Python is 32 bit.
            dwrite = os.path.join(os.environ["WINDIR"], "SysWOW64", "dwrite.dll")

    dwrite_lib = windll.LoadLibrary(dwrite)
except OSError:
    # Doesn't exist? Should stop import of library.
    msg = "DirectWrite Not Found"
    raise ImportError(msg)  # noqa: B904

_debug_font = pyglet.options["debug_font"]

_debug_print = debug_print("debug_font")


def DWRITE_MAKE_OPENTYPE_TAG(a: str, b: str, c: str, d: str) -> int:
    return ord(d) << 24 | ord(c) << 16 | ord(b) << 8 | ord(a)


DWRITE_FACTORY_TYPE = UINT
DWRITE_FACTORY_TYPE_SHARED = 0
DWRITE_FACTORY_TYPE_ISOLATED = 1

DWRITE_FONT_WEIGHT = UINT
DWRITE_FONT_WEIGHT_THIN = 100
DWRITE_FONT_WEIGHT_EXTRA_LIGHT = 200
DWRITE_FONT_WEIGHT_ULTRA_LIGHT = 200
DWRITE_FONT_WEIGHT_LIGHT = 300
DWRITE_FONT_WEIGHT_SEMI_LIGHT = 350
DWRITE_FONT_WEIGHT_NORMAL = 400
DWRITE_FONT_WEIGHT_REGULAR = 400
DWRITE_FONT_WEIGHT_MEDIUM = 500
DWRITE_FONT_WEIGHT_DEMI_BOLD = 600
DWRITE_FONT_WEIGHT_SEMI_BOLD = 600
DWRITE_FONT_WEIGHT_BOLD = 700
DWRITE_FONT_WEIGHT_EXTRA_BOLD = 800
DWRITE_FONT_WEIGHT_ULTRA_BOLD = 800
DWRITE_FONT_WEIGHT_BLACK = 900
DWRITE_FONT_WEIGHT_HEAVY = 900
DWRITE_FONT_WEIGHT_EXTRA_BLACK = 950

name_to_weight = {
    "thin": DWRITE_FONT_WEIGHT_THIN,
    "extralight": DWRITE_FONT_WEIGHT_EXTRA_LIGHT,
    "ultralight": DWRITE_FONT_WEIGHT_ULTRA_LIGHT,
    "light": DWRITE_FONT_WEIGHT_LIGHT,
    "semilight": DWRITE_FONT_WEIGHT_SEMI_LIGHT,
    "normal": DWRITE_FONT_WEIGHT_NORMAL,
    "regular": DWRITE_FONT_WEIGHT_REGULAR,
    "medium": DWRITE_FONT_WEIGHT_MEDIUM,
    "demibold": DWRITE_FONT_WEIGHT_DEMI_BOLD,
    "semibold": DWRITE_FONT_WEIGHT_SEMI_BOLD,
    "bold": DWRITE_FONT_WEIGHT_BOLD,
    "extrabold": DWRITE_FONT_WEIGHT_EXTRA_BOLD,
    "ultrabold": DWRITE_FONT_WEIGHT_ULTRA_BOLD,
    "black": DWRITE_FONT_WEIGHT_BLACK,
    "heavy": DWRITE_FONT_WEIGHT_HEAVY,
    "extrablack": DWRITE_FONT_WEIGHT_EXTRA_BLACK,
}

DWRITE_FONT_STRETCH = UINT
DWRITE_FONT_STRETCH_UNDEFINED = 0
DWRITE_FONT_STRETCH_ULTRA_CONDENSED = 1
DWRITE_FONT_STRETCH_EXTRA_CONDENSED = 2
DWRITE_FONT_STRETCH_CONDENSED = 3
DWRITE_FONT_STRETCH_SEMI_CONDENSED = 4
DWRITE_FONT_STRETCH_NORMAL = 5
DWRITE_FONT_STRETCH_MEDIUM = 5
DWRITE_FONT_STRETCH_SEMI_EXPANDED = 6
DWRITE_FONT_STRETCH_EXPANDED = 7
DWRITE_FONT_STRETCH_EXTRA_EXPANDED = 8

name_to_stretch = {
    "undefined": DWRITE_FONT_STRETCH_UNDEFINED,
    "ultracondensed": DWRITE_FONT_STRETCH_ULTRA_CONDENSED,
    "extracondensed": DWRITE_FONT_STRETCH_EXTRA_CONDENSED,
    "condensed": DWRITE_FONT_STRETCH_CONDENSED,
    "semicondensed": DWRITE_FONT_STRETCH_SEMI_CONDENSED,
    "normal": DWRITE_FONT_STRETCH_NORMAL,
    "medium": DWRITE_FONT_STRETCH_MEDIUM,
    "semiexpanded": DWRITE_FONT_STRETCH_SEMI_EXPANDED,
    "expanded": DWRITE_FONT_STRETCH_EXPANDED,
    "extraexpanded": DWRITE_FONT_STRETCH_EXTRA_EXPANDED,
    "narrow": DWRITE_FONT_STRETCH_CONDENSED,
}

DWRITE_GLYPH_IMAGE_FORMATS = c_int

DWRITE_GLYPH_IMAGE_FORMATS_NONE = 0x00000000
DWRITE_GLYPH_IMAGE_FORMATS_TRUETYPE = 0x00000001
DWRITE_GLYPH_IMAGE_FORMATS_CFF = 0x00000002
DWRITE_GLYPH_IMAGE_FORMATS_COLR = 0x00000004
DWRITE_GLYPH_IMAGE_FORMATS_SVG = 0x00000008
DWRITE_GLYPH_IMAGE_FORMATS_PNG = 0x00000010
DWRITE_GLYPH_IMAGE_FORMATS_JPEG = 0x00000020
DWRITE_GLYPH_IMAGE_FORMATS_TIFF = 0x00000040
DWRITE_GLYPH_IMAGE_FORMATS_PREMULTIPLIED_B8G8R8A8 = 0x00000080

DWRITE_MEASURING_MODE = UINT
DWRITE_MEASURING_MODE_NATURAL = 0
DWRITE_MEASURING_MODE_GDI_CLASSIC = 1
DWRITE_MEASURING_MODE_GDI_NATURAL = 2

DWRITE_GLYPH_IMAGE_FORMATS_ALL = DWRITE_GLYPH_IMAGE_FORMATS_TRUETYPE | \
                                 DWRITE_GLYPH_IMAGE_FORMATS_CFF | \
                                 DWRITE_GLYPH_IMAGE_FORMATS_COLR | \
                                 DWRITE_GLYPH_IMAGE_FORMATS_SVG | \
                                 DWRITE_GLYPH_IMAGE_FORMATS_PNG | \
                                 DWRITE_GLYPH_IMAGE_FORMATS_JPEG | \
                                 DWRITE_GLYPH_IMAGE_FORMATS_TIFF | \
                                 DWRITE_GLYPH_IMAGE_FORMATS_PREMULTIPLIED_B8G8R8A8

DWRITE_FONT_STYLE = UINT
DWRITE_FONT_STYLE_NORMAL = 0
DWRITE_FONT_STYLE_OBLIQUE = 1
DWRITE_FONT_STYLE_ITALIC = 2

name_to_style = {
    "normal": DWRITE_FONT_STYLE_NORMAL,
    "oblique": DWRITE_FONT_STYLE_OBLIQUE,
    "italic": DWRITE_FONT_STYLE_ITALIC,
}

UINT8 = c_uint8
UINT16 = c_uint16
INT16 = c_int16
INT32 = c_int32
UINT32 = c_uint32
UINT64 = c_uint64

DWRITE_INFORMATIONAL_STRING_ID = UINT32

DWRITE_INFORMATIONAL_STRING_NONE = 0
DWRITE_INFORMATIONAL_STRING_COPYRIGHT_NOTICE = 1
DWRITE_INFORMATIONAL_STRING_VERSION_STRINGS = 2
DWRITE_INFORMATIONAL_STRING_TRADEMARK = 3
DWRITE_INFORMATIONAL_STRING_MANUFACTURER = 4
DWRITE_INFORMATIONAL_STRING_DESIGNER = 5
DWRITE_INFORMATIONAL_STRING_DESIGNER_URL = 6
DWRITE_INFORMATIONAL_STRING_DESCRIPTION = 7
DWRITE_INFORMATIONAL_STRING_FONT_VENDOR_URL = 8
DWRITE_INFORMATIONAL_STRING_LICENSE_DESCRIPTION = 9
DWRITE_INFORMATIONAL_STRING_LICENSE_INFO_URL = 10
DWRITE_INFORMATIONAL_STRING_WIN32_FAMILY_NAMES = 11
DWRITE_INFORMATIONAL_STRING_WIN32_SUBFAMILY_NAMES = 12
DWRITE_INFORMATIONAL_STRING_TYPOGRAPHIC_FAMILY_NAMES = 13
DWRITE_INFORMATIONAL_STRING_TYPOGRAPHIC_SUBFAMILY_NAMES = 14
DWRITE_INFORMATIONAL_STRING_SAMPLE_TEXT = 15
DWRITE_INFORMATIONAL_STRING_FULL_NAME = 16
DWRITE_INFORMATIONAL_STRING_POSTSCRIPT_NAME = 17
DWRITE_INFORMATIONAL_STRING_POSTSCRIPT_CID_NAME = 18
DWRITE_INFORMATIONAL_STRING_WEIGHT_STRETCH_STYLE_FAMILY_NAME = 19
DWRITE_INFORMATIONAL_STRING_DESIGN_SCRIPT_LANGUAGE_TAG = 20
DWRITE_INFORMATIONAL_STRING_SUPPORTED_SCRIPT_LANGUAGE_TAG = 21
DWRITE_INFORMATIONAL_STRING_PREFERRED_FAMILY_NAMES = 22
DWRITE_INFORMATIONAL_STRING_PREFERRED_SUBFAMILY_NAMES = 23
DWRITE_INFORMATIONAL_STRING_WWS_FAMILY_NAME = 24


class D2D_POINT_2F(Structure):
    _fields_ = (
        ("x", FLOAT),
        ("y", FLOAT),
    )


class D2D1_RECT_F(Structure):
    _fields_ = (
        ("left", FLOAT),
        ("top", FLOAT),
        ("right", FLOAT),
        ("bottom", FLOAT),
    )


class D2D1_COLOR_F(Structure):
    _fields_ = (
        ("r", FLOAT),
        ("g", FLOAT),
        ("b", FLOAT),
        ("a", FLOAT),
    )


class DWRITE_TEXT_METRICS(Structure):
    _fields_ = (
        ("left", FLOAT),
        ("top", FLOAT),
        ("width", FLOAT),
        ("widthIncludingTrailingWhitespace", FLOAT),
        ("height", FLOAT),
        ("layoutWidth", FLOAT),
        ("layoutHeight", FLOAT),
        ("maxBidiReorderingDepth", UINT32),
        ("lineCount", UINT32),
    )


class DWRITE_FONT_METRICS(Structure):
    _fields_ = (
        ("designUnitsPerEm", UINT16),
        ("ascent", UINT16),
        ("descent", UINT16),
        ("lineGap", INT16),
        ("capHeight", UINT16),
        ("xHeight", UINT16),
        ("underlinePosition", INT16),
        ("underlineThickness", UINT16),
        ("strikethroughPosition", INT16),
        ("strikethroughThickness", UINT16),
    )


class DWRITE_GLYPH_METRICS(Structure):
    _fields_ = (
        ("leftSideBearing", INT32),
        ("advanceWidth", UINT32),
        ("rightSideBearing", INT32),
        ("topSideBearing", INT32),
        ("advanceHeight", UINT32),
        ("bottomSideBearing", INT32),
        ("verticalOriginY", INT32),
    )


class DWRITE_GLYPH_OFFSET(Structure):
    _fields_ = (
        ("advanceOffset", FLOAT),
        ("ascenderOffset", FLOAT),
    )

    def __repr__(self) -> str:
        return f"DWRITE_GLYPH_OFFSET({self.advanceOffset}, {self.ascenderOffset})"


class DWRITE_CLUSTER_METRICS(Structure):
    _fields_ = (
        ("width", FLOAT),
        ("length", UINT16),
        ("canWrapLineAfter", UINT16, 1),
        ("isWhitespace", UINT16, 1),
        ("isNewline", UINT16, 1),
        ("isSoftHyphen", UINT16, 1),
        ("isRightToLeft", UINT16, 1),
        ("padding", UINT16, 11),
    )


class IDWriteFontFileStream(com.IUnknown):
    _methods_ = [
        ("ReadFileFragment",
         com.STDMETHOD(POINTER(c_void_p), UINT64, UINT64, POINTER(c_void_p))),
        ("ReleaseFileFragment",
         com.STDMETHOD(c_void_p)),
        ("GetFileSize",
         com.STDMETHOD(POINTER(UINT64))),
        ("GetLastWriteTime",
         com.STDMETHOD(POINTER(UINT64))),
    ]


class IDWriteFontFileLoader_LI(com.IUnknown):  # Local implementation use only.
    _methods_ = [
        ("CreateStreamFromKey",
         com.STDMETHOD(c_void_p, UINT32, POINTER(POINTER(IDWriteFontFileStream)))),
    ]


class IDWriteFontFileLoader(com.pIUnknown):
    _methods_ = [
        ("CreateStreamFromKey",
         com.STDMETHOD(c_void_p, UINT32, POINTER(POINTER(IDWriteFontFileStream)))),
    ]


class IDWriteLocalFontFileLoader(IDWriteFontFileLoader, com.pIUnknown):
    _methods_ = [
        ("GetFilePathLengthFromKey",
         com.STDMETHOD(c_void_p, UINT32, POINTER(UINT32))),
        ("GetFilePathFromKey",
         com.STDMETHOD(c_void_p, UINT32, c_wchar_p, UINT32)),
        ("GetLastWriteTimeFromKey",
         com.STDMETHOD()),
    ]


IID_IDWriteLocalFontFileLoader = com.GUID(0xb2d9f3ec, 0xc9fe, 0x4a11, 0xa2, 0xec, 0xd8, 0x62, 0x08, 0xf7, 0xc0, 0xa2)


class IDWriteFontFile(com.pIUnknown):
    _methods_ = [
        ("GetReferenceKey",
         com.STDMETHOD(POINTER(c_void_p), POINTER(UINT32))),
        ("GetLoader",
         com.STDMETHOD(POINTER(IDWriteFontFileLoader))),
        ("Analyze",
         com.STDMETHOD()),
    ]


class IDWriteFontFace(com.pIUnknown):
    _methods_ = [
        ("GetType",
         com.STDMETHOD()),
        ("GetFiles",
         com.STDMETHOD(POINTER(UINT32), POINTER(IDWriteFontFile))),
        ("GetIndex",
         com.STDMETHOD()),
        ("GetSimulations",
         com.STDMETHOD()),
        ("IsSymbolFont",
         com.STDMETHOD()),
        ("GetMetrics",
         com.METHOD(c_void, POINTER(DWRITE_FONT_METRICS))),
        ("GetGlyphCount",
         com.METHOD(UINT16)),
        ("GetDesignGlyphMetrics",
         com.STDMETHOD(POINTER(UINT16), UINT32, POINTER(DWRITE_GLYPH_METRICS), BOOL)),
        ("GetGlyphIndices",
         com.STDMETHOD(POINTER(UINT32), UINT32, POINTER(UINT16))),
        ("TryGetFontTable",
         com.STDMETHOD(UINT32, c_void_p, POINTER(UINT32), c_void_p, POINTER(BOOL))),
        ("ReleaseFontTable",
         com.METHOD(c_void)),
        ("GetGlyphRunOutline",
         com.STDMETHOD()),
        ("GetRecommendedRenderingMode",
         com.STDMETHOD()),
        ("GetGdiCompatibleMetrics",
         com.STDMETHOD()),
        ("GetGdiCompatibleGlyphMetrics",
         com.STDMETHOD()),
    ]


IID_IDWriteFontFace1 = com.GUID(0xa71efdb4, 0x9fdb, 0x4838, 0xad, 0x90, 0xcf, 0xc3, 0xbe, 0x8c, 0x3d, 0xaf)


class IDWriteFontFace1(IDWriteFontFace, com.pIUnknown):
    _methods_ = [
        ("GetMetric1",
         com.STDMETHOD()),
        ("GetGdiCompatibleMetrics1",
         com.STDMETHOD()),
        ("GetCaretMetrics",
         com.STDMETHOD()),
        ("GetUnicodeRanges",
         com.STDMETHOD()),
        ("IsMonospacedFont",
         com.STDMETHOD()),
        ("GetDesignGlyphAdvances",
         com.METHOD(c_void, POINTER(DWRITE_FONT_METRICS))),
        ("GetGdiCompatibleGlyphAdvances",
         com.STDMETHOD()),
        ("GetKerningPairAdjustments",
         com.STDMETHOD(UINT32, POINTER(UINT16), POINTER(INT32))),
        ("HasKerningPairs",
         com.METHOD(BOOL)),
        ("GetRecommendedRenderingMode1",
         com.STDMETHOD()),
        ("GetVerticalGlyphVariants",
         com.STDMETHOD()),
        ("HasVerticalGlyphVariants",
         com.STDMETHOD()),
    ]


class DWRITE_GLYPH_RUN(Structure):
    _fields_ = (
        ("fontFace", IDWriteFontFace),
        ("fontEmSize", FLOAT),
        ("glyphCount", UINT32),
        ("glyphIndices", POINTER(UINT16)),
        ("glyphAdvances", POINTER(FLOAT)),
        ("glyphOffsets", POINTER(DWRITE_GLYPH_OFFSET)),
        ("isSideways", BOOL),
        ("bidiLevel", UINT32),
    )


DWRITE_SCRIPT_SHAPES = UINT
DWRITE_SCRIPT_SHAPES_DEFAULT = 0


class DWRITE_SCRIPT_ANALYSIS(Structure):
    _fields_ = (
        ("script", UINT16),
        ("shapes", DWRITE_SCRIPT_SHAPES),
    )


DWRITE_FONT_FEATURE_TAG = UINT


class DWRITE_FONT_FEATURE(Structure):
    _fields_ = (
        ("nameTag", DWRITE_FONT_FEATURE_TAG),
        ("parameter", UINT32),
    )


class DWRITE_TYPOGRAPHIC_FEATURES(Structure):
    _fields_ = (
        ("features", POINTER(DWRITE_FONT_FEATURE)),
        ("featureCount", UINT32),
    )


class DWRITE_SHAPING_TEXT_PROPERTIES(Structure):
    _fields_ = (
        ("isShapedAlone", UINT16, 1),
        ("reserved1", UINT16, 1),
        ("canBreakShapingAfter", UINT16, 1),
        ("reserved", UINT16, 13),
    )

    def __repr__(self) -> str:
        return f"DWRITE_SHAPING_TEXT_PROPERTIES({self.isShapedAlone}, {self.reserved1}, {self.canBreakShapingAfter})"


class DWRITE_SHAPING_GLYPH_PROPERTIES(Structure):
    _fields_ = (
        ("justification", UINT16, 4),
        ("isClusterStart", UINT16, 1),
        ("isDiacritic", UINT16, 1),
        ("isZeroWidthSpace", UINT16, 1),
        ("reserved", UINT16, 9),
    )


DWRITE_READING_DIRECTION = UINT
DWRITE_READING_DIRECTION_LEFT_TO_RIGHT = 0


class IDWriteTextAnalysisSource(com.IUnknown):
    _methods_ = [
        ("GetTextAtPosition",
         com.STDMETHOD(UINT32, POINTER(c_wchar_p), POINTER(UINT32))),
        ("GetTextBeforePosition",
         com.STDMETHOD(UINT32, POINTER(c_wchar_p), POINTER(UINT32))),
        ("GetParagraphReadingDirection",
         com.METHOD(DWRITE_READING_DIRECTION)),
        ("GetLocaleName",
         com.STDMETHOD(UINT32, POINTER(UINT32), POINTER(c_wchar_p))),
        ("GetNumberSubstitution",
         com.STDMETHOD(UINT32, POINTER(UINT32), c_void_p)),
    ]


class IDWriteTextAnalysisSink(com.IUnknown):
    _methods_ = [
        ("SetScriptAnalysis",
         com.STDMETHOD(UINT32, UINT32, POINTER(DWRITE_SCRIPT_ANALYSIS))),
        ("SetLineBreakpoints",
         com.STDMETHOD(UINT32, UINT32, c_void_p)),
        ("SetBidiLevel",
         com.STDMETHOD(UINT32, UINT32, UINT8, UINT8)),
        ("SetNumberSubstitution",
         com.STDMETHOD(UINT32, UINT32, c_void_p)),
    ]


class Run:
    def __init__(self) -> None:
        self.text_start = 0
        self.text_length = 0
        self.glyph_start = 0
        self.glyph_count = 0
        self.script = DWRITE_SCRIPT_ANALYSIS()
        self.bidi = 0
        self.isNumberSubstituted = False
        self.isSideways = False

        self.next_run = None

    def ContainsTextPosition(self, textPosition: int) -> bool:
        return textPosition >= self.text_start and textPosition < self.text_start + self.text_length


class TextAnalysis(com.COMObject):
    _interfaces_ = [IDWriteTextAnalysisSource, IDWriteTextAnalysisSink]

    def __init__(self) -> None:
        super().__init__()
        self._textstart = 0
        self._textlength = 0
        self._glyphstart = 0
        self._glyphcount = 0
        self._ptrs = []

        self._script = None
        self._bidi = 0
        # self._sideways = False  # noqa: ERA001

    def GenerateResults(self, analyzer: IDWriteTextAnalyzer, text: c_wchar_p, text_length: int):
        self._text = text
        self._textstart = 0
        self._textlength = text_length
        self._glyphstart = 0
        self._glyphcount = 0
        self._ptrs.clear()

        self._start_run = Run()
        self._start_run.text_length = text_length

        self._current_run = self._start_run

        analyzer.AnalyzeScript(self, 0, text_length, self)

    def SetScriptAnalysis(self, textPosition: UINT32, textLength: UINT32,
                          scriptAnalysis: POINTER(DWRITE_SCRIPT_ANALYSIS)) -> int:
        # textPosition - The index of the first character in the string that the result applies to
        # textLength - How many characters of the string from the index that the result applies to
        # scriptAnalysis - The analysis information for all glyphs starting at position for length.
        self.SetCurrentRun(textPosition)
        self.SplitCurrentRun(textPosition)

        while textLength > 0:
            run, textLength = self.FetchNextRun(textLength)

            run.script.script = scriptAnalysis[0].script
            run.script.shapes = scriptAnalysis[0].shapes

            self._script = run.script

        return 0
        # return 0x80004001

    def GetTextBeforePosition(self, textPosition: UINT32, textString: POINTER(POINTER(WCHAR)),
                              textLength: POINTER(UINT32)) -> NoReturn:
        msg = "Currently not implemented."
        raise Exception(msg)

    def GetTextAtPosition(self, textPosition: UINT32, textString: c_wchar_p, textLength: POINTER(UINT32)) -> int:
        # This method will retrieve a substring of the text in this layout
        #   to be used in an analysis step.
        # Arguments:
        # textPosition - The index of the first character of the text to retrieve.
        # textString - The pointer to the first character of text at the index requested.
        # textLength - The characters available at/after the textString pointer (string length).

        if textPosition >= self._textlength:
            self._no_ptr = c_wchar_p(None)
            textString[0] = self._no_ptr
            textLength[0] = 0
        else:
            ptr = c_wchar_p(self._text[textPosition:])
            self._ptrs.append(ptr)
            textString[0] = ptr
            textLength[0] = self._textlength - textPosition

        return 0

    def GetParagraphReadingDirection(self) -> int:
        return 0

    def GetLocaleName(self, textPosition: UINT32, textLength: POINTER(UINT32),
                      localeName: POINTER(POINTER(WCHAR))) -> int:
        self.__local_name = c_wchar_p("")  # TODO: Add more locales.
        localeName[0] = self.__local_name
        textLength[0] = self._textlength - textPosition
        return 0

    def GetNumberSubstitution(self) -> int:
        return 0

    def SetCurrentRun(self, textPosition: UINT32) -> None:
        if self._current_run and self._current_run.ContainsTextPosition(textPosition):
            return

    def SplitCurrentRun(self, textPosition: UINT32) -> None:
        if not self._current_run:
            return

        if textPosition <= self._current_run.text_start:
            # Already first start of the run.
            return

        new_run = copy.copy(self._current_run)

        new_run.next_run = self._current_run.next_run
        self._current_run.next_run = new_run

        splitPoint = textPosition - self._current_run.text_start
        new_run.text_start += splitPoint
        new_run.text_length -= splitPoint

        self._current_run.text_length = splitPoint
        self._current_run = new_run

    def FetchNextRun(self, textLength: UINT32) -> tuple[Run, int]:
        original_run = self._current_run

        if (textLength < self._current_run.text_length):
            self.SplitCurrentRun(self._current_run.text_start + textLength)
        else:
            self._current_run = self._current_run.next_run

        textLength -= original_run.text_length

        return original_run, textLength


class IDWriteTextAnalyzer(com.pIUnknown):
    _methods_ = [
        ("AnalyzeScript",
         com.STDMETHOD(POINTER(IDWriteTextAnalysisSource), UINT32, UINT32, POINTER(IDWriteTextAnalysisSink))),
        ("AnalyzeBidi",
         com.STDMETHOD()),
        ("AnalyzeNumberSubstitution",
         com.STDMETHOD()),
        ("AnalyzeLineBreakpoints",
         com.STDMETHOD()),
        ("GetGlyphs",
         com.STDMETHOD(c_wchar_p, UINT32, IDWriteFontFace, BOOL, BOOL, POINTER(DWRITE_SCRIPT_ANALYSIS),
                       c_wchar_p, c_void_p, POINTER(POINTER(DWRITE_TYPOGRAPHIC_FEATURES)), POINTER(UINT32),
                       UINT32, UINT32, POINTER(UINT16), POINTER(DWRITE_SHAPING_TEXT_PROPERTIES),
                       POINTER(UINT16), POINTER(DWRITE_SHAPING_GLYPH_PROPERTIES), POINTER(UINT32))),
        ("GetGlyphPlacements",
         com.STDMETHOD(c_wchar_p, POINTER(UINT16), POINTER(DWRITE_SHAPING_TEXT_PROPERTIES), UINT32, POINTER(UINT16),
                       POINTER(DWRITE_SHAPING_GLYPH_PROPERTIES), UINT32, IDWriteFontFace, FLOAT, BOOL, BOOL,
                       POINTER(DWRITE_SCRIPT_ANALYSIS), c_wchar_p, POINTER(DWRITE_TYPOGRAPHIC_FEATURES),
                       POINTER(UINT32), UINT32, POINTER(FLOAT), POINTER(DWRITE_GLYPH_OFFSET))),
        ("GetGdiCompatibleGlyphPlacements",
         com.STDMETHOD()),
    ]


class IDWriteLocalizedStrings(com.pIUnknown):
    _methods_ = [
        ("GetCount",
         com.METHOD(UINT32)),
        ("FindLocaleName",
         com.STDMETHOD(c_wchar_p, POINTER(UINT32), POINTER(BOOL))),
        ("GetLocaleNameLength",
         com.STDMETHOD(UINT32, POINTER(UINT32))),
        ("GetLocaleName",
         com.STDMETHOD(UINT32, c_wchar_p, UINT32)),
        ("GetStringLength",
         com.STDMETHOD(UINT32, POINTER(UINT32))),
        ("GetString",
         com.STDMETHOD(UINT32, c_wchar_p, UINT32)),
    ]


class IDWriteFontList(com.pIUnknown):
    _methods_ = [
        ("GetFontCollection",
         com.STDMETHOD()),
        ("GetFontCount",
         com.METHOD(UINT32)),
        ("GetFont",
         com.STDMETHOD(UINT32, c_void_p)),  # IDWriteFont, use void because of forward ref.
    ]


class IDWriteFontFamily(IDWriteFontList, com.pIUnknown):
    _methods_ = [
        ("GetFamilyNames",
         com.STDMETHOD(POINTER(IDWriteLocalizedStrings))),
        ("GetFirstMatchingFont",
         com.STDMETHOD(DWRITE_FONT_WEIGHT, DWRITE_FONT_STRETCH, DWRITE_FONT_STYLE, c_void_p)),
        ("GetMatchingFonts",
         com.STDMETHOD()),
    ]


class IDWriteFontFamily1(IDWriteFontFamily, IDWriteFontList, com.pIUnknown):
    _methods_ = [
        ("GetFontLocality",
         com.STDMETHOD()),
        ("GetFont1",
         com.STDMETHOD()),
        ("GetFontFaceReference",
         com.STDMETHOD()),
    ]


class IDWriteFont(com.pIUnknown):
    _methods_ = [
        ("GetFontFamily",
         com.STDMETHOD(POINTER(IDWriteFontFamily))),
        ("GetWeight",
         com.METHOD(DWRITE_FONT_WEIGHT)),
        ("GetStretch",
         com.METHOD(DWRITE_FONT_STRETCH)),
        ("GetStyle",
         com.METHOD(DWRITE_FONT_STYLE)),
        ("IsSymbolFont",
         com.METHOD(BOOL)),
        ("GetFaceNames",
         com.STDMETHOD(POINTER(IDWriteLocalizedStrings))),
        ("GetInformationalStrings",
         com.STDMETHOD(DWRITE_INFORMATIONAL_STRING_ID, POINTER(IDWriteLocalizedStrings), POINTER(BOOL))),
        ("GetSimulations",
         com.STDMETHOD()),
        ("GetMetrics",
         com.STDMETHOD()),
        ("HasCharacter",
         com.STDMETHOD(UINT32, POINTER(BOOL))),
        ("CreateFontFace",
         com.STDMETHOD(POINTER(IDWriteFontFace))),
    ]


class IDWriteFont1(IDWriteFont, com.pIUnknown):
    _methods_ = [
        ("GetMetrics1",
         com.STDMETHOD()),
        ("GetPanose",
         com.STDMETHOD()),
        ("GetUnicodeRanges",
         com.STDMETHOD()),
        ("IsMonospacedFont",
         com.STDMETHOD()),
    ]


class IDWriteFontCollection(com.pIUnknown):
    _methods_ = [
        ("GetFontFamilyCount",
         com.METHOD(UINT32)),
        ("GetFontFamily",
         com.STDMETHOD(UINT32, POINTER(IDWriteFontFamily))),
        ("FindFamilyName",
         com.STDMETHOD(c_wchar_p, POINTER(UINT), POINTER(BOOL))),
        ("GetFontFromFontFace",
         com.STDMETHOD()),
    ]


class IDWriteFontCollection1(IDWriteFontCollection, com.pIUnknown):
    _methods_ = [
        ("GetFontSet",
         com.STDMETHOD()),
        ("GetFontFamily1",
         com.STDMETHOD(POINTER(IDWriteFontFamily1))),
    ]


DWRITE_TEXT_ALIGNMENT = UINT
DWRITE_TEXT_ALIGNMENT_LEADING = 1
DWRITE_TEXT_ALIGNMENT_TRAILING = 2
DWRITE_TEXT_ALIGNMENT_CENTER = 3
DWRITE_TEXT_ALIGNMENT_JUSTIFIED = 4


class IDWriteGdiInterop(com.pIUnknown):
    _methods_ = [
        ("CreateFontFromLOGFONT",
         com.STDMETHOD(POINTER(LOGFONTW), POINTER(IDWriteFont))),
        ("ConvertFontToLOGFONT",
         com.STDMETHOD()),
        ("ConvertFontFaceToLOGFONT",
         com.STDMETHOD()),
        ("CreateFontFaceFromHdc",
         com.STDMETHOD(HDC, POINTER(IDWriteFontFace))),
        ("CreateBitmapRenderTarget",
         com.STDMETHOD()),
    ]


class IDWriteTextFormat(com.pIUnknown):
    _methods_ = [
        ("SetTextAlignment",
         com.STDMETHOD(DWRITE_TEXT_ALIGNMENT)),
        ("SetParagraphAlignment",
         com.STDMETHOD()),
        ("SetWordWrapping",
         com.STDMETHOD()),
        ("SetReadingDirection",
         com.STDMETHOD()),
        ("SetFlowDirection",
         com.STDMETHOD()),
        ("SetIncrementalTabStop",
         com.STDMETHOD()),
        ("SetTrimming",
         com.STDMETHOD()),
        ("SetLineSpacing",
         com.STDMETHOD()),
        ("GetTextAlignment",
         com.STDMETHOD()),
        ("GetParagraphAlignment",
         com.STDMETHOD()),
        ("GetWordWrapping",
         com.STDMETHOD()),
        ("GetReadingDirection",
         com.STDMETHOD()),
        ("GetFlowDirection",
         com.STDMETHOD()),
        ("GetIncrementalTabStop",
         com.STDMETHOD()),
        ("GetTrimming",
         com.STDMETHOD()),
        ("GetLineSpacing",
         com.STDMETHOD()),
        ("GetFontCollection",
         com.STDMETHOD()),
        ("GetFontFamilyNameLength",
         com.STDMETHOD(UINT32, POINTER(UINT32))),
        ("GetFontFamilyName",
         com.STDMETHOD(UINT32, c_wchar_p, UINT32)),
        ("GetFontWeight",
         com.STDMETHOD()),
        ("GetFontStyle",
         com.STDMETHOD()),
        ("GetFontStretch",
         com.STDMETHOD()),
        ("GetFontSize",
         com.STDMETHOD()),
        ("GetLocaleNameLength",
         com.STDMETHOD()),
        ("GetLocaleName",
         com.STDMETHOD()),
    ]


class IDWriteTypography(com.pIUnknown):
    _methods_ = [
        ("AddFontFeature",
         com.STDMETHOD(DWRITE_FONT_FEATURE)),
        ("GetFontFeatureCount",
         com.METHOD(UINT32)),
        ("GetFontFeature",
         com.STDMETHOD()),
    ]


class DWRITE_TEXT_RANGE(Structure):
    _fields_ = (
        ("startPosition", UINT32),
        ("length", UINT32),
    )


class DWRITE_OVERHANG_METRICS(Structure):
    _fields_ = (
        ("left", FLOAT),
        ("top", FLOAT),
        ("right", FLOAT),
        ("bottom", FLOAT),
    )


class IDWriteTextLayout(IDWriteTextFormat, com.pIUnknown):
    _methods_ = [
        ("SetMaxWidth",
         com.STDMETHOD()),
        ("SetMaxHeight",
         com.STDMETHOD()),
        ("SetFontCollection",
         com.STDMETHOD()),
        ("SetFontFamilyName",
         com.STDMETHOD()),
        ("SetFontWeight",  # 30
         com.STDMETHOD()),
        ("SetFontStyle",
         com.STDMETHOD()),
        ("SetFontStretch",
         com.STDMETHOD()),
        ("SetFontSize",
         com.STDMETHOD()),
        ("SetUnderline",
         com.STDMETHOD()),
        ("SetStrikethrough",
         com.STDMETHOD()),
        ("SetDrawingEffect",
         com.STDMETHOD()),
        ("SetInlineObject",
         com.STDMETHOD()),
        ("SetTypography",
         com.STDMETHOD(IDWriteTypography, DWRITE_TEXT_RANGE)),
        ("SetLocaleName",
         com.STDMETHOD()),
        ("GetMaxWidth",  # 40
         com.METHOD(FLOAT)),
        ("GetMaxHeight",
         com.METHOD(FLOAT)),
        ("GetFontCollection2",
         com.STDMETHOD()),
        ("GetFontFamilyNameLength2",
         com.STDMETHOD(UINT32, POINTER(UINT32), c_void_p)),
        ("GetFontFamilyName2",
         com.STDMETHOD(UINT32, c_wchar_p, UINT32, c_void_p)),
        ("GetFontWeight2",
         com.STDMETHOD(UINT32, POINTER(DWRITE_FONT_WEIGHT), POINTER(DWRITE_TEXT_RANGE))),
        ("GetFontStyle2",
         com.STDMETHOD()),
        ("GetFontStretch2",
         com.STDMETHOD()),
        ("GetFontSize2",
         com.STDMETHOD()),
        ("GetUnderline",
         com.STDMETHOD()),
        ("GetStrikethrough",
         com.STDMETHOD(UINT32, POINTER(BOOL), POINTER(DWRITE_TEXT_RANGE))),
        ("GetDrawingEffect",
         com.STDMETHOD()),
        ("GetInlineObject",
         com.STDMETHOD()),
        ("GetTypography",  # Always returns NULL without SetTypography being called.
         com.STDMETHOD(UINT32, POINTER(IDWriteTypography), POINTER(DWRITE_TEXT_RANGE))),
        ("GetLocaleNameLength1",
         com.STDMETHOD()),
        ("GetLocaleName1",
         com.STDMETHOD()),
        ("Draw",
         com.STDMETHOD()),
        ("GetLineMetrics",
         com.STDMETHOD()),
        ("GetMetrics",
         com.STDMETHOD(POINTER(DWRITE_TEXT_METRICS))),
        ("GetOverhangMetrics",
         com.STDMETHOD(POINTER(DWRITE_OVERHANG_METRICS))),
        ("GetClusterMetrics",
         com.STDMETHOD(POINTER(DWRITE_CLUSTER_METRICS), UINT32, POINTER(UINT32))),
        ("DetermineMinWidth",
         com.STDMETHOD(POINTER(FLOAT))),
        ("HitTestPoint",
         com.STDMETHOD()),
        ("HitTestTextPosition",
         com.STDMETHOD()),
        ("HitTestTextRange",
         com.STDMETHOD()),
    ]


class IDWriteTextLayout1(IDWriteTextLayout, IDWriteTextFormat, com.pIUnknown):
    _methods_ = [
        ("SetPairKerning",
         com.STDMETHOD()),
        ("GetPairKerning",
         com.STDMETHOD()),
        ("SetCharacterSpacing",
         com.STDMETHOD()),
        ("GetCharacterSpacing",
         com.STDMETHOD(UINT32, POINTER(FLOAT), POINTER(FLOAT), POINTER(FLOAT), POINTER(DWRITE_TEXT_RANGE))),
    ]


class IDWriteFontFileEnumerator(com.IUnknown):
    _methods_ = [
        ("MoveNext",
         com.STDMETHOD(POINTER(BOOL))),
        ("GetCurrentFontFile",
         com.STDMETHOD(c_void_p)),
    ]


class IDWriteFontCollectionLoader(com.IUnknown):
    _methods_ = [
        ("CreateEnumeratorFromKey",
         com.STDMETHOD(c_void_p, c_void_p, UINT32, POINTER(POINTER(IDWriteFontFileEnumerator)))),
    ]


class MyFontFileStream(com.COMObject):
    _interfaces_ = [IDWriteFontFileStream]

    def __init__(self, data: bytes) -> None:
        super().__init__()
        self._data = data
        self._size = len(data)
        self._ptrs = []

    def ReadFileFragment(self, fragmentStart: POINTER(c_void_p), fileOffset: UINT64, fragmentSize: UINT64,
                         fragmentContext: POINTER(c_void_p)) -> int:
        if fileOffset + fragmentSize > self._size:
            return 0x80004005  # E_FAIL

        fragment = self._data[fileOffset:]
        buffer = (c_ubyte * len(fragment)).from_buffer(bytearray(fragment))
        ptr = cast(buffer, c_void_p)

        self._ptrs.append(ptr)
        fragmentStart[0] = ptr
        fragmentContext[0] = None
        return 0

    def ReleaseFileFragment(self, fragmentContext: c_void_p) -> int:
        return 0

    def GetFileSize(self, fileSize: POINTER(UINT64)) -> int:
        fileSize[0] = self._size
        return 0

    def GetLastWriteTime(self, lastWriteTime: POINTER(UINT64)) -> int:
        return 0x80004001  # E_NOTIMPL


class LegacyFontFileLoader(com.COMObject):
    _interfaces_ = [IDWriteFontFileLoader_LI]

    def __init__(self) -> None:
        super().__init__()
        self._streams = {}

    def CreateStreamFromKey(self, fontfileReferenceKey: c_void_p, fontFileReferenceKeySize: UINT32,
                            fontFileStream: POINTER(IDWriteFontFileStream)) -> int:
        convert_index = cast(fontfileReferenceKey, POINTER(c_uint32))

        self._ptr = cast(self._streams[convert_index.contents.value].as_interface(IDWriteFontFileStream),
                         POINTER(IDWriteFontFileStream))
        fontFileStream[0] = self._ptr
        return 0

    def SetCurrentFont(self, index: int, data: bytes) -> int:
        self._streams[index] = MyFontFileStream(data)


class MyEnumerator(com.COMObject):
    _interfaces_ = [IDWriteFontFileEnumerator]

    def __init__(self, factory: c_void_p, loader: LegacyFontFileLoader) -> None:
        super().__init__()
        self.factory = cast(factory, IDWriteFactory)
        self.key = "pyglet_dwrite"
        self.size = len(self.key)
        self.current_index = -1

        self._keys = []
        self._font_data = []
        self._font_files = []
        self._current_file = None

        self._font_key_ref = create_unicode_buffer("none")
        self._font_key_len = len(self._font_key_ref)

        self._file_loader = loader

    def AddFontData(self, fonts: list[str]) -> None:
        self._font_data = fonts

    def MoveNext(self, hasCurrentFile: BOOL) -> None:

        self.current_index += 1
        if self.current_index != len(self._font_data):
            font_file = IDWriteFontFile()

            self._file_loader.SetCurrentFont(self.current_index, self._font_data[self.current_index])

            key = self.current_index

            if self.current_index not in self._keys:
                buffer = pointer(c_uint32(key))

                ptr = cast(buffer, c_void_p)

                self._keys.append(ptr)

            self.factory.CreateCustomFontFileReference(self._keys[self.current_index],
                                                       sizeof(buffer),
                                                       self._file_loader,
                                                       byref(font_file))

            self._font_files.append(font_file)

            hasCurrentFile[0] = 1
        else:
            hasCurrentFile[0] = 0

    def GetCurrentFontFile(self, fontFile: IDWriteFontFile) -> int:
        fontFile = cast(fontFile, POINTER(IDWriteFontFile))
        fontFile[0] = self._font_files[self.current_index]
        return 0


class LegacyCollectionLoader(com.COMObject):
    _interfaces_ = [IDWriteFontCollectionLoader]

    def __init__(self, factory: c_void_p, loader: LegacyFontFileLoader) -> None:
        super().__init__()
        self._enumerator = MyEnumerator(factory, loader)

    def AddFontData(self, fonts) -> None:
        self._enumerator.AddFontData(fonts)

    def CreateEnumeratorFromKey(self, factory: IDWriteFactory, key: c_void_p, key_size: UINT32,
                                enumerator: MyEnumerator) -> int:
        self._ptr = cast(self._enumerator.as_interface(IDWriteFontFileEnumerator),
                         POINTER(IDWriteFontFileEnumerator))

        enumerator[0] = self._ptr
        return 0


IID_IDWriteFactory = com.GUID(0xb859ee5a, 0xd838, 0x4b5b, 0xa2, 0xe8, 0x1a, 0xdc, 0x7d, 0x93, 0xdb, 0x48)


class IDWriteRenderingParams(com.pIUnknown):
    _methods_ = [
        ("GetGamma",
         com.METHOD(FLOAT)),
        ("GetEnhancedContrast",
         com.METHOD(FLOAT)),
        ("GetClearTypeLevel",
         com.METHOD(FLOAT)),
        ("GetPixelGeometry",
         com.METHOD(UINT)),
        ("GetRenderingMode",
         com.METHOD(UINT)),
    ]


class IDWriteFactory(com.pIUnknown):
    _methods_ = [
        ("GetSystemFontCollection",
         com.STDMETHOD(POINTER(IDWriteFontCollection), BOOL)),
        ("CreateCustomFontCollection",
         com.STDMETHOD(POINTER(IDWriteFontCollectionLoader), c_void_p, UINT32, POINTER(IDWriteFontCollection))),
        ("RegisterFontCollectionLoader",
         com.STDMETHOD(POINTER(IDWriteFontCollectionLoader))),
        ("UnregisterFontCollectionLoader",
         com.STDMETHOD(POINTER(IDWriteFontCollectionLoader))),
        ("CreateFontFileReference",
         com.STDMETHOD(c_wchar_p, c_void_p, POINTER(IDWriteFontFile))),
        ("CreateCustomFontFileReference",
         com.STDMETHOD(c_void_p, UINT32, POINTER(IDWriteFontFileLoader_LI), POINTER(IDWriteFontFile))),
        ("CreateFontFace",
         com.STDMETHOD()),
        ("CreateRenderingParams",
         com.STDMETHOD(POINTER(IDWriteRenderingParams))),
        ("CreateMonitorRenderingParams",
         com.STDMETHOD()),
        ("CreateCustomRenderingParams",
         com.STDMETHOD(FLOAT, FLOAT, FLOAT, UINT, UINT, POINTER(IDWriteRenderingParams))),
        ("RegisterFontFileLoader",
         com.STDMETHOD(c_void_p)),  # Ambigious as newer is a pIUnknown and legacy is IUnknown.
        ("UnregisterFontFileLoader",
         com.STDMETHOD(POINTER(IDWriteFontFileLoader_LI))),
        ("CreateTextFormat",
         com.STDMETHOD(c_wchar_p, IDWriteFontCollection, DWRITE_FONT_WEIGHT, DWRITE_FONT_STYLE, DWRITE_FONT_STRETCH,
                       FLOAT, c_wchar_p, POINTER(IDWriteTextFormat))),
        ("CreateTypography",
         com.STDMETHOD(POINTER(IDWriteTypography))),
        ("GetGdiInterop",
         com.STDMETHOD(POINTER(IDWriteGdiInterop))),
        ("CreateTextLayout",
         com.STDMETHOD(c_wchar_p, UINT32, IDWriteTextFormat, FLOAT, FLOAT, POINTER(IDWriteTextLayout))),
        ("CreateGdiCompatibleTextLayout",
         com.STDMETHOD()),
        ("CreateEllipsisTrimmingSign",
         com.STDMETHOD()),
        ("CreateTextAnalyzer",
         com.STDMETHOD(POINTER(IDWriteTextAnalyzer))),
        ("CreateNumberSubstitution",
         com.STDMETHOD()),
        ("CreateGlyphRunAnalysis",
         com.STDMETHOD()),
    ]


IID_IDWriteFactory1 = com.GUID(0x30572f99, 0xdac6, 0x41db, 0xa1, 0x6e, 0x04, 0x86, 0x30, 0x7e, 0x60, 0x6a)


class IDWriteFactory1(IDWriteFactory, com.pIUnknown):
    _methods_ = [
        ("GetEudcFontCollection",
         com.STDMETHOD()),
        ("CreateCustomRenderingParams1",
         com.STDMETHOD()),
    ]


class IDWriteFontFallback(com.pIUnknown):
    _methods_ = [
        ("MapCharacters",
         com.STDMETHOD(POINTER(IDWriteTextAnalysisSource), UINT32, UINT32, IDWriteFontCollection, c_wchar_p,
                       DWRITE_FONT_WEIGHT, DWRITE_FONT_STYLE, DWRITE_FONT_STRETCH, POINTER(UINT32),
                       POINTER(IDWriteFont),
                       POINTER(FLOAT))),
    ]


class IDWriteColorGlyphRunEnumerator(com.pIUnknown):
    _methods_ = [
        ("MoveNext",
         com.STDMETHOD()),
        ("GetCurrentRun",
         com.STDMETHOD()),
    ]


class IDWriteFactory2(IDWriteFactory1, IDWriteFactory, com.pIUnknown):
    _methods_ = [
        ("GetSystemFontFallback",
         com.STDMETHOD(POINTER(IDWriteFontFallback))),
        ("CreateFontFallbackBuilder",
         com.STDMETHOD()),
        ("TranslateColorGlyphRun",
         com.STDMETHOD(FLOAT, FLOAT, POINTER(DWRITE_GLYPH_RUN), c_void_p, DWRITE_MEASURING_MODE, c_void_p, UINT32,
                       POINTER(IDWriteColorGlyphRunEnumerator))),
        ("CreateCustomRenderingParams2",
         com.STDMETHOD()),
        ("CreateGlyphRunAnalysis",
         com.STDMETHOD()),
    ]


IID_IDWriteFactory2 = com.GUID(0x0439fc60, 0xca44, 0x4994, 0x8d, 0xee, 0x3a, 0x9a, 0xf7, 0xb7, 0x32, 0xec)


class IDWriteFontSet(com.pIUnknown):
    _methods_ = [
        ("GetFontCount",
         com.STDMETHOD()),
        ("GetFontFaceReference",
         com.STDMETHOD()),
        ("FindFontFaceReference",
         com.STDMETHOD()),
        ("FindFontFace",
         com.STDMETHOD()),
        ("GetPropertyValues",
         com.STDMETHOD()),
        ("GetPropertyOccurrenceCount",
         com.STDMETHOD()),
        ("GetMatchingFonts",
         com.STDMETHOD()),
        ("GetMatchingFonts",
         com.STDMETHOD()),
    ]


class IDWriteFontSetBuilder(com.pIUnknown):
    _methods_ = [
        ("AddFontFaceReference",
         com.STDMETHOD()),
        ("AddFontFaceReference",
         com.STDMETHOD()),
        ("AddFontSet",
         com.STDMETHOD()),
        ("CreateFontSet",
         com.STDMETHOD(POINTER(IDWriteFontSet))),
    ]


class IDWriteFontSetBuilder1(IDWriteFontSetBuilder, com.pIUnknown):
    _methods_ = [
        ("AddFontFile",
         com.STDMETHOD(IDWriteFontFile)),
    ]


class IDWriteFactory3(IDWriteFactory2, com.pIUnknown):
    _methods_ = [
        ("CreateGlyphRunAnalysis",
         com.STDMETHOD()),
        ("CreateCustomRenderingParams3",
         com.STDMETHOD()),
        ("CreateFontFaceReference",
         com.STDMETHOD()),
        ("CreateFontFaceReference",
         com.STDMETHOD()),
        ("GetSystemFontSet",
         com.STDMETHOD()),
        ("CreateFontSetBuilder",
         com.STDMETHOD(POINTER(IDWriteFontSetBuilder))),
        ("CreateFontCollectionFromFontSet",
         com.STDMETHOD(IDWriteFontSet, POINTER(IDWriteFontCollection1))),
        ("GetSystemFontCollection3",
         com.STDMETHOD()),
        ("GetFontDownloadQueue",
         com.STDMETHOD()),
        # ('GetSystemFontSet',
        # com.STDMETHOD()),
    ]


class IDWriteColorGlyphRunEnumerator1(IDWriteColorGlyphRunEnumerator, com.pIUnknown):
    _methods_ = [
        ("GetCurrentRun1",
         com.STDMETHOD()),
    ]


class IDWriteFactory4(IDWriteFactory3, com.pIUnknown):
    _methods_ = [
        ("TranslateColorGlyphRun4",  # Renamed to prevent clash from previous factories.
         com.STDMETHOD(D2D_POINT_2F, POINTER(DWRITE_GLYPH_RUN), c_void_p, DWRITE_GLYPH_IMAGE_FORMATS,
                       DWRITE_MEASURING_MODE, c_void_p, UINT32, POINTER(IDWriteColorGlyphRunEnumerator1))),
        ("ComputeGlyphOrigins_",
         com.STDMETHOD()),
        ("ComputeGlyphOrigins",
         com.STDMETHOD()),
    ]


class IDWriteInMemoryFontFileLoader(com.pIUnknown):
    _methods_ = [
        ("CreateStreamFromKey",
         com.STDMETHOD()),
        ("CreateInMemoryFontFileReference",
         com.STDMETHOD(IDWriteFactory, c_void_p, UINT, c_void_p, POINTER(IDWriteFontFile))),
        ("GetFileCount",
         com.STDMETHOD()),
    ]


IID_IDWriteFactory5 = com.GUID(0x958DB99A, 0xBE2A, 0x4F09, 0xAF, 0x7D, 0x65, 0x18, 0x98, 0x03, 0xD1, 0xD3)


class IDWriteFactory5(IDWriteFactory4, IDWriteFactory3, IDWriteFactory2, IDWriteFactory1, IDWriteFactory,
                      com.pIUnknown):
    _methods_ = [
        ("CreateFontSetBuilder1",
         com.STDMETHOD(POINTER(IDWriteFontSetBuilder1))),
        ("CreateInMemoryFontFileLoader",
         com.STDMETHOD(POINTER(IDWriteInMemoryFontFileLoader))),
        ("CreateHttpFontFileLoader",
         com.STDMETHOD()),
        ("AnalyzeContainerType",
         com.STDMETHOD()),
    ]


DWriteCreateFactory = dwrite_lib.DWriteCreateFactory
DWriteCreateFactory.restype = HRESULT
DWriteCreateFactory.argtypes = [DWRITE_FACTORY_TYPE, com.REFIID, POINTER(com.pIUnknown)]


class ID2D1Resource(com.pIUnknown):
    _methods_ = [
        ("GetFactory",
         com.STDMETHOD()),
    ]


class ID2D1Brush(ID2D1Resource, com.pIUnknown):
    _methods_ = [
        ("SetOpacity",
         com.STDMETHOD()),
        ("SetTransform",
         com.STDMETHOD()),
        ("GetOpacity",
         com.STDMETHOD()),
        ("GetTransform",
         com.STDMETHOD()),
    ]


class ID2D1SolidColorBrush(ID2D1Brush, ID2D1Resource, com.pIUnknown):
    _methods_ = [
        ("SetColor",
         com.STDMETHOD()),
        ("GetColor",
         com.STDMETHOD()),
    ]


D2D1_TEXT_ANTIALIAS_MODE = UINT
D2D1_TEXT_ANTIALIAS_MODE_DEFAULT = 0
D2D1_TEXT_ANTIALIAS_MODE_CLEARTYPE = 1
D2D1_TEXT_ANTIALIAS_MODE_GRAYSCALE = 2
D2D1_TEXT_ANTIALIAS_MODE_ALIASED = 3

D2D1_RENDER_TARGET_TYPE = UINT
D2D1_RENDER_TARGET_TYPE_DEFAULT = 0
D2D1_RENDER_TARGET_TYPE_SOFTWARE = 1
D2D1_RENDER_TARGET_TYPE_HARDWARE = 2

D2D1_FEATURE_LEVEL = UINT
D2D1_FEATURE_LEVEL_DEFAULT = 0

D2D1_RENDER_TARGET_USAGE = UINT
D2D1_RENDER_TARGET_USAGE_NONE = 0
D2D1_RENDER_TARGET_USAGE_FORCE_BITMAP_REMOTING = 1
D2D1_RENDER_TARGET_USAGE_GDI_COMPATIBLE = 2

DXGI_FORMAT = UINT
DXGI_FORMAT_UNKNOWN = 0

D2D1_ALPHA_MODE = UINT
D2D1_ALPHA_MODE_UNKNOWN = 0
D2D1_ALPHA_MODE_PREMULTIPLIED = 1
D2D1_ALPHA_MODE_STRAIGHT = 2
D2D1_ALPHA_MODE_IGNORE = 3

D2D1_DRAW_TEXT_OPTIONS = UINT
D2D1_DRAW_TEXT_OPTIONS_NO_SNAP = 0x00000001
D2D1_DRAW_TEXT_OPTIONS_CLIP = 0x00000002
D2D1_DRAW_TEXT_OPTIONS_ENABLE_COLOR_FONT = 0x00000004
D2D1_DRAW_TEXT_OPTIONS_DISABLE_COLOR_BITMAP_SNAPPING = 0x00000008
D2D1_DRAW_TEXT_OPTIONS_NONE = 0x00000000
D2D1_DRAW_TEXT_OPTIONS_FORCE_DWORD = 0xffffffff


class D2D1_PIXEL_FORMAT(Structure):
    _fields_ = (
        ("format", DXGI_FORMAT),
        ("alphaMode", D2D1_ALPHA_MODE),
    )


class D2D1_RENDER_TARGET_PROPERTIES(Structure):
    _fields_ = (
        ("type", D2D1_RENDER_TARGET_TYPE),
        ("pixelFormat", D2D1_PIXEL_FORMAT),
        ("dpiX", FLOAT),
        ("dpiY", FLOAT),
        ("usage", D2D1_RENDER_TARGET_USAGE),
        ("minLevel", D2D1_FEATURE_LEVEL),
    )


DXGI_FORMAT_B8G8R8A8_UNORM = 87

pixel_format = D2D1_PIXEL_FORMAT()
pixel_format.format = DXGI_FORMAT_UNKNOWN
pixel_format.alphaMode = D2D1_ALPHA_MODE_UNKNOWN

default_target_properties = D2D1_RENDER_TARGET_PROPERTIES()
default_target_properties.type = D2D1_RENDER_TARGET_TYPE_DEFAULT
default_target_properties.pixelFormat = pixel_format
default_target_properties.dpiX = 0.0
default_target_properties.dpiY = 0.0
default_target_properties.usage = D2D1_RENDER_TARGET_USAGE_NONE
default_target_properties.minLevel = D2D1_FEATURE_LEVEL_DEFAULT


class ID2D1RenderTarget(ID2D1Resource, com.pIUnknown):
    _methods_ = [
        ("CreateBitmap",
         com.STDMETHOD()),
        ("CreateBitmapFromWicBitmap",
         com.STDMETHOD()),
        ("CreateSharedBitmap",
         com.STDMETHOD()),
        ("CreateBitmapBrush",
         com.STDMETHOD()),
        ("CreateSolidColorBrush",
         com.STDMETHOD(POINTER(D2D1_COLOR_F), c_void_p, POINTER(ID2D1SolidColorBrush))),
        ("CreateGradientStopCollection",
         com.STDMETHOD()),
        ("CreateLinearGradientBrush",
         com.STDMETHOD()),
        ("CreateRadialGradientBrush",
         com.STDMETHOD()),
        ("CreateCompatibleRenderTarget",
         com.STDMETHOD()),
        ("CreateLayer",
         com.STDMETHOD()),
        ("CreateMesh",
         com.STDMETHOD()),
        ("DrawLine",
         com.STDMETHOD()),
        ("DrawRectangle",
         com.STDMETHOD()),
        ("FillRectangle",
         com.STDMETHOD()),
        ("DrawRoundedRectangle",
         com.STDMETHOD()),
        ("FillRoundedRectangle",
         com.STDMETHOD()),
        ("DrawEllipse",
         com.STDMETHOD()),
        ("FillEllipse",
         com.STDMETHOD()),
        ("DrawGeometry",
         com.STDMETHOD()),
        ("FillGeometry",
         com.STDMETHOD()),
        ("FillMesh",
         com.STDMETHOD()),
        ("FillOpacityMask",
         com.STDMETHOD()),
        ("DrawBitmap",
         com.STDMETHOD()),
        ("DrawText",
         com.STDMETHOD(c_wchar_p, UINT, IDWriteTextFormat, POINTER(D2D1_RECT_F), ID2D1Brush, D2D1_DRAW_TEXT_OPTIONS,
                       DWRITE_MEASURING_MODE)),
        ("DrawTextLayout",
         com.METHOD(c_void, D2D_POINT_2F, IDWriteTextLayout, ID2D1Brush, UINT32)),
        ("DrawGlyphRun",
         com.METHOD(c_void, D2D_POINT_2F, POINTER(DWRITE_GLYPH_RUN), ID2D1Brush, UINT32)),
        ("SetTransform",
         com.METHOD(c_void)),
        ("GetTransform",
         com.STDMETHOD()),
        ("SetAntialiasMode",
         com.METHOD(c_void, D2D1_TEXT_ANTIALIAS_MODE)),
        ("GetAntialiasMode",
         com.STDMETHOD()),
        ("SetTextAntialiasMode",
         com.METHOD(c_void, D2D1_TEXT_ANTIALIAS_MODE)),
        ("GetTextAntialiasMode",
         com.STDMETHOD()),
        ("SetTextRenderingParams",
         com.STDMETHOD(IDWriteRenderingParams)),
        ("GetTextRenderingParams",
         com.STDMETHOD()),
        ("SetTags",
         com.STDMETHOD()),
        ("GetTags",
         com.STDMETHOD()),
        ("PushLayer",
         com.STDMETHOD()),
        ("PopLayer",
         com.STDMETHOD()),
        ("Flush",
         com.STDMETHOD(c_void_p, c_void_p)),
        ("SaveDrawingState",
         com.STDMETHOD()),
        ("RestoreDrawingState",
         com.STDMETHOD()),
        ("PushAxisAlignedClip",
         com.STDMETHOD()),
        ("PopAxisAlignedClip",
         com.STDMETHOD()),
        ("Clear",
         com.METHOD(c_void, POINTER(D2D1_COLOR_F))),
        ("BeginDraw",
         com.METHOD(c_void)),
        ("EndDraw",
         com.STDMETHOD(c_void_p, c_void_p)),
        ("GetPixelFormat",
         com.STDMETHOD()),
        ("SetDpi",
         com.STDMETHOD()),
        ("GetDpi",
         com.STDMETHOD()),
        ("GetSize",
         com.STDMETHOD()),
        ("GetPixelSize",
         com.STDMETHOD()),
        ("GetMaximumBitmapSize",
         com.STDMETHOD()),
        ("IsSupported",
         com.STDMETHOD()),
    ]


IID_ID2D1Factory = com.GUID(0x06152247, 0x6f50, 0x465a, 0x92, 0x45, 0x11, 0x8b, 0xfd, 0x3b, 0x60, 0x07)


class ID2D1Factory(com.pIUnknown):
    _methods_ = [
        ("ReloadSystemMetrics",
         com.STDMETHOD()),
        ("GetDesktopDpi",
         com.STDMETHOD()),
        ("CreateRectangleGeometry",
         com.STDMETHOD()),
        ("CreateRoundedRectangleGeometry",
         com.STDMETHOD()),
        ("CreateEllipseGeometry",
         com.STDMETHOD()),
        ("CreateGeometryGroup",
         com.STDMETHOD()),
        ("CreateTransformedGeometry",
         com.STDMETHOD()),
        ("CreatePathGeometry",
         com.STDMETHOD()),
        ("CreateStrokeStyle",
         com.STDMETHOD()),
        ("CreateDrawingStateBlock",
         com.STDMETHOD()),
        ("CreateWicBitmapRenderTarget",
         com.STDMETHOD(IWICBitmap, POINTER(D2D1_RENDER_TARGET_PROPERTIES), POINTER(ID2D1RenderTarget))),
        ("CreateHwndRenderTarget",
         com.STDMETHOD()),
        ("CreateDxgiSurfaceRenderTarget",
         com.STDMETHOD()),
        ("CreateDCRenderTarget",
         com.STDMETHOD()),
    ]


d2d_lib = windll.d2d1

D2D1_FACTORY_TYPE = UINT
D2D1_FACTORY_TYPE_SINGLE_THREADED = 0
D2D1_FACTORY_TYPE_MULTI_THREADED = 1

D2D1CreateFactory = d2d_lib.D2D1CreateFactory
D2D1CreateFactory.restype = HRESULT
D2D1CreateFactory.argtypes = [D2D1_FACTORY_TYPE, com.REFIID, c_void_p, c_void_p]

# We need a WIC factory to make this work. Make sure one is in the initialized decoders.
wic_decoder = None
for decoder in pyglet.image.codecs.get_decoders():
    if isinstance(decoder, WICDecoder):
        wic_decoder = decoder

if not wic_decoder:
    raise Exception("Cannot use DirectWrite without a WIC Decoder")


def get_system_locale() -> str:
    """Retrieve the string representing the system locale."""
    local_name = create_unicode_buffer(LOCALE_NAME_MAX_LENGTH)
    kernel32.GetUserDefaultLocaleName(local_name, LOCALE_NAME_MAX_LENGTH)
    return local_name.value


class DirectWriteGlyphRenderer(base.GlyphRenderer):
    font: Win32DirectWriteFont
    antialias_mode = D2D1_TEXT_ANTIALIAS_MODE_DEFAULT
    draw_options = D2D1_DRAW_TEXT_OPTIONS_ENABLE_COLOR_FONT if WINDOWS_8_1_OR_GREATER else D2D1_DRAW_TEXT_OPTIONS_NONE
    measuring_mode = DWRITE_MEASURING_MODE_NATURAL

    def __init__(self, font: Win32DirectWriteFont) -> None:
        self._render_target = None
        self._bitmap = None
        self._brush = None
        self._bitmap_dimensions = (0, 0)
        super().__init__(font)
        self.font = font

        self._analyzer = IDWriteTextAnalyzer()
        self.font._write_factory.CreateTextAnalyzer(byref(self._analyzer))

        self._text_analysis = TextAnalysis()

    def render(self, text: str) -> Glyph:
        pass

    def render_to_image(self, text: str, width: int, height: int) -> ImageData:
        """This process takes Pyglet out of the equation and uses only DirectWrite to shape and render text.
        This may allows more accurate fonts (bidi, rtl, etc) in very special circumstances.
        """
        text_buffer = create_unicode_buffer(text)

        text_layout = IDWriteTextLayout()
        self.font._write_factory.CreateTextLayout(
            text_buffer,
            len(text_buffer),
            self.font._text_format,
            width,  # Doesn't affect bitmap size.
            height,
            byref(text_layout),
        )

        layout_metrics = DWRITE_TEXT_METRICS()
        text_layout.GetMetrics(byref(layout_metrics))

        width, height = int(math.ceil(layout_metrics.width)), int(math.ceil(layout_metrics.height))

        bitmap = IWICBitmap()
        wic_decoder._factory.CreateBitmap(
            width,
            height,
            GUID_WICPixelFormat32bppPBGRA,
            WICBitmapCacheOnDemand,
            byref(bitmap),
        )

        rt = ID2D1RenderTarget()
        d2d_factory.CreateWicBitmapRenderTarget(bitmap, default_target_properties, byref(rt))

        # Font aliasing rendering quality.
        rt.SetTextAntialiasMode(self.antialias_mode)

        if not self._brush:
            self._brush = ID2D1SolidColorBrush()

        rt.CreateSolidColorBrush(white, None, byref(self._brush))

        rt.BeginDraw()

        rt.Clear(transparent)

        rt.DrawTextLayout(no_offset,
                          text_layout,
                          self._brush,
                          self.draw_options)

        rt.EndDraw(None, None)

        rt.Release()

        return wic_decoder.get_image(bitmap)

    def get_string_info(self, text: str, font_face: IDWriteFontFace) -> tuple[
        c_wchar, int, Array[UINT16], Array[FLOAT], Array[DWRITE_GLYPH_OFFSET], Array[UINT16]]:
        """Converts a string of text into a list of indices and advances used for shaping."""
        text_length = len(text.encode("utf-16-le")) // 2

        # Unicode buffer splits each two byte chars into separate indices.
        text_buffer = create_unicode_buffer(text, text_length)

        # Analyze the text.
        # noinspection PyTypeChecker
        self._text_analysis.GenerateResults(self._analyzer, text_buffer, len(text_buffer))

        # Formula for text buffer size from Microsoft.
        max_glyph_size = int(3 * text_length / 2 + 16)

        length = text_length
        clusters = (UINT16 * length)()
        text_props = (DWRITE_SHAPING_TEXT_PROPERTIES * length)()
        indices = (UINT16 * max_glyph_size)()
        glyph_props = (DWRITE_SHAPING_GLYPH_PROPERTIES * max_glyph_size)()
        actual_count = UINT32()

        self._analyzer.GetGlyphs(
            text_buffer,
            length,
            font_face,
            False,  # sideways
            False,  # righttoleft
            self._text_analysis._script,  # scriptAnalysis
            None,  # localName
            None,  # numberSub
            None,  # typo features
            None,  # feature range length
            0,  # feature range
            max_glyph_size,  # max glyph size
            clusters,  # cluster map
            text_props,  # text props
            indices,  # glyph indices
            glyph_props,  # glyph pops
            byref(actual_count),  # glyph count
        )

        advances = (FLOAT * length)()
        offsets = (DWRITE_GLYPH_OFFSET * length)()
        self._analyzer.GetGlyphPlacements(
            text_buffer,
            clusters,
            text_props,
            text_length,
            indices,
            glyph_props,
            actual_count,
            font_face,
            self.font._font_metrics.designUnitsPerEm,
            False, False,
            self._text_analysis._script,
            self.font.locale,
            None,
            None,
            0,
            advances,
            offsets,
        )

        return text_buffer, actual_count.value, indices, advances, offsets, clusters

    def get_glyph_metrics(self, font_face: IDWriteFontFace, indices: Array[UINT16], count: int) -> list[
        tuple[float, float, float, float, float]]:
        """Returns a list of tuples with the following metrics per indice:
        .       (glyph width, glyph height, lsb, advanceWidth)
        """
        glyph_metrics = (DWRITE_GLYPH_METRICS * count)()
        font_face.GetDesignGlyphMetrics(indices, count, glyph_metrics, False)

        metrics_out = []
        for metric in glyph_metrics:
            glyph_width = (metric.advanceWidth - metric.leftSideBearing - metric.rightSideBearing)

            # width must have a minimum of 1. For example, spaces are actually 0 width, still need glyph bitmap size.
            if glyph_width == 0:
                glyph_width = 1

            glyph_height = (metric.advanceHeight - metric.topSideBearing - metric.bottomSideBearing)

            lsb = metric.leftSideBearing

            bsb = metric.bottomSideBearing

            advance_width = metric.advanceWidth

            metrics_out.append((glyph_width, glyph_height, lsb, advance_width, bsb))

        return metrics_out

    def _get_single_glyph_run(self, font_face: IDWriteFontFace, size: float, indices: Array[UINT16],
                              advances: Array[FLOAT], offsets: Array[DWRITE_GLYPH_OFFSET], sideways: bool,
                              bidi: int) -> DWRITE_GLYPH_RUN:
        run = DWRITE_GLYPH_RUN(
            font_face,
            size,
            1,
            indices,
            advances,
            offsets,
            sideways,
            bidi,
        )
        return run

    def is_color_run(self, run: DWRITE_GLYPH_RUN) -> bool:
        """Will return True if the run contains a colored glyph."""
        try:
            if WINDOWS_10_CREATORS_UPDATE_OR_GREATER:
                enumerator = IDWriteColorGlyphRunEnumerator1()
                color = self.font._write_factory.TranslateColorGlyphRun4(
                    no_offset,
                    run,
                    None,
                    DWRITE_GLYPH_IMAGE_FORMATS_ALL,
                    self.measuring_mode,
                    None,
                    0,
                    byref(enumerator),
                )
            elif WINDOWS_8_1_OR_GREATER:
                enumerator = IDWriteColorGlyphRunEnumerator()
                color = self.font._write_factory.TranslateColorGlyphRun(
                    0.0, 0.0,
                    run,
                    None,
                    self.measuring_mode,
                    None,
                    0,
                    byref(enumerator),
                )
            else:
                return False

            return True
        except OSError as dw_err:
            # HRESULT returns -2003283956 (DWRITE_E_NOCOLOR) if no color run is detected. Anything else is unexpected.
            if dw_err.winerror != -2003283956:
                raise dw_err

        return False

    def render_single_glyph(self, font_face: IDWriteFontFace, indice: int, advance: float, offset: DWRITE_GLYPH_OFFSET,
                            metrics: tuple[float, float, float, float, float]):
        """Renders a single glyph using D2D DrawGlyphRun"""
        glyph_width, glyph_height, glyph_lsb, glyph_advance, glyph_bsb = metrics  # We use a shaped advance instead
        # of the fonts.

        # Slicing an array turns it into a python object. Maybe a better way to keep it a ctypes value?
        new_indice = (UINT16 * 1)(indice)
        new_advance = (FLOAT * 1)(advance)

        run = self._get_single_glyph_run(
            font_face,
            self.font._real_size,
            new_indice,  # indice,
            new_advance,  # advance,
            pointer(offset),  # offset,
            False,
            0,
        )

        # If it's colored, return to render it using layout.
        if self.draw_options & D2D1_DRAW_TEXT_OPTIONS_ENABLE_COLOR_FONT and self.is_color_run(run):
            return None

        # Use the glyph's advance as a width as bitmap width.
        # Some characters such as diacritics (̃) may have 0 advance width. In that case, just use glyph_width
        if glyph_advance:
            render_width = int(math.ceil(glyph_advance * self.font.font_scale_ratio))
        else:
            render_width = int(math.ceil(glyph_width * self.font.font_scale_ratio))

        render_offset_x = 0
        if glyph_lsb < 0:
            # Negative LSB: we shift the offset, otherwise the glyph will be cut off.
            render_offset_x = glyph_lsb * self.font.font_scale_ratio

        # Increase width by arbitrary amount to accommodate size of italic.
        # No way to get actual size of italics outside of rendering to larger texture and checking pixels.
        if self.font.italic:
            render_width += (render_width // 2)

        # Create new bitmap.
        # TODO: We can probably adjust bitmap/baseline to reduce the whitespace and save a lot of texture space.
        # Note: Floating point precision makes this a giant headache, will need to be solved for this approach.
        self._create_bitmap(render_width + 1,  # Add 1, sometimes AA can add an extra pixel or so.
                            int(math.ceil(self.font.max_glyph_height)))

        # Glyphs are drawn at the baseline, and with LSB, so we need to offset it based on top left position.
        baseline_offset = D2D_POINT_2F(-render_offset_x - offset.advanceOffset,
                                       self.font.ascent + offset.ascenderOffset)

        self._render_target.BeginDraw()

        self._render_target.Clear(transparent)

        self._render_target.DrawGlyphRun(baseline_offset,
                                         run,
                                         self._brush,
                                         self.measuring_mode)

        self._render_target.EndDraw(None, None)
        image = wic_decoder.get_image(self._bitmap)

        glyph = self.font.create_glyph(image)

        glyph.set_bearings(-self.font.descent, render_offset_x,
                           advance,
                           offset.advanceOffset,
                           offset.ascenderOffset)

        return glyph

    def render_using_layout(self, text: str) -> Glyph | None:
        """This will render text given the built in DirectWrite layout.

        This process allows us to take advantage of color glyphs and fallback handling that is built into DirectWrite.
        This can also handle shaping and many other features if you want to render directly to a texture.
        """
        text_layout = self.font.create_text_layout(text)

        layout_metrics = DWRITE_TEXT_METRICS()
        text_layout.GetMetrics(byref(layout_metrics))

        width = int(math.ceil(layout_metrics.width))
        height = int(math.ceil(layout_metrics.height))

        if width == 0 or height == 0:
            return None

        self._create_bitmap(width, height)

        # This offsets the characters if needed.
        point = D2D_POINT_2F(0, 0)

        self._render_target.BeginDraw()

        self._render_target.Clear(transparent)

        self._render_target.DrawTextLayout(point,
                                           text_layout,
                                           self._brush,
                                           self.draw_options)

        self._render_target.EndDraw(None, None)

        image = wic_decoder.get_image(self._bitmap)

        glyph = self.font.create_glyph(image)
        glyph.set_bearings(-self.font.descent, 0, int(math.ceil(layout_metrics.width)))
        return glyph

    def create_zero_glyph(self) -> Glyph:
        """Zero glyph is a 1x1 image that has a -1 advance.

        This is to fill in for ligature substitutions since font system requires 1 glyph per character in a string.
        """
        self._create_bitmap(1, 1)
        image = wic_decoder.get_image(self._bitmap)

        glyph = self.font.create_glyph(image)
        glyph.set_bearings(-self.font.descent, 0, -1)
        return glyph

    def _create_bitmap(self, width: int, height: int) -> None:
        """Creates a bitmap using Direct2D and WIC."""
        # Create a new bitmap, try to re-use the bitmap as much as we can to minimize creations.
        if self._bitmap_dimensions[0] != width or self._bitmap_dimensions[1] != height:
            # If dimensions aren't the same, release bitmap to create new ones.
            if self._bitmap:
                self._bitmap.Release()

            self._bitmap = IWICBitmap()
            wic_decoder._factory.CreateBitmap(width, height,
                                              GUID_WICPixelFormat32bppPBGRA,
                                              WICBitmapCacheOnDemand,
                                              byref(self._bitmap))

            self._render_target = ID2D1RenderTarget()
            d2d_factory.CreateWicBitmapRenderTarget(self._bitmap, default_target_properties, byref(self._render_target))

            # Font aliasing rendering quality.
            self._render_target.SetTextAntialiasMode(self.antialias_mode)

            if not self._brush:
                self._brush = ID2D1SolidColorBrush()
                self._render_target.CreateSolidColorBrush(white, None, byref(self._brush))


class Win32DirectWriteFont(base.Font):
    # To load fonts from files, we need to produce a custom collection.
    _custom_collection = None

    # Shared loader values
    _write_factory = None  # Factory required to run any DirectWrite interfaces.
    _font_loader = None

    # Windows 10 loader values.
    _font_builder = None
    _font_set = None

    # Legacy loader values
    _font_collection_loader = None
    _font_cache = []
    _font_loader_key = None

    _default_name = "Segoe UI"  # Default font for Win7/10.

    _glyph_renderer = None
    _empty_glyph = None
    _zero_glyph = None

    glyph_renderer_class = DirectWriteGlyphRenderer
    texture_internalformat = pyglet.gl.GL_RGBA

    def __init__(self, name: str, size: float, bold: bool | str = False, italic: bool | str = False,
                 stretch: bool | str = False, dpi: int | None = None, locale: str | None = None) -> None:
        self._filename: str | None = None
        self._advance_cache = {}  # Stores glyph's by the indice and advance.

        super().__init__()

        if not name:
            name = self._default_name

        self._name = name
        self.bold = bold
        self.size = size
        self.italic = italic
        self.stretch = stretch
        self.dpi = dpi
        self.locale = locale

        if self.locale is None:
            self.locale = ""
            self.rtl = False  # Right to left should be handled by pyglet?
            # TODO: Use system locale string?

        if self.dpi is None:
            self.dpi = 96

        # From DPI to DIP (Device Independent Pixels) which is what the fonts rely on.
        self._real_size = (self.size * self.dpi) // 72

        if self.bold:
            if isinstance(self.bold, str):
                self._weight = name_to_weight[self.bold]
            else:
                self._weight = DWRITE_FONT_WEIGHT_BOLD
        else:
            self._weight = DWRITE_FONT_WEIGHT_NORMAL

        if self.italic:
            if isinstance(self.italic, str):
                self._style = name_to_style[self.italic]
            else:
                self._style = DWRITE_FONT_STYLE_ITALIC
        else:
            self._style = DWRITE_FONT_STYLE_NORMAL

        if self.stretch:
            if isinstance(self.stretch, str):
                self._stretch = name_to_stretch[self.stretch]
            else:
                self._stretch = DWRITE_FONT_STRETCH_EXPANDED
        else:
            self._stretch = DWRITE_FONT_STRETCH_NORMAL

        self._font_index, self._collection = self.get_collection(name)
        write_font = None
        # If not font found, search all collections for legacy GDI naming.
        if pyglet.options["dw_legacy_naming"]:
            if self._font_index is None and self._collection is None:
                write_font, self._collection = self.find_font_face(name, self._weight, self._style, self._stretch)

        assert self._collection is not None, f"Font: '{name}' not found in loaded or system font collection."

        if self._font_index is not None:
            font_family = IDWriteFontFamily1()
            self._collection.GetFontFamily(self._font_index, byref(font_family))

            write_font = IDWriteFont()
            font_family.GetFirstMatchingFont(
                self._weight,
                self._stretch,
                self._style,
                byref(write_font),
            )

        # Create the text format this font will use permanently.
        # Could technically be recreated, but will keep to be inline with other font objects.
        self._text_format = IDWriteTextFormat()
        self._write_factory.CreateTextFormat(
            self._name,
            self._collection,
            self._weight,
            self._style,
            self._stretch,
            self._real_size,
            create_unicode_buffer(self.locale),
            byref(self._text_format),
        )

        font_face = IDWriteFontFace()
        write_font.CreateFontFace(byref(font_face))

        self.font_face = IDWriteFontFace1()
        font_face.QueryInterface(IID_IDWriteFontFace1, byref(self.font_face))

        self._font_metrics = DWRITE_FONT_METRICS()
        self.font_face.GetMetrics(byref(self._font_metrics))

        self.font_scale_ratio = (self._real_size / self._font_metrics.designUnitsPerEm)

        self.ascent = math.ceil(self._font_metrics.ascent * self.font_scale_ratio)
        self.descent = -round(self._font_metrics.descent * self.font_scale_ratio)
        self.max_glyph_height = (self._font_metrics.ascent + self._font_metrics.descent) * self.font_scale_ratio

        self.line_gap = self._font_metrics.lineGap * self.font_scale_ratio

        self._fallback = None
        if WINDOWS_8_1_OR_GREATER:
            self._fallback = IDWriteFontFallback()
            self._write_factory.GetSystemFontFallback(byref(self._fallback))
        else:
            assert _debug_print("Windows 8.1+ is required for font fallback. Colored glyphs cannot be omitted.")

    @property
    def filename(self) -> str:
        """Returns a filename associated with the font face.

        Note: Capable of returning more than 1 file in the future, but will do just one for now.
        """
        if self._filename is not None:
            return self._filename

        file_ct = UINT32()
        self.font_face.GetFiles(byref(file_ct), None)

        font_files = (IDWriteFontFile * file_ct.value)()

        self.font_face.GetFiles(byref(file_ct), font_files)

        self._filename = "Not Available"

        pff = font_files[0]

        key_data = c_void_p()
        ff_key_size = UINT32()

        pff.GetReferenceKey(byref(key_data), byref(ff_key_size))

        loader = IDWriteFontFileLoader()
        pff.GetLoader(byref(loader))

        try:
            local_loader = IDWriteLocalFontFileLoader()
            loader.QueryInterface(IID_IDWriteLocalFontFileLoader, byref(local_loader))
        except OSError:  # E_NOTIMPL
            loader.Release()
            pff.Release()
            return self._filename

        path_len = UINT32()
        local_loader.GetFilePathLengthFromKey(key_data, ff_key_size, byref(path_len))

        buffer = create_unicode_buffer(path_len.value + 1)
        local_loader.GetFilePathFromKey(key_data, ff_key_size, buffer, len(buffer))

        loader.Release()
        local_loader.Release()
        pff.Release()

        self._filename = pathlib.PureWindowsPath(buffer.value).as_posix()  # Convert to forward slashes.
        return self._filename

    @property
    def name(self) -> str:
        return self._name

    def render_to_image(self, text: str, width: int=10000, height: int=80) -> ImageData:
        """This process takes Pyglet out of the equation and uses only DirectWrite to shape and render text.
        This may allow more accurate fonts (bidi, rtl, etc) in very special circumstances at the cost of
        additional texture space.
        """
        if not self._glyph_renderer:
            self._glyph_renderer = self.glyph_renderer_class(self)

        return self._glyph_renderer.render_to_image(text, width, height)

    def copy_glyph(self, glyph: base.Glyph, advance: int, offset: DWRITE_GLYPH_OFFSET) -> base.Glyph:
        """This takes the existing glyph texture and puts it into a new Glyph with a new advance.
        Texture memory is shared between both glyphs.
        """
        new_glyph = base.Glyph(glyph.x, glyph.y, glyph.z, glyph.width, glyph.height, glyph.owner)
        new_glyph.set_bearings(
            glyph.baseline,
            glyph.lsb,
            advance,
            offset.advanceOffset,
            offset.ascenderOffset,
        )
        return new_glyph

    def _render_layout_glyph(self, text_buffer: str, i: int, clusters: list[DWRITE_CLUSTER_METRICS], check_color: bool=True):
        # Some glyphs can be more than 1 char. We use the clusters to determine how many of an index exist.
        text_length = clusters.count(i)

        # Amount of glyphs don't always match 1:1 with text as some can be substituted or omitted. Get
        # actual text buffer index.
        text_index = clusters.index(i)

        # Get actual text based on the index and length.
        actual_text = text_buffer[text_index:text_index + text_length]

        # Since we can't store as indice 0 without overriding, we have to store as text
        if actual_text not in self.glyphs:
            glyph = self._glyph_renderer.render_using_layout(text_buffer[text_index:text_index + text_length])
            if glyph:
                if check_color and self._glyph_renderer.draw_options & D2D1_DRAW_TEXT_OPTIONS_ENABLE_COLOR_FONT:
                    fb_ff = self._get_fallback_font_face(text_index, text_length)
                    if fb_ff:
                        glyph.colored = self.is_fallback_str_colored(fb_ff, actual_text)
            else:
                glyph = self._empty_glyph

            self.glyphs[actual_text] = glyph

        return self.glyphs[actual_text]

    def is_fallback_str_colored(self, font_face: IDWriteFontFace, text: str) -> bool:
        indice = UINT16()
        code_points = (UINT32 * len(text))(*[ord(c) for c in text])

        font_face.GetGlyphIndices(code_points, len(text), byref(indice))

        new_indice = (UINT16 * 1)(indice)
        new_advance = (FLOAT * 1)(100)  # dummy
        offset = (DWRITE_GLYPH_OFFSET * 1)()

        run = self._glyph_renderer._get_single_glyph_run(
            font_face,
            self._real_size,
            new_indice,  # indice,
            new_advance,  # advance,
            offset,  # offset,
            False,
            False,
        )

        return self._glyph_renderer.is_color_run(run)

    def _get_fallback_font_face(self, text_index: int, text_length: int) -> IDWriteFontFace | None:
        if WINDOWS_8_1_OR_GREATER:
            out_length = UINT32()
            fb_font = IDWriteFont()
            scale = FLOAT()

            self._fallback.MapCharacters(
                self._glyph_renderer._text_analysis,
                text_index,
                text_length,
                None,
                None,
                self._weight,
                self._style,
                self._stretch,
                byref(out_length),
                byref(fb_font),
                byref(scale),
            )

            if fb_font:
                fb_font_face = IDWriteFontFace()
                fb_font.CreateFontFace(byref(fb_font_face))

                return fb_font_face

        return None

    def get_glyphs_no_shape(self, text: str) -> list[Glyph]:
        """This differs in that it does not attempt to shape the text at all. May be useful in cases where your font
        has no special shaping requirements, spacing is the same, or some other reason where faster performance is
        wanted and you can get away with this.
        """
        if not self._glyph_renderer:
            self._glyph_renderer = self.glyph_renderer_class(self)
            self._empty_glyph = self._glyph_renderer.render_using_layout(" ")

        glyphs = []
        for c in text:
            if c == "\t":
                c = " "

            if c not in self.glyphs:
                self.glyphs[c] = self._glyph_renderer.render_using_layout(c)
                if not self.glyphs[c]:
                    self.glyphs[c] = self._empty_glyph

            glyphs.append(self.glyphs[c])

        return glyphs

    def get_glyphs(self, text: str) -> list[Glyph]:
        if not self._glyph_renderer:
            self._glyph_renderer = self.glyph_renderer_class(self)
            self._empty_glyph = self._glyph_renderer.render_using_layout(" ")
            self._zero_glyph = self._glyph_renderer.create_zero_glyph()

        text_buffer, actual_count, indices, advances, offsets, clusters = self._glyph_renderer.get_string_info(text,
                                                                                                               self.font_face)

        metrics = self._glyph_renderer.get_glyph_metrics(self.font_face, indices, actual_count)

        formatted_clusters = list(clusters)

        # Convert to real sizes.
        for i in range(actual_count):
            advances[i] *= self.font_scale_ratio

        for i in range(actual_count):
            offsets[i].advanceOffset *= self.font_scale_ratio
            offsets[i].ascenderOffset *= self.font_scale_ratio

        glyphs = []

        # Pyglet expects 1 glyph for every string. However, ligatures can combine 1 or more glyphs, leading
        # to issues with multilines producing wrong output.
        substitutions = {}
        for idx in clusters:
            ct = formatted_clusters.count(idx)
            if ct > 1:
                substitutions[idx] = ct - 1

        for i in range(actual_count):
            indice = indices[i]

            if indice == 0:
                # If an indice is 0, it will return no glyph. In this case we attempt to render leveraging
                # the built in text layout from MS. Which depending on version can use fallback fonts and other tricks
                # to possibly get something of use.
                glyph = self._render_layout_glyph(text_buffer, i, formatted_clusters)
                glyphs.append(glyph)
            else:
                advance_key = (indice, advances[i], offsets[i].advanceOffset, offsets[i].ascenderOffset)

                # Glyphs can vary depending on shaping. We will cache it by indice, advance, and offset.
                # Possible to just cache without offset and set them each time. This may be faster?
                if indice in self.glyphs:
                    if advance_key in self._advance_cache:
                        glyph = self._advance_cache[advance_key]
                    else:
                        glyph = self.copy_glyph(self.glyphs[indice], advances[i], offsets[i])
                        self._advance_cache[advance_key] = glyph
                else:
                    glyph = self._glyph_renderer.render_single_glyph(self.font_face, indice, advances[i], offsets[i],
                                                                     metrics[i])
                    if glyph is None:  # Will only return None if a color glyph is found. Use DW to render it directly.
                        glyph = self._render_layout_glyph(text_buffer, i, formatted_clusters, check_color=False)
                        glyph.colored = True

                    self.glyphs[indice] = glyph
                    self._advance_cache[advance_key] = glyph

                glyphs.append(glyph)

            if i in substitutions:
                for _ in range(substitutions[i]):
                    glyphs.append(self._zero_glyph)

        return glyphs

    def create_text_layout(self, text: str) -> IDWriteTextLayout:
        text_buffer = create_unicode_buffer(text)

        text_layout = IDWriteTextLayout()
        hr = self._write_factory.CreateTextLayout(text_buffer,
                                                  len(text_buffer),
                                                  self._text_format,
                                                  10000,  # Doesn't affect bitmap size.
                                                  80,
                                                  byref(text_layout),
                                                  )

        return text_layout

    @classmethod
    def _initialize_direct_write(cls: type[Win32DirectWriteFont]) -> None:
        """All direct write fonts needs factory access as well as the loaders."""
        if WINDOWS_10_CREATORS_UPDATE_OR_GREATER:
            cls._write_factory = IDWriteFactory5()
            guid = IID_IDWriteFactory5
        elif WINDOWS_8_1_OR_GREATER:
            cls._write_factory = IDWriteFactory2()
            guid = IID_IDWriteFactory2
        else:
            cls._write_factory = IDWriteFactory()
            guid = IID_IDWriteFactory

        DWriteCreateFactory(DWRITE_FACTORY_TYPE_SHARED, guid, byref(cls._write_factory))

    @classmethod
    def _initialize_custom_loaders(cls: type[Win32DirectWriteFont]) -> None:
        """Initialize the loaders needed to load custom fonts."""
        if WINDOWS_10_CREATORS_UPDATE_OR_GREATER:
            # Windows 10 finally has a built in loader that can take data and make a font out of it w/ COMs.
            cls._font_loader = IDWriteInMemoryFontFileLoader()
            cls._write_factory.CreateInMemoryFontFileLoader(byref(cls._font_loader))
            cls._write_factory.RegisterFontFileLoader(cls._font_loader)

            # Used for grouping fonts together.
            cls._font_builder = IDWriteFontSetBuilder1()
            cls._write_factory.CreateFontSetBuilder1(byref(cls._font_builder))
        else:
            cls._font_loader = LegacyFontFileLoader()

            # Note: RegisterFontLoader takes a pointer. However, for legacy we implement our own callback interface.
            # Therefore we need to pass to the actual pointer directly.
            cls._write_factory.RegisterFontFileLoader(cls._font_loader.as_interface(IDWriteFontFileLoader_LI))

            cls._font_collection_loader = LegacyCollectionLoader(cls._write_factory, cls._font_loader)
            cls._write_factory.RegisterFontCollectionLoader(cls._font_collection_loader)

            cls._font_loader_key = cast(create_unicode_buffer("legacy_font_loader"), c_void_p)

    @classmethod
    def add_font_data(cls: type[Win32DirectWriteFont], data: BinaryIO) -> None:
        if not cls._write_factory:
            cls._initialize_direct_write()

        if not cls._font_loader:
            cls._initialize_custom_loaders()

        if WINDOWS_10_CREATORS_UPDATE_OR_GREATER:
            font_file = IDWriteFontFile()
            hr = cls._font_loader.CreateInMemoryFontFileReference(cls._write_factory,
                                                                  data,
                                                                  len(data),
                                                                  None,
                                                                  byref(font_file))

            hr = cls._font_builder.AddFontFile(font_file)
            if hr != 0:
                raise Exception("This font file data is not not a font or unsupported.")

            # We have to rebuild collection everytime we add a font.
            # No way to add fonts to the collection once the FontSet and Collection are created.
            # Release old one and renew.
            if cls._custom_collection:
                cls._font_set.Release()
                cls._custom_collection.Release()

            cls._font_set = IDWriteFontSet()
            cls._font_builder.CreateFontSet(byref(cls._font_set))

            cls._custom_collection = IDWriteFontCollection1()
            cls._write_factory.CreateFontCollectionFromFontSet(cls._font_set, byref(cls._custom_collection))

        else:
            cls._font_cache.append(data)

            # If a collection exists, we need to completely remake the collection, delete everything and start over.
            if cls._custom_collection:
                cls._custom_collection = None

                cls._write_factory.UnregisterFontCollectionLoader(cls._font_collection_loader)
                cls._write_factory.UnregisterFontFileLoader(cls._font_loader)

                cls._font_loader = LegacyFontFileLoader()
                cls._font_collection_loader = LegacyCollectionLoader(cls._write_factory, cls._font_loader)

                cls._write_factory.RegisterFontCollectionLoader(cls._font_collection_loader)
                cls._write_factory.RegisterFontFileLoader(cls._font_loader.as_interface(IDWriteFontFileLoader_LI))

            cls._font_collection_loader.AddFontData(cls._font_cache)

            cls._custom_collection = IDWriteFontCollection()

            cls._write_factory.CreateCustomFontCollection(cls._font_collection_loader,
                                                          cls._font_loader_key,
                                                          sizeof(cls._font_loader_key),
                                                          byref(cls._custom_collection))

    @classmethod
    def get_collection(cls: type[Win32DirectWriteFont], font_name: str) -> tuple[int | None, IDWriteFontCollection1 | None]:
        """Returns which collection this font belongs to (system or custom collection), as well as its index in the
        collection.
        """
        if not cls._write_factory:
            cls._initialize_direct_write()

        """Returns a collection the font_name belongs to."""
        font_index = UINT()
        font_exists = BOOL()

        # Check custom loaded font collections.
        if cls._custom_collection:
            cls._custom_collection.FindFamilyName(create_unicode_buffer(font_name),
                                                  byref(font_index),
                                                  byref(font_exists))

            if font_exists.value:
                return font_index.value, cls._custom_collection

        # Check if font is in the system collection.
        # Do not cache these values permanently as system font collection can be updated during runtime.
        sys_collection = IDWriteFontCollection()
        if not font_exists.value:
            cls._write_factory.GetSystemFontCollection(byref(sys_collection), 1)
            sys_collection.FindFamilyName(create_unicode_buffer(font_name),
                                          byref(font_index),
                                          byref(font_exists))

            if font_exists.value:
                return font_index.value, sys_collection

        return None, None

    @classmethod
    def find_font_face(cls, font_name: str, bold: bool | str, italic: bool | str, stretch: bool | str) -> tuple[
        IDWriteFont | None, IDWriteFontCollection | None]:
        """This will search font collections for legacy RBIZ names. However, matching to bold, italic, stretch is
        problematic in that there are many values. We parse the font name looking for matches to the name database,
        and attempt to pick the closest match.
        This will search all fonts on the system and custom loaded, and all of their font faces. Returns a collection
        and IDWriteFont if successful.
        """
        p_bold, p_italic, p_stretch = cls.parse_name(font_name, bold, italic, stretch)

        _debug_print(f"directwrite: '{font_name}' not found. Attempting legacy name lookup in all collections.")
        if cls._custom_collection:
            collection_idx = cls.find_legacy_font(cls._custom_collection, font_name, p_bold, p_italic, p_stretch)
            if collection_idx is not None:
                return collection_idx, cls._custom_collection

        sys_collection = IDWriteFontCollection()
        cls._write_factory.GetSystemFontCollection(byref(sys_collection), 1)

        collection_idx = cls.find_legacy_font(sys_collection, font_name, p_bold, p_italic, p_stretch)
        if collection_idx is not None:
            return collection_idx, sys_collection

        return None, None

    @classmethod
    def have_font(cls: type[Win32DirectWriteFont], name: str) -> bool:
        if cls.get_collection(name)[0] is not None:
            return True

        return False

    @staticmethod
    def parse_name(font_name: str, weight: int, style: int, stretch: int) -> tuple[int, int, int]:
        """Attempt at parsing any special names in a font for legacy checks. Takes the first found."""
        font_name = font_name.lower()
        split_name = font_name.split(" ")

        found_weight = weight
        found_style = style
        found_stretch = stretch

        # Only search if name is split more than once.
        if len(split_name) > 1:
            for name, value in name_to_weight.items():
                if name in split_name:
                    found_weight = value
                    break

            for name, value in name_to_style.items():
                if name in split_name:
                    found_style = value
                    break

            for name, value in name_to_stretch.items():
                if name in split_name:
                    found_stretch = value
                    break

        return found_weight, found_style, found_stretch

    @staticmethod
    def find_legacy_font(collection: IDWriteFontCollection, font_name: str, bold: bool | str, italic: bool | str, stretch: bool | str, full_debug: bool=False) -> IDWriteFont | None:
        coll_count = collection.GetFontFamilyCount()

        assert _debug_print(f"directwrite: Found {coll_count} fonts in collection.")

        locale = get_system_locale()

        for i in range(coll_count):
            family = IDWriteFontFamily()
            collection.GetFontFamily(i, byref(family))

            # Just check the first character in Family Names to reduce search time. Arial -> A's only.
            family_name_str = IDWriteLocalizedStrings()
            family.GetFamilyNames(byref(family_name_str))

            family_names = Win32DirectWriteFont.unpack_localized_string(family_name_str, locale)
            family_name = family_names[0]

            if family_name[0] != font_name[0]:
                family.Release()
                continue

            assert _debug_print(f"directwrite: Inspecting family name: {family_name}")

            # Fonts in the family. Full search to search all font faces, typically the first will be good enough to tell
            ft_ct = family.GetFontCount()

            face_names = []
            matches = []
            for j in range(ft_ct):
                temp_ft = IDWriteFont()
                family.GetFont(j, byref(temp_ft))

                if _debug_font and full_debug:
                    fc_str = IDWriteLocalizedStrings()
                    temp_ft.GetFaceNames(byref(fc_str))

                    strings = Win32DirectWriteFont.unpack_localized_string(fc_str, locale)
                    face_names.extend(strings)

                    print(f"directwrite: Face names found: {strings}")

                # Check for GDI compatibility name
                compat_names = IDWriteLocalizedStrings()
                exists = BOOL()
                temp_ft.GetInformationalStrings(DWRITE_INFORMATIONAL_STRING_WIN32_FAMILY_NAMES,
                                                byref(compat_names),
                                                byref(exists))

                # Successful in finding GDI name.
                match_found = False
                if exists.value != 0:
                    for compat_name in Win32DirectWriteFont.unpack_localized_string(compat_names, locale):
                        if compat_name == font_name:
                            assert _debug_print(
                                f"Found legacy name '{font_name}' as '{family_name}' in font face '{j}' (collection "
                                f"id #{i}).")

                            match_found = True
                            matches.append((temp_ft.GetWeight(), temp_ft.GetStyle(), temp_ft.GetStretch(), temp_ft))
                            break

                # Release resource if not a match.
                if not match_found:
                    temp_ft.Release()

            family.Release()

            # If we have matches, we've already parsed through the proper family. Now try to match.
            if matches:
                write_font = Win32DirectWriteFont.match_closest_font(matches, bold, italic, stretch)

                # Cleanup other matches not used.
                for match in matches:
                    if match[3] != write_font:
                        match[3].Release()  # Release all other matches.

                return write_font

        return None

    @staticmethod
    def match_closest_font(font_list: list[tuple[int, int, int, IDWriteFont]], bold: int, italic: int, stretch: int) -> IDWriteFont | None:
        """Match the closest font to the parameters specified.

        If a full match is not found, a secondary match will be found based on similar features. This can probably
        be improved, but it is possible you could get a different font style than expected.
        """
        closest = []
        for match in font_list:
            (f_weight, f_style, f_stretch, writefont) = match

            # Found perfect match, no need for the rest.
            if f_weight == bold and f_style == italic and f_stretch == stretch:
                _debug_print(
                    f"directwrite: full match found. (bold: {f_weight}, italic: {f_style}, stretch: {f_stretch})")
                return writefont

            prop_match = 0
            similar_match = 0
            # Look for a full match, otherwise look for close enough.
            # For example, Arial Black only has Oblique, not Italic, but good enough if you want slanted text.
            if f_weight == bold:
                prop_match += 1
            elif bold != DWRITE_FONT_WEIGHT_NORMAL and f_weight != DWRITE_FONT_WEIGHT_NORMAL:
                similar_match += 1

            if f_style == italic:
                prop_match += 1
            elif italic != DWRITE_FONT_STYLE_NORMAL and f_style != DWRITE_FONT_STYLE_NORMAL:
                similar_match += 1

            if stretch == f_stretch:
                prop_match += 1
            elif stretch != DWRITE_FONT_STRETCH_NORMAL and f_stretch != DWRITE_FONT_STRETCH_NORMAL:
                similar_match += 1

            closest.append((prop_match, similar_match, *match))

        # If we get here, no perfect match, sort by highest perfect match, to secondary matches.
        closest.sort(key=lambda fts: (fts[0], fts[1]), reverse=True)

        if closest:
            # Take the first match after sorting.
            closest_match = closest[0]
            _debug_print(f"directwrite: falling back to partial match. "
                         f"(bold: {closest_match[2]}, italic: {closest_match[3]}, stretch: {closest_match[4]})")
            return closest_match[5]

        return None

    @staticmethod
    def unpack_localized_string(local_string: IDWriteLocalizedStrings, locale: str) -> list[str]:
        """Takes IDWriteLocalizedStrings and unpacks the strings inside of it into a list."""
        str_array_len = local_string.GetCount()

        strings = []
        for _ in range(str_array_len):
            string_size = UINT32()

            idx = Win32DirectWriteFont.get_localized_index(local_string, locale)

            local_string.GetStringLength(idx, byref(string_size))

            buffer_size = string_size.value

            buffer = create_unicode_buffer(buffer_size + 1)

            local_string.GetString(idx, buffer, len(buffer))

            strings.append(buffer.value)

        local_string.Release()

        return strings

    @staticmethod
    def get_localized_index(strings: IDWriteLocalizedStrings, locale: str) -> int:
        idx = UINT32()
        exists = BOOL()

        if locale:
            strings.FindLocaleName(locale, byref(idx), byref(exists))

            if not exists.value:
                # fallback to english.
                strings.FindLocaleName("en-us", byref(idx), byref(exists))

                if not exists:
                    return 0

            return idx.value

        return 0


d2d_factory = ID2D1Factory()
hr = D2D1CreateFactory(D2D1_FACTORY_TYPE_SINGLE_THREADED, IID_ID2D1Factory, None, byref(d2d_factory))

WICBitmapCreateCacheOption = UINT
WICBitmapNoCache = 0
WICBitmapCacheOnDemand = 0x1
WICBitmapCacheOnLoad = 0x2

transparent = D2D1_COLOR_F(0.0, 0.0, 0.0, 0.0)
white = D2D1_COLOR_F(1.0, 1.0, 1.0, 1.0)
no_offset = D2D_POINT_2F(0, 0)

# If we are not shaping, monkeypatch to no shape function.
if pyglet.options["win32_disable_shaping"]:
    Win32DirectWriteFont.get_glyphs = Win32DirectWriteFont.get_glyphs_no_shape
