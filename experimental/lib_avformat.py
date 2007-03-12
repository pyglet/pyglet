'''Wrapper for avformat

Generated with:
../tools/wraptypes/wrap.py /usr/include/ffmpeg/avformat.h -o lib_avformat.py

.. Then hacked.  DON'T REGENERATE.
'''

__docformat__ =  'restructuredtext'
__version__ = '$Id$'

import ctypes
from ctypes import *
from avcodec import get_library

_lib = get_library('avformat')

_int_types = (c_int16, c_int32)
if hasattr(ctypes, 'c_int64'):
    # Some builds of ctypes apparently do not have c_int64
    # defined; it's a pretty good bet that these builds do not
    # have 64-bit pointers.
    _int_types += (ctypes.c_int64,)
for t in _int_types:
    if sizeof(t) == sizeof(c_size_t):
        c_ptrdiff_t = t

class c_void(Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', c_int)]



LIBAVFORMAT_BUILD = 4621 	# /usr/include/ffmpeg/avformat.h:8
LIBAVFORMAT_VERSION_INT = 0 	# /usr/include/ffmpeg/avformat.h:10
LIBAVFORMAT_VERSION = 0 	# /usr/include/ffmpeg/avformat.h:11
class struct_AVPacket(Structure):
    __slots__ = [
        'pts',
        'dts',
        'data',
        'size',
        'stream_index',
        'flags',
        'duration',
        'destruct',
        'priv',
    ]
struct_AVPacket._fields_ = [
    ('pts', c_int64),
    ('dts', c_int64),
    ('data', POINTER(c_uint8)),
    ('size', c_int),
    ('stream_index', c_int),
    ('flags', c_int),
    ('duration', c_int),
    ('destruct', POINTER(CFUNCTYPE(None, POINTER(struct_AVPacket)))),
    ('priv', POINTER(None)),
]

AVPacket = struct_AVPacket 	# /usr/include/ffmpeg/avformat.h:42
PKT_FLAG_KEY = 1 	# /usr/include/ffmpeg/avformat.h:43
# /usr/include/ffmpeg/avformat.h:45
av_destruct_packet_nofree = _lib.av_destruct_packet_nofree
av_destruct_packet_nofree.restype = None
av_destruct_packet_nofree.argtypes = [POINTER(AVPacket)]

# /usr/include/ffmpeg/avformat.h:58
av_new_packet = _lib.av_new_packet
av_new_packet.restype = c_int
av_new_packet.argtypes = [POINTER(AVPacket), c_int]

# /usr/include/ffmpeg/avformat.h:59
av_dup_packet = _lib.av_dup_packet
av_dup_packet.restype = c_int
av_dup_packet.argtypes = [POINTER(AVPacket)]

class struct_AVFrac(Structure):
    __slots__ = [
        'val',
        'num',
        'den',
    ]
struct_AVFrac._fields_ = [
    ('val', c_int64),
    ('num', c_int64),
    ('den', c_int64),
]

AVFrac = struct_AVFrac 	# /usr/include/ffmpeg/avformat.h:80
# /usr/include/ffmpeg/avformat.h:82
av_frac_init = _lib.av_frac_init
av_frac_init.restype = None
av_frac_init.argtypes = [POINTER(AVFrac), c_int64, c_int64, c_int64]

# /usr/include/ffmpeg/avformat.h:83
av_frac_add = _lib.av_frac_add
av_frac_add.restype = None
av_frac_add.argtypes = [POINTER(AVFrac), c_int64]

# /usr/include/ffmpeg/avformat.h:84
av_frac_set = _lib.av_frac_set
av_frac_set.restype = None
av_frac_set.argtypes = [POINTER(AVFrac), c_int64]

class struct_AVProbeData(Structure):
    __slots__ = [
        'filename',
        'buf',
        'buf_size',
    ]
struct_AVProbeData._fields_ = [
    ('filename', c_char_p),
    ('buf', POINTER(c_ubyte)),
    ('buf_size', c_int),
]

AVProbeData = struct_AVProbeData 	# /usr/include/ffmpeg/avformat.h:96
AVPROBE_SCORE_MAX = 100 	# /usr/include/ffmpeg/avformat.h:98
class struct_AVFormatParameters(Structure):
    __slots__ = [
        'frame_rate',
        'frame_rate_base',
        'sample_rate',
        'channels',
        'width',
        'height',
        'pix_fmt',
        'image_format',
        'channel',
        'device',
        'standard',
        'mpeg2ts_raw',
        'mpeg2ts_compute_pcr',
        'initial_pause',
        'video_codec_id',
        'audio_codec_id',
    ]
enum_PixelFormat = c_int
class struct_AVImageFormat(Structure):
    __slots__ = [
    ]
struct_AVImageFormat._fields_ = [
    ('_opaque_struct', c_int)
]

enum_CodecID = c_int
struct_AVFormatParameters._fields_ = [
    ('frame_rate', c_int),
    ('frame_rate_base', c_int),
    ('sample_rate', c_int),
    ('channels', c_int),
    ('width', c_int),
    ('height', c_int),
    ('pix_fmt', enum_PixelFormat),
    ('image_format', POINTER(struct_AVImageFormat)),
    ('channel', c_int),
    ('device', c_char_p),
    ('standard', c_char_p),
    ('mpeg2ts_raw', c_int),
    ('mpeg2ts_compute_pcr', c_int),
    ('initial_pause', c_int),
    ('video_codec_id', enum_CodecID),
    ('audio_codec_id', enum_CodecID),
]

AVFormatParameters = struct_AVFormatParameters 	# /usr/include/ffmpeg/avformat.h:120
AVFMT_NOFILE = 1 	# /usr/include/ffmpeg/avformat.h:122
AVFMT_NEEDNUMBER = 2 	# /usr/include/ffmpeg/avformat.h:123
AVFMT_SHOW_IDS = 8 	# /usr/include/ffmpeg/avformat.h:124
AVFMT_RAWPICTURE = 32 	# /usr/include/ffmpeg/avformat.h:125
class struct_AVOutputFormat(Structure):
    __slots__ = [
        'name',
        'long_name',
        'mime_type',
        'extensions',
        'priv_data_size',
        'audio_codec',
        'video_codec',
        'write_header',
        'write_packet',
        'write_trailer',
        'flags',
        'set_parameters',
        'interleave_packet',
        'next',
    ]
class struct_AVFormatContext(Structure):
    __slots__ = [
    ]
struct_AVFormatContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVFormatContext(Structure):
    __slots__ = [
    ]
struct_AVFormatContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVFormatContext(Structure):
    __slots__ = [
    ]
struct_AVFormatContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVFormatContext(Structure):
    __slots__ = [
    ]
struct_AVFormatContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVFormatContext(Structure):
    __slots__ = [
    ]
struct_AVFormatContext._fields_ = [
    ('_opaque_struct', c_int)
]

struct_AVOutputFormat._fields_ = [
    ('name', c_char_p),
    ('long_name', c_char_p),
    ('mime_type', c_char_p),
    ('extensions', c_char_p),
    ('priv_data_size', c_int),
    ('audio_codec', enum_CodecID),
    ('video_codec', enum_CodecID),
    ('write_header', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVFormatContext)))),
    ('write_packet', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVFormatContext), POINTER(AVPacket)))),
    ('write_trailer', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVFormatContext)))),
    ('flags', c_int),
    ('set_parameters', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVFormatContext), POINTER(AVFormatParameters)))),
    ('interleave_packet', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVFormatContext), POINTER(AVPacket), POINTER(AVPacket), c_int))),
    ('next', POINTER(struct_AVOutputFormat)),
]

AVOutputFormat = struct_AVOutputFormat 	# /usr/include/ffmpeg/avformat.h:148
class struct_AVInputFormat(Structure):
    __slots__ = [
        'name',
        'long_name',
        'priv_data_size',
        'read_probe',
        'read_header',
        'read_packet',
        'read_close',
        'read_seek',
        'read_timestamp',
        'flags',
        'extensions',
        'value',
        'read_play',
        'read_pause',
        'next',
    ]
class struct_AVFormatContext(Structure):
    __slots__ = [
    ]
struct_AVFormatContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVFormatContext(Structure):
    __slots__ = [
    ]
struct_AVFormatContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVFormatContext(Structure):
    __slots__ = [
    ]
struct_AVFormatContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVFormatContext(Structure):
    __slots__ = [
    ]
struct_AVFormatContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVFormatContext(Structure):
    __slots__ = [
    ]
struct_AVFormatContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVFormatContext(Structure):
    __slots__ = [
    ]
struct_AVFormatContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVFormatContext(Structure):
    __slots__ = [
    ]
struct_AVFormatContext._fields_ = [
    ('_opaque_struct', c_int)
]

struct_AVInputFormat._fields_ = [
    ('name', c_char_p),
    ('long_name', c_char_p),
    ('priv_data_size', c_int),
    ('read_probe', POINTER(CFUNCTYPE(c_int, POINTER(AVProbeData)))),
    ('read_header', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVFormatContext), POINTER(AVFormatParameters)))),
    ('read_packet', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVFormatContext), POINTER(AVPacket)))),
    ('read_close', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVFormatContext)))),
    ('read_seek', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVFormatContext), c_int, c_int64, c_int))),
    ('read_timestamp', POINTER(CFUNCTYPE(c_int64, POINTER(struct_AVFormatContext), c_int, POINTER(c_int64), c_int64))),
    ('flags', c_int),
    ('extensions', c_char_p),
    ('value', c_int),
    ('read_play', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVFormatContext)))),
    ('read_pause', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVFormatContext)))),
    ('next', POINTER(struct_AVInputFormat)),
]

AVInputFormat = struct_AVInputFormat 	# /usr/include/ffmpeg/avformat.h:203
AVINDEX_KEYFRAME = 1 	# /usr/include/ffmpeg/avformat.h:208
class struct_AVIndexEntry(Structure):
    __slots__ = [
        'pos',
        'timestamp',
        'flags',
        'min_distance',
    ]
struct_AVIndexEntry._fields_ = [
    ('pos', c_int64),
    ('timestamp', c_int64),
    ('flags', c_int),
    ('min_distance', c_int),
]

AVIndexEntry = struct_AVIndexEntry 	# /usr/include/ffmpeg/avformat.h:212
class struct_AVStream(Structure):
    __slots__ = [
        'index',
        'id',
        'codec',
        'r_frame_rate',
        'r_frame_rate_base',
        'priv_data',
        'codec_info_duration',
        'codec_info_nb_frames',
        'pts',
        'time_base',
        'pts_wrap_bits',
        'stream_copy',
        'discard',
        'quality',
        'start_time',
        'duration',
        'need_parsing',
        'parser',
        'cur_dts',
        'last_IP_duration',
        'last_IP_pts',
        'index_entries',
        'nb_index_entries',
        'index_entries_allocated_size',
    ]
class struct_AVCodecContext(Structure):
    __slots__ = [
        'av_class',
        'bit_rate',
        'bit_rate_tolerance',
        'flags',
        'sub_id',
        'me_method',
        'extradata',
        'extradata_size',
        'frame_rate',
        'width',
        'height',
        'gop_size',
        'pix_fmt',
        'rate_emu',
        'draw_horiz_band',
        'sample_rate',
        'channels',
        'sample_fmt',
        'frame_size',
        'frame_number',
        'real_pict_num',
        'delay',
        'qcompress',
        'qblur',
        'qmin',
        'qmax',
        'max_qdiff',
        'max_b_frames',
        'b_quant_factor',
        'rc_strategy',
        'b_frame_strategy',
        'hurry_up',
        'codec',
        'priv_data',
        'rtp_mode',
        'rtp_payload_size',
        'rtp_callback',
        'mv_bits',
        'header_bits',
        'i_tex_bits',
        'p_tex_bits',
        'i_count',
        'p_count',
        'skip_count',
        'misc_bits',
        'frame_bits',
        'opaque',
        'codec_name',
        'codec_type',
        'codec_id',
        'codec_tag',
        'workaround_bugs',
        'luma_elim_threshold',
        'chroma_elim_threshold',
        'strict_std_compliance',
        'b_quant_offset',
        'error_resilience',
        'get_buffer',
        'release_buffer',
        'has_b_frames',
        'block_align',
        'parse_only',
        'mpeg_quant',
        'stats_out',
        'stats_in',
        'rc_qsquish',
        'rc_qmod_amp',
        'rc_qmod_freq',
        'rc_override',
        'rc_override_count',
        'rc_eq',
        'rc_max_rate',
        'rc_min_rate',
        'rc_buffer_size',
        'rc_buffer_aggressivity',
        'i_quant_factor',
        'i_quant_offset',
        'rc_initial_cplx',
        'dct_algo',
        'lumi_masking',
        'temporal_cplx_masking',
        'spatial_cplx_masking',
        'p_masking',
        'dark_masking',
        'unused',
        'idct_algo',
        'slice_count',
        'slice_offset',
        'error_concealment',
        'dsp_mask',
        'bits_per_sample',
        'prediction_method',
        'sample_aspect_ratio',
        'coded_frame',
        'debug',
        'debug_mv',
        'error',
        'mb_qmin',
        'mb_qmax',
        'me_cmp',
        'me_sub_cmp',
        'mb_cmp',
        'ildct_cmp',
        'dia_size',
        'last_predictor_count',
        'pre_me',
        'me_pre_cmp',
        'pre_dia_size',
        'me_subpel_quality',
        'get_format',
        'dtg_active_format',
        'me_range',
        'frame_rate_base',
        'intra_quant_bias',
        'inter_quant_bias',
        'color_table_id',
        'internal_buffer_count',
        'internal_buffer',
        'global_quality',
        'coder_type',
        'context_model',
        'slice_flags',
        'xvmc_acceleration',
        'mb_decision',
        'intra_matrix',
        'inter_matrix',
        'stream_codec_tag',
        'scenechange_threshold',
        'lmin',
        'lmax',
        'palctrl',
        'noise_reduction',
        'reget_buffer',
        'rc_initial_buffer_occupancy',
        'inter_threshold',
        'flags2',
        'error_rate',
        'antialias_algo',
        'quantizer_noise_shaping',
        'thread_count',
        'execute',
        'thread_opaque',
        'me_threshold',
        'mb_threshold',
        'intra_dc_precision',
        'nsse_weight',
        'skip_top',
        'skip_bottom',
        'profile',
        'level',
        'lowres',
        'coded_width',
        'coded_height',
        'frame_skip_threshold',
        'frame_skip_factor',
        'frame_skip_exp',
        'frame_skip_cmp',
        'border_masking',
        'mb_lmin',
        'mb_lmax',
    ]
class struct_AVCLASS(Structure):
    __slots__ = [
    ]
struct_AVCLASS._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVCLASS(Structure):
    __slots__ = [
    ]
struct_AVCLASS._fields_ = [
    ('_opaque_struct', c_int)
]

AVClass = struct_AVCLASS 	# /usr/include/ffmpeg/avcodec.h:728
class struct_AVFrame(Structure):
    __slots__ = [
        'data',
        'linesize',
        'base',
        'key_frame',
        'pict_type',
        'pts',
        'coded_picture_number',
        'display_picture_number',
        'quality',
        'age',
        'reference',
        'qscale_table',
        'qstride',
        'mbskip_table',
        'motion_val',
        'mb_type',
        'motion_subsample_log2',
        'opaque',
        'error',
        'type',
        'repeat_pict',
        'qscale_type',
        'interlaced_frame',
        'top_field_first',
        'pan_scan',
        'palette_has_changed',
        'buffer_hints',
        'dct_coeff',
        'ref_index',
    ]
class struct_AVPanScan(Structure):
    __slots__ = [
        'id',
        'width',
        'height',
        'position',
    ]
struct_AVPanScan._fields_ = [
    ('id', c_int),
    ('width', c_int),
    ('height', c_int),
    ('position', (c_int16 * 2) * 3),
]

AVPanScan = struct_AVPanScan 	# /usr/include/ffmpeg/avcodec.h:474
struct_AVFrame._fields_ = [
    ('data', POINTER(c_uint8) * 4),
    ('linesize', c_int * 4),
    ('base', POINTER(c_uint8) * 4),
    ('key_frame', c_int),
    ('pict_type', c_int),
    ('pts', c_int64),
    ('coded_picture_number', c_int),
    ('display_picture_number', c_int),
    ('quality', c_int),
    ('age', c_int),
    ('reference', c_int),
    ('qscale_table', POINTER(c_int8)),
    ('qstride', c_int),
    ('mbskip_table', POINTER(c_uint8)),
    ('motion_val', POINTER(c_int16 * 2) * 2),
    ('mb_type', POINTER(c_uint32)),
    ('motion_subsample_log2', c_uint8),
    ('opaque', POINTER(None)),
    ('error', c_uint64 * 4),
    ('type', c_int),
    ('repeat_pict', c_int),
    ('qscale_type', c_int),
    ('interlaced_frame', c_int),
    ('top_field_first', c_int),
    ('pan_scan', POINTER(AVPanScan)),
    ('palette_has_changed', c_int),
    ('buffer_hints', c_int),
    ('dct_coeff', POINTER(c_short)),
    ('ref_index', POINTER(c_int8) * 2),
]

AVFrame = struct_AVFrame 	# /usr/include/ffmpeg/avcodec.h:721
enum_SampleFormat = c_int
class struct_AVCodec(Structure):
    __slots__ = [
    ]
struct_AVCodec._fields_ = [
    ('_opaque_struct', c_int)
]

enum_CodecType = c_int
class struct_RcOverride(Structure):
    __slots__ = [
        'start_frame',
        'end_frame',
        'qscale',
        'quality_factor',
    ]
struct_RcOverride._fields_ = [
    ('start_frame', c_int),
    ('end_frame', c_int),
    ('qscale', c_int),
    ('quality_factor', c_float),
]

RcOverride = struct_RcOverride 	# /usr/include/ffmpeg/avcodec.h:308
class struct_AVRational(Structure):
    __slots__ = [
        'num',
        'den',
    ]
struct_AVRational._fields_ = [
    ('num', c_int),
    ('den', c_int),
]

AVRational = struct_AVRational 	# /usr/include/ffmpeg/rational.h:38
class struct_AVPaletteControl(Structure):
    __slots__ = [
    ]
struct_AVPaletteControl._fields_ = [
    ('_opaque_struct', c_int)
]

struct_AVCodecContext._fields_ = [
    ('av_class', POINTER(AVClass)),
    ('bit_rate', c_int),
    ('bit_rate_tolerance', c_int),
    ('flags', c_int),
    ('sub_id', c_int),
    ('me_method', c_int),
    ('extradata', POINTER(None)),
    ('extradata_size', c_int),
    ('frame_rate', c_int),
    ('width', c_int),
    ('height', c_int),
    ('gop_size', c_int),
    ('pix_fmt', enum_PixelFormat),
    ('rate_emu', c_int),
    ('draw_horiz_band', POINTER(CFUNCTYPE(None, POINTER(struct_AVCodecContext), POINTER(AVFrame), c_int * 4, c_int, c_int, c_int))),
    ('sample_rate', c_int),
    ('channels', c_int),
    ('sample_fmt', enum_SampleFormat),
    ('frame_size', c_int),
    ('frame_number', c_int),
    ('real_pict_num', c_int),
    ('delay', c_int),
    ('qcompress', c_float),
    ('qblur', c_float),
    ('qmin', c_int),
    ('qmax', c_int),
    ('max_qdiff', c_int),
    ('max_b_frames', c_int),
    ('b_quant_factor', c_float),
    ('rc_strategy', c_int),
    ('b_frame_strategy', c_int),
    ('hurry_up', c_int),
    ('codec', POINTER(struct_AVCodec)),
    ('priv_data', POINTER(None)),
    ('rtp_mode', c_int),
    ('rtp_payload_size', c_int),
    ('rtp_callback', POINTER(CFUNCTYPE(None, POINTER(struct_AVCodecContext), POINTER(None), c_int, c_int))),
    ('mv_bits', c_int),
    ('header_bits', c_int),
    ('i_tex_bits', c_int),
    ('p_tex_bits', c_int),
    ('i_count', c_int),
    ('p_count', c_int),
    ('skip_count', c_int),
    ('misc_bits', c_int),
    ('frame_bits', c_int),
    ('opaque', POINTER(None)),
    ('codec_name', c_char * 32),
    ('codec_type', enum_CodecType),
    ('codec_id', enum_CodecID),
    ('codec_tag', c_uint),
    ('workaround_bugs', c_int),
    ('luma_elim_threshold', c_int),
    ('chroma_elim_threshold', c_int),
    ('strict_std_compliance', c_int),
    ('b_quant_offset', c_float),
    ('error_resilience', c_int),
    ('get_buffer', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVCodecContext), POINTER(AVFrame)))),
    ('release_buffer', POINTER(CFUNCTYPE(None, POINTER(struct_AVCodecContext), POINTER(AVFrame)))),
    ('has_b_frames', c_int),
    ('block_align', c_int),
    ('parse_only', c_int),
    ('mpeg_quant', c_int),
    ('stats_out', c_char_p),
    ('stats_in', c_char_p),
    ('rc_qsquish', c_float),
    ('rc_qmod_amp', c_float),
    ('rc_qmod_freq', c_int),
    ('rc_override', POINTER(RcOverride)),
    ('rc_override_count', c_int),
    ('rc_eq', c_char_p),
    ('rc_max_rate', c_int),
    ('rc_min_rate', c_int),
    ('rc_buffer_size', c_int),
    ('rc_buffer_aggressivity', c_float),
    ('i_quant_factor', c_float),
    ('i_quant_offset', c_float),
    ('rc_initial_cplx', c_float),
    ('dct_algo', c_int),
    ('lumi_masking', c_float),
    ('temporal_cplx_masking', c_float),
    ('spatial_cplx_masking', c_float),
    ('p_masking', c_float),
    ('dark_masking', c_float),
    ('unused', c_int),
    ('idct_algo', c_int),
    ('slice_count', c_int),
    ('slice_offset', POINTER(c_int)),
    ('error_concealment', c_int),
    ('dsp_mask', c_uint),
    ('bits_per_sample', c_int),
    ('prediction_method', c_int),
    ('sample_aspect_ratio', AVRational),
    ('coded_frame', POINTER(AVFrame)),
    ('debug', c_int),
    ('debug_mv', c_int),
    ('error', c_uint64 * 4),
    ('mb_qmin', c_int),
    ('mb_qmax', c_int),
    ('me_cmp', c_int),
    ('me_sub_cmp', c_int),
    ('mb_cmp', c_int),
    ('ildct_cmp', c_int),
    ('dia_size', c_int),
    ('last_predictor_count', c_int),
    ('pre_me', c_int),
    ('me_pre_cmp', c_int),
    ('pre_dia_size', c_int),
    ('me_subpel_quality', c_int),
    ('get_format', POINTER(CFUNCTYPE(enum_PixelFormat, POINTER(struct_AVCodecContext), POINTER(enum_PixelFormat)))),
    ('dtg_active_format', c_int),
    ('me_range', c_int),
    ('frame_rate_base', c_int),
    ('intra_quant_bias', c_int),
    ('inter_quant_bias', c_int),
    ('color_table_id', c_int),
    ('internal_buffer_count', c_int),
    ('internal_buffer', POINTER(None)),
    ('global_quality', c_int),
    ('coder_type', c_int),
    ('context_model', c_int),
    ('slice_flags', c_int),
    ('xvmc_acceleration', c_int),
    ('mb_decision', c_int),
    ('intra_matrix', POINTER(c_uint16)),
    ('inter_matrix', POINTER(c_uint16)),
    ('stream_codec_tag', c_uint),
    ('scenechange_threshold', c_int),
    ('lmin', c_int),
    ('lmax', c_int),
    ('palctrl', POINTER(struct_AVPaletteControl)),
    ('noise_reduction', c_int),
    ('reget_buffer', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVCodecContext), POINTER(AVFrame)))),
    ('rc_initial_buffer_occupancy', c_int),
    ('inter_threshold', c_int),
    ('flags2', c_int),
    ('error_rate', c_int),
    ('antialias_algo', c_int),
    ('quantizer_noise_shaping', c_int),
    ('thread_count', c_int),
    ('execute', POINTER(CFUNCTYPE(c_int, POINTER(struct_AVCodecContext), CFUNCTYPE(c_int, POINTER(struct_AVCodecContext), POINTER(None)), POINTER(POINTER(None)), POINTER(c_int), c_int))),
    ('thread_opaque', POINTER(None)),
    ('me_threshold', c_int),
    ('mb_threshold', c_int),
    ('intra_dc_precision', c_int),
    ('nsse_weight', c_int),
    ('skip_top', c_int),
    ('skip_bottom', c_int),
    ('profile', c_int),
    ('level', c_int),
    ('lowres', c_int),
    ('coded_width', c_int),
    ('coded_height', c_int),
    ('frame_skip_threshold', c_int),
    ('frame_skip_factor', c_int),
    ('frame_skip_exp', c_int),
    ('frame_skip_cmp', c_int),
    ('border_masking', c_float),
    ('mb_lmin', c_int),
    ('mb_lmax', c_int),
]

AVCodecContext = struct_AVCodecContext 	# /usr/include/ffmpeg/avcodec.h:1883
class struct_AVCodecParserContext(Structure):
    __slots__ = [
    ]
struct_AVCodecParserContext._fields_ = [
    ('_opaque_struct', c_int)
]

struct_AVStream._fields_ = [
    ('index', c_int),
    ('id', c_int),
    ('codec', AVCodecContext),
    ('r_frame_rate', c_int),
    ('r_frame_rate_base', c_int),
    ('priv_data', POINTER(None)),
    ('codec_info_duration', c_int64),
    ('codec_info_nb_frames', c_int),
    ('pts', AVFrac),
    ('time_base', AVRational),
    ('pts_wrap_bits', c_int),
    ('stream_copy', c_int),
    ('discard', c_int),
    ('quality', c_float),
    ('start_time', c_int64),
    ('duration', c_int64),
    ('need_parsing', c_int),
    ('parser', POINTER(struct_AVCodecParserContext)),
    ('cur_dts', c_int64),
    ('last_IP_duration', c_int),
    ('last_IP_pts', c_int64),
    ('index_entries', POINTER(AVIndexEntry)),
    ('nb_index_entries', c_int),
    ('index_entries_allocated_size', c_int),
]

AVStream = struct_AVStream 	# /usr/include/ffmpeg/avformat.h:256
AVFMTCTX_NOHEADER = 1 	# /usr/include/ffmpeg/avformat.h:258
MAX_STREAMS = 20 	# /usr/include/ffmpeg/avformat.h:261
class struct_AVFormatContext(Structure):
    __slots__ = [
        'av_class',
        'iformat',
        'oformat',
        'priv_data',
        'pb',
        'nb_streams',
        'streams',
        'filename',
        'timestamp',
        'title',
        'author',
        'copyright',
        'comment',
        'album',
        'year',
        'track',
        'genre',
        'ctx_flags',
        'packet_buffer',
        'start_time',
        'duration',
        'file_size',
        'bit_rate',
        'cur_st',
        'cur_ptr',
        'cur_len',
        'cur_pkt',
        'data_offset',
        'index_built',
        'mux_rate',
        'packet_size',
        'preload',
        'max_delay',
    ]
class struct_anon_17(Structure):
    __slots__ = [
        'buffer',
        'buffer_size',
        'buf_ptr',
        'buf_end',
        'opaque',
        'read_packet',
        'write_packet',
        'seek',
        'pos',
        'must_flush',
        'eof_reached',
        'write_flag',
        'is_streamed',
        'max_packet_size',
        'checksum',
        'checksum_ptr',
        'update_checksum',
        'error',
    ]
offset_t = c_int64 	# /usr/include/ffmpeg/avio.h:6
struct_anon_17._fields_ = [
    ('buffer', POINTER(c_ubyte)),
    ('buffer_size', c_int),
    ('buf_ptr', POINTER(c_ubyte)),
    ('buf_end', POINTER(c_ubyte)),
    ('opaque', POINTER(None)),
    ('read_packet', POINTER(CFUNCTYPE(c_int, POINTER(None), POINTER(c_uint8), c_int))),
    ('write_packet', POINTER(CFUNCTYPE(c_int, POINTER(None), POINTER(c_uint8), c_int))),
    ('seek', POINTER(CFUNCTYPE(c_int, POINTER(None), offset_t, c_int))),
    ('pos', offset_t),
    ('must_flush', c_int),
    ('eof_reached', c_int),
    ('write_flag', c_int),
    ('is_streamed', c_int),
    ('max_packet_size', c_int),
    ('checksum', c_ulong),
    ('checksum_ptr', POINTER(c_ubyte)),
    ('update_checksum', POINTER(CFUNCTYPE(c_ulong, c_ulong, POINTER(c_uint8), c_uint))),
    ('error', c_int),
]

ByteIOContext = struct_anon_17 	# /usr/include/ffmpeg/avio.h:86
class struct_AVPacketList(Structure):
    __slots__ = [
    ]
struct_AVPacketList._fields_ = [
    ('_opaque_struct', c_int)
]

struct_AVFormatContext._fields_ = [
    ('av_class', POINTER(AVClass)),
    ('iformat', POINTER(struct_AVInputFormat)),
    ('oformat', POINTER(struct_AVOutputFormat)),
    ('priv_data', POINTER(None)),
    ('pb', ByteIOContext),
    ('nb_streams', c_int),
    ('streams', POINTER(AVStream) * 20),
    ('filename', c_char * 1024),
    ('timestamp', c_int64),
    ('title', c_char * 512),
    ('author', c_char * 512),
    ('copyright', c_char * 512),
    ('comment', c_char * 512),
    ('album', c_char * 512),
    ('year', c_int),
    ('track', c_int),
    ('genre', c_char * 32),
    ('ctx_flags', c_int),
    ('packet_buffer', POINTER(struct_AVPacketList)),
    ('start_time', c_int64),
    ('duration', c_int64),
    ('file_size', c_int64),
    ('bit_rate', c_int),
    ('cur_st', POINTER(AVStream)),
    ('cur_ptr', POINTER(c_uint8)),
    ('cur_len', c_int),
    ('cur_pkt', AVPacket),
    ('data_offset', c_int64),
    ('index_built', c_int),
    ('mux_rate', c_int),
    ('packet_size', c_int),
    ('preload', c_int),
    ('max_delay', c_int),
]

AVFormatContext = struct_AVFormatContext 	# /usr/include/ffmpeg/avformat.h:321
class struct_AVPacketList(Structure):
    __slots__ = [
        'pkt',
        'next',
    ]
struct_AVPacketList._fields_ = [
    ('pkt', AVPacket),
    ('next', POINTER(struct_AVPacketList)),
]

AVPacketList = struct_AVPacketList 	# /usr/include/ffmpeg/avformat.h:326
class struct_AVInputImageContext(Structure):
    __slots__ = [
    ]
struct_AVInputImageContext._fields_ = [
    ('_opaque_struct', c_int)
]

class struct_AVInputImageContext(Structure):
    __slots__ = [
    ]
struct_AVInputImageContext._fields_ = [
    ('_opaque_struct', c_int)
]

AVInputImageContext = struct_AVInputImageContext 	# /usr/include/ffmpeg/avformat.h:333
class struct_AVImageInfo(Structure):
    __slots__ = [
        'pix_fmt',
        'width',
        'height',
        'interleaved',
        'pict',
    ]
class struct_AVPicture(Structure):
    __slots__ = [
        'data',
        'linesize',
    ]
struct_AVPicture._fields_ = [
    ('data', POINTER(c_uint8) * 4),
    ('linesize', c_int * 4),
]

AVPicture = struct_AVPicture 	# /usr/include/ffmpeg/avcodec.h:1975
struct_AVImageInfo._fields_ = [
    ('pix_fmt', enum_PixelFormat),
    ('width', c_int),
    ('height', c_int),
    ('interleaved', c_int),
    ('pict', AVPicture),
]

AVImageInfo = struct_AVImageInfo 	# /usr/include/ffmpeg/avformat.h:341
AVIMAGE_INTERLEAVED = 1 	# /usr/include/ffmpeg/avformat.h:344
class struct_AVImageFormat(Structure):
    __slots__ = [
        'name',
        'extensions',
        'img_probe',
        'img_read',
        'supported_pixel_formats',
        'img_write',
        'flags',
        'next',
    ]
struct_AVImageFormat._fields_ = [
    ('name', c_char_p),
    ('extensions', c_char_p),
    ('img_probe', POINTER(CFUNCTYPE(c_int, POINTER(AVProbeData)))),
    ('img_read', POINTER(CFUNCTYPE(c_int, POINTER(ByteIOContext), CFUNCTYPE(c_int, POINTER(None), POINTER(AVImageInfo)), POINTER(None)))),
    ('supported_pixel_formats', c_int),
    ('img_write', POINTER(CFUNCTYPE(c_int, POINTER(ByteIOContext), POINTER(AVImageInfo)))),
    ('flags', c_int),
    ('next', POINTER(struct_AVImageFormat)),
]

AVImageFormat = struct_AVImageFormat 	# /usr/include/ffmpeg/avformat.h:362
# /usr/include/ffmpeg/avformat.h:364
av_register_image_format = _lib.av_register_image_format
av_register_image_format.restype = None
av_register_image_format.argtypes = [POINTER(AVImageFormat)]

# /usr/include/ffmpeg/avformat.h:365
av_probe_image_format = _lib.av_probe_image_format
av_probe_image_format.restype = POINTER(AVImageFormat)
av_probe_image_format.argtypes = [POINTER(AVProbeData)]

# /usr/include/ffmpeg/avformat.h:366
guess_image_format = _lib.guess_image_format
guess_image_format.restype = POINTER(AVImageFormat)
guess_image_format.argtypes = [c_char_p]

# /usr/include/ffmpeg/avformat.h:367
av_guess_image2_codec = _lib.av_guess_image2_codec
av_guess_image2_codec.restype = enum_CodecID
av_guess_image2_codec.argtypes = [c_char_p]

# /usr/include/ffmpeg/avformat.h:368
av_read_image = _lib.av_read_image
av_read_image.restype = c_int
av_read_image.argtypes = [POINTER(ByteIOContext), c_char_p, POINTER(AVImageFormat), CFUNCTYPE(c_int, POINTER(None), POINTER(AVImageInfo)), POINTER(None)]

# /usr/include/ffmpeg/avformat.h:371
av_write_image = _lib.av_write_image
av_write_image.restype = c_int
av_write_image.argtypes = [POINTER(ByteIOContext), POINTER(AVImageFormat), POINTER(AVImageInfo)]

# /usr/include/ffmpeg/avformat.h:528
av_register_input_format = _lib.av_register_input_format
av_register_input_format.restype = None
av_register_input_format.argtypes = [POINTER(AVInputFormat)]

# /usr/include/ffmpeg/avformat.h:529
av_register_output_format = _lib.av_register_output_format
av_register_output_format.restype = None
av_register_output_format.argtypes = [POINTER(AVOutputFormat)]

# /usr/include/ffmpeg/avformat.h:530
guess_stream_format = _lib.guess_stream_format
guess_stream_format.restype = POINTER(AVOutputFormat)
guess_stream_format.argtypes = [c_char_p, c_char_p, c_char_p]

# /usr/include/ffmpeg/avformat.h:532
guess_format = _lib.guess_format
guess_format.restype = POINTER(AVOutputFormat)
guess_format.argtypes = [c_char_p, c_char_p, c_char_p]

# /usr/include/ffmpeg/avformat.h:534
av_guess_codec = _lib.av_guess_codec
av_guess_codec.restype = enum_CodecID
av_guess_codec.argtypes = [POINTER(AVOutputFormat), c_char_p, c_char_p, c_char_p, enum_CodecType]

class struct__IO_FILE(Structure):
    __slots__ = [
    ]
struct__IO_FILE._fields_ = [
    ('_opaque_struct', c_int)
]

class struct__IO_FILE(Structure):
    __slots__ = [
    ]
struct__IO_FILE._fields_ = [
    ('_opaque_struct', c_int)
]

FILE = struct__IO_FILE 	# /usr/include/gentoo-multilib/amd64/stdio.h:46
# /usr/include/ffmpeg/avformat.h:537
av_hex_dump = _lib.av_hex_dump
av_hex_dump.restype = None
av_hex_dump.argtypes = [POINTER(FILE), POINTER(c_uint8), c_int]

# /usr/include/ffmpeg/avformat.h:538
av_pkt_dump = _lib.av_pkt_dump
av_pkt_dump.restype = None
av_pkt_dump.argtypes = [POINTER(FILE), POINTER(AVPacket), c_int]

# /usr/include/ffmpeg/avformat.h:540
av_register_all = _lib.av_register_all
av_register_all.restype = None
av_register_all.argtypes = []

class struct_FifoBuffer(Structure):
    __slots__ = [
        'buffer',
        'rptr',
        'wptr',
        'end',
    ]
struct_FifoBuffer._fields_ = [
    ('buffer', POINTER(c_uint8)),
    ('rptr', POINTER(c_uint8)),
    ('wptr', POINTER(c_uint8)),
    ('end', POINTER(c_uint8)),
]

FifoBuffer = struct_FifoBuffer 	# /usr/include/ffmpeg/avformat.h:545
# /usr/include/ffmpeg/avformat.h:547
fifo_init = _lib.fifo_init
fifo_init.restype = c_int
fifo_init.argtypes = [POINTER(FifoBuffer), c_int]

# /usr/include/ffmpeg/avformat.h:548
fifo_free = _lib.fifo_free
fifo_free.restype = None
fifo_free.argtypes = [POINTER(FifoBuffer)]

# /usr/include/ffmpeg/avformat.h:549
fifo_size = _lib.fifo_size
fifo_size.restype = c_int
fifo_size.argtypes = [POINTER(FifoBuffer), POINTER(c_uint8)]

# /usr/include/ffmpeg/avformat.h:550
fifo_read = _lib.fifo_read
fifo_read.restype = c_int
fifo_read.argtypes = [POINTER(FifoBuffer), POINTER(c_uint8), c_int, POINTER(POINTER(c_uint8))]

# /usr/include/ffmpeg/avformat.h:551
fifo_write = _lib.fifo_write
fifo_write.restype = None
fifo_write.argtypes = [POINTER(FifoBuffer), POINTER(c_uint8), c_int, POINTER(POINTER(c_uint8))]

# /usr/include/ffmpeg/avformat.h:552
put_fifo = _lib.put_fifo
put_fifo.restype = c_int
put_fifo.argtypes = [POINTER(ByteIOContext), POINTER(FifoBuffer), c_int, POINTER(POINTER(c_uint8))]

# /usr/include/ffmpeg/avformat.h:553
fifo_realloc = _lib.fifo_realloc
fifo_realloc.restype = None
fifo_realloc.argtypes = [POINTER(FifoBuffer), c_uint]

# /usr/include/ffmpeg/avformat.h:556
av_find_input_format = _lib.av_find_input_format
av_find_input_format.restype = POINTER(AVInputFormat)
av_find_input_format.argtypes = [c_char_p]

# /usr/include/ffmpeg/avformat.h:557
av_probe_input_format = _lib.av_probe_input_format
av_probe_input_format.restype = POINTER(AVInputFormat)
av_probe_input_format.argtypes = [POINTER(AVProbeData), c_int]

# /usr/include/ffmpeg/avformat.h:558
av_open_input_stream = _lib.av_open_input_stream
av_open_input_stream.restype = c_int
av_open_input_stream.argtypes = [POINTER(POINTER(AVFormatContext)), POINTER(ByteIOContext), c_char_p, POINTER(AVInputFormat), POINTER(AVFormatParameters)]

# /usr/include/ffmpeg/avformat.h:561
av_open_input_file = _lib.av_open_input_file
av_open_input_file.restype = c_int
av_open_input_file.argtypes = [POINTER(POINTER(AVFormatContext)), c_char_p, POINTER(AVInputFormat), c_int, POINTER(AVFormatParameters)]

# /usr/include/ffmpeg/avformat.h:566
av_alloc_format_context = _lib.av_alloc_format_context
av_alloc_format_context.restype = POINTER(AVFormatContext)
av_alloc_format_context.argtypes = []

AVERROR_UNKNOWN = -1 	# /usr/include/ffmpeg/avformat.h:568
AVERROR_IO = -2 	# /usr/include/ffmpeg/avformat.h:569
AVERROR_NUMEXPECTED = -3 	# /usr/include/ffmpeg/avformat.h:570
AVERROR_INVALIDDATA = -4 	# /usr/include/ffmpeg/avformat.h:571
AVERROR_NOMEM = -5 	# /usr/include/ffmpeg/avformat.h:572
AVERROR_NOFMT = -6 	# /usr/include/ffmpeg/avformat.h:573
AVERROR_NOTSUPP = -7 	# /usr/include/ffmpeg/avformat.h:574
# /usr/include/ffmpeg/avformat.h:576
av_find_stream_info = _lib.av_find_stream_info
av_find_stream_info.restype = c_int
av_find_stream_info.argtypes = [POINTER(AVFormatContext)]

# /usr/include/ffmpeg/avformat.h:577
av_read_packet = _lib.av_read_packet
av_read_packet.restype = c_int
av_read_packet.argtypes = [POINTER(AVFormatContext), POINTER(AVPacket)]

# /usr/include/ffmpeg/avformat.h:578
av_read_frame = _lib.av_read_frame
av_read_frame.restype = c_int
av_read_frame.argtypes = [POINTER(AVFormatContext), POINTER(AVPacket)]

# /usr/include/ffmpeg/avformat.h:579
av_seek_frame = _lib.av_seek_frame
av_seek_frame.restype = c_int
av_seek_frame.argtypes = [POINTER(AVFormatContext), c_int, c_int64, c_int]

# /usr/include/ffmpeg/avformat.h:580
av_read_play = _lib.av_read_play
av_read_play.restype = c_int
av_read_play.argtypes = [POINTER(AVFormatContext)]

# /usr/include/ffmpeg/avformat.h:581
av_read_pause = _lib.av_read_pause
av_read_pause.restype = c_int
av_read_pause.argtypes = [POINTER(AVFormatContext)]

# /usr/include/ffmpeg/avformat.h:582
av_close_input_file = _lib.av_close_input_file
av_close_input_file.restype = None
av_close_input_file.argtypes = [POINTER(AVFormatContext)]

# /usr/include/ffmpeg/avformat.h:583
av_new_stream = _lib.av_new_stream
av_new_stream.restype = POINTER(AVStream)
av_new_stream.argtypes = [POINTER(AVFormatContext), c_int]

# /usr/include/ffmpeg/avformat.h:584
av_set_pts_info = _lib.av_set_pts_info
av_set_pts_info.restype = None
av_set_pts_info.argtypes = [POINTER(AVStream), c_int, c_int, c_int]

AVSEEK_FLAG_BACKWARD = 1 	# /usr/include/ffmpeg/avformat.h:587
AVSEEK_FLAG_BYTE = 2 	# /usr/include/ffmpeg/avformat.h:589
# /usr/include/ffmpeg/avformat.h:592
av_find_default_stream_index = _lib.av_find_default_stream_index
av_find_default_stream_index.restype = c_int
av_find_default_stream_index.argtypes = [POINTER(AVFormatContext)]

# /usr/include/ffmpeg/avformat.h:593
av_index_search_timestamp = _lib.av_index_search_timestamp
av_index_search_timestamp.restype = c_int
av_index_search_timestamp.argtypes = [POINTER(AVStream), c_int64, c_int]

# /usr/include/ffmpeg/avformat.h:594
av_add_index_entry = _lib.av_add_index_entry
av_add_index_entry.restype = c_int
av_add_index_entry.argtypes = [POINTER(AVStream), c_int64, c_int64, c_int, c_int]

# /usr/include/ffmpeg/avformat.h:596
av_seek_frame_binary = _lib.av_seek_frame_binary
av_seek_frame_binary.restype = c_int
av_seek_frame_binary.argtypes = [POINTER(AVFormatContext), c_int, c_int64, c_int]

# /usr/include/ffmpeg/avformat.h:599
av_set_parameters = _lib.av_set_parameters
av_set_parameters.restype = c_int
av_set_parameters.argtypes = [POINTER(AVFormatContext), POINTER(AVFormatParameters)]

# /usr/include/ffmpeg/avformat.h:600
av_write_header = _lib.av_write_header
av_write_header.restype = c_int
av_write_header.argtypes = [POINTER(AVFormatContext)]

# /usr/include/ffmpeg/avformat.h:601
av_write_frame = _lib.av_write_frame
av_write_frame.restype = c_int
av_write_frame.argtypes = [POINTER(AVFormatContext), POINTER(AVPacket)]

# /usr/include/ffmpeg/avformat.h:602
av_interleaved_write_frame = _lib.av_interleaved_write_frame
av_interleaved_write_frame.restype = c_int
av_interleaved_write_frame.argtypes = [POINTER(AVFormatContext), POINTER(AVPacket)]

# /usr/include/ffmpeg/avformat.h:604
av_write_trailer = _lib.av_write_trailer
av_write_trailer.restype = c_int
av_write_trailer.argtypes = [POINTER(AVFormatContext)]

# /usr/include/ffmpeg/avformat.h:606
dump_format = _lib.dump_format
dump_format.restype = None
dump_format.argtypes = [POINTER(AVFormatContext), c_int, c_char_p, c_int]

# /usr/include/ffmpeg/avformat.h:610
parse_image_size = _lib.parse_image_size
parse_image_size.restype = c_int
parse_image_size.argtypes = [POINTER(c_int), POINTER(c_int), c_char_p]

# /usr/include/ffmpeg/avformat.h:611
parse_frame_rate = _lib.parse_frame_rate
parse_frame_rate.restype = c_int
parse_frame_rate.argtypes = [POINTER(c_int), POINTER(c_int), c_char_p]

# /usr/include/ffmpeg/avformat.h:612
parse_date = _lib.parse_date
parse_date.restype = c_int64
parse_date.argtypes = [c_char_p, c_int]

# /usr/include/ffmpeg/avformat.h:614
av_gettime = _lib.av_gettime
av_gettime.restype = c_int64
av_gettime.argtypes = []

FFM_PACKET_SIZE = 4096 	# /usr/include/ffmpeg/avformat.h:617
# /usr/include/ffmpeg/avformat.h:618
ffm_read_write_index = _lib.ffm_read_write_index
ffm_read_write_index.restype = offset_t
ffm_read_write_index.argtypes = [c_int]

# /usr/include/ffmpeg/avformat.h:619
ffm_write_write_index = _lib.ffm_write_write_index
ffm_write_write_index.restype = None
ffm_write_write_index.argtypes = [c_int, offset_t]

# /usr/include/ffmpeg/avformat.h:620
ffm_set_write_index = _lib.ffm_set_write_index
ffm_set_write_index.restype = None
ffm_set_write_index.argtypes = [POINTER(AVFormatContext), offset_t, offset_t]

# /usr/include/ffmpeg/avformat.h:622
find_info_tag = _lib.find_info_tag
find_info_tag.restype = c_int
find_info_tag.argtypes = [c_char_p, c_int, c_char_p, c_char_p]

# /usr/include/ffmpeg/avformat.h:624
get_frame_filename = _lib.get_frame_filename
get_frame_filename.restype = c_int
get_frame_filename.argtypes = [c_char_p, c_int, c_char_p, c_int]

# /usr/include/ffmpeg/avformat.h:626
filename_number_test = _lib.filename_number_test
filename_number_test.restype = c_int
filename_number_test.argtypes = [c_char_p]


__all__ = ['LIBAVFORMAT_BUILD', 'LIBAVFORMAT_VERSION_INT',
'LIBAVFORMAT_VERSION', 'AVPacket', 'PKT_FLAG_KEY',
'av_destruct_packet_nofree', 'av_new_packet', 'av_dup_packet', 'AVFrac',
'av_frac_init', 'av_frac_add', 'av_frac_set', 'AVProbeData',
'AVPROBE_SCORE_MAX', 'AVFormatParameters', 'AVFMT_NOFILE', 'AVFMT_NEEDNUMBER',
'AVFMT_SHOW_IDS', 'AVFMT_RAWPICTURE', 'AVOutputFormat', 'AVInputFormat',
'AVINDEX_KEYFRAME', 'AVIndexEntry', 'AVStream', 'AVFMTCTX_NOHEADER',
'MAX_STREAMS', 'AVFormatContext', 'AVPacketList', 'AVInputImageContext',
'AVImageInfo', 'AVIMAGE_INTERLEAVED', 'AVImageFormat',
'av_register_image_format', 'av_probe_image_format', 'guess_image_format',
'av_guess_image2_codec', 'av_read_image', 'av_write_image', 'mpegps_init',
'mpegts_init', 'rm_init', 'crc_init', 'img_init', 'img2_init', 'asf_init',
'avienc_init', 'avidec_init', 'swf_init', 'mov_init', 'movenc_init',
'flvenc_init', 'flvdec_init', 'jpeg_init', 'gif_init', 'au_init', 'amr_init',
'ff_wav_init', 'pcm_read_seek', 'raw_init', 'mp3_init', 'yuv4mpeg_init',
'ogg_init', 'ff_dv_init', 'ffm_init', 'redir_open', 'fourxm_init', 'str_init',
'roq_init', 'ipmovie_init', 'nut_init', 'wc3_init', 'westwood_init',
'film_init', 'idcin_init', 'flic_init', 'vmd_init', 'matroska_init',
'sol_init', 'ea_init', 'nsvdec_init', 'av_register_input_format',
'av_register_output_format', 'guess_stream_format', 'guess_format',
'av_guess_codec', 'av_hex_dump', 'av_pkt_dump', 'av_register_all',
'FifoBuffer', 'fifo_init', 'fifo_free', 'fifo_size', 'fifo_read',
'fifo_write', 'put_fifo', 'fifo_realloc', 'av_find_input_format',
'av_probe_input_format', 'av_open_input_stream', 'av_open_input_file',
'av_alloc_format_context', 'AVERROR_UNKNOWN', 'AVERROR_IO',
'AVERROR_NUMEXPECTED', 'AVERROR_INVALIDDATA', 'AVERROR_NOMEM',
'AVERROR_NOFMT', 'AVERROR_NOTSUPP', 'av_find_stream_info', 'av_read_packet',
'av_read_frame', 'av_seek_frame', 'av_read_play', 'av_read_pause',
'av_close_input_file', 'av_new_stream', 'av_set_pts_info',
'AVSEEK_FLAG_BACKWARD', 'AVSEEK_FLAG_BYTE', 'av_find_default_stream_index',
'av_index_search_timestamp', 'av_add_index_entry', 'av_seek_frame_binary',
'av_set_parameters', 'av_write_header', 'av_write_frame',
'av_interleaved_write_frame', 'av_write_trailer', 'dump_format',
'parse_image_size', 'parse_frame_rate', 'parse_date', 'av_gettime',
'FFM_PACKET_SIZE', 'ffm_read_write_index', 'ffm_write_write_index',
'ffm_set_write_index', 'find_info_tag', 'get_frame_filename',
'filename_number_test', 'video_grab_init', 'audio_init', 'dv1394_init',
'dc1394_init']
