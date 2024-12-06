"""Wrapper for include/libavcodec/avcodec.h
"""

from ctypes import c_int, c_uint16, c_int64, c_uint32, c_uint64, c_size_t
from ctypes import c_uint8, c_uint, c_float, c_char_p
from ctypes import c_void_p, POINTER, CFUNCTYPE, Structure

import pyglet.lib
from pyglet.util import debug_print
from . import compat
from . import libavutil
from .libavutil import AVChannelLayout, AVDictionary

_debug = debug_print('debug_media')

avcodec = pyglet.lib.load_library(
    'avcodec',
    win32=('avcodec-61', 'avcodec-60', 'avcodec-59', 'avcodec-58'),
    darwin=('avcodec.61', 'avcodec.60', 'avcodec.59', 'avcodec.58')
)

avcodec.avcodec_version.restype = c_int

avcodec_version = avcodec.avcodec_version() >> 16

compat.set_version('avcodec', avcodec_version)


FF_INPUT_BUFFER_PADDING_SIZE = 32


class AVPacketSideData(Structure):
    _fields_ = [
        ('data', POINTER(c_uint8)),
        ('size', c_int),
        ('type', c_int)
    ]


AVBufferRef = libavutil.AVBufferRef

AVRational = libavutil.AVRational


class AVPacket(Structure):
    pass

AVPacket_Fields = [
        ('buf', POINTER(AVBufferRef)),
        ('pts', c_int64),
        ('dts', c_int64),
        ('data', POINTER(c_uint8)),
        ('size', c_int),
        ('stream_index', c_int),
        ('flags', c_int),
        ('side_data', POINTER(AVPacketSideData)),
        ('side_data_elems', c_int),
        ('duration', c_int64),
        ('pos', c_int64),
        ('opaque', c_void_p),  # 5.x+
        ('opaque_ref', c_void_p),  # 5.x+
        ('time_base', AVRational),  # 5.x+
        ('convergence_duration', c_int64)  # 4.x only
    ]


compat.add_version_changes('avcodec', 58, AVPacket, AVPacket_Fields,
                           removals=('opaque', 'opaque_ref', 'time_base'))

for compat_ver in (59, 60, 61):
    compat.add_version_changes('avcodec', compat_ver, AVPacket, AVPacket_Fields,
                               removals=('convergence_duration',))

class AVCodecParserContext(Structure):
    pass


class AVCodecParameters(Structure):
    pass

AVCodecParameters_Fields = [
    ('codec_type', c_int),
    ('codec_id', c_int),
    ('codec_tag', c_uint32),
    ('extradata', POINTER(c_uint8)),
    ('extradata_size', c_int),
    ('coded_side_data', POINTER(AVPacketSideData)),  # added in 61
    ('nb_coded_side_data', c_int),  # added in 61
    ('format', c_int),
    ('bit_rate', c_int64),
    ('bits_per_coded_sample', c_int),
    ('bits_per_raw_sample', c_int),
    ('profile', c_int),
    ('level', c_int),
    ('width', c_int),
    ('height', c_int),
    ('sample_aspect_ratio', AVRational),
    ('framerate', AVRational),  # added in 61
    ('field_order', c_int),
    ('color_range', c_int),
    ('color_primaries', c_int),
    ('color_trc', c_int),
    ('color_space', c_int),
    ('chroma_location', c_int),
    ('video_delay', c_int),
    ('ch_layout', AVChannelLayout),  # added in 61
    ('channel_layout', c_uint64),  # deprecated as of 59. removed in 61
    ('channels', c_int),  # deprecated as of 59. removed in 61
    ('sample_rate', c_int),
    ('block_align', c_int),
    ('frame_size', c_int),
    ('initial_padding', c_int),
    ('trailing_padding', c_int),
    ('seek_preroll', c_int),
]

for compat_ver in (58, 59, 60):
    compat.add_version_changes('avcodec', compat_ver, AVCodecParameters, AVCodecParameters_Fields,
                               removals=('coded_side_data', 'nb_coded_side_data', 'ch_layout', 'framerate'))

compat.add_version_changes('avcodec', 61, AVCodecParameters, AVCodecParameters_Fields,
                           removals=('channel_layout', 'channels'))


class AVProfile(Structure):
    _fields_ = [
        ('profile', c_int),
        ('name', c_char_p),
    ]


class AVCodecDescriptor(Structure):
    _fields_ = [
        ('id', c_int),
        ('type', c_int),
        ('name', c_char_p),
        ('long_name', c_char_p),
        ('props', c_int),
        ('mime_types', c_char_p),
        ('profiles', POINTER(AVProfile))
    ]


class AVCodecInternal(Structure):
    pass


class AVCodec(Structure):
    _fields_ = [
        ('name', c_char_p),
        ('long_name', c_char_p),
        ('type', c_int),
        ('id', c_int),
        ('capabilities', c_int),
        ('supported_framerates', POINTER(AVRational)),
        ('pix_fmts', POINTER(c_int)),
        ('supported_samplerates', POINTER(c_int)),
        ('sample_fmts', POINTER(c_int)),
        ('channel_layouts', POINTER(c_uint64)),
        ('max_lowres', c_uint8),
        # And more...
    ]


class AVCodecContext(Structure):
    pass


class RcOverride(Structure):
    pass


class AVHWAccel(Structure):
    pass

AVFrameSideDataType = c_int

class AVFrameSideData(Structure):
    _fields_ = [
        ("type", AVFrameSideDataType),
        ("data", POINTER(c_uint8)),
        ("size", c_size_t),
        ("metadata", POINTER(AVDictionary)),
        ("buf", POINTER(AVBufferRef))
    ]

AVClass = libavutil.AVClass
AVFrame = libavutil.AVFrame
AV_NUM_DATA_POINTERS = libavutil.AV_NUM_DATA_POINTERS

# Significant deprecation and re-ordering of the entire structure makes it unmanagable to
# track of all the changes via compat module. Re-define the structure and compat the new one going forward.
if avcodec_version >= 61:
    AVCodecContext_Fields = [
        # Basic fields
        ("av_class", POINTER(AVClass)),
        ("log_level_offset", c_int),

        # Codec fields
        ("codec_type", c_int),  # enum AVMediaType
        ("codec", POINTER(AVCodec)),
        ("codec_id", c_int),  # enum AVCodecID
        ("codec_tag", c_uint),

        ("priv_data", c_void_p),
        ("internal", POINTER(AVCodecInternal)),
        ("opaque", c_void_p),
        ("bit_rate", c_int64),
        ("flags", c_int),
        ("flags2", c_int),
        ("extradata", POINTER(c_uint8)),
        ("extradata_size", c_int),

        # Timebase
        ("time_base", AVRational),
        ("pkt_timebase", AVRational),
        ("framerate", AVRational),

        # Video fields
        ("ticks_per_frame", c_int),  # Deprecated in 61.
        ("delay", c_int),
        ("width", c_int),
        ("height", c_int),
        ("coded_width", c_int),
        ("coded_height", c_int),
        ("sample_aspect_ratio", AVRational),  # AVRational
        ("pix_fmt", c_int),  # enum AVPixelFormat
        ("sw_pix_fmt", c_int),  # enum AVPixelFormat
        ("color_primaries", c_int),  # enum AVColorPrimaries
        ("color_trc", c_int),  # enum AVColorTransferCharacteristic
        ("colorspace", c_int),  # enum AVColorSpace
        ("color_range", c_int),  # enum AVColorRange
        ("chroma_sample_location", c_int),  # enum AVChromaLocation
        ("field_order", c_int),  # enum AVFieldOrder
        ("refs", c_int),
        ("has_b_frames", c_int),
        ("slice_flags", c_int),

        ("draw_horiz_band", CFUNCTYPE(None, POINTER(AVCodecContext), POINTER(AVFrame), POINTER(c_int), c_int, c_int, c_int)),
        ("get_format", CFUNCTYPE(c_int, POINTER(AVCodecContext), POINTER(c_int))),

        # Video encoding parameters
        ("max_b_frames", c_int),
        ("b_quant_factor", c_float),
        ("b_quant_offset", c_float),
        ("i_quant_factor", c_float),
        ("i_quant_offset", c_float),
        ("lumi_masking", c_float),
        ("temporal_cplx_masking", c_float),
        ("spatial_cplx_masking", c_float),
        ("p_masking", c_float),
        ("dark_masking", c_float),
        ("nsse_weight", c_int),
        ("me_cmp", c_int),
        ("me_sub_cmp", c_int),
        ("mb_cmp", c_int),
        ("ildct_cmp", c_int),
        ("dia_size", c_int),
        ("last_predictor_count", c_int),
        ("me_pre_cmp", c_int),
        ("pre_dia_size", c_int),
        ("me_subpel_quality", c_int),
        ("me_range", c_int),
        ("mb_decision", c_int),
        ("intra_matrix", POINTER(c_uint16)),
        ("inter_matrix", POINTER(c_uint16)),
        ("chroma_intra_matrix", POINTER(c_uint16)),
        ("intra_dc_precision", c_int),
        ("mb_lmin", c_int),
        ("mb_lmax", c_int),
        ("bidir_refine", c_int),
        ("keyint_min", c_int),
        ("gop_size", c_int),
        ("mv0_threshold", c_int),
        ("slices", c_int),

        # Audio fields
        ("sample_rate", c_int),
        ("sample_fmt", c_int),  # enum AVSampleFormat
        ("ch_layout", AVChannelLayout),  # AVChannelLayout
        ("frame_size", c_int),
        ("block_align", c_int),
        ("cutoff", c_int),
        ("audio_service_type", c_int),  # enum AVAudioServiceType
        ("request_sample_fmt", c_int),  # enum AVSampleFormat
        ("initial_padding", c_int),
        ("trailing_padding", c_int),
        ("seek_preroll", c_int),

        # Encoding parameters
        ("bit_rate_tolerance", c_int),
        ("global_quality", c_int),
        ("compression_level", c_int),
        ("qcompress", c_float),
        ("qblur", c_float),
        ("qmin", c_int),
        ("qmax", c_int),
        ("max_qdiff", c_int),
        ("rc_buffer_size", c_int),
        ("rc_override_count", c_int),
        ("rc_override", POINTER(RcOverride)),
        ("rc_max_rate", c_int64),
        ("rc_min_rate", c_int64),
        ("rc_max_available_vbv_use", c_float),
        ("rc_min_vbv_overflow_use", c_float),
        ("rc_initial_buffer_occupancy", c_int),
        ("trellis", c_int),
        ("stats_out", c_char_p),
        ("stats_in", c_char_p),
        ("workaround_bugs", c_int),
        ("strict_std_compliance", c_int),
        ("error_concealment", c_int),
        ("debug", c_int),
        ("err_recognition", c_int),
        ("hwaccel", POINTER(AVHWAccel)),
        ("hwaccel_context", c_void_p),
        ("hw_frames_ctx", POINTER(AVBufferRef)),
        ("hw_device_ctx", POINTER(AVBufferRef)),
        ("hwaccel_flags", c_int),
        ("extra_hw_frames", c_int),
        ("error", c_uint64 * AV_NUM_DATA_POINTERS),
        ("dct_algo", c_int),
        ("idct_algo", c_int),
        ("bits_per_coded_sample", c_int),
        ("bits_per_raw_sample", c_int),
        ("thread_count", c_int),
        ("thread_type", c_int),
        ("active_thread_type", c_int),
        ("execute",
         CFUNCTYPE(c_int, POINTER(AVCodecContext), CFUNCTYPE(c_int, POINTER(AVCodecContext), c_void_p), c_void_p,
                   POINTER(c_int), c_int, c_int)),
        ("execute2", CFUNCTYPE(c_int, POINTER(AVCodecContext),
                               CFUNCTYPE(c_int, POINTER(AVCodecContext), c_void_p, c_int, c_int), c_void_p,
                               POINTER(c_int), c_int)),
        ("profile", c_int),
        ("level", c_int),
        ("properties", c_uint),
        ("skip_loop_filter", c_int),  # enum AVDiscard
        ("skip_idct", c_int),  # enum AVDiscard
        ("skip_frame", c_int),  # enum AVDiscard
        ("skip_alpha", c_int),
        ("skip_top", c_int),
        ("skip_bottom", c_int),
        ("lowres", c_int),
        ("codec_descriptor", POINTER(AVCodecDescriptor)),
        ("sub_charenc", c_char_p),
        ("sub_charenc_mode", c_int),
        ("subtitle_header_size", c_int),
        ("subtitle_header", POINTER(c_uint8)),
        ("dump_separator", POINTER(c_uint8)),
        ("codec_whitelist", c_char_p),
        ("coded_side_data", POINTER(AVPacketSideData)),
        ("nb_coded_side_data", c_int),
        ("export_side_data", c_int),
        ("max_pixels", c_int64),
        ("apply_cropping", c_int),
        ("discard_damaged_percentage", c_int),
        ("max_samples", c_int64),
        ("get_encode_buffer", CFUNCTYPE(c_int, POINTER(AVCodecContext), POINTER(AVPacket), c_int)),
        ("frame_num", c_int64),
        ("side_data_prefer_packet", POINTER(c_int)),
        ("nb_side_data_prefer_packet", c_uint),
        ("decoded_side_data", POINTER(POINTER(AVFrameSideData))),
        ("nb_decoded_side_data", c_int),
    ]

    compat.add_version_changes('avcodec', 61, AVCodecContext, AVCodecContext_Fields, removals=None)

else:
    AVCodecContext_Fields = [
        ('av_class', POINTER(AVClass)),
        ('log_level_offset', c_int),
        ('codec_type', c_int),
        ('codec', POINTER(AVCodec)),
        ('codec_id', c_int),
        ('codec_tag', c_uint),
        ('priv_data', c_void_p),
        ('internal', POINTER(AVCodecInternal)),
        ('opaque', c_void_p),
        ('bit_rate', c_int64),
        ('bit_rate_tolerance', c_int),
        ('global_quality', c_int),
        ('compression_level', c_int),
        ('flags', c_int),
        ('flags2', c_int),
        ('extradata', POINTER(c_uint8)),
        ('extradata_size', c_int),
        ('time_base', AVRational),
        ('ticks_per_frame', c_int),  # deprecated. to be removed post 61.
        ('delay', c_int),
        ('width', c_int),
        ('height', c_int),
        ('coded_width', c_int),
        ('coded_height', c_int),
        ('gop_size', c_int),
        ('pix_fmt', c_int),
        ('draw_horiz_band', CFUNCTYPE(None,
                                      POINTER(AVCodecContext), POINTER(AVFrame),
                                      c_int * 8, c_int, c_int, c_int)),
        ('get_format', CFUNCTYPE(c_int, POINTER(AVCodecContext), POINTER(c_int))),
        ('max_b_frames', c_int),
        ('b_quant_factor', c_float),
        ('b_frame_strategy', c_int),  # Deprecated. Removed in 59.
        ('b_quant_offset', c_float),
        ('has_b_frames', c_int),
        ('mpeg_quant', c_int),  # Deprecated. Removed in 59.
        ('i_quant_factor', c_float),
        ('i_quant_offset', c_float),
        ('lumi_masking', c_float),
        ('temporal_cplx_masking', c_float),
        ('spatial_cplx_masking', c_float),
        ('p_masking', c_float),
        ('dark_masking', c_float),
        ('slice_count', c_int),
        ('prediction_method', c_int),  # Deprecated. Removed in 59.
        ('slice_offset', POINTER(c_int)),
        ('sample_aspect_ratio', AVRational),  # Moved in 61
        ('me_cmp', c_int),
        ('me_sub_cmp', c_int),
        ('mb_cmp', c_int),
        ('ildct_cmp', c_int),
        ('dia_size', c_int),
        ('last_predictor_count', c_int),
        ('pre_me', c_int),  # Deprecated. Removed in 59.
        ('me_pre_cmp', c_int),
        ('pre_dia_size', c_int),
        ('me_subpel_quality', c_int),
        ('me_range', c_int),
        ('slice_flags', c_int),
        ('mb_decision', c_int),
        ('intra_matrix', POINTER(c_uint16)),
        ('inter_matrix', POINTER(c_uint16)),
        ('scenechange_threshold', c_int),  # Deprecated. Removed in 59.
        ('noise_reduction', c_int),  # Deprecated. Removed in 59.
        ('intra_dc_precision', c_int),
        ('skip_top', c_int),
        ('skip_bottom', c_int),
        ('mb_lmin', c_int),
        ('mb_lmax', c_int),
        ('me_penalty_compensation', c_int),  # Deprecated. Removed in 59.
        ('bidir_refine', c_int),
        ('brd_scale', c_int),  # Deprecated. Removed in 59.
        ('keyint_min', c_int),
        ('refs', c_int),
        ('chromaoffset', c_int),  # Deprecated. Removed in 59.
        ('mv0_threshold', c_int),
        ('b_sensitivity', c_int),  # Deprecated. Removed in 59.
        ('color_primaries', c_int),
        ('color_trc', c_int),
        ('colorspace', c_int),
        ('color_range', c_int),
        ('chroma_sample_location', c_int),
        ('slices', c_int),
        ('field_order', c_int),
        ('sample_rate', c_int),
        ('channels', c_int),
        ('sample_fmt', c_int),
        ('frame_size', c_int),
        ('frame_number', c_int),
        ('block_align', c_int),
        ('cutoff', c_int),
        ('channel_layout', c_uint64),
        ('request_channel_layout', c_uint64),
        ('audio_service_type', c_int),
        ('request_sample_fmt', c_int),
        ('get_buffer2', CFUNCTYPE(c_int, POINTER(AVCodecContext), POINTER(AVFrame), c_int)),
        ('refcounted_frames', c_int),  # Deprecated. Removed in 59.
        ('qcompress', c_float),
        ('qblur', c_float),
        ('qmin', c_int),
        ('qmax', c_int),
        ('max_qdiff', c_int),
        ('rc_buffer_size', c_int),
        ('rc_override_count', c_int),
        ('rc_override', POINTER(RcOverride)),
        ('rc_max_rate', c_int64),
        ('rc_min_rate', c_int64),
        ('rc_max_available_vbv_use', c_float),
        ('rc_min_vbv_overflow_use', c_float),
        ('rc_initial_buffer_occupancy', c_int),
        ('coder_type', c_int),  # Deprecated. Removed in 59.
        ('context_model', c_int),  # Deprecated. Removed in 59.
        ('frame_skip_threshold', c_int),  # Deprecated. Removed in 59.
        ('frame_skip_factor', c_int),  # Deprecated. Removed in 59.
        ('frame_skip_exp', c_int),  # Deprecated. Removed in 59.
        ('frame_skip_cmp', c_int),  # Deprecated. Removed in 59.
        ('trellis', c_int),
        ('min_prediction_order', c_int),  # Deprecated. Removed in 59.
        ('max_prediction_order', c_int),  # Deprecated. Removed in 59.
        ('timecode_frame_start', c_int64),  # Deprecated. Removed in 59.
        ('rtp_callback', CFUNCTYPE(None,  # Deprecated. Removed in 59.
                                  POINTER(AVCodecContext), c_void_p, c_int, c_int)),
        ('rtp_payload_size', c_int),  # Deprecated. Removed in 59.
        ('mv_bits', c_int),  # Deprecated. Removed in 59.
        ('header_bits', c_int),  # Deprecated. Removed in 59.
        ('i_tex_bits', c_int),  # Deprecated. Removed in 59.
        ('p_tex_bits', c_int),  # Deprecated. Removed in 59.
        ('i_count', c_int),  # Deprecated. Removed in 59.
        ('p_count', c_int),  # Deprecated. Removed in 59.
        ('skip_count', c_int),  # Deprecated. Removed in 59.
        ('misc_bits', c_int),  # Deprecated. Removed in 59.
        ('frame_bits', c_int),  # Deprecated. Removed in 59.
        ('stats_out', c_char_p),
        ('stats_in', c_char_p),
        ('workaround_bugs', c_int),
        ('strict_std_compliance', c_int),
        ('error_concealment', c_int),
        ('debug', c_int),
        ('err_recognition', c_int),
        ('reordered_opaque', c_int64),
        ('hwaccel', POINTER(AVHWAccel)),
        ('hwaccel_context', c_void_p),
        ('error', c_uint64 * AV_NUM_DATA_POINTERS),
        ('dct_algo', c_int),
        ('idct_algo', c_int),
        ('bits_per_coded_sample', c_int),
        ('bits_per_raw_sample', c_int),
        ('lowres', c_int),
        ('coded_frame', POINTER(AVFrame)),  # Deprecated. Removed in 59.
        ('thread_count', c_int),
        ('thread_type', c_int),
        ('active_thread_type', c_int),
        ('thread_safe_callbacks', c_int),
        ('execute', CFUNCTYPE(c_int,
                              POINTER(AVCodecContext),
                              CFUNCTYPE(c_int, POINTER(AVCodecContext), c_void_p),
                              c_void_p, c_int, c_int, c_int)),
        ('execute2', CFUNCTYPE(c_int,
                               POINTER(AVCodecContext),
                               CFUNCTYPE(c_int, POINTER(AVCodecContext), c_void_p, c_int, c_int),
                               c_void_p, c_int, c_int)),
        ('nsse_weight', c_int),
        ('profile', c_int),
        ('level', c_int),
        ('skip_loop_filter', c_int),
        ('skip_idct', c_int),
        ('skip_frame', c_int),
        ('subtitle_header', POINTER(c_uint8)),
        ('subtitle_header_size', c_int),
        ('vbv_delay', c_uint64),  # Deprecated. Removed in 59.
        ('side_data_only_packets', c_int),  # Deprecated. Removed in 59.
        ('initial_padding', c_int),
        ('framerate', AVRational),
        # !
        ('sw_pix_fmt', c_int),
        ('pkt_timebase', AVRational),
        ('codec_dexcriptor', AVCodecDescriptor),
        ('pts_correction_num_faulty_pts', c_int64),
        ('pts_correction_num_faulty_dts', c_int64),
        ('pts_correction_last_pts', c_int64),
        ('pts_correction_last_dts', c_int64),
        ('sub_charenc', c_char_p),
        ('sub_charenc_mode', c_int),
        ('skip_alpha', c_int),
        ('seek_preroll', c_int),
        ('debug_mv', c_int),
        ('chroma_intra_matrix', POINTER(c_uint16)),
        ('dump_separator', POINTER(c_uint8)),
        ('codec_whitelist', c_char_p),
        ('properties', c_uint),
        ('coded_side_data', POINTER(AVPacketSideData)),
        ('nb_coded_side_data', c_int),
        ('hw_frames_ctx', POINTER(AVBufferRef)),
        ('sub_text_format', c_int),
        ('trailing_padding', c_int),
        ('max_pixels', c_int64),
        ('hw_device_ctx', POINTER(AVBufferRef)),
        ('hwaccel_flags', c_int),
        ('apply_cropping', c_int),
        ('extra_hw_frames', c_int)
    ]

    compat.add_version_changes('avcodec', 58, AVCodecContext, AVCodecContext_Fields, removals=None)

    for compat_ver in (59, 60):
        compat.add_version_changes('avcodec', compat_ver, AVCodecContext, AVCodecContext_Fields,
            removals=('b_frame_strategy', 'mpeg_quant', 'prediction_method', 'pre_me', 'scenechange_threshold',
                          'noise_reduction', 'me_penalty_compensation', 'brd_scale', 'chromaoffset', 'b_sensitivity',
                          'refcounted_frames', 'coder_type', 'context_model', 'coder_type', 'context_model',
                          'frame_skip_threshold', 'frame_skip_factor', 'frame_skip_exp', 'frame_skip_cmp',
                          'min_prediction_order', 'max_prediction_order', 'timecode_frame_start', 'rtp_callback',
                          'rtp_payload_size', 'mv_bits', 'header_bits', 'i_tex_bits', 'p_tex_bits', 'i_count', 'p_count',
                          'skip_count', 'misc_bits', 'frames_bits', 'coded_frame', 'vbv_delay', 'side_data_only_packets')
        )

AV_CODEC_ID_VP8 = 139
AV_CODEC_ID_VP9 = 167

avcodec.av_packet_unref.argtypes = [POINTER(AVPacket)]
avcodec.av_packet_free.argtypes = [POINTER(POINTER(AVPacket))]
avcodec.av_packet_clone.restype = POINTER(AVPacket)
avcodec.av_packet_clone.argtypes = [POINTER(AVPacket)]
avcodec.av_packet_move_ref.argtypes = [POINTER(AVPacket), POINTER(AVPacket)]
avcodec.avcodec_find_decoder.restype = POINTER(AVCodec)
avcodec.avcodec_find_decoder.argtypes = [c_int]
AVDictionary = libavutil.AVDictionary
avcodec.avcodec_open2.restype = c_int
avcodec.avcodec_open2.argtypes = [POINTER(AVCodecContext),
                                  POINTER(AVCodec),
                                  POINTER(POINTER(AVDictionary))]
avcodec.avcodec_free_context.argtypes = [POINTER(POINTER(AVCodecContext))]
avcodec.av_packet_alloc.restype = POINTER(AVPacket)
avcodec.av_init_packet.argtypes = [POINTER(AVPacket)]

avcodec.avcodec_receive_frame.restype = c_int
avcodec.avcodec_receive_frame.argtypes = [POINTER(AVCodecContext), POINTER(AVFrame)]

avcodec.avcodec_send_packet.restype = c_int
avcodec.avcodec_send_packet.argtypes = [POINTER(AVCodecContext), POINTER(AVPacket)]

avcodec.avcodec_flush_buffers.argtypes = [POINTER(AVCodecContext)]
avcodec.avcodec_alloc_context3.restype = POINTER(AVCodecContext)
avcodec.avcodec_alloc_context3.argtypes = [POINTER(AVCodec)]
avcodec.avcodec_free_context.argtypes = [POINTER(POINTER(AVCodecContext))]
avcodec.avcodec_parameters_to_context.restype = c_int
avcodec.avcodec_parameters_to_context.argtypes = [POINTER(AVCodecContext),
                                                  POINTER(AVCodecParameters)]
avcodec.avcodec_get_name.restype = c_char_p
avcodec.avcodec_get_name.argtypes = [c_int]
avcodec.avcodec_find_decoder_by_name.restype = POINTER(AVCodec)
avcodec.avcodec_find_decoder_by_name.argtypes = [c_char_p]

__all__ = [
    'avcodec',
    'FF_INPUT_BUFFER_PADDING_SIZE',
    'AVPacket',
    'AVCodecContext',
    'AV_CODEC_ID_VP8',
    'AV_CODEC_ID_VP9',
]
