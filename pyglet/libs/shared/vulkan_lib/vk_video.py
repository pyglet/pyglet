#
# Vulkan wrapper generated from Vulkan headers
#
from typing import Any
from ctypes import c_int, c_int8, c_uint8, c_int16, c_uint16, c_int32, c_uint32, c_int64, c_uint64, c_size_t, c_float, c_double, c_char, c_char_p, c_void_p, POINTER, Structure, Union, cast, CFUNCTYPE
from platform import system

from . import define_struct

def VK_MAKE_VIDEO_STD_VERSION(major: int, minor: int, patch: int) -> int:
    """Constructs a Vulkan video standard version from major, minor, and patch versions.

    Args:
        major: Major version.
        minor: Minor version.
        patch: Patch version.

    Returns:
        The 32-bit packed version number.
    """
    return ((major << 22) | (minor << 12) | patch)


# ---- header: vulkan_video_codec_av1std.h
VULKAN_VIDEO_CODEC_AV1STD_H_: int = 1

STD_VIDEO_AV1_NUM_REF_FRAMES: int = 8
STD_VIDEO_AV1_REFS_PER_FRAME: int = 7
STD_VIDEO_AV1_TOTAL_REFS_PER_FRAME: int = 8
STD_VIDEO_AV1_MAX_TILE_COLS: int = 64
STD_VIDEO_AV1_MAX_TILE_ROWS: int = 64
STD_VIDEO_AV1_MAX_SEGMENTS: int = 8
STD_VIDEO_AV1_SEG_LVL_MAX: int = 8
STD_VIDEO_AV1_PRIMARY_REF_NONE: int = 7
STD_VIDEO_AV1_SELECT_INTEGER_MV: int = 2
STD_VIDEO_AV1_SELECT_SCREEN_CONTENT_TOOLS: int = 2
STD_VIDEO_AV1_SKIP_MODE_FRAMES: int = 2
STD_VIDEO_AV1_MAX_LOOP_FILTER_STRENGTHS: int = 4
STD_VIDEO_AV1_LOOP_FILTER_ADJUSTMENTS: int = 2
STD_VIDEO_AV1_MAX_CDEF_FILTER_STRENGTHS: int = 8
STD_VIDEO_AV1_MAX_NUM_PLANES: int = 3
STD_VIDEO_AV1_GLOBAL_MOTION_PARAMS: int = 6
STD_VIDEO_AV1_MAX_NUM_Y_POINTS: int = 14
STD_VIDEO_AV1_MAX_NUM_CB_POINTS: int = 10
STD_VIDEO_AV1_MAX_NUM_CR_POINTS: int = 10
STD_VIDEO_AV1_MAX_NUM_POS_LUMA: int = 24
STD_VIDEO_AV1_MAX_NUM_POS_CHROMA: int = 25

StdVideoAV1Profile = c_int32
STD_VIDEO_AV1_PROFILE_MAIN: int = 0
STD_VIDEO_AV1_PROFILE_HIGH: int = 1
STD_VIDEO_AV1_PROFILE_PROFESSIONAL: int = 2
STD_VIDEO_AV1_PROFILE_INVALID: int = 0x7FFFFFFF
STD_VIDEO_AV1_PROFILE_MAX_ENUM: int = 0x7FFFFFFF

StdVideoAV1Level = c_int32
STD_VIDEO_AV1_LEVEL_2_0: int = 0
STD_VIDEO_AV1_LEVEL_2_1: int = 1
STD_VIDEO_AV1_LEVEL_2_2: int = 2
STD_VIDEO_AV1_LEVEL_2_3: int = 3
STD_VIDEO_AV1_LEVEL_3_0: int = 4
STD_VIDEO_AV1_LEVEL_3_1: int = 5
STD_VIDEO_AV1_LEVEL_3_2: int = 6
STD_VIDEO_AV1_LEVEL_3_3: int = 7
STD_VIDEO_AV1_LEVEL_4_0: int = 8
STD_VIDEO_AV1_LEVEL_4_1: int = 9
STD_VIDEO_AV1_LEVEL_4_2: int = 10
STD_VIDEO_AV1_LEVEL_4_3: int = 11
STD_VIDEO_AV1_LEVEL_5_0: int = 12
STD_VIDEO_AV1_LEVEL_5_1: int = 13
STD_VIDEO_AV1_LEVEL_5_2: int = 14
STD_VIDEO_AV1_LEVEL_5_3: int = 15
STD_VIDEO_AV1_LEVEL_6_0: int = 16
STD_VIDEO_AV1_LEVEL_6_1: int = 17
STD_VIDEO_AV1_LEVEL_6_2: int = 18
STD_VIDEO_AV1_LEVEL_6_3: int = 19
STD_VIDEO_AV1_LEVEL_7_0: int = 20
STD_VIDEO_AV1_LEVEL_7_1: int = 21
STD_VIDEO_AV1_LEVEL_7_2: int = 22
STD_VIDEO_AV1_LEVEL_7_3: int = 23
STD_VIDEO_AV1_LEVEL_INVALID: int = 0x7FFFFFFF
STD_VIDEO_AV1_LEVEL_MAX_ENUM: int = 0x7FFFFFFF

StdVideoAV1FrameType = c_int32
STD_VIDEO_AV1_FRAME_TYPE_KEY: int = 0
STD_VIDEO_AV1_FRAME_TYPE_INTER: int = 1
STD_VIDEO_AV1_FRAME_TYPE_INTRA_ONLY: int = 2
STD_VIDEO_AV1_FRAME_TYPE_SWITCH: int = 3
STD_VIDEO_AV1_FRAME_TYPE_INVALID: int = 0x7FFFFFFF
STD_VIDEO_AV1_FRAME_TYPE_MAX_ENUM: int = 0x7FFFFFFF

StdVideoAV1ReferenceName = c_int32
STD_VIDEO_AV1_REFERENCE_NAME_INTRA_FRAME: int = 0
STD_VIDEO_AV1_REFERENCE_NAME_LAST_FRAME: int = 1
STD_VIDEO_AV1_REFERENCE_NAME_LAST2_FRAME: int = 2
STD_VIDEO_AV1_REFERENCE_NAME_LAST3_FRAME: int = 3
STD_VIDEO_AV1_REFERENCE_NAME_GOLDEN_FRAME: int = 4
STD_VIDEO_AV1_REFERENCE_NAME_BWDREF_FRAME: int = 5
STD_VIDEO_AV1_REFERENCE_NAME_ALTREF2_FRAME: int = 6
STD_VIDEO_AV1_REFERENCE_NAME_ALTREF_FRAME: int = 7
STD_VIDEO_AV1_REFERENCE_NAME_INVALID: int = 0x7FFFFFFF
STD_VIDEO_AV1_REFERENCE_NAME_MAX_ENUM: int = 0x7FFFFFFF

StdVideoAV1InterpolationFilter = c_int32
STD_VIDEO_AV1_INTERPOLATION_FILTER_EIGHTTAP: int = 0
STD_VIDEO_AV1_INTERPOLATION_FILTER_EIGHTTAP_SMOOTH: int = 1
STD_VIDEO_AV1_INTERPOLATION_FILTER_EIGHTTAP_SHARP: int = 2
STD_VIDEO_AV1_INTERPOLATION_FILTER_BILINEAR: int = 3
STD_VIDEO_AV1_INTERPOLATION_FILTER_SWITCHABLE: int = 4
STD_VIDEO_AV1_INTERPOLATION_FILTER_INVALID: int = 0x7FFFFFFF
STD_VIDEO_AV1_INTERPOLATION_FILTER_MAX_ENUM: int = 0x7FFFFFFF

StdVideoAV1TxMode = c_int32
STD_VIDEO_AV1_TX_MODE_ONLY_4X4: int = 0
STD_VIDEO_AV1_TX_MODE_LARGEST: int = 1
STD_VIDEO_AV1_TX_MODE_SELECT: int = 2
STD_VIDEO_AV1_TX_MODE_INVALID: int = 0x7FFFFFFF
STD_VIDEO_AV1_TX_MODE_MAX_ENUM: int = 0x7FFFFFFF

StdVideoAV1FrameRestorationType = c_int32
STD_VIDEO_AV1_FRAME_RESTORATION_TYPE_NONE: int = 0
STD_VIDEO_AV1_FRAME_RESTORATION_TYPE_WIENER: int = 1
STD_VIDEO_AV1_FRAME_RESTORATION_TYPE_SGRPROJ: int = 2
STD_VIDEO_AV1_FRAME_RESTORATION_TYPE_SWITCHABLE: int = 3
STD_VIDEO_AV1_FRAME_RESTORATION_TYPE_INVALID: int = 0x7FFFFFFF
STD_VIDEO_AV1_FRAME_RESTORATION_TYPE_MAX_ENUM: int = 0x7FFFFFFF

StdVideoAV1ColorPrimaries = c_int32
STD_VIDEO_AV1_COLOR_PRIMARIES_BT_709: int = 1
STD_VIDEO_AV1_COLOR_PRIMARIES_BT_UNSPECIFIED: int = 2
STD_VIDEO_AV1_COLOR_PRIMARIES_BT_470_M: int = 4
STD_VIDEO_AV1_COLOR_PRIMARIES_BT_470_B_G: int = 5
STD_VIDEO_AV1_COLOR_PRIMARIES_BT_601: int = 6
STD_VIDEO_AV1_COLOR_PRIMARIES_SMPTE_240: int = 7
STD_VIDEO_AV1_COLOR_PRIMARIES_GENERIC_FILM: int = 8
STD_VIDEO_AV1_COLOR_PRIMARIES_BT_2020: int = 9
STD_VIDEO_AV1_COLOR_PRIMARIES_XYZ: int = 10
STD_VIDEO_AV1_COLOR_PRIMARIES_SMPTE_431: int = 11
STD_VIDEO_AV1_COLOR_PRIMARIES_SMPTE_432: int = 12
STD_VIDEO_AV1_COLOR_PRIMARIES_EBU_3213: int = 22
STD_VIDEO_AV1_COLOR_PRIMARIES_INVALID: int = 0x7FFFFFFF
STD_VIDEO_AV1_COLOR_PRIMARIES_MAX_ENUM: int = 0x7FFFFFFF

StdVideoAV1TransferCharacteristics = c_int32
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_RESERVED_0: int = 0
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_BT_709: int = 1
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_UNSPECIFIED: int = 2
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_RESERVED_3: int = 3
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_BT_470_M: int = 4
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_BT_470_B_G: int = 5
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_BT_601: int = 6
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_SMPTE_240: int = 7
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_LINEAR: int = 8
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_LOG_100: int = 9
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_LOG_100_SQRT10: int = 10
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_IEC_61966: int = 11
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_BT_1361: int = 12
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_SRGB: int = 13
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_BT_2020_10_BIT: int = 14
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_BT_2020_12_BIT: int = 15
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_SMPTE_2084: int = 16
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_SMPTE_428: int = 17
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_HLG: int = 18
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_INVALID: int = 0x7FFFFFFF
STD_VIDEO_AV1_TRANSFER_CHARACTERISTICS_MAX_ENUM: int = 0x7FFFFFFF

StdVideoAV1MatrixCoefficients = c_int32
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_IDENTITY: int = 0
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_BT_709: int = 1
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_UNSPECIFIED: int = 2
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_RESERVED_3: int = 3
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_FCC: int = 4
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_BT_470_B_G: int = 5
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_BT_601: int = 6
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_SMPTE_240: int = 7
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_SMPTE_YCGCO: int = 8
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_BT_2020_NCL: int = 9
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_BT_2020_CL: int = 10
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_SMPTE_2085: int = 11
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_CHROMAT_NCL: int = 12
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_CHROMAT_CL: int = 13
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_ICTCP: int = 14
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_INVALID: int = 0x7FFFFFFF
STD_VIDEO_AV1_MATRIX_COEFFICIENTS_MAX_ENUM: int = 0x7FFFFFFF

StdVideoAV1ChromaSamplePosition = c_int32
STD_VIDEO_AV1_CHROMA_SAMPLE_POSITION_UNKNOWN: int = 0
STD_VIDEO_AV1_CHROMA_SAMPLE_POSITION_VERTICAL: int = 1
STD_VIDEO_AV1_CHROMA_SAMPLE_POSITION_COLOCATED: int = 2
STD_VIDEO_AV1_CHROMA_SAMPLE_POSITION_RESERVED: int = 3
STD_VIDEO_AV1_CHROMA_SAMPLE_POSITION_INVALID: int = 0x7FFFFFFF
STD_VIDEO_AV1_CHROMA_SAMPLE_POSITION_MAX_ENUM: int = 0x7FFFFFFF
StdVideoAV1ColorConfigFlags = define_struct('StdVideoAV1ColorConfigFlags',
    ('mono_chrome', c_uint32, 1),
    ('color_range', c_uint32, 1),
    ('separate_uv_delta_q', c_uint32, 1),
    ('color_description_present_flag', c_uint32, 1),
    ('reserved', c_uint32, 28),
)

StdVideoAV1ColorConfig = define_struct('StdVideoAV1ColorConfig',
    ('flags', StdVideoAV1ColorConfigFlags),
    ('BitDepth', c_uint8),
    ('subsampling_x', c_uint8),
    ('subsampling_y', c_uint8),
    ('reserved1', c_uint8),
    ('color_primaries', StdVideoAV1ColorPrimaries),
    ('transfer_characteristics', StdVideoAV1TransferCharacteristics),
    ('matrix_coefficients', StdVideoAV1MatrixCoefficients),
    ('chroma_sample_position', StdVideoAV1ChromaSamplePosition),
)

StdVideoAV1TimingInfoFlags = define_struct('StdVideoAV1TimingInfoFlags',
    ('equal_picture_interval', c_uint32, 1),
    ('reserved', c_uint32, 31),
)

StdVideoAV1TimingInfo = define_struct('StdVideoAV1TimingInfo',
    ('flags', StdVideoAV1TimingInfoFlags),
    ('num_units_in_display_tick', c_uint32),
    ('time_scale', c_uint32),
    ('num_ticks_per_picture_minus_1', c_uint32),
)

StdVideoAV1LoopFilterFlags = define_struct('StdVideoAV1LoopFilterFlags',
    ('loop_filter_delta_enabled', c_uint32, 1),
    ('loop_filter_delta_update', c_uint32, 1),
    ('reserved', c_uint32, 30),
)

StdVideoAV1LoopFilter = define_struct('StdVideoAV1LoopFilter',
    ('flags', StdVideoAV1LoopFilterFlags),
    ('loop_filter_level', c_uint8 * STD_VIDEO_AV1_MAX_LOOP_FILTER_STRENGTHS),
    ('loop_filter_sharpness', c_uint8),
    ('update_ref_delta', c_uint8),
    ('loop_filter_ref_deltas', c_int8 * STD_VIDEO_AV1_TOTAL_REFS_PER_FRAME),
    ('update_mode_delta', c_uint8),
    ('loop_filter_mode_deltas', c_int8 * STD_VIDEO_AV1_LOOP_FILTER_ADJUSTMENTS),
)

StdVideoAV1QuantizationFlags = define_struct('StdVideoAV1QuantizationFlags',
    ('using_qmatrix', c_uint32, 1),
    ('diff_uv_delta', c_uint32, 1),
    ('reserved', c_uint32, 30),
)

StdVideoAV1Quantization = define_struct('StdVideoAV1Quantization',
    ('flags', StdVideoAV1QuantizationFlags),
    ('base_q_idx', c_uint8),
    ('DeltaQYDc', c_int8),
    ('DeltaQUDc', c_int8),
    ('DeltaQUAc', c_int8),
    ('DeltaQVDc', c_int8),
    ('DeltaQVAc', c_int8),
    ('qm_y', c_uint8),
    ('qm_u', c_uint8),
    ('qm_v', c_uint8),
)

StdVideoAV1Segmentation = define_struct('StdVideoAV1Segmentation',
    ('FeatureEnabled', c_uint8 * STD_VIDEO_AV1_MAX_SEGMENTS),
    ('FeatureData', c_int16 * STD_VIDEO_AV1_SEG_LVL_MAX * STD_VIDEO_AV1_MAX_SEGMENTS),
)

StdVideoAV1TileInfoFlags = define_struct('StdVideoAV1TileInfoFlags',
    ('uniform_tile_spacing_flag', c_uint32, 1),
    ('reserved', c_uint32, 31),
)

StdVideoAV1TileInfo = define_struct('StdVideoAV1TileInfo',
    ('flags', StdVideoAV1TileInfoFlags),
    ('TileCols', c_uint8),
    ('TileRows', c_uint8),
    ('context_update_tile_id', c_uint16),
    ('tile_size_bytes_minus_1', c_uint8),
    ('reserved1', c_uint8 * 7),
    ('pMiColStarts', POINTER(c_uint16)),
    ('pMiRowStarts', POINTER(c_uint16)),
    ('pWidthInSbsMinus1', POINTER(c_uint16)),
    ('pHeightInSbsMinus1', POINTER(c_uint16)),
)

StdVideoAV1CDEF = define_struct('StdVideoAV1CDEF',
    ('cdef_damping_minus_3', c_uint8),
    ('cdef_bits', c_uint8),
    ('cdef_y_pri_strength', c_uint8 * STD_VIDEO_AV1_MAX_CDEF_FILTER_STRENGTHS),
    ('cdef_y_sec_strength', c_uint8 * STD_VIDEO_AV1_MAX_CDEF_FILTER_STRENGTHS),
    ('cdef_uv_pri_strength', c_uint8 * STD_VIDEO_AV1_MAX_CDEF_FILTER_STRENGTHS),
    ('cdef_uv_sec_strength', c_uint8 * STD_VIDEO_AV1_MAX_CDEF_FILTER_STRENGTHS),
)

StdVideoAV1LoopRestoration = define_struct('StdVideoAV1LoopRestoration',
    ('FrameRestorationType', StdVideoAV1FrameRestorationType * STD_VIDEO_AV1_MAX_NUM_PLANES),
    ('LoopRestorationSize', c_uint16 * STD_VIDEO_AV1_MAX_NUM_PLANES),
)

StdVideoAV1GlobalMotion = define_struct('StdVideoAV1GlobalMotion',
    ('GmType', c_uint8 * STD_VIDEO_AV1_NUM_REF_FRAMES),
    ('gm_params', c_int32 * STD_VIDEO_AV1_GLOBAL_MOTION_PARAMS * STD_VIDEO_AV1_NUM_REF_FRAMES),
)

StdVideoAV1FilmGrainFlags = define_struct('StdVideoAV1FilmGrainFlags',
    ('chroma_scaling_from_luma', c_uint32, 1),
    ('overlap_flag', c_uint32, 1),
    ('clip_to_restricted_range', c_uint32, 1),
    ('update_grain', c_uint32, 1),
    ('reserved', c_uint32, 28),
)

StdVideoAV1FilmGrain = define_struct('StdVideoAV1FilmGrain',
    ('flags', StdVideoAV1FilmGrainFlags),
    ('grain_scaling_minus_8', c_uint8),
    ('ar_coeff_lag', c_uint8),
    ('ar_coeff_shift_minus_6', c_uint8),
    ('grain_scale_shift', c_uint8),
    ('grain_seed', c_uint16),
    ('film_grain_params_ref_idx', c_uint8),
    ('num_y_points', c_uint8),
    ('point_y_value', c_uint8 * STD_VIDEO_AV1_MAX_NUM_Y_POINTS),
    ('point_y_scaling', c_uint8 * STD_VIDEO_AV1_MAX_NUM_Y_POINTS),
    ('num_cb_points', c_uint8),
    ('point_cb_value', c_uint8 * STD_VIDEO_AV1_MAX_NUM_CB_POINTS),
    ('point_cb_scaling', c_uint8 * STD_VIDEO_AV1_MAX_NUM_CB_POINTS),
    ('num_cr_points', c_uint8),
    ('point_cr_value', c_uint8 * STD_VIDEO_AV1_MAX_NUM_CR_POINTS),
    ('point_cr_scaling', c_uint8 * STD_VIDEO_AV1_MAX_NUM_CR_POINTS),
    ('ar_coeffs_y_plus_128', c_int8 * STD_VIDEO_AV1_MAX_NUM_POS_LUMA),
    ('ar_coeffs_cb_plus_128', c_int8 * STD_VIDEO_AV1_MAX_NUM_POS_CHROMA),
    ('ar_coeffs_cr_plus_128', c_int8 * STD_VIDEO_AV1_MAX_NUM_POS_CHROMA),
    ('cb_mult', c_uint8),
    ('cb_luma_mult', c_uint8),
    ('cb_offset', c_uint16),
    ('cr_mult', c_uint8),
    ('cr_luma_mult', c_uint8),
    ('cr_offset', c_uint16),
)

StdVideoAV1SequenceHeaderFlags = define_struct('StdVideoAV1SequenceHeaderFlags',
    ('still_picture', c_uint32, 1),
    ('reduced_still_picture_header', c_uint32, 1),
    ('use_128x128_superblock', c_uint32, 1),
    ('enable_filter_intra', c_uint32, 1),
    ('enable_intra_edge_filter', c_uint32, 1),
    ('enable_interintra_compound', c_uint32, 1),
    ('enable_masked_compound', c_uint32, 1),
    ('enable_warped_motion', c_uint32, 1),
    ('enable_dual_filter', c_uint32, 1),
    ('enable_order_hint', c_uint32, 1),
    ('enable_jnt_comp', c_uint32, 1),
    ('enable_ref_frame_mvs', c_uint32, 1),
    ('frame_id_numbers_present_flag', c_uint32, 1),
    ('enable_superres', c_uint32, 1),
    ('enable_cdef', c_uint32, 1),
    ('enable_restoration', c_uint32, 1),
    ('film_grain_params_present', c_uint32, 1),
    ('timing_info_present_flag', c_uint32, 1),
    ('initial_display_delay_present_flag', c_uint32, 1),
    ('reserved', c_uint32, 13),
)

StdVideoAV1SequenceHeader = define_struct('StdVideoAV1SequenceHeader',
    ('flags', StdVideoAV1SequenceHeaderFlags),
    ('seq_profile', StdVideoAV1Profile),
    ('frame_width_bits_minus_1', c_uint8),
    ('frame_height_bits_minus_1', c_uint8),
    ('max_frame_width_minus_1', c_uint16),
    ('max_frame_height_minus_1', c_uint16),
    ('delta_frame_id_length_minus_2', c_uint8),
    ('additional_frame_id_length_minus_1', c_uint8),
    ('order_hint_bits_minus_1', c_uint8),
    ('seq_force_integer_mv', c_uint8),
    ('seq_force_screen_content_tools', c_uint8),
    ('reserved1', c_uint8 * 5),
    ('pColorConfig', POINTER(StdVideoAV1ColorConfig)),
    ('pTimingInfo', POINTER(StdVideoAV1TimingInfo)),
)

# ---- header: vulkan_video_codec_av1std_decode.h
VULKAN_VIDEO_CODEC_AV1STD_DECODE_H_: int = 1

VK_STD_VULKAN_VIDEO_CODEC_AV1_DECODE_API_VERSION_1_0_0: int = VK_MAKE_VIDEO_STD_VERSION(1, 0, 0)  # Alias or macro
VK_STD_VULKAN_VIDEO_CODEC_AV1_DECODE_SPEC_VERSION: int = VK_STD_VULKAN_VIDEO_CODEC_AV1_DECODE_API_VERSION_1_0_0  # Alias or macro
VK_STD_VULKAN_VIDEO_CODEC_AV1_DECODE_EXTENSION_NAME = "VK_STD_vulkan_video_codec_av1_decode"
StdVideoDecodeAV1PictureInfoFlags = define_struct('StdVideoDecodeAV1PictureInfoFlags',
    ('error_resilient_mode', c_uint32, 1),
    ('disable_cdf_update', c_uint32, 1),
    ('use_superres', c_uint32, 1),
    ('render_and_frame_size_different', c_uint32, 1),
    ('allow_screen_content_tools', c_uint32, 1),
    ('is_filter_switchable', c_uint32, 1),
    ('force_integer_mv', c_uint32, 1),
    ('frame_size_override_flag', c_uint32, 1),
    ('buffer_removal_time_present_flag', c_uint32, 1),
    ('allow_intrabc', c_uint32, 1),
    ('frame_refs_short_signaling', c_uint32, 1),
    ('allow_high_precision_mv', c_uint32, 1),
    ('is_motion_mode_switchable', c_uint32, 1),
    ('use_ref_frame_mvs', c_uint32, 1),
    ('disable_frame_end_update_cdf', c_uint32, 1),
    ('allow_warped_motion', c_uint32, 1),
    ('reduced_tx_set', c_uint32, 1),
    ('reference_select', c_uint32, 1),
    ('skip_mode_present', c_uint32, 1),
    ('delta_q_present', c_uint32, 1),
    ('delta_lf_present', c_uint32, 1),
    ('delta_lf_multi', c_uint32, 1),
    ('segmentation_enabled', c_uint32, 1),
    ('segmentation_update_map', c_uint32, 1),
    ('segmentation_temporal_update', c_uint32, 1),
    ('segmentation_update_data', c_uint32, 1),
    ('UsesLr', c_uint32, 1),
    ('usesChromaLr', c_uint32, 1),
    ('apply_grain', c_uint32, 1),
    ('reserved', c_uint32, 3),
)

StdVideoDecodeAV1PictureInfo = define_struct('StdVideoDecodeAV1PictureInfo',
    ('flags', StdVideoDecodeAV1PictureInfoFlags),
    ('frame_type', StdVideoAV1FrameType),
    ('current_frame_id', c_uint32),
    ('OrderHint', c_uint8),
    ('primary_ref_frame', c_uint8),
    ('refresh_frame_flags', c_uint8),
    ('reserved1', c_uint8),
    ('interpolation_filter', StdVideoAV1InterpolationFilter),
    ('TxMode', StdVideoAV1TxMode),
    ('delta_q_res', c_uint8),
    ('delta_lf_res', c_uint8),
    ('SkipModeFrame', c_uint8 * STD_VIDEO_AV1_SKIP_MODE_FRAMES),
    ('coded_denom', c_uint8),
    ('reserved2', c_uint8 * 3),
    ('OrderHints', c_uint8 * STD_VIDEO_AV1_NUM_REF_FRAMES),
    ('expectedFrameId', c_uint32 * STD_VIDEO_AV1_NUM_REF_FRAMES),
    ('pTileInfo', POINTER(StdVideoAV1TileInfo)),
    ('pQuantization', POINTER(StdVideoAV1Quantization)),
    ('pSegmentation', POINTER(StdVideoAV1Segmentation)),
    ('pLoopFilter', POINTER(StdVideoAV1LoopFilter)),
    ('pCDEF', POINTER(StdVideoAV1CDEF)),
    ('pLoopRestoration', POINTER(StdVideoAV1LoopRestoration)),
    ('pGlobalMotion', POINTER(StdVideoAV1GlobalMotion)),
    ('pFilmGrain', POINTER(StdVideoAV1FilmGrain)),
)

StdVideoDecodeAV1ReferenceInfoFlags = define_struct('StdVideoDecodeAV1ReferenceInfoFlags',
    ('disable_frame_end_update_cdf', c_uint32, 1),
    ('segmentation_enabled', c_uint32, 1),
    ('reserved', c_uint32, 30),
)

StdVideoDecodeAV1ReferenceInfo = define_struct('StdVideoDecodeAV1ReferenceInfo',
    ('flags', StdVideoDecodeAV1ReferenceInfoFlags),
    ('frame_type', c_uint8),
    ('RefFrameSignBias', c_uint8),
    ('OrderHint', c_uint8),
    ('SavedOrderHints', c_uint8 * STD_VIDEO_AV1_NUM_REF_FRAMES),
)

# ---- header: vulkan_video_codec_h264std.h
VULKAN_VIDEO_CODEC_H264STD_H_: int = 1

STD_VIDEO_H264_CPB_CNT_LIST_SIZE: int = 32
STD_VIDEO_H264_SCALING_LIST_4X4_NUM_LISTS: int = 6
STD_VIDEO_H264_SCALING_LIST_4X4_NUM_ELEMENTS: int = 16
STD_VIDEO_H264_SCALING_LIST_8X8_NUM_LISTS: int = 6
STD_VIDEO_H264_SCALING_LIST_8X8_NUM_ELEMENTS: int = 64
STD_VIDEO_H264_MAX_NUM_LIST_REF: int = 32
STD_VIDEO_H264_MAX_CHROMA_PLANES: int = 2
STD_VIDEO_H264_NO_REFERENCE_PICTURE: int = 0xFF  # Alias or macro

StdVideoH264ChromaFormatIdc = c_int32
STD_VIDEO_H264_CHROMA_FORMAT_IDC_MONOCHROME: int = 0
STD_VIDEO_H264_CHROMA_FORMAT_IDC_420: int = 1
STD_VIDEO_H264_CHROMA_FORMAT_IDC_422: int = 2
STD_VIDEO_H264_CHROMA_FORMAT_IDC_444: int = 3
STD_VIDEO_H264_CHROMA_FORMAT_IDC_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_CHROMA_FORMAT_IDC_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH264ProfileIdc = c_int32
STD_VIDEO_H264_PROFILE_IDC_BASELINE: int = 66
STD_VIDEO_H264_PROFILE_IDC_MAIN: int = 77
STD_VIDEO_H264_PROFILE_IDC_HIGH: int = 100
STD_VIDEO_H264_PROFILE_IDC_HIGH_444_PREDICTIVE: int = 244
STD_VIDEO_H264_PROFILE_IDC_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_PROFILE_IDC_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH264LevelIdc = c_int32
STD_VIDEO_H264_LEVEL_IDC_1_0: int = 0
STD_VIDEO_H264_LEVEL_IDC_1_1: int = 1
STD_VIDEO_H264_LEVEL_IDC_1_2: int = 2
STD_VIDEO_H264_LEVEL_IDC_1_3: int = 3
STD_VIDEO_H264_LEVEL_IDC_2_0: int = 4
STD_VIDEO_H264_LEVEL_IDC_2_1: int = 5
STD_VIDEO_H264_LEVEL_IDC_2_2: int = 6
STD_VIDEO_H264_LEVEL_IDC_3_0: int = 7
STD_VIDEO_H264_LEVEL_IDC_3_1: int = 8
STD_VIDEO_H264_LEVEL_IDC_3_2: int = 9
STD_VIDEO_H264_LEVEL_IDC_4_0: int = 10
STD_VIDEO_H264_LEVEL_IDC_4_1: int = 11
STD_VIDEO_H264_LEVEL_IDC_4_2: int = 12
STD_VIDEO_H264_LEVEL_IDC_5_0: int = 13
STD_VIDEO_H264_LEVEL_IDC_5_1: int = 14
STD_VIDEO_H264_LEVEL_IDC_5_2: int = 15
STD_VIDEO_H264_LEVEL_IDC_6_0: int = 16
STD_VIDEO_H264_LEVEL_IDC_6_1: int = 17
STD_VIDEO_H264_LEVEL_IDC_6_2: int = 18
STD_VIDEO_H264_LEVEL_IDC_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_LEVEL_IDC_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH264PocType = c_int32
STD_VIDEO_H264_POC_TYPE_0: int = 0
STD_VIDEO_H264_POC_TYPE_1: int = 1
STD_VIDEO_H264_POC_TYPE_2: int = 2
STD_VIDEO_H264_POC_TYPE_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_POC_TYPE_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH264AspectRatioIdc = c_int32
STD_VIDEO_H264_ASPECT_RATIO_IDC_UNSPECIFIED: int = 0
STD_VIDEO_H264_ASPECT_RATIO_IDC_SQUARE: int = 1
STD_VIDEO_H264_ASPECT_RATIO_IDC_12_11: int = 2
STD_VIDEO_H264_ASPECT_RATIO_IDC_10_11: int = 3
STD_VIDEO_H264_ASPECT_RATIO_IDC_16_11: int = 4
STD_VIDEO_H264_ASPECT_RATIO_IDC_40_33: int = 5
STD_VIDEO_H264_ASPECT_RATIO_IDC_24_11: int = 6
STD_VIDEO_H264_ASPECT_RATIO_IDC_20_11: int = 7
STD_VIDEO_H264_ASPECT_RATIO_IDC_32_11: int = 8
STD_VIDEO_H264_ASPECT_RATIO_IDC_80_33: int = 9
STD_VIDEO_H264_ASPECT_RATIO_IDC_18_11: int = 10
STD_VIDEO_H264_ASPECT_RATIO_IDC_15_11: int = 11
STD_VIDEO_H264_ASPECT_RATIO_IDC_64_33: int = 12
STD_VIDEO_H264_ASPECT_RATIO_IDC_160_99: int = 13
STD_VIDEO_H264_ASPECT_RATIO_IDC_4_3: int = 14
STD_VIDEO_H264_ASPECT_RATIO_IDC_3_2: int = 15
STD_VIDEO_H264_ASPECT_RATIO_IDC_2_1: int = 16
STD_VIDEO_H264_ASPECT_RATIO_IDC_EXTENDED_SAR: int = 255
STD_VIDEO_H264_ASPECT_RATIO_IDC_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_ASPECT_RATIO_IDC_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH264WeightedBipredIdc = c_int32
STD_VIDEO_H264_WEIGHTED_BIPRED_IDC_DEFAULT: int = 0
STD_VIDEO_H264_WEIGHTED_BIPRED_IDC_EXPLICIT: int = 1
STD_VIDEO_H264_WEIGHTED_BIPRED_IDC_IMPLICIT: int = 2
STD_VIDEO_H264_WEIGHTED_BIPRED_IDC_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_WEIGHTED_BIPRED_IDC_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH264ModificationOfPicNumsIdc = c_int32
STD_VIDEO_H264_MODIFICATION_OF_PIC_NUMS_IDC_SHORT_TERM_SUBTRACT: int = 0
STD_VIDEO_H264_MODIFICATION_OF_PIC_NUMS_IDC_SHORT_TERM_ADD: int = 1
STD_VIDEO_H264_MODIFICATION_OF_PIC_NUMS_IDC_LONG_TERM: int = 2
STD_VIDEO_H264_MODIFICATION_OF_PIC_NUMS_IDC_END: int = 3
STD_VIDEO_H264_MODIFICATION_OF_PIC_NUMS_IDC_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_MODIFICATION_OF_PIC_NUMS_IDC_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH264MemMgmtControlOp = c_int32
STD_VIDEO_H264_MEM_MGMT_CONTROL_OP_END: int = 0
STD_VIDEO_H264_MEM_MGMT_CONTROL_OP_UNMARK_SHORT_TERM: int = 1
STD_VIDEO_H264_MEM_MGMT_CONTROL_OP_UNMARK_LONG_TERM: int = 2
STD_VIDEO_H264_MEM_MGMT_CONTROL_OP_MARK_LONG_TERM: int = 3
STD_VIDEO_H264_MEM_MGMT_CONTROL_OP_SET_MAX_LONG_TERM_INDEX: int = 4
STD_VIDEO_H264_MEM_MGMT_CONTROL_OP_UNMARK_ALL: int = 5
STD_VIDEO_H264_MEM_MGMT_CONTROL_OP_MARK_CURRENT_AS_LONG_TERM: int = 6
STD_VIDEO_H264_MEM_MGMT_CONTROL_OP_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_MEM_MGMT_CONTROL_OP_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH264CabacInitIdc = c_int32
STD_VIDEO_H264_CABAC_INIT_IDC_0: int = 0
STD_VIDEO_H264_CABAC_INIT_IDC_1: int = 1
STD_VIDEO_H264_CABAC_INIT_IDC_2: int = 2
STD_VIDEO_H264_CABAC_INIT_IDC_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_CABAC_INIT_IDC_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH264DisableDeblockingFilterIdc = c_int32
STD_VIDEO_H264_DISABLE_DEBLOCKING_FILTER_IDC_DISABLED: int = 0
STD_VIDEO_H264_DISABLE_DEBLOCKING_FILTER_IDC_ENABLED: int = 1
STD_VIDEO_H264_DISABLE_DEBLOCKING_FILTER_IDC_PARTIAL: int = 2
STD_VIDEO_H264_DISABLE_DEBLOCKING_FILTER_IDC_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_DISABLE_DEBLOCKING_FILTER_IDC_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH264SliceType = c_int32
STD_VIDEO_H264_SLICE_TYPE_P: int = 0
STD_VIDEO_H264_SLICE_TYPE_B: int = 1
STD_VIDEO_H264_SLICE_TYPE_I: int = 2
STD_VIDEO_H264_SLICE_TYPE_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_SLICE_TYPE_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH264PictureType = c_int32
STD_VIDEO_H264_PICTURE_TYPE_P: int = 0
STD_VIDEO_H264_PICTURE_TYPE_B: int = 1
STD_VIDEO_H264_PICTURE_TYPE_I: int = 2
STD_VIDEO_H264_PICTURE_TYPE_IDR: int = 5
STD_VIDEO_H264_PICTURE_TYPE_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_PICTURE_TYPE_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH264NonVclNaluType = c_int32
STD_VIDEO_H264_NON_VCL_NALU_TYPE_SPS: int = 0
STD_VIDEO_H264_NON_VCL_NALU_TYPE_PPS: int = 1
STD_VIDEO_H264_NON_VCL_NALU_TYPE_AUD: int = 2
STD_VIDEO_H264_NON_VCL_NALU_TYPE_PREFIX: int = 3
STD_VIDEO_H264_NON_VCL_NALU_TYPE_END_OF_SEQUENCE: int = 4
STD_VIDEO_H264_NON_VCL_NALU_TYPE_END_OF_STREAM: int = 5
STD_VIDEO_H264_NON_VCL_NALU_TYPE_PRECODED: int = 6
STD_VIDEO_H264_NON_VCL_NALU_TYPE_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H264_NON_VCL_NALU_TYPE_MAX_ENUM: int = 0x7FFFFFFF
StdVideoH264SpsVuiFlags = define_struct('StdVideoH264SpsVuiFlags',
    ('aspect_ratio_info_present_flag', c_uint32, 1),
    ('overscan_info_present_flag', c_uint32, 1),
    ('overscan_appropriate_flag', c_uint32, 1),
    ('video_signal_type_present_flag', c_uint32, 1),
    ('video_full_range_flag', c_uint32, 1),
    ('color_description_present_flag', c_uint32, 1),
    ('chroma_loc_info_present_flag', c_uint32, 1),
    ('timing_info_present_flag', c_uint32, 1),
    ('fixed_frame_rate_flag', c_uint32, 1),
    ('bitstream_restriction_flag', c_uint32, 1),
    ('nal_hrd_parameters_present_flag', c_uint32, 1),
    ('vcl_hrd_parameters_present_flag', c_uint32, 1),
)

StdVideoH264HrdParameters = define_struct('StdVideoH264HrdParameters',
    ('cpb_cnt_minus1', c_uint8),
    ('bit_rate_scale', c_uint8),
    ('cpb_size_scale', c_uint8),
    ('reserved1', c_uint8),
    ('bit_rate_value_minus1', c_uint32 * STD_VIDEO_H264_CPB_CNT_LIST_SIZE),
    ('cpb_size_value_minus1', c_uint32 * STD_VIDEO_H264_CPB_CNT_LIST_SIZE),
    ('cbr_flag', c_uint8 * STD_VIDEO_H264_CPB_CNT_LIST_SIZE),
    ('initial_cpb_removal_delay_length_minus1', c_uint32),
    ('cpb_removal_delay_length_minus1', c_uint32),
    ('dpb_output_delay_length_minus1', c_uint32),
    ('time_offset_length', c_uint32),
)

StdVideoH264SequenceParameterSetVui = define_struct('StdVideoH264SequenceParameterSetVui',
    ('flags', StdVideoH264SpsVuiFlags),
    ('aspect_ratio_idc', StdVideoH264AspectRatioIdc),
    ('sar_width', c_uint16),
    ('sar_height', c_uint16),
    ('video_format', c_uint8),
    ('colour_primaries', c_uint8),
    ('transfer_characteristics', c_uint8),
    ('matrix_coefficients', c_uint8),
    ('num_units_in_tick', c_uint32),
    ('time_scale', c_uint32),
    ('max_num_reorder_frames', c_uint8),
    ('max_dec_frame_buffering', c_uint8),
    ('chroma_sample_loc_type_top_field', c_uint8),
    ('chroma_sample_loc_type_bottom_field', c_uint8),
    ('reserved1', c_uint32),
    ('pHrdParameters', POINTER(StdVideoH264HrdParameters)),
)

StdVideoH264SpsFlags = define_struct('StdVideoH264SpsFlags',
    ('constraint_set0_flag', c_uint32, 1),
    ('constraint_set1_flag', c_uint32, 1),
    ('constraint_set2_flag', c_uint32, 1),
    ('constraint_set3_flag', c_uint32, 1),
    ('constraint_set4_flag', c_uint32, 1),
    ('constraint_set5_flag', c_uint32, 1),
    ('direct_8x8_inference_flag', c_uint32, 1),
    ('mb_adaptive_frame_field_flag', c_uint32, 1),
    ('frame_mbs_only_flag', c_uint32, 1),
    ('delta_pic_order_always_zero_flag', c_uint32, 1),
    ('separate_colour_plane_flag', c_uint32, 1),
    ('gaps_in_frame_num_value_allowed_flag', c_uint32, 1),
    ('qpprime_y_zero_transform_bypass_flag', c_uint32, 1),
    ('frame_cropping_flag', c_uint32, 1),
    ('seq_scaling_matrix_present_flag', c_uint32, 1),
    ('vui_parameters_present_flag', c_uint32, 1),
)

StdVideoH264ScalingLists = define_struct('StdVideoH264ScalingLists',
    ('scaling_list_present_mask', c_uint16),
    ('use_default_scaling_matrix_mask', c_uint16),
    ('ScalingList4x4', c_uint8 * STD_VIDEO_H264_SCALING_LIST_4X4_NUM_ELEMENTS * STD_VIDEO_H264_SCALING_LIST_4X4_NUM_LISTS),
    ('ScalingList8x8', c_uint8 * STD_VIDEO_H264_SCALING_LIST_8X8_NUM_ELEMENTS * STD_VIDEO_H264_SCALING_LIST_8X8_NUM_LISTS),
)

StdVideoH264SequenceParameterSet = define_struct('StdVideoH264SequenceParameterSet',
    ('flags', StdVideoH264SpsFlags),
    ('profile_idc', StdVideoH264ProfileIdc),
    ('level_idc', StdVideoH264LevelIdc),
    ('chroma_format_idc', StdVideoH264ChromaFormatIdc),
    ('seq_parameter_set_id', c_uint8),
    ('bit_depth_luma_minus8', c_uint8),
    ('bit_depth_chroma_minus8', c_uint8),
    ('log2_max_frame_num_minus4', c_uint8),
    ('pic_order_cnt_type', StdVideoH264PocType),
    ('offset_for_non_ref_pic', c_int32),
    ('offset_for_top_to_bottom_field', c_int32),
    ('log2_max_pic_order_cnt_lsb_minus4', c_uint8),
    ('num_ref_frames_in_pic_order_cnt_cycle', c_uint8),
    ('max_num_ref_frames', c_uint8),
    ('reserved1', c_uint8),
    ('pic_width_in_mbs_minus1', c_uint32),
    ('pic_height_in_map_units_minus1', c_uint32),
    ('frame_crop_left_offset', c_uint32),
    ('frame_crop_right_offset', c_uint32),
    ('frame_crop_top_offset', c_uint32),
    ('frame_crop_bottom_offset', c_uint32),
    ('reserved2', c_uint32),
    ('pOffsetForRefFrame', POINTER(c_int32)),
    ('pScalingLists', POINTER(StdVideoH264ScalingLists)),
    ('pSequenceParameterSetVui', POINTER(StdVideoH264SequenceParameterSetVui)),
)

StdVideoH264PpsFlags = define_struct('StdVideoH264PpsFlags',
    ('transform_8x8_mode_flag', c_uint32, 1),
    ('redundant_pic_cnt_present_flag', c_uint32, 1),
    ('constrained_intra_pred_flag', c_uint32, 1),
    ('deblocking_filter_control_present_flag', c_uint32, 1),
    ('weighted_pred_flag', c_uint32, 1),
    ('bottom_field_pic_order_in_frame_present_flag', c_uint32, 1),
    ('entropy_coding_mode_flag', c_uint32, 1),
    ('pic_scaling_matrix_present_flag', c_uint32, 1),
)

StdVideoH264PictureParameterSet = define_struct('StdVideoH264PictureParameterSet',
    ('flags', StdVideoH264PpsFlags),
    ('seq_parameter_set_id', c_uint8),
    ('pic_parameter_set_id', c_uint8),
    ('num_ref_idx_l0_default_active_minus1', c_uint8),
    ('num_ref_idx_l1_default_active_minus1', c_uint8),
    ('weighted_bipred_idc', StdVideoH264WeightedBipredIdc),
    ('pic_init_qp_minus26', c_int8),
    ('pic_init_qs_minus26', c_int8),
    ('chroma_qp_index_offset', c_int8),
    ('second_chroma_qp_index_offset', c_int8),
    ('pScalingLists', POINTER(StdVideoH264ScalingLists)),
)

# ---- header: vulkan_video_codec_h264std_decode.h
VULKAN_VIDEO_CODEC_H264STD_DECODE_H_: int = 1

VK_STD_VULKAN_VIDEO_CODEC_H264_DECODE_API_VERSION_1_0_0: int = VK_MAKE_VIDEO_STD_VERSION(1, 0, 0)  # Alias or macro
VK_STD_VULKAN_VIDEO_CODEC_H264_DECODE_SPEC_VERSION: int = VK_STD_VULKAN_VIDEO_CODEC_H264_DECODE_API_VERSION_1_0_0  # Alias or macro
VK_STD_VULKAN_VIDEO_CODEC_H264_DECODE_EXTENSION_NAME = "VK_STD_vulkan_video_codec_h264_decode"
STD_VIDEO_DECODE_H264_FIELD_ORDER_COUNT_LIST_SIZE: int = 2

StdVideoDecodeH264FieldOrderCount = c_int32
STD_VIDEO_DECODE_H264_FIELD_ORDER_COUNT_TOP: int = 0
STD_VIDEO_DECODE_H264_FIELD_ORDER_COUNT_BOTTOM: int = 1
STD_VIDEO_DECODE_H264_FIELD_ORDER_COUNT_INVALID: int = 0x7FFFFFFF
STD_VIDEO_DECODE_H264_FIELD_ORDER_COUNT_MAX_ENUM: int = 0x7FFFFFFF
StdVideoDecodeH264PictureInfoFlags = define_struct('StdVideoDecodeH264PictureInfoFlags',
    ('field_pic_flag', c_uint32, 1),
    ('is_intra', c_uint32, 1),
    ('IdrPicFlag', c_uint32, 1),
    ('bottom_field_flag', c_uint32, 1),
    ('is_reference', c_uint32, 1),
    ('complementary_field_pair', c_uint32, 1),
)

StdVideoDecodeH264PictureInfo = define_struct('StdVideoDecodeH264PictureInfo',
    ('flags', StdVideoDecodeH264PictureInfoFlags),
    ('seq_parameter_set_id', c_uint8),
    ('pic_parameter_set_id', c_uint8),
    ('reserved1', c_uint8),
    ('reserved2', c_uint8),
    ('frame_num', c_uint16),
    ('idr_pic_id', c_uint16),
    ('PicOrderCnt', c_int32 * STD_VIDEO_DECODE_H264_FIELD_ORDER_COUNT_LIST_SIZE),
)

StdVideoDecodeH264ReferenceInfoFlags = define_struct('StdVideoDecodeH264ReferenceInfoFlags',
    ('top_field_flag', c_uint32, 1),
    ('bottom_field_flag', c_uint32, 1),
    ('used_for_long_term_reference', c_uint32, 1),
    ('is_non_existing', c_uint32, 1),
)

StdVideoDecodeH264ReferenceInfo = define_struct('StdVideoDecodeH264ReferenceInfo',
    ('flags', StdVideoDecodeH264ReferenceInfoFlags),
    ('FrameNum', c_uint16),
    ('reserved', c_uint16),
    ('PicOrderCnt', c_int32 * STD_VIDEO_DECODE_H264_FIELD_ORDER_COUNT_LIST_SIZE),
)

# ---- header: vulkan_video_codec_h264std_encode.h
VULKAN_VIDEO_CODEC_H264STD_ENCODE_H_: int = 1

VK_STD_VULKAN_VIDEO_CODEC_H264_ENCODE_API_VERSION_1_0_0: int = VK_MAKE_VIDEO_STD_VERSION(1, 0, 0)  # Alias or macro
VK_STD_VULKAN_VIDEO_CODEC_H264_ENCODE_SPEC_VERSION: int = VK_STD_VULKAN_VIDEO_CODEC_H264_ENCODE_API_VERSION_1_0_0  # Alias or macro
VK_STD_VULKAN_VIDEO_CODEC_H264_ENCODE_EXTENSION_NAME = "VK_STD_vulkan_video_codec_h264_encode"
StdVideoEncodeH264WeightTableFlags = define_struct('StdVideoEncodeH264WeightTableFlags',
    ('luma_weight_l0_flag', c_uint32),
    ('chroma_weight_l0_flag', c_uint32),
    ('luma_weight_l1_flag', c_uint32),
    ('chroma_weight_l1_flag', c_uint32),
)

StdVideoEncodeH264WeightTable = define_struct('StdVideoEncodeH264WeightTable',
    ('flags', StdVideoEncodeH264WeightTableFlags),
    ('luma_log2_weight_denom', c_uint8),
    ('chroma_log2_weight_denom', c_uint8),
    ('luma_weight_l0', c_int8 * STD_VIDEO_H264_MAX_NUM_LIST_REF),
    ('luma_offset_l0', c_int8 * STD_VIDEO_H264_MAX_NUM_LIST_REF),
    ('chroma_weight_l0', c_int8 * STD_VIDEO_H264_MAX_CHROMA_PLANES * STD_VIDEO_H264_MAX_NUM_LIST_REF),
    ('chroma_offset_l0', c_int8 * STD_VIDEO_H264_MAX_CHROMA_PLANES * STD_VIDEO_H264_MAX_NUM_LIST_REF),
    ('luma_weight_l1', c_int8 * STD_VIDEO_H264_MAX_NUM_LIST_REF),
    ('luma_offset_l1', c_int8 * STD_VIDEO_H264_MAX_NUM_LIST_REF),
    ('chroma_weight_l1', c_int8 * STD_VIDEO_H264_MAX_CHROMA_PLANES * STD_VIDEO_H264_MAX_NUM_LIST_REF),
    ('chroma_offset_l1', c_int8 * STD_VIDEO_H264_MAX_CHROMA_PLANES * STD_VIDEO_H264_MAX_NUM_LIST_REF),
)

StdVideoEncodeH264SliceHeaderFlags = define_struct('StdVideoEncodeH264SliceHeaderFlags',
    ('direct_spatial_mv_pred_flag', c_uint32, 1),
    ('num_ref_idx_active_override_flag', c_uint32, 1),
    ('reserved', c_uint32, 30),
)

StdVideoEncodeH264PictureInfoFlags = define_struct('StdVideoEncodeH264PictureInfoFlags',
    ('IdrPicFlag', c_uint32, 1),
    ('is_reference', c_uint32, 1),
    ('no_output_of_prior_pics_flag', c_uint32, 1),
    ('long_term_reference_flag', c_uint32, 1),
    ('adaptive_ref_pic_marking_mode_flag', c_uint32, 1),
    ('reserved', c_uint32, 27),
)

StdVideoEncodeH264ReferenceInfoFlags = define_struct('StdVideoEncodeH264ReferenceInfoFlags',
    ('used_for_long_term_reference', c_uint32, 1),
    ('reserved', c_uint32, 31),
)

StdVideoEncodeH264ReferenceListsInfoFlags = define_struct('StdVideoEncodeH264ReferenceListsInfoFlags',
    ('ref_pic_list_modification_flag_l0', c_uint32, 1),
    ('ref_pic_list_modification_flag_l1', c_uint32, 1),
    ('reserved', c_uint32, 30),
)

StdVideoEncodeH264RefListModEntry = define_struct('StdVideoEncodeH264RefListModEntry',
    ('modification_of_pic_nums_idc', StdVideoH264ModificationOfPicNumsIdc),
    ('abs_diff_pic_num_minus1', c_uint16),
    ('long_term_pic_num', c_uint16),
)

StdVideoEncodeH264RefPicMarkingEntry = define_struct('StdVideoEncodeH264RefPicMarkingEntry',
    ('memory_management_control_operation', StdVideoH264MemMgmtControlOp),
    ('difference_of_pic_nums_minus1', c_uint16),
    ('long_term_pic_num', c_uint16),
    ('long_term_frame_idx', c_uint16),
    ('max_long_term_frame_idx_plus1', c_uint16),
)

StdVideoEncodeH264ReferenceListsInfo = define_struct('StdVideoEncodeH264ReferenceListsInfo',
    ('flags', StdVideoEncodeH264ReferenceListsInfoFlags),
    ('num_ref_idx_l0_active_minus1', c_uint8),
    ('num_ref_idx_l1_active_minus1', c_uint8),
    ('RefPicList0', c_uint8 * STD_VIDEO_H264_MAX_NUM_LIST_REF),
    ('RefPicList1', c_uint8 * STD_VIDEO_H264_MAX_NUM_LIST_REF),
    ('refList0ModOpCount', c_uint8),
    ('refList1ModOpCount', c_uint8),
    ('refPicMarkingOpCount', c_uint8),
    ('reserved1', c_uint8 * 7),
    ('pRefList0ModOperations', POINTER(StdVideoEncodeH264RefListModEntry)),
    ('pRefList1ModOperations', POINTER(StdVideoEncodeH264RefListModEntry)),
    ('pRefPicMarkingOperations', POINTER(StdVideoEncodeH264RefPicMarkingEntry)),
)

StdVideoEncodeH264PictureInfo = define_struct('StdVideoEncodeH264PictureInfo',
    ('flags', StdVideoEncodeH264PictureInfoFlags),
    ('seq_parameter_set_id', c_uint8),
    ('pic_parameter_set_id', c_uint8),
    ('idr_pic_id', c_uint16),
    ('primary_pic_type', StdVideoH264PictureType),
    ('frame_num', c_uint32),
    ('PicOrderCnt', c_int32),
    ('temporal_id', c_uint8),
    ('reserved1', c_uint8 * 3),
    ('pRefLists', POINTER(StdVideoEncodeH264ReferenceListsInfo)),
)

StdVideoEncodeH264ReferenceInfo = define_struct('StdVideoEncodeH264ReferenceInfo',
    ('flags', StdVideoEncodeH264ReferenceInfoFlags),
    ('primary_pic_type', StdVideoH264PictureType),
    ('FrameNum', c_uint32),
    ('PicOrderCnt', c_int32),
    ('long_term_pic_num', c_uint16),
    ('long_term_frame_idx', c_uint16),
    ('temporal_id', c_uint8),
)

StdVideoEncodeH264SliceHeader = define_struct('StdVideoEncodeH264SliceHeader',
    ('flags', StdVideoEncodeH264SliceHeaderFlags),
    ('first_mb_in_slice', c_uint32),
    ('slice_type', StdVideoH264SliceType),
    ('slice_alpha_c0_offset_div2', c_int8),
    ('slice_beta_offset_div2', c_int8),
    ('slice_qp_delta', c_int8),
    ('reserved1', c_uint8),
    ('cabac_init_idc', StdVideoH264CabacInitIdc),
    ('disable_deblocking_filter_idc', StdVideoH264DisableDeblockingFilterIdc),
    ('pWeightTable', POINTER(StdVideoEncodeH264WeightTable)),
)

# ---- header: vulkan_video_codec_h265std.h
VULKAN_VIDEO_CODEC_H265STD_H_: int = 1

STD_VIDEO_H265_CPB_CNT_LIST_SIZE: int = 32
STD_VIDEO_H265_SUBLAYERS_LIST_SIZE: int = 7
STD_VIDEO_H265_SCALING_LIST_4X4_NUM_LISTS: int = 6
STD_VIDEO_H265_SCALING_LIST_4X4_NUM_ELEMENTS: int = 16
STD_VIDEO_H265_SCALING_LIST_8X8_NUM_LISTS: int = 6
STD_VIDEO_H265_SCALING_LIST_8X8_NUM_ELEMENTS: int = 64
STD_VIDEO_H265_SCALING_LIST_16X16_NUM_LISTS: int = 6
STD_VIDEO_H265_SCALING_LIST_16X16_NUM_ELEMENTS: int = 64
STD_VIDEO_H265_SCALING_LIST_32X32_NUM_LISTS: int = 2
STD_VIDEO_H265_SCALING_LIST_32X32_NUM_ELEMENTS: int = 64
STD_VIDEO_H265_CHROMA_QP_OFFSET_LIST_SIZE: int = 6
STD_VIDEO_H265_CHROMA_QP_OFFSET_TILE_COLS_LIST_SIZE: int = 19
STD_VIDEO_H265_CHROMA_QP_OFFSET_TILE_ROWS_LIST_SIZE: int = 21
STD_VIDEO_H265_PREDICTOR_PALETTE_COMPONENTS_LIST_SIZE: int = 3
STD_VIDEO_H265_PREDICTOR_PALETTE_COMP_ENTRIES_LIST_SIZE: int = 128
STD_VIDEO_H265_MAX_NUM_LIST_REF: int = 15
STD_VIDEO_H265_MAX_CHROMA_PLANES: int = 2
STD_VIDEO_H265_MAX_SHORT_TERM_REF_PIC_SETS: int = 64
STD_VIDEO_H265_MAX_DPB_SIZE: int = 16
STD_VIDEO_H265_MAX_LONG_TERM_REF_PICS_SPS: int = 32
STD_VIDEO_H265_MAX_LONG_TERM_PICS: int = 16
STD_VIDEO_H265_MAX_DELTA_POC: int = 48
STD_VIDEO_H265_NO_REFERENCE_PICTURE: int = 0xFF  # Alias or macro

StdVideoH265ChromaFormatIdc = c_int32
STD_VIDEO_H265_CHROMA_FORMAT_IDC_MONOCHROME: int = 0
STD_VIDEO_H265_CHROMA_FORMAT_IDC_420: int = 1
STD_VIDEO_H265_CHROMA_FORMAT_IDC_422: int = 2
STD_VIDEO_H265_CHROMA_FORMAT_IDC_444: int = 3
STD_VIDEO_H265_CHROMA_FORMAT_IDC_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H265_CHROMA_FORMAT_IDC_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH265ProfileIdc = c_int32
STD_VIDEO_H265_PROFILE_IDC_MAIN: int = 1
STD_VIDEO_H265_PROFILE_IDC_MAIN_10: int = 2
STD_VIDEO_H265_PROFILE_IDC_MAIN_STILL_PICTURE: int = 3
STD_VIDEO_H265_PROFILE_IDC_FORMAT_RANGE_EXTENSIONS: int = 4
STD_VIDEO_H265_PROFILE_IDC_SCC_EXTENSIONS: int = 9
STD_VIDEO_H265_PROFILE_IDC_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H265_PROFILE_IDC_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH265LevelIdc = c_int32
STD_VIDEO_H265_LEVEL_IDC_1_0: int = 0
STD_VIDEO_H265_LEVEL_IDC_2_0: int = 1
STD_VIDEO_H265_LEVEL_IDC_2_1: int = 2
STD_VIDEO_H265_LEVEL_IDC_3_0: int = 3
STD_VIDEO_H265_LEVEL_IDC_3_1: int = 4
STD_VIDEO_H265_LEVEL_IDC_4_0: int = 5
STD_VIDEO_H265_LEVEL_IDC_4_1: int = 6
STD_VIDEO_H265_LEVEL_IDC_5_0: int = 7
STD_VIDEO_H265_LEVEL_IDC_5_1: int = 8
STD_VIDEO_H265_LEVEL_IDC_5_2: int = 9
STD_VIDEO_H265_LEVEL_IDC_6_0: int = 10
STD_VIDEO_H265_LEVEL_IDC_6_1: int = 11
STD_VIDEO_H265_LEVEL_IDC_6_2: int = 12
STD_VIDEO_H265_LEVEL_IDC_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H265_LEVEL_IDC_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH265SliceType = c_int32
STD_VIDEO_H265_SLICE_TYPE_B: int = 0
STD_VIDEO_H265_SLICE_TYPE_P: int = 1
STD_VIDEO_H265_SLICE_TYPE_I: int = 2
STD_VIDEO_H265_SLICE_TYPE_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H265_SLICE_TYPE_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH265PictureType = c_int32
STD_VIDEO_H265_PICTURE_TYPE_P: int = 0
STD_VIDEO_H265_PICTURE_TYPE_B: int = 1
STD_VIDEO_H265_PICTURE_TYPE_I: int = 2
STD_VIDEO_H265_PICTURE_TYPE_IDR: int = 3
STD_VIDEO_H265_PICTURE_TYPE_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H265_PICTURE_TYPE_MAX_ENUM: int = 0x7FFFFFFF

StdVideoH265AspectRatioIdc = c_int32
STD_VIDEO_H265_ASPECT_RATIO_IDC_UNSPECIFIED: int = 0
STD_VIDEO_H265_ASPECT_RATIO_IDC_SQUARE: int = 1
STD_VIDEO_H265_ASPECT_RATIO_IDC_12_11: int = 2
STD_VIDEO_H265_ASPECT_RATIO_IDC_10_11: int = 3
STD_VIDEO_H265_ASPECT_RATIO_IDC_16_11: int = 4
STD_VIDEO_H265_ASPECT_RATIO_IDC_40_33: int = 5
STD_VIDEO_H265_ASPECT_RATIO_IDC_24_11: int = 6
STD_VIDEO_H265_ASPECT_RATIO_IDC_20_11: int = 7
STD_VIDEO_H265_ASPECT_RATIO_IDC_32_11: int = 8
STD_VIDEO_H265_ASPECT_RATIO_IDC_80_33: int = 9
STD_VIDEO_H265_ASPECT_RATIO_IDC_18_11: int = 10
STD_VIDEO_H265_ASPECT_RATIO_IDC_15_11: int = 11
STD_VIDEO_H265_ASPECT_RATIO_IDC_64_33: int = 12
STD_VIDEO_H265_ASPECT_RATIO_IDC_160_99: int = 13
STD_VIDEO_H265_ASPECT_RATIO_IDC_4_3: int = 14
STD_VIDEO_H265_ASPECT_RATIO_IDC_3_2: int = 15
STD_VIDEO_H265_ASPECT_RATIO_IDC_2_1: int = 16
STD_VIDEO_H265_ASPECT_RATIO_IDC_EXTENDED_SAR: int = 255
STD_VIDEO_H265_ASPECT_RATIO_IDC_INVALID: int = 0x7FFFFFFF
STD_VIDEO_H265_ASPECT_RATIO_IDC_MAX_ENUM: int = 0x7FFFFFFF
StdVideoH265DecPicBufMgr = define_struct('StdVideoH265DecPicBufMgr',
    ('max_latency_increase_plus1', c_uint32 * STD_VIDEO_H265_SUBLAYERS_LIST_SIZE),
    ('max_dec_pic_buffering_minus1', c_uint8 * STD_VIDEO_H265_SUBLAYERS_LIST_SIZE),
    ('max_num_reorder_pics', c_uint8 * STD_VIDEO_H265_SUBLAYERS_LIST_SIZE),
)

StdVideoH265SubLayerHrdParameters = define_struct('StdVideoH265SubLayerHrdParameters',
    ('bit_rate_value_minus1', c_uint32 * STD_VIDEO_H265_CPB_CNT_LIST_SIZE),
    ('cpb_size_value_minus1', c_uint32 * STD_VIDEO_H265_CPB_CNT_LIST_SIZE),
    ('cpb_size_du_value_minus1', c_uint32 * STD_VIDEO_H265_CPB_CNT_LIST_SIZE),
    ('bit_rate_du_value_minus1', c_uint32 * STD_VIDEO_H265_CPB_CNT_LIST_SIZE),
    ('cbr_flag', c_uint32),
)

StdVideoH265HrdFlags = define_struct('StdVideoH265HrdFlags',
    ('nal_hrd_parameters_present_flag', c_uint32, 1),
    ('vcl_hrd_parameters_present_flag', c_uint32, 1),
    ('sub_pic_hrd_params_present_flag', c_uint32, 1),
    ('sub_pic_cpb_params_in_pic_timing_sei_flag', c_uint32, 1),
    ('fixed_pic_rate_general_flag', c_uint32, 8),
    ('fixed_pic_rate_within_cvs_flag', c_uint32, 8),
    ('low_delay_hrd_flag', c_uint32, 8),
)

StdVideoH265HrdParameters = define_struct('StdVideoH265HrdParameters',
    ('flags', StdVideoH265HrdFlags),
    ('tick_divisor_minus2', c_uint8),
    ('du_cpb_removal_delay_increment_length_minus1', c_uint8),
    ('dpb_output_delay_du_length_minus1', c_uint8),
    ('bit_rate_scale', c_uint8),
    ('cpb_size_scale', c_uint8),
    ('cpb_size_du_scale', c_uint8),
    ('initial_cpb_removal_delay_length_minus1', c_uint8),
    ('au_cpb_removal_delay_length_minus1', c_uint8),
    ('dpb_output_delay_length_minus1', c_uint8),
    ('cpb_cnt_minus1', c_uint8 * STD_VIDEO_H265_SUBLAYERS_LIST_SIZE),
    ('elemental_duration_in_tc_minus1', c_uint16 * STD_VIDEO_H265_SUBLAYERS_LIST_SIZE),
    ('reserved', c_uint16 * 3),
    ('pSubLayerHrdParametersNal', POINTER(StdVideoH265SubLayerHrdParameters)),
    ('pSubLayerHrdParametersVcl', POINTER(StdVideoH265SubLayerHrdParameters)),
)

StdVideoH265VpsFlags = define_struct('StdVideoH265VpsFlags',
    ('vps_temporal_id_nesting_flag', c_uint32, 1),
    ('vps_sub_layer_ordering_info_present_flag', c_uint32, 1),
    ('vps_timing_info_present_flag', c_uint32, 1),
    ('vps_poc_proportional_to_timing_flag', c_uint32, 1),
)

StdVideoH265ProfileTierLevelFlags = define_struct('StdVideoH265ProfileTierLevelFlags',
    ('general_tier_flag', c_uint32, 1),
    ('general_progressive_source_flag', c_uint32, 1),
    ('general_interlaced_source_flag', c_uint32, 1),
    ('general_non_packed_constraint_flag', c_uint32, 1),
    ('general_frame_only_constraint_flag', c_uint32, 1),
)

StdVideoH265ProfileTierLevel = define_struct('StdVideoH265ProfileTierLevel',
    ('flags', StdVideoH265ProfileTierLevelFlags),
    ('general_profile_idc', StdVideoH265ProfileIdc),
    ('general_level_idc', StdVideoH265LevelIdc),
)

StdVideoH265VideoParameterSet = define_struct('StdVideoH265VideoParameterSet',
    ('flags', StdVideoH265VpsFlags),
    ('vps_video_parameter_set_id', c_uint8),
    ('vps_max_sub_layers_minus1', c_uint8),
    ('reserved1', c_uint8),
    ('reserved2', c_uint8),
    ('vps_num_units_in_tick', c_uint32),
    ('vps_time_scale', c_uint32),
    ('vps_num_ticks_poc_diff_one_minus1', c_uint32),
    ('reserved3', c_uint32),
    ('pDecPicBufMgr', POINTER(StdVideoH265DecPicBufMgr)),
    ('pHrdParameters', POINTER(StdVideoH265HrdParameters)),
    ('pProfileTierLevel', POINTER(StdVideoH265ProfileTierLevel)),
)

StdVideoH265ScalingLists = define_struct('StdVideoH265ScalingLists',
    ('ScalingList4x4', c_uint8 * STD_VIDEO_H265_SCALING_LIST_4X4_NUM_ELEMENTS * STD_VIDEO_H265_SCALING_LIST_4X4_NUM_LISTS),
    ('ScalingList8x8', c_uint8 * STD_VIDEO_H265_SCALING_LIST_8X8_NUM_ELEMENTS * STD_VIDEO_H265_SCALING_LIST_8X8_NUM_LISTS),
    ('ScalingList16x16', c_uint8 * STD_VIDEO_H265_SCALING_LIST_16X16_NUM_ELEMENTS * STD_VIDEO_H265_SCALING_LIST_16X16_NUM_LISTS),
    ('ScalingList32x32', c_uint8 * STD_VIDEO_H265_SCALING_LIST_32X32_NUM_ELEMENTS * STD_VIDEO_H265_SCALING_LIST_32X32_NUM_LISTS),
    ('ScalingListDCCoef16x16', c_uint8 * STD_VIDEO_H265_SCALING_LIST_16X16_NUM_LISTS),
    ('ScalingListDCCoef32x32', c_uint8 * STD_VIDEO_H265_SCALING_LIST_32X32_NUM_LISTS),
)

StdVideoH265SpsVuiFlags = define_struct('StdVideoH265SpsVuiFlags',
    ('aspect_ratio_info_present_flag', c_uint32, 1),
    ('overscan_info_present_flag', c_uint32, 1),
    ('overscan_appropriate_flag', c_uint32, 1),
    ('video_signal_type_present_flag', c_uint32, 1),
    ('video_full_range_flag', c_uint32, 1),
    ('colour_description_present_flag', c_uint32, 1),
    ('chroma_loc_info_present_flag', c_uint32, 1),
    ('neutral_chroma_indication_flag', c_uint32, 1),
    ('field_seq_flag', c_uint32, 1),
    ('frame_field_info_present_flag', c_uint32, 1),
    ('default_display_window_flag', c_uint32, 1),
    ('vui_timing_info_present_flag', c_uint32, 1),
    ('vui_poc_proportional_to_timing_flag', c_uint32, 1),
    ('vui_hrd_parameters_present_flag', c_uint32, 1),
    ('bitstream_restriction_flag', c_uint32, 1),
    ('tiles_fixed_structure_flag', c_uint32, 1),
    ('motion_vectors_over_pic_boundaries_flag', c_uint32, 1),
    ('restricted_ref_pic_lists_flag', c_uint32, 1),
)

StdVideoH265SequenceParameterSetVui = define_struct('StdVideoH265SequenceParameterSetVui',
    ('flags', StdVideoH265SpsVuiFlags),
    ('aspect_ratio_idc', StdVideoH265AspectRatioIdc),
    ('sar_width', c_uint16),
    ('sar_height', c_uint16),
    ('video_format', c_uint8),
    ('colour_primaries', c_uint8),
    ('transfer_characteristics', c_uint8),
    ('matrix_coeffs', c_uint8),
    ('chroma_sample_loc_type_top_field', c_uint8),
    ('chroma_sample_loc_type_bottom_field', c_uint8),
    ('reserved1', c_uint8),
    ('reserved2', c_uint8),
    ('def_disp_win_left_offset', c_uint16),
    ('def_disp_win_right_offset', c_uint16),
    ('def_disp_win_top_offset', c_uint16),
    ('def_disp_win_bottom_offset', c_uint16),
    ('vui_num_units_in_tick', c_uint32),
    ('vui_time_scale', c_uint32),
    ('vui_num_ticks_poc_diff_one_minus1', c_uint32),
    ('min_spatial_segmentation_idc', c_uint16),
    ('reserved3', c_uint16),
    ('max_bytes_per_pic_denom', c_uint8),
    ('max_bits_per_min_cu_denom', c_uint8),
    ('log2_max_mv_length_horizontal', c_uint8),
    ('log2_max_mv_length_vertical', c_uint8),
    ('pHrdParameters', POINTER(StdVideoH265HrdParameters)),
)

StdVideoH265PredictorPaletteEntries = define_struct('StdVideoH265PredictorPaletteEntries',
    ('PredictorPaletteEntries', c_uint16 * STD_VIDEO_H265_PREDICTOR_PALETTE_COMP_ENTRIES_LIST_SIZE * STD_VIDEO_H265_PREDICTOR_PALETTE_COMPONENTS_LIST_SIZE),
)

StdVideoH265SpsFlags = define_struct('StdVideoH265SpsFlags',
    ('sps_temporal_id_nesting_flag', c_uint32, 1),
    ('separate_colour_plane_flag', c_uint32, 1),
    ('conformance_window_flag', c_uint32, 1),
    ('sps_sub_layer_ordering_info_present_flag', c_uint32, 1),
    ('scaling_list_enabled_flag', c_uint32, 1),
    ('sps_scaling_list_data_present_flag', c_uint32, 1),
    ('amp_enabled_flag', c_uint32, 1),
    ('sample_adaptive_offset_enabled_flag', c_uint32, 1),
    ('pcm_enabled_flag', c_uint32, 1),
    ('pcm_loop_filter_disabled_flag', c_uint32, 1),
    ('long_term_ref_pics_present_flag', c_uint32, 1),
    ('sps_temporal_mvp_enabled_flag', c_uint32, 1),
    ('strong_intra_smoothing_enabled_flag', c_uint32, 1),
    ('vui_parameters_present_flag', c_uint32, 1),
    ('sps_extension_present_flag', c_uint32, 1),
    ('sps_range_extension_flag', c_uint32, 1),
    ('transform_skip_rotation_enabled_flag', c_uint32, 1),
    ('transform_skip_context_enabled_flag', c_uint32, 1),
    ('implicit_rdpcm_enabled_flag', c_uint32, 1),
    ('explicit_rdpcm_enabled_flag', c_uint32, 1),
    ('extended_precision_processing_flag', c_uint32, 1),
    ('intra_smoothing_disabled_flag', c_uint32, 1),
    ('high_precision_offsets_enabled_flag', c_uint32, 1),
    ('persistent_rice_adaptation_enabled_flag', c_uint32, 1),
    ('cabac_bypass_alignment_enabled_flag', c_uint32, 1),
    ('sps_scc_extension_flag', c_uint32, 1),
    ('sps_curr_pic_ref_enabled_flag', c_uint32, 1),
    ('palette_mode_enabled_flag', c_uint32, 1),
    ('sps_palette_predictor_initializers_present_flag', c_uint32, 1),
    ('intra_boundary_filtering_disabled_flag', c_uint32, 1),
)

StdVideoH265ShortTermRefPicSetFlags = define_struct('StdVideoH265ShortTermRefPicSetFlags',
    ('inter_ref_pic_set_prediction_flag', c_uint32, 1),
    ('delta_rps_sign', c_uint32, 1),
)

StdVideoH265ShortTermRefPicSet = define_struct('StdVideoH265ShortTermRefPicSet',
    ('flags', StdVideoH265ShortTermRefPicSetFlags),
    ('delta_idx_minus1', c_uint32),
    ('use_delta_flag', c_uint16),
    ('abs_delta_rps_minus1', c_uint16),
    ('used_by_curr_pic_flag', c_uint16),
    ('used_by_curr_pic_s0_flag', c_uint16),
    ('used_by_curr_pic_s1_flag', c_uint16),
    ('reserved1', c_uint16),
    ('reserved2', c_uint8),
    ('reserved3', c_uint8),
    ('num_negative_pics', c_uint8),
    ('num_positive_pics', c_uint8),
    ('delta_poc_s0_minus1', c_uint16 * STD_VIDEO_H265_MAX_DPB_SIZE),
    ('delta_poc_s1_minus1', c_uint16 * STD_VIDEO_H265_MAX_DPB_SIZE),
)

StdVideoH265LongTermRefPicsSps = define_struct('StdVideoH265LongTermRefPicsSps',
    ('used_by_curr_pic_lt_sps_flag', c_uint32),
    ('lt_ref_pic_poc_lsb_sps', c_uint32 * STD_VIDEO_H265_MAX_LONG_TERM_REF_PICS_SPS),
)

StdVideoH265SequenceParameterSet = define_struct('StdVideoH265SequenceParameterSet',
    ('flags', StdVideoH265SpsFlags),
    ('chroma_format_idc', StdVideoH265ChromaFormatIdc),
    ('pic_width_in_luma_samples', c_uint32),
    ('pic_height_in_luma_samples', c_uint32),
    ('sps_video_parameter_set_id', c_uint8),
    ('sps_max_sub_layers_minus1', c_uint8),
    ('sps_seq_parameter_set_id', c_uint8),
    ('bit_depth_luma_minus8', c_uint8),
    ('bit_depth_chroma_minus8', c_uint8),
    ('log2_max_pic_order_cnt_lsb_minus4', c_uint8),
    ('log2_min_luma_coding_block_size_minus3', c_uint8),
    ('log2_diff_max_min_luma_coding_block_size', c_uint8),
    ('log2_min_luma_transform_block_size_minus2', c_uint8),
    ('log2_diff_max_min_luma_transform_block_size', c_uint8),
    ('max_transform_hierarchy_depth_inter', c_uint8),
    ('max_transform_hierarchy_depth_intra', c_uint8),
    ('num_short_term_ref_pic_sets', c_uint8),
    ('num_long_term_ref_pics_sps', c_uint8),
    ('pcm_sample_bit_depth_luma_minus1', c_uint8),
    ('pcm_sample_bit_depth_chroma_minus1', c_uint8),
    ('log2_min_pcm_luma_coding_block_size_minus3', c_uint8),
    ('log2_diff_max_min_pcm_luma_coding_block_size', c_uint8),
    ('reserved1', c_uint8),
    ('reserved2', c_uint8),
    ('palette_max_size', c_uint8),
    ('delta_palette_max_predictor_size', c_uint8),
    ('motion_vector_resolution_control_idc', c_uint8),
    ('sps_num_palette_predictor_initializers_minus1', c_uint8),
    ('conf_win_left_offset', c_uint32),
    ('conf_win_right_offset', c_uint32),
    ('conf_win_top_offset', c_uint32),
    ('conf_win_bottom_offset', c_uint32),
    ('pProfileTierLevel', POINTER(StdVideoH265ProfileTierLevel)),
    ('pDecPicBufMgr', POINTER(StdVideoH265DecPicBufMgr)),
    ('pScalingLists', POINTER(StdVideoH265ScalingLists)),
    ('pShortTermRefPicSet', POINTER(StdVideoH265ShortTermRefPicSet)),
    ('pLongTermRefPicsSps', POINTER(StdVideoH265LongTermRefPicsSps)),
    ('pSequenceParameterSetVui', POINTER(StdVideoH265SequenceParameterSetVui)),
    ('pPredictorPaletteEntries', POINTER(StdVideoH265PredictorPaletteEntries)),
)

StdVideoH265PpsFlags = define_struct('StdVideoH265PpsFlags',
    ('dependent_slice_segments_enabled_flag', c_uint32, 1),
    ('output_flag_present_flag', c_uint32, 1),
    ('sign_data_hiding_enabled_flag', c_uint32, 1),
    ('cabac_init_present_flag', c_uint32, 1),
    ('constrained_intra_pred_flag', c_uint32, 1),
    ('transform_skip_enabled_flag', c_uint32, 1),
    ('cu_qp_delta_enabled_flag', c_uint32, 1),
    ('pps_slice_chroma_qp_offsets_present_flag', c_uint32, 1),
    ('weighted_pred_flag', c_uint32, 1),
    ('weighted_bipred_flag', c_uint32, 1),
    ('transquant_bypass_enabled_flag', c_uint32, 1),
    ('tiles_enabled_flag', c_uint32, 1),
    ('entropy_coding_sync_enabled_flag', c_uint32, 1),
    ('uniform_spacing_flag', c_uint32, 1),
    ('loop_filter_across_tiles_enabled_flag', c_uint32, 1),
    ('pps_loop_filter_across_slices_enabled_flag', c_uint32, 1),
    ('deblocking_filter_control_present_flag', c_uint32, 1),
    ('deblocking_filter_override_enabled_flag', c_uint32, 1),
    ('pps_deblocking_filter_disabled_flag', c_uint32, 1),
    ('pps_scaling_list_data_present_flag', c_uint32, 1),
    ('lists_modification_present_flag', c_uint32, 1),
    ('slice_segment_header_extension_present_flag', c_uint32, 1),
    ('pps_extension_present_flag', c_uint32, 1),
    ('cross_component_prediction_enabled_flag', c_uint32, 1),
    ('chroma_qp_offset_list_enabled_flag', c_uint32, 1),
    ('pps_curr_pic_ref_enabled_flag', c_uint32, 1),
    ('residual_adaptive_colour_transform_enabled_flag', c_uint32, 1),
    ('pps_slice_act_qp_offsets_present_flag', c_uint32, 1),
    ('pps_palette_predictor_initializers_present_flag', c_uint32, 1),
    ('monochrome_palette_flag', c_uint32, 1),
    ('pps_range_extension_flag', c_uint32, 1),
)

StdVideoH265PictureParameterSet = define_struct('StdVideoH265PictureParameterSet',
    ('flags', StdVideoH265PpsFlags),
    ('pps_pic_parameter_set_id', c_uint8),
    ('pps_seq_parameter_set_id', c_uint8),
    ('sps_video_parameter_set_id', c_uint8),
    ('num_extra_slice_header_bits', c_uint8),
    ('num_ref_idx_l0_default_active_minus1', c_uint8),
    ('num_ref_idx_l1_default_active_minus1', c_uint8),
    ('init_qp_minus26', c_int8),
    ('diff_cu_qp_delta_depth', c_uint8),
    ('pps_cb_qp_offset', c_int8),
    ('pps_cr_qp_offset', c_int8),
    ('pps_beta_offset_div2', c_int8),
    ('pps_tc_offset_div2', c_int8),
    ('log2_parallel_merge_level_minus2', c_uint8),
    ('log2_max_transform_skip_block_size_minus2', c_uint8),
    ('diff_cu_chroma_qp_offset_depth', c_uint8),
    ('chroma_qp_offset_list_len_minus1', c_uint8),
    ('cb_qp_offset_list', c_int8 * STD_VIDEO_H265_CHROMA_QP_OFFSET_LIST_SIZE),
    ('cr_qp_offset_list', c_int8 * STD_VIDEO_H265_CHROMA_QP_OFFSET_LIST_SIZE),
    ('log2_sao_offset_scale_luma', c_uint8),
    ('log2_sao_offset_scale_chroma', c_uint8),
    ('pps_act_y_qp_offset_plus5', c_int8),
    ('pps_act_cb_qp_offset_plus5', c_int8),
    ('pps_act_cr_qp_offset_plus3', c_int8),
    ('pps_num_palette_predictor_initializers', c_uint8),
    ('luma_bit_depth_entry_minus8', c_uint8),
    ('chroma_bit_depth_entry_minus8', c_uint8),
    ('num_tile_columns_minus1', c_uint8),
    ('num_tile_rows_minus1', c_uint8),
    ('reserved1', c_uint8),
    ('reserved2', c_uint8),
    ('column_width_minus1', c_uint16 * STD_VIDEO_H265_CHROMA_QP_OFFSET_TILE_COLS_LIST_SIZE),
    ('row_height_minus1', c_uint16 * STD_VIDEO_H265_CHROMA_QP_OFFSET_TILE_ROWS_LIST_SIZE),
    ('reserved3', c_uint32),
    ('pScalingLists', POINTER(StdVideoH265ScalingLists)),
    ('pPredictorPaletteEntries', POINTER(StdVideoH265PredictorPaletteEntries)),
)

# ---- header: vulkan_video_codec_h265std_decode.h
VULKAN_VIDEO_CODEC_H265STD_DECODE_H_: int = 1

VK_STD_VULKAN_VIDEO_CODEC_H265_DECODE_API_VERSION_1_0_0: int = VK_MAKE_VIDEO_STD_VERSION(1, 0, 0)  # Alias or macro
VK_STD_VULKAN_VIDEO_CODEC_H265_DECODE_SPEC_VERSION: int = VK_STD_VULKAN_VIDEO_CODEC_H265_DECODE_API_VERSION_1_0_0  # Alias or macro
VK_STD_VULKAN_VIDEO_CODEC_H265_DECODE_EXTENSION_NAME = "VK_STD_vulkan_video_codec_h265_decode"
STD_VIDEO_DECODE_H265_REF_PIC_SET_LIST_SIZE: int = 8
StdVideoDecodeH265PictureInfoFlags = define_struct('StdVideoDecodeH265PictureInfoFlags',
    ('IrapPicFlag', c_uint32, 1),
    ('IdrPicFlag', c_uint32, 1),
    ('IsReference', c_uint32, 1),
    ('short_term_ref_pic_set_sps_flag', c_uint32, 1),
)

StdVideoDecodeH265PictureInfo = define_struct('StdVideoDecodeH265PictureInfo',
    ('flags', StdVideoDecodeH265PictureInfoFlags),
    ('sps_video_parameter_set_id', c_uint8),
    ('pps_seq_parameter_set_id', c_uint8),
    ('pps_pic_parameter_set_id', c_uint8),
    ('NumDeltaPocsOfRefRpsIdx', c_uint8),
    ('PicOrderCntVal', c_int32),
    ('NumBitsForSTRefPicSetInSlice', c_uint16),
    ('reserved', c_uint16),
    ('RefPicSetStCurrBefore', c_uint8 * STD_VIDEO_DECODE_H265_REF_PIC_SET_LIST_SIZE),
    ('RefPicSetStCurrAfter', c_uint8 * STD_VIDEO_DECODE_H265_REF_PIC_SET_LIST_SIZE),
    ('RefPicSetLtCurr', c_uint8 * STD_VIDEO_DECODE_H265_REF_PIC_SET_LIST_SIZE),
)

StdVideoDecodeH265ReferenceInfoFlags = define_struct('StdVideoDecodeH265ReferenceInfoFlags',
    ('used_for_long_term_reference', c_uint32, 1),
    ('unused_for_reference', c_uint32, 1),
)

StdVideoDecodeH265ReferenceInfo = define_struct('StdVideoDecodeH265ReferenceInfo',
    ('flags', StdVideoDecodeH265ReferenceInfoFlags),
    ('PicOrderCntVal', c_int32),
)

# ---- header: vulkan_video_codec_h265std_encode.h
VULKAN_VIDEO_CODEC_H265STD_ENCODE_H_: int = 1

VK_STD_VULKAN_VIDEO_CODEC_H265_ENCODE_API_VERSION_1_0_0: int = VK_MAKE_VIDEO_STD_VERSION(1, 0, 0)  # Alias or macro
VK_STD_VULKAN_VIDEO_CODEC_H265_ENCODE_SPEC_VERSION: int = VK_STD_VULKAN_VIDEO_CODEC_H265_ENCODE_API_VERSION_1_0_0  # Alias or macro
VK_STD_VULKAN_VIDEO_CODEC_H265_ENCODE_EXTENSION_NAME = "VK_STD_vulkan_video_codec_h265_encode"
StdVideoEncodeH265WeightTableFlags = define_struct('StdVideoEncodeH265WeightTableFlags',
    ('luma_weight_l0_flag', c_uint16),
    ('chroma_weight_l0_flag', c_uint16),
    ('luma_weight_l1_flag', c_uint16),
    ('chroma_weight_l1_flag', c_uint16),
)

StdVideoEncodeH265WeightTable = define_struct('StdVideoEncodeH265WeightTable',
    ('flags', StdVideoEncodeH265WeightTableFlags),
    ('luma_log2_weight_denom', c_uint8),
    ('delta_chroma_log2_weight_denom', c_int8),
    ('delta_luma_weight_l0', c_int8 * STD_VIDEO_H265_MAX_NUM_LIST_REF),
    ('luma_offset_l0', c_int8 * STD_VIDEO_H265_MAX_NUM_LIST_REF),
    ('delta_chroma_weight_l0', c_int8 * STD_VIDEO_H265_MAX_CHROMA_PLANES * STD_VIDEO_H265_MAX_NUM_LIST_REF),
    ('delta_chroma_offset_l0', c_int8 * STD_VIDEO_H265_MAX_CHROMA_PLANES * STD_VIDEO_H265_MAX_NUM_LIST_REF),
    ('delta_luma_weight_l1', c_int8 * STD_VIDEO_H265_MAX_NUM_LIST_REF),
    ('luma_offset_l1', c_int8 * STD_VIDEO_H265_MAX_NUM_LIST_REF),
    ('delta_chroma_weight_l1', c_int8 * STD_VIDEO_H265_MAX_CHROMA_PLANES * STD_VIDEO_H265_MAX_NUM_LIST_REF),
    ('delta_chroma_offset_l1', c_int8 * STD_VIDEO_H265_MAX_CHROMA_PLANES * STD_VIDEO_H265_MAX_NUM_LIST_REF),
)

StdVideoEncodeH265SliceSegmentHeaderFlags = define_struct('StdVideoEncodeH265SliceSegmentHeaderFlags',
    ('first_slice_segment_in_pic_flag', c_uint32, 1),
    ('dependent_slice_segment_flag', c_uint32, 1),
    ('slice_sao_luma_flag', c_uint32, 1),
    ('slice_sao_chroma_flag', c_uint32, 1),
    ('num_ref_idx_active_override_flag', c_uint32, 1),
    ('mvd_l1_zero_flag', c_uint32, 1),
    ('cabac_init_flag', c_uint32, 1),
    ('cu_chroma_qp_offset_enabled_flag', c_uint32, 1),
    ('deblocking_filter_override_flag', c_uint32, 1),
    ('slice_deblocking_filter_disabled_flag', c_uint32, 1),
    ('collocated_from_l0_flag', c_uint32, 1),
    ('slice_loop_filter_across_slices_enabled_flag', c_uint32, 1),
    ('reserved', c_uint32, 20),
)

StdVideoEncodeH265SliceSegmentHeader = define_struct('StdVideoEncodeH265SliceSegmentHeader',
    ('flags', StdVideoEncodeH265SliceSegmentHeaderFlags),
    ('slice_type', StdVideoH265SliceType),
    ('slice_segment_address', c_uint32),
    ('collocated_ref_idx', c_uint8),
    ('MaxNumMergeCand', c_uint8),
    ('slice_cb_qp_offset', c_int8),
    ('slice_cr_qp_offset', c_int8),
    ('slice_beta_offset_div2', c_int8),
    ('slice_tc_offset_div2', c_int8),
    ('slice_act_y_qp_offset', c_int8),
    ('slice_act_cb_qp_offset', c_int8),
    ('slice_act_cr_qp_offset', c_int8),
    ('slice_qp_delta', c_int8),
    ('reserved1', c_uint16),
    ('pWeightTable', POINTER(StdVideoEncodeH265WeightTable)),
)

StdVideoEncodeH265ReferenceListsInfoFlags = define_struct('StdVideoEncodeH265ReferenceListsInfoFlags',
    ('ref_pic_list_modification_flag_l0', c_uint32, 1),
    ('ref_pic_list_modification_flag_l1', c_uint32, 1),
    ('reserved', c_uint32, 30),
)

StdVideoEncodeH265ReferenceListsInfo = define_struct('StdVideoEncodeH265ReferenceListsInfo',
    ('flags', StdVideoEncodeH265ReferenceListsInfoFlags),
    ('num_ref_idx_l0_active_minus1', c_uint8),
    ('num_ref_idx_l1_active_minus1', c_uint8),
    ('RefPicList0', c_uint8 * STD_VIDEO_H265_MAX_NUM_LIST_REF),
    ('RefPicList1', c_uint8 * STD_VIDEO_H265_MAX_NUM_LIST_REF),
    ('list_entry_l0', c_uint8 * STD_VIDEO_H265_MAX_NUM_LIST_REF),
    ('list_entry_l1', c_uint8 * STD_VIDEO_H265_MAX_NUM_LIST_REF),
)

StdVideoEncodeH265PictureInfoFlags = define_struct('StdVideoEncodeH265PictureInfoFlags',
    ('is_reference', c_uint32, 1),
    ('IrapPicFlag', c_uint32, 1),
    ('used_for_long_term_reference', c_uint32, 1),
    ('discardable_flag', c_uint32, 1),
    ('cross_layer_bla_flag', c_uint32, 1),
    ('pic_output_flag', c_uint32, 1),
    ('no_output_of_prior_pics_flag', c_uint32, 1),
    ('short_term_ref_pic_set_sps_flag', c_uint32, 1),
    ('slice_temporal_mvp_enabled_flag', c_uint32, 1),
    ('reserved', c_uint32, 23),
)

StdVideoEncodeH265LongTermRefPics = define_struct('StdVideoEncodeH265LongTermRefPics',
    ('num_long_term_sps', c_uint8),
    ('num_long_term_pics', c_uint8),
    ('lt_idx_sps', c_uint8 * STD_VIDEO_H265_MAX_LONG_TERM_REF_PICS_SPS),
    ('poc_lsb_lt', c_uint8 * STD_VIDEO_H265_MAX_LONG_TERM_PICS),
    ('used_by_curr_pic_lt_flag', c_uint16),
    ('delta_poc_msb_present_flag', c_uint8 * STD_VIDEO_H265_MAX_DELTA_POC),
    ('delta_poc_msb_cycle_lt', c_uint8 * STD_VIDEO_H265_MAX_DELTA_POC),
)

StdVideoEncodeH265PictureInfo = define_struct('StdVideoEncodeH265PictureInfo',
    ('flags', StdVideoEncodeH265PictureInfoFlags),
    ('pic_type', StdVideoH265PictureType),
    ('sps_video_parameter_set_id', c_uint8),
    ('pps_seq_parameter_set_id', c_uint8),
    ('pps_pic_parameter_set_id', c_uint8),
    ('short_term_ref_pic_set_idx', c_uint8),
    ('PicOrderCntVal', c_int32),
    ('TemporalId', c_uint8),
    ('reserved1', c_uint8 * 7),
    ('pRefLists', POINTER(StdVideoEncodeH265ReferenceListsInfo)),
    ('pShortTermRefPicSet', POINTER(StdVideoH265ShortTermRefPicSet)),
    ('pLongTermRefPics', POINTER(StdVideoEncodeH265LongTermRefPics)),
)

StdVideoEncodeH265ReferenceInfoFlags = define_struct('StdVideoEncodeH265ReferenceInfoFlags',
    ('used_for_long_term_reference', c_uint32, 1),
    ('unused_for_reference', c_uint32, 1),
    ('reserved', c_uint32, 30),
)

StdVideoEncodeH265ReferenceInfo = define_struct('StdVideoEncodeH265ReferenceInfo',
    ('flags', StdVideoEncodeH265ReferenceInfoFlags),
    ('pic_type', StdVideoH265PictureType),
    ('PicOrderCntVal', c_int32),
    ('TemporalId', c_uint8),
)

# ---- header: vulkan_video_codecs_common.h
VULKAN_VIDEO_CODECS_COMMON_H_: int = 1

InstanceFunctions = (
)

DeviceFunctions = (
)

LoaderFunctions = (
)

