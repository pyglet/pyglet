from __future__ import annotations

import contextlib
from ctypes import (
    CFUNCTYPE,
    POINTER,
    Structure,
    Union,
    c_char_p,
    c_int,
    c_int8,
    c_int16,
    c_int32,
    c_size_t,
    c_uint,
    c_uint8,
    c_uint16,
    c_uint32,
    c_void_p,
)

import pyglet

# Harfbuzz DLL depends on libglib and libintl (for Windows)
hb_lib = None
with contextlib.suppress(ImportError):
    hb_lib = pyglet.lib.load_library("harfbuzz", win32='libharfbuzz-0.dll', darwin='libharfbuzz.0.dylib')


HB_MEMORY_MODE_READONLY = 0  # for read-only font data

HB_DIRECTION_INVALID = 0
HB_DIRECTION_LTR = 4
HB_DIRECTION_RTL = 5
HB_DIRECTION_TTB = 6
HB_DIRECTION_BTT = 7

HB_BUFFER_CLUSTER_LEVEL_MONOTONE_GRAPHEMES = 0
HB_BUFFER_CLUSTER_LEVEL_MONOTONE_CHARACTERS = 1
HB_BUFFER_CLUSTER_LEVEL_CHARACTERS = 2
HB_BUFFER_CLUSTER_LEVEL_DEFAULT = HB_BUFFER_CLUSTER_LEVEL_MONOTONE_GRAPHEMES

HB_GLYPH_FLAG_UNSAFE_TO_BREAK = 0x00000001
HB_GLYPH_FLAG_UNSAFE_TO_CONCAT = 0x00000002
HB_GLYPH_FLAG_SAFE_TO_INSERT_TATWEEL = 0x00000004

HB_GLYPH_FLAG_DEFINED = 0x00000007  # OR of all defined flags

hb_buffer_cluster_level_t = c_uint


class hb_var_int_t(Union):
    _fields_ = [
        ("u32", c_uint32),
        ("i32", c_int32),
        ("u16", c_uint16 * 2),
        ("i16", c_int16 * 2),
        ("u8", c_uint8 * 4),
        ("i8", c_int8 * 4),
    ]


hb_codepoint_t = c_uint32
hb_mask_t = c_uint32


class hb_glyph_info_t(Structure):
    _fields_ = [
        ("codepoint", hb_codepoint_t),  # glyph index
        ("mask", hb_mask_t),
        ("cluster", c_uint32),  # index in the original text
        ("var1", hb_var_int_t),
        ("var2", hb_var_int_t)
    ]

    def __repr__(self) -> str:
        return f"hb_glyph_info_t(codepoint={self.codepoint}, cluster={self.cluster}, flag={self.mask & HB_GLYPH_FLAG_DEFINED})"


hb_position_t = c_int32


# The glyph position structure contains advances and offsets.
class hb_glyph_position_t(Structure):
    _fields_ = [
        ("x_advance", hb_position_t),  # includes kerning
        ("y_advance", hb_position_t),
        ("x_offset", hb_position_t),  # adjustments to the glyph's drawing position
        ("y_offset", hb_position_t),
        ('var', hb_var_int_t),  # Private, do not use, but must be included for proper reading.
    ]


if hb_lib:
    hb_lib.hb_blob_create.argtypes = [
        c_char_p,  # pointer to the font data  const char *data
        c_size_t,  # length of the data
        c_uint,  # memory mode (e.g., HB_MEMORY_MODE_READONLY)  hb_memory_mode_t
        c_void_p,  # user data (None here)  void *user_data
        c_void_p  # destroy callback (None here)  hb_destroy_func_t
    ]
    hb_lib.hb_blob_create.restype = c_void_p

    hb_blob_t = c_void_p
    hb_lib.hb_face_create.argtypes = [
        c_void_p,  # hb_blob_t *blob
        c_uint  # font index in the blob (usually 0)  index
    ]
    hb_lib.hb_face_create.restype = c_void_p

    hb_reference_table_func_t = CFUNCTYPE(c_void_p, c_void_p, c_uint32, c_void_p)
    hb_destroy_func_t = CFUNCTYPE(None, c_void_p)

    hb_lib.hb_face_create_for_tables.argtypes = [
        hb_reference_table_func_t,  # table func
        c_void_p,  # user data ptr
        hb_destroy_func_t  # free memory function
    ]
    hb_lib.hb_face_create_for_tables.restype = c_void_p

    hb_lib.hb_font_create.argtypes = [c_void_p]  # hb_face_t *face
    hb_lib.hb_font_create.restype = c_void_p

    hb_lib.hb_face_get_upem.argtypes = [c_void_p]  # hb_face_t *face
    hb_lib.hb_face_get_upem.restype = c_uint

    hb_lib.hb_font_set_scale.argtypes = [
        c_void_p,  # b_font_t *font
        c_int,  # x_scale
        c_int  # y_scale
    ]
    hb_lib.hb_font_set_scale.restype = None

    hb_lib.hb_buffer_create.argtypes = []
    hb_lib.hb_buffer_create.restype = c_void_p

    hb_lib.hb_buffer_add_utf8.argtypes = [
        c_void_p,  # b_buffer_t *buffer
        c_char_p,  # UTF-8 text  const char *text
        c_int,  # text length (number of bytes)
        c_uint,  # item offset (usually 0)
        c_int  # item length (often the same as text_length)
    ]
    hb_lib.hb_buffer_add_utf8.restype = None

    hb_lib.hb_buffer_set_cluster_level.argtypes = [c_void_p, hb_buffer_cluster_level_t]
    hb_lib.hb_buffer_set_cluster_level.restype = None

    hb_lib.hb_buffer_add_utf16.argtypes = [
        c_void_p,  # hb_buffer_t *buffer
        POINTER(c_uint16),  # UTF-16 text  onst char *text
        c_int,  # text length (number of bytes)
        c_uint,  # item offset (usually 0)
        c_int  # item length (often the same as text_length)
    ]
    hb_lib.hb_buffer_add_utf16.restype = None

    hb_lib.hb_buffer_add_utf32.argtypes = [
        c_void_p,  # hb_buffer_t *buffer
        POINTER(c_uint32),  # UTF-32 text  const char *text
        c_int,  # text length (number of bytes)
        c_uint,  # item offset (usually 0)
        c_int  # item length (often the same as text_length)
    ]
    hb_lib.hb_buffer_add_utf32.restype = None

    hb_lib.hb_buffer_set_direction.argtypes = [
        c_void_p,  # hb_buffer_t *buffer
        c_int  # direction (e.g., HB_DIRECTION_LTR)  hb_direction_t
    ]
    hb_lib.hb_buffer_set_direction.restype = None

    hb_lib.hb_shape.argtypes = [
        c_void_p,  # hb_font_t *font
        c_void_p,  # hb_buffer_t *buffer
        c_void_p,  # hb_feature_t *features (None if not used)
        c_uint  # number of features (0 if features is None)
    ]
    hb_lib.hb_shape.restype = None

    hb_lib.hb_buffer_guess_segment_properties.argtypes = [c_void_p]
    hb_lib.hb_buffer_guess_segment_properties.restype = None

    hb_lib.hb_buffer_get_length.argtypes = [c_void_p]  # hb_buffer_t *buffer
    hb_lib.hb_buffer_get_length.restype = c_uint

    hb_lib.hb_buffer_get_glyph_infos.argtypes = [
        c_void_p,  # hb_buffer_t *buffer,
        POINTER(c_uint)  # pointer for length (can be None)
    ]
    hb_lib.hb_buffer_get_glyph_infos.restype = POINTER(hb_glyph_info_t)

    hb_lib.hb_buffer_get_glyph_positions.argtypes = [
        c_void_p,  # hb_buffer_t *buffer
        POINTER(c_uint)  # pointer for length (can be None)
    ]
    hb_lib.hb_buffer_get_glyph_positions.restype = POINTER(hb_glyph_position_t)

    hb_lib.hb_blob_destroy.argtypes = [c_void_p]  # b_blob_t *blob)
    hb_lib.hb_blob_destroy.restype = None

    hb_lib.hb_face_destroy.argtypes = [c_void_p]  # hb_face_t *face
    hb_lib.hb_face_destroy.restype = None

    hb_lib.hb_font_destroy.argtypes = [c_void_p]  # hb_font_t *font
    hb_lib.hb_font_destroy.restype = None

    hb_lib.hb_buffer_destroy.argtypes = [c_void_p]  # hb_buffer_t *buffer
    hb_lib.hb_buffer_destroy.restype = None

    hb_lib.hb_buffer_normalize_glyphs.argtypes = [c_void_p]
    hb_lib.hb_buffer_normalize_glyphs.restype = None
