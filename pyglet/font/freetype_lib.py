from __future__ import annotations

from ctypes import (
    CFUNCTYPE,
    POINTER,
    Structure,
    Union,
    byref,
    c_byte,
    c_char,
    c_char_p,
    c_int,
    c_int16,
    c_int32,
    c_int64,
    c_long,
    c_short,
    c_size_t,
    c_ubyte,
    c_uint,
    c_uint16,
    c_uint32,
    c_uint64,
    c_ulong,
    c_ushort,
    c_void_p,
)
from typing import Any, Callable, Iterable, Sequence

import pyglet.lib

from .base import FontException

_libfreetype = pyglet.lib.load_library("freetype")

_font_data = {}


def _get_function(name: str, argtypes: Iterable[Any], rtype: Any) -> Callable:
    try:
        func = getattr(_libfreetype, name)
        func.argtypes = argtypes
        func.restype = rtype
        return func
    except AttributeError as e:
        raise ImportError(e)  # noqa: B904


FT_Byte = c_char
FT_Bytes = POINTER(FT_Byte)
FT_Char = c_byte
FT_Int = c_int
FT_UInt = c_uint
FT_Int16 = c_int16
FT_UInt16 = c_uint16
FT_Int32 = c_int32
FT_UInt32 = c_uint32
FT_Int64 = c_int64
FT_UInt64 = c_uint64
FT_Short = c_short
FT_UShort = c_ushort
FT_Long = c_long
FT_ULong = c_ulong
FT_Bool = c_char
FT_Offset = c_size_t
# FT_PtrDist = ?
FT_String = c_char
FT_String_Ptr = c_char_p
FT_Tag = FT_UInt32
FT_Error = c_int
FT_Fixed = c_long
FT_Pointer = c_void_p
FT_Pos = c_long

class TT_OS2(Structure):
    _fields_ = [
        ("version",              c_ushort),
        ("xAvgCharWidth",        c_short),
        ("usWeightClass",        c_ushort),  # This is the key field
        ("usWidthClass",         c_ushort),
        ("fsType",               c_short),
        ("ySubscriptXSize",      c_short),
        ("ySubscriptYSize",      c_short),
        ("ySubscriptXOffset",    c_short),
        ("ySubscriptYOffset",    c_short),
        ("ySuperscriptXSize",    c_short),
        ("ySuperscriptYSize",    c_short),
        ("ySuperscriptXOffset",  c_short),
        ("ySuperscriptYOffset",  c_short),
        ("yStrikeoutSize",       c_short),
        ("yStrikeoutPosition",   c_short),
        ("sFamilyClass",         c_short),
        ("panose",               c_byte * 10),
        ("ulUnicodeRange1",      c_uint),
        ("ulUnicodeRange2",      c_uint),
        ("ulUnicodeRange3",      c_uint),
        ("ulUnicodeRange4",      c_uint),
        ("achVendID",            c_char * 4),
        ("fsSelection",          c_ushort),
        ("usFirstCharIndex",     c_ushort),
        ("usLastCharIndex",      c_ushort),
        ("sTypoAscender",        c_short),
        ("sTypoDescender",       c_short),
        ("sTypoLineGap",         c_short),
        ("usWinAscent",          c_ushort),
        ("usWinDescent",         c_ushort),
        ("ulCodePageRange1",     c_uint),
        ("ulCodePageRange2",     c_uint),
    ]


class FT_Vector(Structure):
    _fields_ = [
        ("x", FT_Pos),
        ("y", FT_Pos),
    ]


class FT_BBox(Structure):
    _fields_ = [
        ("xMin", FT_Pos),
        ("yMin", FT_Pos),
        ("xMax", FT_Pos),
        ("yMax", FT_Pos),
    ]


class FT_Matrix(Structure):
    _fields_ = [
        ("xx", FT_Fixed),
        ("xy", FT_Fixed),
        ("yx", FT_Fixed),
        ("yy", FT_Fixed),
    ]


FT_FWord = c_short
FT_UFWord = c_ushort
FT_F2Dot14 = c_short


class FT_UnitVector(Structure):
    _fields_ = [
        ("x", FT_F2Dot14),
        ("y", FT_F2Dot14),
    ]


FT_F26Dot6 = c_long


class FT_Data(Structure):
    _fields_ = [
        ("pointer", POINTER(FT_Byte)),
        ("length", FT_Int),
    ]


FT_Generic_Finalizer = CFUNCTYPE(None, (c_void_p))


class FT_Generic(Structure):
    _fields_ = [
        ("data", c_void_p),
        ("finalizer", FT_Generic_Finalizer),
    ]


class FT_Bitmap(Structure):
    _fields_ = [
        ("rows", c_uint),
        ("width", c_uint),
        ("pitch", c_int),
        ("buffer", POINTER(c_ubyte)),
        ("num_grays", c_short),
        ("pixel_mode", c_ubyte),
        ("palette_mode", c_ubyte),
        ("palette", c_void_p),
    ]


FT_PIXEL_MODE_NONE = 0
FT_PIXEL_MODE_MONO = 1
FT_PIXEL_MODE_GRAY = 2
FT_PIXEL_MODE_GRAY2 = 3
FT_PIXEL_MODE_GRAY4 = 4
FT_PIXEL_MODE_LCD = 5
FT_PIXEL_MODE_LCD_V = 6
FT_PIXEL_MODE_BGRA = 7

FT_KERNING_DEFAULT = 0
FT_KERNING_UNFITTED = 1
FT_KERNING_UNSCALED = 2


class FT_LibraryRec(Structure):
    _fields_ = [
        ("dummy", c_int),
    ]

    def __del__(self) -> None:
        global _library  # noqa: PLW0603
        try:
            print("FT_LibraryRec.__del__") 
            FT_Done_FreeType(byref(self))
            _library = None
        except:  # noqa: S110, E722
            pass


FT_Library = POINTER(FT_LibraryRec)


class FT_Bitmap_Size(Structure):
    _fields_ = [
        ("height", c_ushort),
        ("width", c_ushort),
        ("size", c_long),
        ("x_ppem", c_long),
        ("y_ppem", c_long),
    ]


class FT_Glyph_Metrics(Structure):
    _fields_ = [
        ("width", FT_Pos),
        ("height", FT_Pos),

        ("horiBearingX", FT_Pos),
        ("horiBearingY", FT_Pos),
        ("horiAdvance", FT_Pos),

        ("vertBearingX", FT_Pos),
        ("vertBearingY", FT_Pos),
        ("vertAdvance", FT_Pos),
    ]

    def dump(self) -> None:
        for (name, _) in self._fields_:
            print("FT_Glyph_Metrics", name, repr(getattr(self, name))) 


FT_Glyph_Format = c_ulong


def FT_IMAGE_TAG(tag: str) -> int:  # noqa: N802
    return (ord(tag[0]) << 24) | (ord(tag[1]) << 16) | (ord(tag[2]) << 8) | ord(tag[3])


FT_GLYPH_FORMAT_NONE = 0
FT_GLYPH_FORMAT_COMPOSITE = FT_IMAGE_TAG("comp")
FT_GLYPH_FORMAT_BITMAP = FT_IMAGE_TAG("bits")
FT_GLYPH_FORMAT_OUTLINE = FT_IMAGE_TAG("outl")
FT_GLYPH_FORMAT_PLOTTER = FT_IMAGE_TAG("plot")


class FT_Outline(Structure):
    _fields_ = [
        ("n_contours", c_short),  # number of contours in glyph
        ("n_points", c_short),  # number of points in the glyph
        ("points", POINTER(FT_Vector)),  # the outline's points
        ("tags", c_char_p),  # the points flags
        ("contours", POINTER(c_short)),  # the contour end points
        ("flags", c_int),  # outline masks
    ]


FT_SubGlyph = c_void_p


class FT_GlyphSlotRec(Structure):
    _fields_ = [
        ("library", FT_Library),
        ("face", c_void_p),
        ("next", c_void_p),
        ("reserved", FT_UInt),
        ("generic", FT_Generic),

        ("metrics", FT_Glyph_Metrics),
        ("linearHoriAdvance", FT_Fixed),
        ("linearVertAdvance", FT_Fixed),
        ("advance", FT_Vector),

        ("format", FT_Glyph_Format),

        ("bitmap", FT_Bitmap),
        ("bitmap_left", FT_Int),
        ("bitmap_top", FT_Int),

        ("outline", FT_Outline),
        ("num_subglyphs", FT_UInt),
        ("subglyphs", FT_SubGlyph),

        ("control_data", c_void_p),
        ("control_len", c_long),

        ("lsb_delta", FT_Pos),
        ("rsb_delta", FT_Pos),

        ("other", c_void_p),

        ("internal", c_void_p),
    ]


FT_GlyphSlot = POINTER(FT_GlyphSlotRec)


class FT_Size_Metrics(Structure):
    _fields_ = [
        ("x_ppem", FT_UShort),  # horizontal pixels per EM
        ("y_ppem", FT_UShort),  # vertical pixels per EM

        ("x_scale", FT_Fixed),  # two scales used to convert font units
        ("y_scale", FT_Fixed),  # to 26.6 frac. pixel coordinates

        ("ascender", FT_Pos),  # ascender in 26.6 frac. pixels
        ("descender", FT_Pos),  # descender in 26.6 frac. pixels
        ("height", FT_Pos),  # text height in 26.6 frac. pixels
        ("max_advance", FT_Pos),  # max horizontal advance, in 26.6 pixels
    ]


class FT_SizeRec(Structure):
    _fields_ = [
        ("face", c_void_p),
        ("generic", FT_Generic),
        ("metrics", FT_Size_Metrics),
        ("internal", c_void_p),
    ]


class FT_StreamDesc(Union):
    _fields_ = [
        ("pointer", c_void_p),
        ("value", c_long)
    ]


FT_Stream_IoFunc = CFUNCTYPE(c_ulong, c_void_p, c_ulong, c_void_p, c_ulong)
FT_Stream_CloseFunc = CFUNCTYPE(None, c_void_p)


class FT_StreamRec(Structure):
    _fields_ = [
        ("base", POINTER(c_ubyte)),  # Pointer to raw font data
        ("size", c_ulong),  # Size of the stream
        ("pos", c_ulong),  # Current read position

        ("descriptor", FT_StreamDesc),  # File descriptor or user data
        ("pathname", FT_StreamDesc),  # Optional pathname

        ("read", FT_Stream_IoFunc),  # Read function
        ("close", FT_Stream_CloseFunc),  # Close function

        ("memory", c_void_p),  # FT_Memory pointer (memory management)
        ("cursor", POINTER(c_ubyte)),  # Current stream position
        ("limit", POINTER(c_ubyte)),  # End of stream data
    ]

FT_Stream = FT_StreamRec
FT_Size = POINTER(FT_SizeRec)


class FT_FaceRec(Structure):
    _fields_ = [
        ("num_faces", FT_Long),
        ("face_index", FT_Long),

        ("face_flags", FT_Long),
        ("style_flags", FT_Long),

        ("num_glyphs", FT_Long),

        ("family_name", FT_String_Ptr),
        ("style_name", FT_String_Ptr),

        ("num_fixed_sizes", FT_Int),
        ("available_sizes", POINTER(FT_Bitmap_Size)),

        ("num_charmaps", FT_Int),
        ("charmaps", c_void_p),

        ("generic", FT_Generic),

        ("bbox", FT_BBox),

        ("units_per_EM", FT_UShort),
        ("ascender", FT_Short),
        ("descender", FT_Short),
        ("height", FT_Short),

        ("max_advance_width", FT_Short),
        ("max_advance_height", FT_Short),

        ("underline_position", FT_Short),
        ("underline_thickness", FT_Short),

        ("glyph", FT_GlyphSlot),
        ("size", FT_Size),
        ("charmap", c_void_p),

        # Internal
        ("driver", c_void_p),
        ("memory", c_void_p),
        ("stream", POINTER(FT_Stream)),

        ("sizes_list", c_void_p),

        ("autohint", FT_Generic),
        ("extensions", c_void_p),
        ("internal", c_void_p),
    ]

    def dump(self) -> None:
        for (name, _) in self._fields_:
            print("FT_FaceRec", name, repr(getattr(self, name)))


FT_Face = POINTER(FT_FaceRec)

# face_flags values
FT_FACE_FLAG_SCALABLE          = 1 << 0   # Vector-based (TTF/OTF
FT_FACE_FLAG_FIXED_SIZES       = 1 << 1   # Has pre-rendered bitmap sizes
FT_FACE_FLAG_FIXED_WIDTH       = 1 << 2   # Monospaced font
FT_FACE_FLAG_SFNT              = 1 << 3   # SFNT-based (TrueType/OpenType/WOFF
FT_FACE_FLAG_HORIZONTAL        = 1 << 4   # Has horizontal glyph metrics
FT_FACE_FLAG_VERTICAL          = 1 << 5   # Has vertical glyph metrics
FT_FACE_FLAG_KERNING           = 1 << 6   # Supports kerning
FT_FACE_FLAG_FAST_GLYPHS       = 1 << 7   # Deprecated (No effect
FT_FACE_FLAG_MULTIPLE_MASTERS  = 1 << 8   # Supports variable fonts (GX/AAT
FT_FACE_FLAG_GLYPH_NAMES       = 1 << 9   # Has glyph names
FT_FACE_FLAG_EXTERNAL_STREAM   = 1 << 10  # Uses external stream (not file-based
FT_FACE_FLAG_HINTER            = 1 << 11  # Font has its own hinter
FT_FACE_FLAG_CID_KEYED         = 1 << 12  # CID-keyed PostScript font
FT_FACE_FLAG_TRICKY            = 1 << 13  # Requires special TrueType bytecode handling
FT_FACE_FLAG_COLOR             = 1 << 14  # Color emoji font
FT_FACE_FLAG_VARIATION         = 1 << 15  # OpenType Variable Fonts
FT_FACE_FLAG_SVG               = 1 << 16  # SVG-based color glyphs
FT_FACE_FLAG_SBIX              = 1 << 17  # sbix color glyphs
FT_FACE_FLAG_SBIX_OVERLAY      = 1 << 18  # sbix overlay support

FT_STYLE_FLAG_ITALIC = 1
FT_STYLE_FLAG_BOLD = 2

(FT_RENDER_MODE_NORMAL,
 FT_RENDER_MODE_LIGHT,
 FT_RENDER_MODE_MONO,
 FT_RENDER_MODE_LCD,
 FT_RENDER_MODE_LCD_V) = range(5)


def FT_LOAD_TARGET_(x: int) -> int:  # noqa: N802
    return (x & 15) << 16


FT_LOAD_TARGET_NORMAL = FT_LOAD_TARGET_(FT_RENDER_MODE_NORMAL)
FT_LOAD_TARGET_LIGHT = FT_LOAD_TARGET_(FT_RENDER_MODE_LIGHT)
FT_LOAD_TARGET_MONO = FT_LOAD_TARGET_(FT_RENDER_MODE_MONO)
FT_LOAD_TARGET_LCD = FT_LOAD_TARGET_(FT_RENDER_MODE_LCD)
FT_LOAD_TARGET_LCD_V = FT_LOAD_TARGET_(FT_RENDER_MODE_LCD_V)


def f16p16_to_float(value: float) -> float:
    return float(value) / (1 << 16)


def float_to_f16p16(value: float) -> float:
    return int(value * (1 << 16))


def f26p6_to_float(value: float) -> float:
    return float(value) / (1 << 6)


def float_to_f26p6(value: float) -> float:
    return int(value * (1 << 6))



_ft_errors = {
    0x00: "no error",
    0x01: "cannot open resource",
    0x02: "unknown file format",
    0x03: "broken file",
    0x04: "invalid FreeType version",
    0x05: "module version is too low",
    0x06: "invalid argument",
    0x07: "unimplemented feature",
    0x08: "broken table",
    0x09: "broken offset within table",
    0x10: "invalid glyph index",
    0x11: "invalid character code",
    0x12: "unsupported glyph image format",
    0x13: "cannot render this glyph format",
    0x14: "invalid outline",
    0x15: "invalid composite glyph",
    0x16: "too many hints",
    0x17: "invalid pixel size",
    0x20: "invalid object handle",
    0x21: "invalid library handle",
    0x22: "invalid module handle",
    0x23: "invalid face handle",
    0x24: "invalid size handle",
    0x25: "invalid glyph slot handle",
    0x26: "invalid charmap handle",
    0x27: "invalid cache manager handle",
    0x28: "invalid stream handle",
    0x30: "too many modules",
    0x31: "too many extensions",
    0x40: "out of memory",
    0x41: "unlisted object",
    0x51: "cannot open stream",
    0x52: "invalid stream seek",
    0x53: "invalid stream skip",
    0x54: "invalid stream read",
    0x55: "invalid stream operation",
    0x56: "invalid frame operation",
    0x57: "nested frame access",
    0x58: "invalid frame read",
    0x60: "raster uninitialized",
    0x61: "raster corrupted",
    0x62: "raster overflow",
    0x63: "negative height while rastering",
    0x70: "too many registered caches",
    0x80: "invalid opcode",
    0x81: "too few arguments",
    0x82: "stack overflow",
    0x83: "code overflow",
    0x84: "bad argument",
    0x85: "division by zero",
    0x86: "invalid reference",
    0x87: "found debug opcode",
    0x88: "found ENDF opcode in execution stream",
    0x89: "nested DEFS",
    0x8A: "invalid code range",
    0x8B: "execution context too long",
    0x8C: "too many function definitions",
    0x8D: "too many instruction definitions",
    0x8E: "SFNT font table missing",
    0x8F: "horizontal header (hhea, table missing",
    0x90: "locations (loca, table missing",
    0x91: "name table missing",
    0x92: "character map (cmap, table missing",
    0x93: "horizontal metrics (hmtx, table missing",
    0x94: "PostScript (post, table missing",
    0x95: "invalid horizontal metrics",
    0x96: "invalid character map (cmap, format",
    0x97: "invalid ppem value",
    0x98: "invalid vertical metrics",
    0x99: "could not find context",
    0x9A: "invalid PostScript (post, table format",
    0x9B: "invalid PostScript (post, table",
    0xA0: "opcode syntax error",
    0xA1: "argument stack underflow",
    0xA2: "ignore",
    0xB0: "`STARTFONT' field missing",
    0xB1: "`FONT' field missing",
    0xB2: "`SIZE' field missing",
    0xB3: "`CHARS' field missing",
    0xB4: "`STARTCHAR' field missing",
    0xB5: "`ENCODING' field missing",
    0xB6: "`BBX' field missing",
    0xB7: "`BBX' too big",
}


class FreeTypeError(FontException):
    def __init__(self, error_code, message):
        self.errcode = error_code
        self.message = message


def _errcheck(result: Any, func: Callable, arguments: Sequence) -> Any:
    if result != 0:
        raise FreeTypeError(result, _ft_errors.get(result, "Unknown."))

def _get_function_with_error_handling(name: str, argtypes: Iterable[Any], rtype: Any) -> Callable:
    func = _get_function(name, argtypes, rtype)
    func.errcheck = _errcheck
    func.__name__ = name
    return func


FT_LOAD_DEFAULT = 0x0  # Use default font loading behavior
FT_LOAD_NO_SCALE = (1 << 0)  # Disable scaling; use unscaled native units
FT_LOAD_NO_HINTING = (1 << 1)  # Disable font hinting (may cause blurriness at small sizes)
FT_LOAD_RENDER = (1 << 2)  # Automatically render the glyph after loading
FT_LOAD_NO_BITMAP = (1 << 3)  # Ignore bitmap strikes, force vector rendering
FT_LOAD_VERTICAL_LAYOUT = (1 << 4)  # Load glyph with vertical metrics if available
FT_LOAD_FORCE_AUTOHINT = (1 << 5)  # Force FreeType’s auto-hinter, ignoring native hints
FT_LOAD_CROP_BITMAP = (1 << 6)  # Crop bitmaps to bounding box (removes empty padding)
FT_LOAD_PEDANTIC = (1 << 7)  # Enable strict font parsing (useful for debugging malformed fonts)
FT_LOAD_IGNORE_GLOBAL_ADVANCE_WIDTH = (1 << 9)  # Ignore font-wide advance width; use glyph-specific advance
FT_LOAD_NO_RECURSE = (1 << 10)  # Load only composite glyphs, do not load sub-glyphs recursively
FT_LOAD_IGNORE_TRANSFORM = (1 << 11)  # Disable any transformations with FT_Set_Transform()
FT_LOAD_MONOCHROME = (1 << 12)  # Render glyphs in monochrome (1-bit, no anti-aliasing)
FT_LOAD_LINEAR_DESIGN = (1 << 13)  # Use linear design metrics instead of transformed metrics
FT_LOAD_SBITS_ONLY = (1 << 14)  # Load only embedded bitmap strikes (ignore vector outlines)
FT_LOAD_NO_AUTOHINT = (1 << 15)  # Disable FreeType’s auto-hinter
FT_LOAD_COLOR = (1 << 20)  # Load color emoji glyphs (e.g., sbix, CBDT/CBLC, SVG fonts)
FT_LOAD_COMPUTE_METRICS = (1 << 21)  # Compute glyph metrics even if loading only a bitmap
FT_LOAD_BITMAP_METRICS_ONLY = (1 << 22)  # Compute bitmap glyph metrics but do not load the glyph itself
FT_LOAD_NO_SVG = (1 << 24)  # Disable loading of SVG glyphs (for fonts that contain both vector and SVG glyphs)

FT_Sfnt_Tag = c_int
class FT_Sfnt_Tags:
    """SFNT table tags for use with FT_Get_Sfnt_Table."""
    HEAD  = 0
    MAXP  = 1
    OS2   = 2
    HHEA  = 3
    VHEA  = 4
    POST  = 5
    NAME  = 6
    CFF   = 7
    GASP  = 8
    PCLT  = 9


FT_Init_FreeType = _get_function_with_error_handling("FT_Init_FreeType",
                                                     [POINTER(FT_Library)], FT_Error)
FT_Done_FreeType = _get_function_with_error_handling("FT_Done_FreeType",
                                                     [FT_Library], FT_Error)

FT_New_Face = _get_function_with_error_handling("FT_New_Face",
                                                [FT_Library, c_char_p, FT_Long, POINTER(FT_Face)], FT_Error)
FT_Done_Face = _get_function_with_error_handling("FT_Done_Face",
                                                 [FT_Face], FT_Error)
FT_Reference_Face = _get_function_with_error_handling("FT_Reference_Face",
                                                      [FT_Face], FT_Error)
FT_New_Memory_Face = _get_function_with_error_handling("FT_New_Memory_Face",
                                                       [FT_Library, POINTER(FT_Byte), FT_Long, FT_Long,
                                                        POINTER(FT_Face)], FT_Error)

FT_Set_Char_Size = _get_function_with_error_handling("FT_Set_Char_Size",
                                                     [FT_Face, FT_F26Dot6, FT_F26Dot6, FT_UInt, FT_UInt], FT_Error)
FT_Set_Pixel_Sizes = _get_function_with_error_handling("FT_Set_Pixel_Sizes",
                                                       [FT_Face, FT_UInt, FT_UInt], FT_Error)
FT_Load_Glyph = _get_function_with_error_handling("FT_Load_Glyph",
                                                  [FT_Face, FT_UInt, FT_Int32], FT_Error)
FT_Get_Char_Index = _get_function("FT_Get_Char_Index",
                                                      [FT_Face, FT_ULong], FT_UInt)
FT_Load_Char = _get_function_with_error_handling("FT_Load_Char",
                                                 [FT_Face, FT_ULong, FT_Int32], FT_Error)
FT_Get_Kerning = _get_function_with_error_handling("FT_Get_Kerning",
                                                   [FT_Face, FT_UInt, FT_UInt, FT_UInt, POINTER(FT_Vector)], FT_Error)

FT_Get_Sfnt_Table = _get_function("FT_Get_Sfnt_Table", [FT_Face, FT_Sfnt_Tag], c_void_p)

try:
    FT_Select_Size = _get_function_with_error_handling("FT_Select_Size", [FT_Face, FT_Int], FT_Error)
except ImportError:
    FT_Select_Size = None

# SFNT interface

class FT_SfntName(Structure):
    _fields_ = [
        ("platform_id", FT_UShort),
        ("encoding_id", FT_UShort),
        ("language_id", FT_UShort),
        ("name_id", FT_UShort),
        ("string", POINTER(FT_Byte)),
        ("string_len", FT_UInt),
    ]


FT_Get_Sfnt_Name_Count = _get_function("FT_Get_Sfnt_Name_Count",
                                       [FT_Face], FT_UInt)
FT_Get_Sfnt_Name = _get_function_with_error_handling("FT_Get_Sfnt_Name",
                                                     [FT_Face, FT_UInt, POINTER(FT_SfntName)], FT_Error)

TT_PLATFORM_MICROSOFT = 3
TT_MS_ID_UNICODE_CS = 1
TT_NAME_ID_COPYRIGHT = 0
TT_NAME_ID_FONT_FAMILY = 1
TT_NAME_ID_FONT_SUBFAMILY = 2
TT_NAME_ID_UNIQUE_ID = 3
TT_NAME_ID_FULL_NAME = 4
TT_NAME_ID_VERSION_STRING = 5
TT_NAME_ID_PS_NAME = 6
TT_NAME_ID_TRADEMARK = 7
TT_NAME_ID_MANUFACTURER = 8
TT_NAME_ID_DESIGNER = 9
TT_NAME_ID_DESCRIPTION = 10
TT_NAME_ID_VENDOR_URL = 11
TT_NAME_ID_DESIGNER_URL = 12
TT_NAME_ID_LICENSE = 13
TT_NAME_ID_LICENSE_URL = 14
TT_NAME_ID_PREFERRED_FAMILY = 16
TT_NAME_ID_PREFERRED_SUBFAMILY = 17
TT_NAME_ID_MAC_FULL_NAME = 18
TT_NAME_ID_CID_FINDFONT_NAME = 20

_library = None


def ft_get_library() -> FT_Library:
    global _library  # noqa: PLW0603
    if not _library:
        _library = FT_Library()
        error = FT_Init_FreeType(byref(_library))
        if error:
            msg = "an error occurred during library initialization"
            raise FontException(msg, error)
    return _library
