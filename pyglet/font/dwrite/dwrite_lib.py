from __future__ import annotations

import copy
import ctypes
import os
import platform
from _ctypes import _Pointer
from ctypes import (
    HRESULT,
    POINTER,
    Structure,
    byref,
    c_uint32,
    c_void_p,
    c_wchar_p,
    cast,
    create_unicode_buffer,
    pointer,
    sizeof,
    windll,
)
from ctypes.wintypes import BOOL, FLOAT, HDC, UINT, WCHAR
from typing import NoReturn

from pyglet.font.dwrite.d2d1_types_lib import (
    D2D1_COLOR_F,
    D2D1_POINT_2L,
    D2D1_SIZE_U,
    D2D_POINT_2F,
)
from pyglet.libs.win32 import INT16, INT32, LOGFONTW, UINT8, UINT16, UINT32, UINT64, c_void, com

try:
    dwrite = "dwrite"

    # System32 and SysWOW64 folders are opposite perception in Windows x64.
    # System32 = x64 dll's | SysWOW64 = x86 dlls
    # By default ctypes only seems to look in system32 regardless of Python architecture, which has x64 dlls.
    if platform.architecture()[0] == "32bit" and platform.machine().endswith("64"):  # Machine is x64, Python is x86.
        dwrite = os.path.join(os.environ["WINDIR"], "SysWOW64", "dwrite.dll")

    dwrite_lib = windll.LoadLibrary(dwrite)
except OSError:
    # Doesn't exist? Should stop import of library.
    msg = "DirectWrite Not Found"
    raise ImportError(msg)  # noqa: B904


def DWRITE_MAKE_OPENTYPE_TAG(a: str, b: str, c: str, d: str) -> int:
    return ord(d) << 24 | ord(c) << 16 | ord(b) << 8 | ord(a)

DWRITE_NO_PALETTE_INDEX = 0xFFFF

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

DWRITE_GLYPH_IMAGE_FORMATS = UINT
DWRITE_GLYPH_IMAGE_FORMATS_NONE = 0x00000000
DWRITE_GLYPH_IMAGE_FORMATS_TRUETYPE = 0x00000001
DWRITE_GLYPH_IMAGE_FORMATS_CFF = 0x00000002
DWRITE_GLYPH_IMAGE_FORMATS_COLR = 0x00000004
DWRITE_GLYPH_IMAGE_FORMATS_SVG = 0x00000008
DWRITE_GLYPH_IMAGE_FORMATS_PNG = 0x00000010
DWRITE_GLYPH_IMAGE_FORMATS_JPEG = 0x00000020
DWRITE_GLYPH_IMAGE_FORMATS_TIFF = 0x00000040
DWRITE_GLYPH_IMAGE_FORMATS_PREMULTIPLIED_B8G8R8A8 = 0x00000080
DWRITE_GLYPH_IMAGE_FORMATS_COLR_PAINT_TREE = 0x00000100

DWRITE_GLYPH_IMAGE_FORMATS_BITMAP = (DWRITE_GLYPH_IMAGE_FORMATS_PNG |
                                     DWRITE_GLYPH_IMAGE_FORMATS_JPEG |
                                     DWRITE_GLYPH_IMAGE_FORMATS_TIFF |
                                     DWRITE_GLYPH_IMAGE_FORMATS_PREMULTIPLIED_B8G8R8A8)

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


DWRITE_TEXT_ALIGNMENT = UINT
DWRITE_TEXT_ALIGNMENT_LEADING = 1
DWRITE_TEXT_ALIGNMENT_TRAILING = 2
DWRITE_TEXT_ALIGNMENT_CENTER = 3
DWRITE_TEXT_ALIGNMENT_JUSTIFIED = 4

DWRITE_FONT_FACE_TYPE = UINT
DWRITE_FONT_FACE_TYPE_CFF = 0
DWRITE_FONT_FACE_TYPE_TRUETYPE = 1
DWRITE_FONT_FACE_TYPE_OPENTYPE_COLLECTION = 2
DWRITE_FONT_FACE_TYPE_TYPE1 = 3
DWRITE_FONT_FACE_TYPE_VECTOR = 4
DWRITE_FONT_FACE_TYPE_BITMAP = 5
DWRITE_FONT_FACE_TYPE_UNKNOWN = 6
DWRITE_FONT_FACE_TYPE_RAW_CFF = 7
DWRITE_FONT_FACE_TYPE_TRUETYPE_COLLECTION = 8

def repr_func(self):
    field_values = []
    for field_value in self._fields_:
        try:
            name, typ, _ = field_value  # bitfields
        except ValueError:
            name, typ = field_value

        value = getattr(self, name)

        # Check if the field is a POINTER to any ctypes structure
        if isinstance(value, _Pointer):
            value = repr(value.contents) if value else "NULL"

        field_values.append(f"{name}={value}")

    return f"{self.__class__.__name__}({', '.join(field_values)})"

DWRITE_COLOR_F = D2D1_COLOR_F

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

class DWRITE_FONT_METRICS1(Structure):
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
        ("glyphBoxLeft", INT16),  # New starting here.
        ("glyphBoxTop", INT16),
        ("glyphBoxRight", INT16),
        ("glyphBoxBottom", INT16),
        ("subscriptPositionX", INT16),
        ("subscriptPositionY", INT16),
        ("subscriptSizeX", INT16),
        ("subscriptSizeY", INT16),
        ("superscriptPositionX", INT16),
        ("superscriptPositionY", INT16),
        ("superscriptSizeX", INT16),
        ("superscriptSizeY", INT16),
        ("hasTypographicMetrics", BOOL),
    )

class DWRITE_CARET_METRICS(Structure):
    _fields_ = (
        ("slopeRise", INT16),
        ("slopeRun", INT16),
        ("offset", INT16),
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

    def __repr__(self):
        return (f"DWRITE_GLYPH_METRICS(leftSideBearing={self.leftSideBearing}, advanceWidth={self.advanceWidth}, "
                f"rightSideBearing={self.rightSideBearing}, topSideBearing={self.topSideBearing}, advanceHeight={self.advanceHeight}, "
                f"bottomSideBearing={self.bottomSideBearing}, verticalOriginY={self.verticalOriginY})")


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

DWRITE_CLUSTER_METRICS.__repr__ = repr_func

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
         com.METHOD(DWRITE_FONT_FACE_TYPE)),
        ("GetFiles",
         com.STDMETHOD(POINTER(UINT32), POINTER(IDWriteFontFile))),
        ("GetIndex",
         com.METHOD(UINT32)),
        ("GetSimulations",
         com.STDMETHOD()),
        ("IsSymbolFont",
         com.METHOD(BOOL)),
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


class IDWriteFontFace1(IDWriteFontFace):
    _methods_ = [
        ("GetMetrics1",
         com.STDMETHOD(POINTER(DWRITE_FONT_METRICS1))),
        ("GetGdiCompatibleMetrics1",
         com.STDMETHOD()),
        ("GetCaretMetrics",
         com.STDMETHOD(POINTER(DWRITE_CARET_METRICS))),
        ("GetUnicodeRanges",
         com.STDMETHOD()),
        ("IsMonospacedFont",
         com.METHOD(BOOL)),
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
         com.METHOD(BOOL)),
    ]

IID_IDWriteFontFace2 = com.GUID(0xd8b768ff, 0x64bc, 0x4e66, 0x98,0x2b, 0xec,0x8e,0x87,0xf6,0x93,0xf7)

class IDWriteFontFace2(IDWriteFontFace1):
    _methods_ = [
        ("IsColorFont",
         com.METHOD(BOOL)),
        ("GetColorPaletteCount",
         com.METHOD(UINT32)),
        ("GetPaletteEntryCount",
         com.METHOD(UINT32)),
        ("GetPaletteEntries",
         com.STDMETHOD()),
        ("GetRecommendedRenderingMode2",
         com.STDMETHOD()),
    ]

IID_IDWriteFontFace3 = com.GUID(0xd37d7598, 0x09be, 0x4222, 0xa2,0x36, 0x20,0x81,0x34,0x1c,0xc1,0xf2)

class IDWriteFontFace3(IDWriteFontFace2):
    _methods_ = [
        ("GetFontFaceReference",
         com.STDMETHOD()),
        ("GetPanose",
         com.STDMETHOD()),
        ("GetWeight",
         com.METHOD(DWRITE_FONT_WEIGHT)),
        ("GetStretch",
         com.METHOD(DWRITE_FONT_STRETCH)),
        ("GetStyle",
         com.METHOD(DWRITE_FONT_STYLE)),
        ("GetFamilyNames",
         com.STDMETHOD(POINTER(IDWriteLocalizedStrings))),
        ("GetFaceNames",
         com.STDMETHOD(POINTER(IDWriteLocalizedStrings))),
        ("GetInformationalStrings",
         com.STDMETHOD()),
        ("HasCharacter",
         com.METHOD(BOOL, UINT32)),
        ("GetRecommendedRenderingMode3",
         com.STDMETHOD()),
        ("IsCharacterLocal",
         com.STDMETHOD()),
        ("IsGlyphLocal",
         com.STDMETHOD()),
        ("AreCharactersLocal",
         com.STDMETHOD()),
        ("AreGlyphsLocal",
         com.STDMETHOD()),
    ]


class DWRITE_GLYPH_IMAGE_DATA(Structure):
    _fields_ = [
        ("imageData", c_void_p),
        ("imageDataSize", UINT32),
        ("uniqueDataId", UINT32),
        ("pixelsPerEm", UINT32),
        ("pixelSize", D2D1_SIZE_U),
        ("horizontalLeftOrigin", D2D1_POINT_2L),
        ("horizontalRightOrigin", D2D1_POINT_2L),
        ("verticalTopOrigin", D2D1_POINT_2L),
        ("verticalBottomOrigin", D2D1_POINT_2L),
    ]

IID_IDWriteFontFace4 = com.GUID(0x27f2a904, 0x4eb8, 0x441d, 0x96,0x78, 0x05,0x63,0xf5,0x3e,0x3e,0x2f)

class IDWriteFontFace4(IDWriteFontFace3):
    _methods_ = [
        ("GetGlyphImageFormats_",
         com.STDMETHOD(UINT16, UINT32, UINT32, POINTER(DWRITE_GLYPH_IMAGE_FORMATS))),
        ("GetGlyphImageFormats",
         com.METHOD(DWRITE_GLYPH_IMAGE_FORMATS)),
        ("GetGlyphImageData",
         com.STDMETHOD(UINT16, UINT32, DWRITE_GLYPH_IMAGE_FORMATS, POINTER(DWRITE_GLYPH_IMAGE_DATA),
                       POINTER(c_void_p))),
        ("ReleaseGlyphImageData",
         com.METHOD(None, c_void_p))
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

    def get_info(self):
        print(f"DWRITE_GLYPH_RUN(face: {self.fontFace}, fontEmSize: {self.fontEmSize}, count: {self.glyphCount}")
        for i in range(self.glyphCount):
            print(f"glyph: {i}, indice: {self.glyphIndices[i]}, advance: {self.glyphAdvances[i]}, offset: {self.glyphOffsets[i]}")


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
DWRITE_SHAPING_GLYPH_PROPERTIES.__repr__ = repr_func

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


class DWRITE_GLYPH_RUN_DESCRIPTION(Structure):
    _fields_ = [
        ('localeName', c_wchar_p),
        ('text', c_wchar_p),
        ('textLength', UINT32),
        ('clusterMap', POINTER(UINT16)),
        ('textPosition', UINT32)
    ]

class DWRITE_COLOR_GLYPH_RUN(Structure):
    _fields_ = [
        ('glyphRun', DWRITE_GLYPH_RUN),
        ('glyphRunDescription', POINTER(DWRITE_GLYPH_RUN_DESCRIPTION)),
        ('baselineOriginX', FLOAT),
        ('baselineOriginY', FLOAT),
        ('runColor', DWRITE_COLOR_F),
        ('paletteIndex', UINT16),
    ]


DWRITE_COLOR_GLYPH_RUN1_Fields = [
    ('glyphRun', DWRITE_GLYPH_RUN),
    ('glyphRunDescription', POINTER(DWRITE_GLYPH_RUN_DESCRIPTION)),
    ('baselineOriginX', FLOAT),
    ('baselineOriginY', FLOAT),
    ('runColor', DWRITE_COLOR_F),
    ('paletteIndex', UINT16),
    ("_pad", UINT32),  # Padding only exists in 64 bit... only info found in header.
    ('glyphImageFormat', DWRITE_GLYPH_IMAGE_FORMATS),
    ('measuringMode', DWRITE_MEASURING_MODE)
]

if platform.architecture()[0] == "32bit":
    DWRITE_COLOR_GLYPH_RUN1_Fields.remove(("_pad", UINT32))


class DWRITE_COLOR_GLYPH_RUN1(Structure):
    _fields_ = DWRITE_COLOR_GLYPH_RUN1_Fields

class DWRITE_MATRIX(Structure):
    _fields_ = [
        ("m11", FLOAT),
        ("m12", FLOAT),
        ("m21", FLOAT),
        ("m22", FLOAT),
        ("dx", FLOAT),
        ("dy", FLOAT),
    ]

class IDWritePixelSnapping(com.IUnknown):
    _methods_ = [
        ("IsPixelSnappingDisabled", com.STDMETHOD(c_void_p, POINTER(FLOAT))),
        ("GetCurrentTransform", com.STDMETHOD(c_void_p, POINTER(DWRITE_MATRIX))),
        ("GetPixelsPerDip", com.STDMETHOD(c_void_p, POINTER(FLOAT))),
    ]

class IDWriteTextRenderer(IDWritePixelSnapping):
    _methods_ = [
        ("DrawGlyphRun",
            com.STDMETHOD(c_void_p, FLOAT, FLOAT, DWRITE_MEASURING_MODE,
                          POINTER(DWRITE_GLYPH_RUN),
                          POINTER(DWRITE_GLYPH_RUN_DESCRIPTION), c_void_p)),
        ("DrawUnderline",
         com.STDMETHOD(c_void_p, FLOAT, FLOAT, c_void_p, c_void_p)
         ),
        ("DrawStrikethrough",
         com.STDMETHOD(c_void_p, FLOAT, FLOAT, c_void_p, c_void_p)),
        ("DrawInlineObject",
         com.STDMETHOD(c_void_p, FLOAT, FLOAT, c_void_p, BOOL, BOOL, c_void_p)),
    ]


class IDWriteTextLayout(IDWriteTextFormat):
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
         com.STDMETHOD(UINT32, POINTER(IDWriteFontCollection), POINTER(DWRITE_TEXT_RANGE))),
        ("GetFontFamilyNameLength2",
         com.STDMETHOD(UINT32, POINTER(UINT32), c_void_p)),
        ("GetFontFamilyName2",
         com.STDMETHOD(UINT32, c_wchar_p, UINT32, POINTER(DWRITE_TEXT_RANGE))),
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
         com.STDMETHOD(c_void_p, POINTER(IDWriteTextRenderer), FLOAT, FLOAT)),
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

# Windows 7
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
         com.STDMETHOD(c_void_p)),  # Ambiguous as newer is a pIUnknown and legacy is IUnknown.
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

# Windows 8
IID_IDWriteFactory1 = com.GUID(0x30572f99, 0xdac6, 0x41db, 0xa1, 0x6e, 0x04, 0x86, 0x30, 0x7e, 0x60, 0x6a)


class IDWriteFactory1(IDWriteFactory, com.pIUnknown):
    _methods_ = [
        ("GetEudcFontCollection",
         com.STDMETHOD()),
        ("CreateCustomRenderingParams1",
         com.STDMETHOD()),
    ]


class DWRITE_UNICODE_RANGE(Structure):
    _fields_ = [
        ("first", UINT32),
        ("last", UINT32)
    ]


class IDWriteFontFallback(com.pIUnknown):
    _methods_ = [
        ("MapCharacters",
         com.STDMETHOD(POINTER(IDWriteTextAnalysisSource), UINT32, UINT32, IDWriteFontCollection, c_wchar_p,
                       DWRITE_FONT_WEIGHT, DWRITE_FONT_STYLE, DWRITE_FONT_STRETCH, POINTER(UINT32),
                       POINTER(IDWriteFont),
                       POINTER(FLOAT))),
    ]

class IDWriteFontFallbackBuilder(com.pIUnknown):
    _methods_ = [
        ("AddMapping",
         com.STDMETHOD(POINTER(DWRITE_UNICODE_RANGE), UINT32, POINTER(c_wchar_p), UINT32,
                       IDWriteFontCollection,
                       c_wchar_p, c_wchar_p, FLOAT)),
        ("AddMappings",
         com.STDMETHOD(IDWriteFontFallback)),
        ("CreateFontFallback",
         com.STDMETHOD(POINTER(IDWriteFontFallback))),
    ]



class IDWriteColorGlyphRunEnumerator(com.pIUnknown):
    _methods_ = [
        ("MoveNext",
         com.STDMETHOD(POINTER(BOOL))),
        ("GetCurrentRun",
         com.STDMETHOD(POINTER(POINTER(DWRITE_COLOR_GLYPH_RUN)))),
    ]


class IDWriteFactory2(IDWriteFactory1, IDWriteFactory, com.pIUnknown):
    _methods_ = [
        ("GetSystemFontFallback",
         com.STDMETHOD(POINTER(IDWriteFontFallback))),
        ("CreateFontFallbackBuilder",
         com.STDMETHOD(POINTER(IDWriteFontFallbackBuilder))),
        ("TranslateColorGlyphRun",
         com.STDMETHOD(FLOAT, FLOAT, POINTER(DWRITE_GLYPH_RUN), c_void_p, DWRITE_MEASURING_MODE, c_void_p, UINT32,
                       POINTER(IDWriteColorGlyphRunEnumerator))),
        ("CreateCustomRenderingParams2",
         com.STDMETHOD()),
        ("CreateGlyphRunAnalysis2",
         com.STDMETHOD()),
    ]

# Windows 8.1
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
        ("GetPropertyValues__",
         com.STDMETHOD()),
        ("GetPropertyValues_",
         com.STDMETHOD()),
        ("GetPropertyValues",
         com.STDMETHOD()),
        ("GetPropertyOccurrenceCount",
         com.STDMETHOD()),
        ("GetMatchingFonts_",
         com.STDMETHOD()),
        ("GetMatchingFonts",
         com.STDMETHOD()),
    ]


class IDWriteFontSetBuilder(com.pIUnknown):
    _methods_ = [
        ("AddFontFaceReference_",
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
        ("CreateGlyphRunAnalysis3",
         com.STDMETHOD()),
        ("CreateCustomRenderingParams3",
         com.STDMETHOD()),
        ("CreateFontFaceReference_",
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


class IDWriteColorGlyphRunEnumerator1(IDWriteColorGlyphRunEnumerator):
    _methods_ = [
        ("GetCurrentRun1",
         com.STDMETHOD(POINTER(POINTER(DWRITE_COLOR_GLYPH_RUN1)))),
    ]

IID_IDWriteColorGlyphRunEnumerator1 = com.GUID(0x7c5f86da, 0xc7a1, 0x4f05, 0xb8,0xe1, 0x55,0xa1,0x79,0xfe,0x5a,0x35)


class IDWriteFactory4(IDWriteFactory3, com.pIUnknown):
    _methods_ = [
        ("TranslateColorGlyphRun4",
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

# Windows 10 - Creators
IID_IDWriteFactory5 = com.GUID(0x958DB99A, 0xBE2A, 0x4F09, 0xAF, 0x7D, 0x65, 0x18, 0x98, 0x03, 0xD1, 0xD3)


class IDWriteFactory5(IDWriteFactory4, IDWriteFactory3, IDWriteFactory2, IDWriteFactory1, IDWriteFactory,
                      com.pIUnknown):
    _methods_ = [
        ("CreateFontSetBuilder5",
         com.STDMETHOD(POINTER(IDWriteFontSetBuilder1))),
        ("CreateInMemoryFontFileLoader",
         com.STDMETHOD(POINTER(IDWriteInMemoryFontFileLoader))),
        ("CreateHttpFontFileLoader",
         com.STDMETHOD()),
        ("AnalyzeContainerType",
         com.STDMETHOD()),
        ("UnpackFontFile",
         com.STDMETHOD()),
    ]


ID_IDWriteFactory6 = com.GUID(0xf3744d80, 0x21f7, 0x42eb, 0xb3,0x5d, 0x99,0x5b,0xc7,0x2f,0xc2,0x23)

class IDWriteFactory6(IDWriteFactory5, IDWriteFactory4, IDWriteFactory3, IDWriteFactory2, IDWriteFactory1, IDWriteFactory,
                      com.pIUnknown):
    _methods_ = [
        ("CreateFontFaceReference6",
         com.STDMETHOD()),
        ("CreateFontResource",
         com.STDMETHOD()),
        ("GetSystemFontSet6",
         com.STDMETHOD()),
        ("GetSystemFontCollection6",
         com.STDMETHOD()),
        ("CreateFontCollectionFromFontSet6",
         com.STDMETHOD()),
        ("CreateFontSetBuilder6",
         com.STDMETHOD()),
        ("CreateTextFormat6",
         com.STDMETHOD()),
    ]


class IDWriteFactory7(IDWriteFactory6, IDWriteFactory5, IDWriteFactory4, IDWriteFactory3, IDWriteFactory2,
                      IDWriteFactory1, IDWriteFactory, com.pIUnknown):
    _methods_ = [
        ("GetSystemFontSet7",
         com.STDMETHOD()),
        ("GetSystemFontCollection7",
         com.STDMETHOD()),
    ]

IID_IDWriteFactory7 = com.GUID(0x35d0e0b3, 0x9076, 0x4d2e, 0xa0,0x16, 0xa9,0x1b,0x56,0x8a,0x06,0xb4)


DWriteCreateFactory = dwrite_lib.DWriteCreateFactory
DWriteCreateFactory.restype = HRESULT
DWriteCreateFactory.argtypes = [DWRITE_FACTORY_TYPE, com.REFIID, POINTER(com.pIUnknown)]


# ---- COM Interface implementations.
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

    def GenerateResults(self, analyzer: IDWriteTextAnalyzer, text: c_wchar_p, text_length: int) -> None:
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
        buffer = (ctypes.c_ubyte * len(fragment)).from_buffer(bytearray(fragment))
        ptr = ctypes.cast(buffer, c_void_p)

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
        return com.E_NOTIMPL


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
        self.factory = ctypes.cast(factory, IDWriteFactory)
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
