from ctypes import *

import pyglet.lib


_lib = pyglet.lib.load_library('xkbcommon')


class c_void(Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', c_int)]


class struct_xkb_context(Structure):
    __slots__ = [
    ]


struct_xkb_context._fields_ = [
    ('_opaque_struct', c_int)
]


class struct_xkb_keymap(Structure):
    __slots__ = [
    ]


struct_xkb_keymap._fields_ = [
    ('_opaque_struct', c_int)
]


class struct_xkb_rule_names(Structure):
    _fields_ = [
        ('rules', c_char_p),
        ('model', c_char_p),
        ('layout', c_char_p),
        ('variant', c_char_p),
        ('options', c_char_p),
    ]


class struct_xkb_state(Structure):
    __slots__ = [
    ]


struct_xkb_state._fields_ = [
    ('_opaque_struct', c_int)
]


class struct__IO_FILE(Structure):
    __slots__ = [
    ]


struct__IO_FILE._fields_ = [
    ('_opaque_struct', c_int)
]

XKB_CONTEXT_NO_FLAGS = 0
XKB_CONTEXT_NO_DEFAULT_INCLUDES = (1 << 0)
XKB_CONTEXT_NO_ENVIRONMENT_NAMES = (1 << 1)

XKB_KEYMAP_COMPILE_NO_FLAGS = 0
XKB_KEYMAP_FORMAT_TEXT_V1 = 1

xkb_keycode_t = c_uint32  # /usr/include/xkbcommon/xkbcommon.h:165
xkb_keysym_t = c_uint32  # /usr/include/xkbcommon/xkbcommon.h:195
xkb_layout_index_t = c_uint32  # /usr/include/xkbcommon/xkbcommon.h:224
xkb_layout_mask_t = c_uint32  # /usr/include/xkbcommon/xkbcommon.h:226
xkb_level_index_t = c_uint32  # /usr/include/xkbcommon/xkbcommon.h:240
xkb_mod_index_t = c_uint32  # /usr/include/xkbcommon/xkbcommon.h:265
xkb_mod_mask_t = c_uint32  # /usr/include/xkbcommon/xkbcommon.h:267
xkb_led_index_t = c_uint32  # /usr/include/xkbcommon/xkbcommon.h:294
xkb_led_mask_t = c_uint32  # /usr/include/xkbcommon/xkbcommon.h:296
XKB_KEYCODE_INVALID = 4294967295  # /usr/include/xkbcommon/xkbcommon.h:298
XKB_LAYOUT_INVALID = 4294967295  # /usr/include/xkbcommon/xkbcommon.h:299
XKB_LEVEL_INVALID = 4294967295  # /usr/include/xkbcommon/xkbcommon.h:300
XKB_MOD_INVALID = 4294967295  # /usr/include/xkbcommon/xkbcommon.h:301
XKB_LED_INVALID = 4294967295  # /usr/include/xkbcommon/xkbcommon.h:302
XKB_KEYCODE_MAX = 4294967294  # /usr/include/xkbcommon/xkbcommon.h:304
# /usr/include/xkbcommon/xkbcommon.h:438
xkb_keysym_get_name = _lib.xkb_keysym_get_name
xkb_keysym_get_name.restype = c_int
xkb_keysym_get_name.argtypes = [xkb_keysym_t, c_char_p, c_size_t]

enum_xkb_keysym_flags = c_int
# /usr/include/xkbcommon/xkbcommon.h:472
xkb_keysym_from_name = _lib.xkb_keysym_from_name
xkb_keysym_from_name.restype = xkb_keysym_t
xkb_keysym_from_name.argtypes = [c_char_p, enum_xkb_keysym_flags]

# /usr/include/xkbcommon/xkbcommon.h:491
xkb_keysym_to_utf8 = _lib.xkb_keysym_to_utf8
xkb_keysym_to_utf8.restype = c_int
xkb_keysym_to_utf8.argtypes = [xkb_keysym_t, c_char_p, c_size_t]

# /usr/include/xkbcommon/xkbcommon.h:506
xkb_keysym_to_utf32 = _lib.xkb_keysym_to_utf32
xkb_keysym_to_utf32.restype = c_uint32
xkb_keysym_to_utf32.argtypes = [xkb_keysym_t]

# /usr/include/xkbcommon/xkbcommon.h:529
xkb_utf32_to_keysym = _lib.xkb_utf32_to_keysym
xkb_utf32_to_keysym.restype = xkb_keysym_t
xkb_utf32_to_keysym.argtypes = [c_uint32]

# /usr/include/xkbcommon/xkbcommon.h:540
xkb_keysym_to_upper = _lib.xkb_keysym_to_upper
xkb_keysym_to_upper.restype = xkb_keysym_t
xkb_keysym_to_upper.argtypes = [xkb_keysym_t]

# /usr/include/xkbcommon/xkbcommon.h:549
xkb_keysym_to_lower = _lib.xkb_keysym_to_lower
xkb_keysym_to_lower.restype = xkb_keysym_t
xkb_keysym_to_lower.argtypes = [xkb_keysym_t]

enum_xkb_context_flags = c_int
# /usr/include/xkbcommon/xkbcommon.h:597
xkb_context_new = _lib.xkb_context_new
xkb_context_new.restype = POINTER(struct_xkb_context)
xkb_context_new.argtypes = [enum_xkb_context_flags]

# /usr/include/xkbcommon/xkbcommon.h:607
xkb_context_ref = _lib.xkb_context_ref
xkb_context_ref.restype = POINTER(struct_xkb_context)
xkb_context_ref.argtypes = [POINTER(struct_xkb_context)]

# /usr/include/xkbcommon/xkbcommon.h:618
xkb_context_unref = _lib.xkb_context_unref
xkb_context_unref.restype = None
xkb_context_unref.argtypes = [POINTER(struct_xkb_context)]

# /usr/include/xkbcommon/xkbcommon.h:629
xkb_context_set_user_data = _lib.xkb_context_set_user_data
xkb_context_set_user_data.restype = None
xkb_context_set_user_data.argtypes = [POINTER(struct_xkb_context), POINTER(None)]

# /usr/include/xkbcommon/xkbcommon.h:642
xkb_context_get_user_data = _lib.xkb_context_get_user_data
xkb_context_get_user_data.restype = POINTER(c_void)
xkb_context_get_user_data.argtypes = [POINTER(struct_xkb_context)]

# /usr/include/xkbcommon/xkbcommon.h:677
xkb_context_include_path_append = _lib.xkb_context_include_path_append
xkb_context_include_path_append.restype = c_int
xkb_context_include_path_append.argtypes = [POINTER(struct_xkb_context), c_char_p]

# /usr/include/xkbcommon/xkbcommon.h:687
xkb_context_include_path_append_default = _lib.xkb_context_include_path_append_default
xkb_context_include_path_append_default.restype = c_int
xkb_context_include_path_append_default.argtypes = [POINTER(struct_xkb_context)]

# /usr/include/xkbcommon/xkbcommon.h:700
xkb_context_include_path_reset_defaults = _lib.xkb_context_include_path_reset_defaults
xkb_context_include_path_reset_defaults.restype = c_int
xkb_context_include_path_reset_defaults.argtypes = [POINTER(struct_xkb_context)]

# /usr/include/xkbcommon/xkbcommon.h:708
xkb_context_include_path_clear = _lib.xkb_context_include_path_clear
xkb_context_include_path_clear.restype = None
xkb_context_include_path_clear.argtypes = [POINTER(struct_xkb_context)]

# /usr/include/xkbcommon/xkbcommon.h:716
xkb_context_num_include_paths = _lib.xkb_context_num_include_paths
xkb_context_num_include_paths.restype = c_uint
xkb_context_num_include_paths.argtypes = [POINTER(struct_xkb_context)]

# /usr/include/xkbcommon/xkbcommon.h:726
xkb_context_include_path_get = _lib.xkb_context_include_path_get
xkb_context_include_path_get.restype = c_char_p
xkb_context_include_path_get.argtypes = [POINTER(struct_xkb_context), c_uint]

enum_xkb_log_level = c_int
# /usr/include/xkbcommon/xkbcommon.h:761
xkb_context_set_log_level = _lib.xkb_context_set_log_level
xkb_context_set_log_level.restype = None
xkb_context_set_log_level.argtypes = [POINTER(struct_xkb_context), enum_xkb_log_level]

# /usr/include/xkbcommon/xkbcommon.h:770
xkb_context_get_log_level = _lib.xkb_context_get_log_level
xkb_context_get_log_level.restype = enum_xkb_log_level
xkb_context_get_log_level.argtypes = [POINTER(struct_xkb_context)]

# /usr/include/xkbcommon/xkbcommon.h:792
xkb_context_set_log_verbosity = _lib.xkb_context_set_log_verbosity
xkb_context_set_log_verbosity.restype = None
xkb_context_set_log_verbosity.argtypes = [POINTER(struct_xkb_context), c_int]

# /usr/include/xkbcommon/xkbcommon.h:800
xkb_context_get_log_verbosity = _lib.xkb_context_get_log_verbosity
xkb_context_get_log_verbosity.restype = c_int
xkb_context_get_log_verbosity.argtypes = [POINTER(struct_xkb_context)]

enum_xkb_keymap_compile_flags = c_int
# /usr/include/xkbcommon/xkbcommon.h:859
xkb_keymap_new_from_names = _lib.xkb_keymap_new_from_names
xkb_keymap_new_from_names.restype = POINTER(struct_xkb_keymap)
xkb_keymap_new_from_names.argtypes = [POINTER(struct_xkb_context), POINTER(struct_xkb_rule_names),
                                      enum_xkb_keymap_compile_flags]

FILE = struct__IO_FILE  # /usr/include/bits/types/FILE.h:7
enum_xkb_keymap_format = c_int
# /usr/include/xkbcommon/xkbcommon.h:888
xkb_keymap_new_from_file = _lib.xkb_keymap_new_from_file
xkb_keymap_new_from_file.restype = POINTER(struct_xkb_keymap)
xkb_keymap_new_from_file.argtypes = [POINTER(struct_xkb_context), POINTER(FILE), enum_xkb_keymap_format,
                                     enum_xkb_keymap_compile_flags]

# /usr/include/xkbcommon/xkbcommon.h:902
xkb_keymap_new_from_string = _lib.xkb_keymap_new_from_string
xkb_keymap_new_from_string.restype = POINTER(struct_xkb_keymap)
xkb_keymap_new_from_string.argtypes = [POINTER(struct_xkb_context), c_char_p, enum_xkb_keymap_format,
                                       enum_xkb_keymap_compile_flags]

# /usr/include/xkbcommon/xkbcommon.h:917
xkb_keymap_new_from_buffer = _lib.xkb_keymap_new_from_buffer
xkb_keymap_new_from_buffer.restype = POINTER(struct_xkb_keymap)
xkb_keymap_new_from_buffer.argtypes = [POINTER(struct_xkb_context), c_char_p, c_size_t, enum_xkb_keymap_format,
                                       enum_xkb_keymap_compile_flags]

# /usr/include/xkbcommon/xkbcommon.h:929
xkb_keymap_ref = _lib.xkb_keymap_ref
xkb_keymap_ref.restype = POINTER(struct_xkb_keymap)
xkb_keymap_ref.argtypes = [POINTER(struct_xkb_keymap)]

# /usr/include/xkbcommon/xkbcommon.h:940
xkb_keymap_unref = _lib.xkb_keymap_unref
xkb_keymap_unref.restype = None
xkb_keymap_unref.argtypes = [POINTER(struct_xkb_keymap)]

# /usr/include/xkbcommon/xkbcommon.h:966
xkb_keymap_get_as_string = _lib.xkb_keymap_get_as_string
xkb_keymap_get_as_string.restype = c_char_p
xkb_keymap_get_as_string.argtypes = [POINTER(struct_xkb_keymap), enum_xkb_keymap_format]

# /usr/include/xkbcommon/xkbcommon.h:987
xkb_keymap_min_keycode = _lib.xkb_keymap_min_keycode
xkb_keymap_min_keycode.restype = xkb_keycode_t
xkb_keymap_min_keycode.argtypes = [POINTER(struct_xkb_keymap)]

# /usr/include/xkbcommon/xkbcommon.h:997
xkb_keymap_max_keycode = _lib.xkb_keymap_max_keycode
xkb_keymap_max_keycode.restype = xkb_keycode_t
xkb_keymap_max_keycode.argtypes = [POINTER(struct_xkb_keymap)]

xkb_keymap_key_iter_t = CFUNCTYPE(None, POINTER(struct_xkb_keymap), xkb_keycode_t, POINTER(None))

# /usr/include/xkbcommon/xkbcommon.h:1020
xkb_keymap_key_for_each = _lib.xkb_keymap_key_for_each
xkb_keymap_key_for_each.restype = None
xkb_keymap_key_for_each.argtypes = [POINTER(struct_xkb_keymap), xkb_keymap_key_iter_t, POINTER(None)]

# /usr/include/xkbcommon/xkbcommon.h:1036
xkb_keymap_key_get_name = _lib.xkb_keymap_key_get_name
xkb_keymap_key_get_name.restype = c_char_p
xkb_keymap_key_get_name.argtypes = [POINTER(struct_xkb_keymap), xkb_keycode_t]

# /usr/include/xkbcommon/xkbcommon.h:1052
xkb_keymap_key_by_name = _lib.xkb_keymap_key_by_name
xkb_keymap_key_by_name.restype = xkb_keycode_t
xkb_keymap_key_by_name.argtypes = [POINTER(struct_xkb_keymap), c_char_p]

# /usr/include/xkbcommon/xkbcommon.h:1061
xkb_keymap_num_mods = _lib.xkb_keymap_num_mods
xkb_keymap_num_mods.restype = xkb_mod_index_t
xkb_keymap_num_mods.argtypes = [POINTER(struct_xkb_keymap)]

# /usr/include/xkbcommon/xkbcommon.h:1071
xkb_keymap_mod_get_name = _lib.xkb_keymap_mod_get_name
xkb_keymap_mod_get_name.restype = c_char_p
xkb_keymap_mod_get_name.argtypes = [POINTER(struct_xkb_keymap), xkb_mod_index_t]

# /usr/include/xkbcommon/xkbcommon.h:1084
xkb_keymap_mod_get_index = _lib.xkb_keymap_mod_get_index
xkb_keymap_mod_get_index.restype = xkb_mod_index_t
xkb_keymap_mod_get_index.argtypes = [POINTER(struct_xkb_keymap), c_char_p]

# /usr/include/xkbcommon/xkbcommon.h:1093
xkb_keymap_num_layouts = _lib.xkb_keymap_num_layouts
xkb_keymap_num_layouts.restype = xkb_layout_index_t
xkb_keymap_num_layouts.argtypes = [POINTER(struct_xkb_keymap)]

# /usr/include/xkbcommon/xkbcommon.h:1105
xkb_keymap_layout_get_name = _lib.xkb_keymap_layout_get_name
xkb_keymap_layout_get_name.restype = c_char_p
xkb_keymap_layout_get_name.argtypes = [POINTER(struct_xkb_keymap), xkb_layout_index_t]

# /usr/include/xkbcommon/xkbcommon.h:1120
xkb_keymap_layout_get_index = _lib.xkb_keymap_layout_get_index
xkb_keymap_layout_get_index.restype = xkb_layout_index_t
xkb_keymap_layout_get_index.argtypes = [POINTER(struct_xkb_keymap), c_char_p]

# /usr/include/xkbcommon/xkbcommon.h:1134
xkb_keymap_num_leds = _lib.xkb_keymap_num_leds
xkb_keymap_num_leds.restype = xkb_led_index_t
xkb_keymap_num_leds.argtypes = [POINTER(struct_xkb_keymap)]

# /usr/include/xkbcommon/xkbcommon.h:1143
xkb_keymap_led_get_name = _lib.xkb_keymap_led_get_name
xkb_keymap_led_get_name.restype = c_char_p
xkb_keymap_led_get_name.argtypes = [POINTER(struct_xkb_keymap), xkb_led_index_t]

# /usr/include/xkbcommon/xkbcommon.h:1155
xkb_keymap_led_get_index = _lib.xkb_keymap_led_get_index
xkb_keymap_led_get_index.restype = xkb_led_index_t
xkb_keymap_led_get_index.argtypes = [POINTER(struct_xkb_keymap), c_char_p]

# /usr/include/xkbcommon/xkbcommon.h:1168
xkb_keymap_num_layouts_for_key = _lib.xkb_keymap_num_layouts_for_key
xkb_keymap_num_layouts_for_key.restype = xkb_layout_index_t
xkb_keymap_num_layouts_for_key.argtypes = [POINTER(struct_xkb_keymap), xkb_keycode_t]

# /usr/include/xkbcommon/xkbcommon.h:1181
xkb_keymap_num_levels_for_key = _lib.xkb_keymap_num_levels_for_key
xkb_keymap_num_levels_for_key.restype = xkb_level_index_t
xkb_keymap_num_levels_for_key.argtypes = [POINTER(struct_xkb_keymap), xkb_keycode_t, xkb_layout_index_t]

# /usr/include/xkbcommon/xkbcommon.h:1221
xkb_keymap_key_get_mods_for_level = _lib.xkb_keymap_key_get_mods_for_level
xkb_keymap_key_get_mods_for_level.restype = c_size_t
xkb_keymap_key_get_mods_for_level.argtypes = [POINTER(struct_xkb_keymap), xkb_keycode_t, xkb_layout_index_t,
                                              xkb_level_index_t, POINTER(xkb_mod_mask_t), c_size_t]

# /usr/include/xkbcommon/xkbcommon.h:1257
xkb_keymap_key_get_syms_by_level = _lib.xkb_keymap_key_get_syms_by_level
xkb_keymap_key_get_syms_by_level.restype = c_int
xkb_keymap_key_get_syms_by_level.argtypes = [POINTER(struct_xkb_keymap), xkb_keycode_t, xkb_layout_index_t,
                                             xkb_level_index_t, POINTER(POINTER(xkb_keysym_t))]

# /usr/include/xkbcommon/xkbcommon.h:1279
xkb_keymap_key_repeats = _lib.xkb_keymap_key_repeats
xkb_keymap_key_repeats.restype = c_int
xkb_keymap_key_repeats.argtypes = [POINTER(struct_xkb_keymap), xkb_keycode_t]

# /usr/include/xkbcommon/xkbcommon.h:1299
xkb_state_new = _lib.xkb_state_new
xkb_state_new.restype = POINTER(struct_xkb_state)
xkb_state_new.argtypes = [POINTER(struct_xkb_keymap)]

# /usr/include/xkbcommon/xkbcommon.h:1309
xkb_state_ref = _lib.xkb_state_ref
xkb_state_ref.restype = POINTER(struct_xkb_state)
xkb_state_ref.argtypes = [POINTER(struct_xkb_state)]

# /usr/include/xkbcommon/xkbcommon.h:1320
xkb_state_unref = _lib.xkb_state_unref
xkb_state_unref.restype = None
xkb_state_unref.argtypes = [POINTER(struct_xkb_state)]

# /usr/include/xkbcommon/xkbcommon.h:1334
xkb_state_get_keymap = _lib.xkb_state_get_keymap
xkb_state_get_keymap.restype = POINTER(struct_xkb_keymap)
xkb_state_get_keymap.argtypes = [POINTER(struct_xkb_state)]

enum_xkb_state_component = c_int
enum_xkb_key_direction = c_int

# /usr/include/xkbcommon/xkbcommon.h:1409
xkb_state_update_key = _lib.xkb_state_update_key
xkb_state_update_key.restype = enum_xkb_state_component
xkb_state_update_key.argtypes = [POINTER(struct_xkb_state), xkb_keycode_t, enum_xkb_key_direction]

# /usr/include/xkbcommon/xkbcommon.h:1440
xkb_state_update_mask = _lib.xkb_state_update_mask
xkb_state_update_mask.restype = enum_xkb_state_component
xkb_state_update_mask.argtypes = [POINTER(struct_xkb_state), xkb_mod_mask_t, xkb_mod_mask_t, xkb_mod_mask_t,
                                  xkb_layout_index_t, xkb_layout_index_t, xkb_layout_index_t]

# /usr/include/xkbcommon/xkbcommon.h:1475
xkb_state_key_get_syms = _lib.xkb_state_key_get_syms
xkb_state_key_get_syms.restype = c_int
xkb_state_key_get_syms.argtypes = [POINTER(struct_xkb_state), xkb_keycode_t, POINTER(POINTER(xkb_keysym_t))]

# /usr/include/xkbcommon/xkbcommon.h:1505
xkb_state_key_get_utf8 = _lib.xkb_state_key_get_utf8
xkb_state_key_get_utf8.restype = c_int
xkb_state_key_get_utf8.argtypes = [POINTER(struct_xkb_state), xkb_keycode_t, c_char_p, c_size_t]

# /usr/include/xkbcommon/xkbcommon.h:1522
xkb_state_key_get_utf32 = _lib.xkb_state_key_get_utf32
xkb_state_key_get_utf32.restype = c_uint32
xkb_state_key_get_utf32.argtypes = [POINTER(struct_xkb_state), xkb_keycode_t]

# /usr/include/xkbcommon/xkbcommon.h:1542
xkb_state_key_get_one_sym = _lib.xkb_state_key_get_one_sym
xkb_state_key_get_one_sym.restype = xkb_keysym_t
xkb_state_key_get_one_sym.argtypes = [POINTER(struct_xkb_state), xkb_keycode_t]

# /usr/include/xkbcommon/xkbcommon.h:1559
xkb_state_key_get_layout = _lib.xkb_state_key_get_layout
xkb_state_key_get_layout.restype = xkb_layout_index_t
xkb_state_key_get_layout.argtypes = [POINTER(struct_xkb_state), xkb_keycode_t]

# /usr/include/xkbcommon/xkbcommon.h:1584
xkb_state_key_get_level = _lib.xkb_state_key_get_level
xkb_state_key_get_level.restype = xkb_level_index_t
xkb_state_key_get_level.argtypes = [POINTER(struct_xkb_state), xkb_keycode_t, xkb_layout_index_t]

# /usr/include/xkbcommon/xkbcommon.h:1622
xkb_state_serialize_mods = _lib.xkb_state_serialize_mods
xkb_state_serialize_mods.restype = xkb_mod_mask_t
xkb_state_serialize_mods.argtypes = [POINTER(struct_xkb_state), enum_xkb_state_component]

# /usr/include/xkbcommon/xkbcommon.h:1644
xkb_state_serialize_layout = _lib.xkb_state_serialize_layout
xkb_state_serialize_layout.restype = xkb_layout_index_t
xkb_state_serialize_layout.argtypes = [POINTER(struct_xkb_state), enum_xkb_state_component]

# /usr/include/xkbcommon/xkbcommon.h:1656
xkb_state_mod_name_is_active = _lib.xkb_state_mod_name_is_active
xkb_state_mod_name_is_active.restype = c_int
xkb_state_mod_name_is_active.argtypes = [POINTER(struct_xkb_state), c_char_p, enum_xkb_state_component]

enum_xkb_state_match = c_int
# /usr/include/xkbcommon/xkbcommon.h:1677
xkb_state_mod_names_are_active = _lib.xkb_state_mod_names_are_active
xkb_state_mod_names_are_active.restype = c_int
xkb_state_mod_names_are_active.argtypes = [POINTER(struct_xkb_state), enum_xkb_state_component, enum_xkb_state_match]

# /usr/include/xkbcommon/xkbcommon.h:1691
xkb_state_mod_index_is_active = _lib.xkb_state_mod_index_is_active
xkb_state_mod_index_is_active.restype = c_int
xkb_state_mod_index_is_active.argtypes = [POINTER(struct_xkb_state), xkb_mod_index_t, enum_xkb_state_component]

# /usr/include/xkbcommon/xkbcommon.h:1712
xkb_state_mod_indices_are_active = _lib.xkb_state_mod_indices_are_active
xkb_state_mod_indices_are_active.restype = c_int
xkb_state_mod_indices_are_active.argtypes = [POINTER(struct_xkb_state), enum_xkb_state_component, enum_xkb_state_match]

enum_xkb_consumed_mode = c_int
# /usr/include/xkbcommon/xkbcommon.h:1832
xkb_state_key_get_consumed_mods2 = _lib.xkb_state_key_get_consumed_mods2
xkb_state_key_get_consumed_mods2.restype = xkb_mod_mask_t
xkb_state_key_get_consumed_mods2.argtypes = [POINTER(struct_xkb_state), xkb_keycode_t, enum_xkb_consumed_mode]

# /usr/include/xkbcommon/xkbcommon.h:1842
xkb_state_key_get_consumed_mods = _lib.xkb_state_key_get_consumed_mods
xkb_state_key_get_consumed_mods.restype = xkb_mod_mask_t
xkb_state_key_get_consumed_mods.argtypes = [POINTER(struct_xkb_state), xkb_keycode_t]

# /usr/include/xkbcommon/xkbcommon.h:1862
xkb_state_mod_index_is_consumed2 = _lib.xkb_state_mod_index_is_consumed2
xkb_state_mod_index_is_consumed2.restype = c_int
xkb_state_mod_index_is_consumed2.argtypes = [POINTER(struct_xkb_state), xkb_keycode_t, xkb_mod_index_t,
                                             enum_xkb_consumed_mode]

# /usr/include/xkbcommon/xkbcommon.h:1874
xkb_state_mod_index_is_consumed = _lib.xkb_state_mod_index_is_consumed
xkb_state_mod_index_is_consumed.restype = c_int
xkb_state_mod_index_is_consumed.argtypes = [POINTER(struct_xkb_state), xkb_keycode_t, xkb_mod_index_t]

# /usr/include/xkbcommon/xkbcommon.h:1889
xkb_state_mod_mask_remove_consumed = _lib.xkb_state_mod_mask_remove_consumed
xkb_state_mod_mask_remove_consumed.restype = xkb_mod_mask_t
xkb_state_mod_mask_remove_consumed.argtypes = [POINTER(struct_xkb_state), xkb_keycode_t, xkb_mod_mask_t]

# /usr/include/xkbcommon/xkbcommon.h:1905
xkb_state_layout_name_is_active = _lib.xkb_state_layout_name_is_active
xkb_state_layout_name_is_active.restype = c_int
xkb_state_layout_name_is_active.argtypes = [POINTER(struct_xkb_state), c_char_p, enum_xkb_state_component]

# /usr/include/xkbcommon/xkbcommon.h:1918
xkb_state_layout_index_is_active = _lib.xkb_state_layout_index_is_active
xkb_state_layout_index_is_active.restype = c_int
xkb_state_layout_index_is_active.argtypes = [POINTER(struct_xkb_state), xkb_layout_index_t, enum_xkb_state_component]

# /usr/include/xkbcommon/xkbcommon.h:1932
xkb_state_led_name_is_active = _lib.xkb_state_led_name_is_active
xkb_state_led_name_is_active.restype = c_int
xkb_state_led_name_is_active.argtypes = [POINTER(struct_xkb_state), c_char_p]

# /usr/include/xkbcommon/xkbcommon.h:1944
xkb_state_led_index_is_active = _lib.xkb_state_led_index_is_active
xkb_state_led_index_is_active.restype = c_int
xkb_state_led_index_is_active.argtypes = [POINTER(struct_xkb_state), xkb_led_index_t]
