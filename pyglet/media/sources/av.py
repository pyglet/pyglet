# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------
"""Wrap FFmpeg using ctypes and provide a similar API to AVbin which is now
unmaintained.
"""
from ctypes import (c_int, c_uint16, c_int32, c_int64, c_uint32, c_uint64, 
    c_uint8, c_uint, c_double, c_float, c_ubyte, c_size_t, c_char, c_char_p, 
    c_void_p, addressof, byref, cast, POINTER, CFUNCTYPE, Structure, Union, 
    create_string_buffer, memmove)

import pyglet.lib
from pyglet.media.exceptions import MediaFormatException
from pyglet.compat import asbytes

avformat = pyglet.lib.load_library('avformat-57')
avcodec = pyglet.lib.load_library('avcodec-57')
avutil = pyglet.lib.load_library('avutil-55')
swscale = pyglet.lib.load_library('swscale-4')
swresample = pyglet.lib.load_library('swresample-2')

AVBIN_RESULT_ERROR = -1
AVBIN_RESULT_OK = 0
AVbinResult = c_int

AVBIN_STREAM_TYPE_UNKNOWN = 0
AVBIN_STREAM_TYPE_VIDEO = 1
AVBIN_STREAM_TYPE_AUDIO = 2
AVbinStreamType = c_int

AVBIN_SAMPLE_FORMAT_U8 = 0
AVBIN_SAMPLE_FORMAT_S16 = 1
AVBIN_SAMPLE_FORMAT_S32 = 2
AVBIN_SAMPLE_FORMAT_FLOAT = 3
AVBIN_SAMPLE_FORMAT_DOUBLE = 4
AVBIN_SAMPLE_FORMAT_U8P = 5
AVBIN_SAMPLE_FORMAT_S16P = 6
AVBIN_SAMPLE_FORMAT_S32P = 7
AVBIN_SAMPLE_FORMAT_FLTP = 8
AVBIN_SAMPLE_FORMAT_DBLP = 9
AVBIN_SAMPLE_FORMAT_S64 = 10
AVBIN_SAMPLE_FORMAT_S64P = 11
AVbinSampleFormat = c_int

AVBIN_LOG_QUIET = -8
AVBIN_LOG_PANIC = 0
AVBIN_LOG_FATAL = 8
AVBIN_LOG_ERROR = 16
AVBIN_LOG_WARNING = 24
AVBIN_LOG_INFO = 32
AVBIN_LOG_VERBOSE = 40
AVBIN_LOG_DEBUG = 48
AVbinLogLevel = c_int

AVbinFileP = c_void_p
AVbinStreamP = c_void_p

Timestamp = c_int64

AVMEDIA_TYPE_UNKNOWN = -1
AVMEDIA_TYPE_VIDEO = 0
AVMEDIA_TYPE_AUDIO = 1
AVMEDIA_TYPE_DATA = 2
AVMEDIA_TYPE_SUBTITLE = 3
AVMEDIA_TYPE_ATTACHMENT = 4
AVMEDIA_TYPE_NB = 5

AV_SAMPLE_FMT_U8 = 0
AV_SAMPLE_FMT_S16 = 1
AV_SAMPLE_FMT_S32 = 2
AV_SAMPLE_FMT_FLT = 3
AV_SAMPLE_FORMAT_DOUBLE = 4
AV_SAMPLE_FMT_U8P = 5
AV_SAMPLE_FMT_S16P = 6
AV_SAMPLE_FMT_S32P = 7
AV_SAMPLE_FMT_FLTP = 8
AV_SAMPLE_FMT_DBLP = 9
AV_SAMPLE_FMT_S64 = 10
AV_SAMPLE_FMT_S64P = 11

AV_NUM_DATA_POINTERS = 8
PIX_FMT_RGB24 = 2
SWS_FAST_BILINEAR = 1

AVSEEK_FLAG_BACKWARD = 1 # ///< seek backward
AVSEEK_FLAG_BYTE = 2     # ///< seeking based on position in bytes
AVSEEK_FLAG_ANY = 4      # ///< seek to any frame, even non-keyframes
AVSEEK_FLAG_FRAME = 8    # ///< seeking based on frame number

MAX_REORDER_DELAY = 16
FF_INPUT_BUFFER_PADDING_SIZE = 32
SWR_CH_MAX = 64

INT64_MIN = -2**63+1
INT64_MAX = 0x7FFFFFFFFFFFFFFF

class AVbinFileInfo(Structure):
    _fields_ = [
        ('n_streams', c_int),
        ('start_time', Timestamp),
        ('duration', Timestamp),
        ('title', c_char * 512),
        ('author', c_char * 512),
        ('copyright', c_char * 512),
        ('comment', c_char * 512),
        ('album', c_char * 512),
        ('year', c_int),
        ('track', c_char * 32),
        ('genre', c_char * 32),
    ]

class _AVbinStreamInfoVideo8(Structure):
    _fields_ = [
        ('width', c_uint),
        ('height', c_uint),
        ('sample_aspect_num', c_uint),
        ('sample_aspect_den', c_uint),
        ('frame_rate_num', c_uint),
        ('frame_rate_den', c_uint),
    ]

class _AVbinStreamInfoAudio8(Structure):
    _fields_ = [
        ('sample_format', c_int),
        ('sample_rate', c_uint),
        ('sample_bits', c_uint),
        ('channels', c_uint),
    ]

class _AVbinStreamInfoUnion8(Union):
    _fields_ = [
        ('video', _AVbinStreamInfoVideo8),
        ('audio', _AVbinStreamInfoAudio8),
    ]

class AVbinStreamInfo8(Structure):
    _fields_ = [
        ('type', c_int),
        ('u', _AVbinStreamInfoUnion8)
    ]

class AVbinPacket(Structure):
    _fields_ = [
        ('timestamp', Timestamp),
        ('stream_index', c_int),
        ('data', POINTER(c_uint8)),
        ('size', c_size_t),
    ]

class AVPacketSideData(Structure): pass
class AVBufferRef(Structure): pass
class AVPacket(Structure):
    _fields_ = [
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
        ('convergence_duration', c_int64) #Deprecated
    ]

class AVPacketList(Structure): pass
class AVInputFormat(Structure): 
    _fields_ = [
        ('name', c_char_p)
    ]
class AVOutputFormat(Structure): pass
class AVDictionaryEntry(Structure):
    _fields_ = [
        ('key', c_char_p),
        ('value', c_char_p)
    ]
class AVDictionary(Structure):
    _fields_ = [
        ('count', c_int),
        ('elems', POINTER(AVDictionaryEntry))
    ]
class AVClass(Structure): pass
class AVIOContext(Structure): pass
class AVIndexEntry(Structure): pass
class AVCodecParserContext(Structure): pass
class AVRational(Structure):
    _fields_ = [
        ('num', c_int),
        ('den', c_int)
    ]
class AVStreamInfo(Structure):
    _fields_ = [
        ('last_dts', c_int64),
        ('duration_gcd', c_int64),
        ('duration_count', c_int),
        ('rfps_duration_sum', c_int64),
        ('duration_error', POINTER(c_double * 2 * (30*12+30+3+6))),
        ('codec_info_duration', c_int64), 
        ('codec_info_duration_fields', c_int64), 
        ('found_decoder', c_int), 
        ('last_duration', c_int64), 
        ('fps_first_dts', c_int64), 
        ('fps_first_dts_idx', c_int), 
        ('fps_last_dts', c_int64), 
        ('fps_last_dts_idx', c_int), 
     ]

class AVProbeData(Structure):
    _fields_ = [
        ('filename', c_char_p),
        ('buf', POINTER(c_ubyte)),
        ('buf_size', c_int),
        ('mime_type', c_char_p)
    ]

class FFFrac(Structure): pass
class AVStreamInternal(Structure): pass

class AVCodecParameters(Structure):
    _fields_ = [
        ('codec_type', c_int),
        ('codec_id', c_int),
        ('codec_tag', c_uint32),
        ('extradata', POINTER(c_uint8)),
        ('extradata_size', c_int),
        ('format', c_int),
        ('bit_rate', c_int64),
        ('bits_per_coded_sample', c_int),
        ('bits_per_raw_sample', c_int),
        ('profile', c_int),
        ('level', c_int),
        ('width', c_int),
        ('height', c_int),
        ('sample_aspect_ratio', AVRational),
        ('field_order', c_int),
        ('color_range', c_int),
        ('color_primaries', c_int),
        ('color_trc', c_int),
        ('color_space', c_int),
        ('chroma_location', c_int),
        ('video_delay', c_int),
        ('channel_layout', c_uint64),
        ('channels', c_int),
        ('sample_rate', c_int),
        ('block_align', c_int),
        ('frame_size', c_int),
        ('initial_padding', c_int),
        ('trailing_padding', c_int),
        ('seek_preroll', c_int),
    ]

class AVCodecInternal(Structure): pass
class AVCodec(Structure):
    _fields_ = [
        ('name', c_char_p),
        ('long_name', c_char_p),
        # And more...
    ]

class AVFrameSideData(Structure): pass
class AVFrame(Structure): 
    _fields_ = [
        ('data', POINTER(c_uint8) * AV_NUM_DATA_POINTERS),
        ('linesize', c_int * AV_NUM_DATA_POINTERS),
        ('extended_data', POINTER(POINTER(c_uint8))),
        ('width', c_int),
        ('height', c_int),
        ('nb_samples', c_int),
        ('format', c_int),
        ('key_frame', c_int),
        ('pict_type', c_int),
        ('sample_aspect_ratio', AVRational),
        ('pts', c_int64),
        ('pkt_pts', c_int64),
        ('pkt_dts', c_int64),
        ('coded_picture_number', c_int),
        ('display_picture_number', c_int),
        ('quality', c_int),
        ('opaque', c_void_p),
        ('error', c_uint64),
        ('repeat_pict', c_int),
        ('interlaced_frame', c_int),
        ('top_field_first', c_int),
        ('palette_has_changed', c_int),
        ('reordered_opaque', c_int64),
        ('sample_rate', c_int),
        ('channel_layout', c_uint64),
        ('buf', POINTER(AVBufferRef) * AV_NUM_DATA_POINTERS),
        ('extended_buf', POINTER(POINTER(AVBufferRef))),
        ('nb_extended_buf', c_int),
        ('side_data', POINTER(POINTER(AVFrameSideData))),
        ('nb_side_data', c_int)
    ]

class AVCodecContext(Structure): pass

AVCodecContext._fields_ = [
        ('av_class', POINTER(AVClass)),
        ('log_level_offset', c_int),
        ('codec_type', c_int),
        ('codec', POINTER(AVCodec)),
        ('name', c_char * 32),
        ('codec_id', c_int),
        ('codec_tag', c_uint),
        ('stream_codec_tag', c_uint),
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
        ('ticks_per_frame', c_int),
        ('delay', c_int),
        ('width', c_int),
        ('height', c_int),
        ('coded_width', c_int),
        ('coded_height', c_int),
        ('gop_size', c_int),
        ('pix_fmt', c_int),
        ('me_method', c_int),
        ('draw_horiz_band', CFUNCTYPE(None,
            POINTER(AVCodecContext), POINTER(AVFrame),
            c_int*8, c_int, c_int, c_int)),
        ('get_format', CFUNCTYPE(c_int,
            POINTER(AVCodecContext), POINTER(c_int))),
        ('max_b_frames', c_int),
        ('b_quant_factor', c_float),
        ('rc_strategy', c_int),
        ('b_frame_strategy', c_int),
        ('b_quant_offset', c_float),
        ('has_b_frames', c_int),
        ('mpeg_quant', c_int),
        ('i_quant_factor', c_float),
        ('i_quant_offset', c_float),
        ('lumi_masking', c_float),
        ('temporal_cplx_masking', c_float),
        ('spatial_cplx_masking', c_float),
        ('p_masking', c_float),
        ('dark_masking', c_float),
        ('slice_count', c_int),
        ('prediction_method', c_int),
        ('slice_offset', POINTER(c_int)),
        ('sample_aspect_ratio', AVRational),
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
        ('dtg_active_format', c_int),
        ('me_range', c_int),
        ('intra_quant_bias', c_int),
        ('inter_quant_bias', c_int),
        ('slice_flags', c_int),
        ('xvmc_acceleration', c_int),
        ('mb_decision', c_int),
        ('intra_matrix', POINTER(c_uint16)),
        ('inter_matrix', POINTER(c_uint16)),
        ('scenechange_threshold', c_int),
        ('noise_reduction', c_int),
        ('me_threshold', c_int),
        ('mb_threshold', c_int),
        ('intra_dc_precision', c_int),
        ('skip_top', c_int),
        ('skip_bottom', c_int),
        ('border_masking', c_float),
        ('mb_lmin', c_int),
        ('mb_lmax', c_int),
        ('me_penalty_compensation', c_int),
        ('bidir_refine', c_int),
        ('brd_scale', c_int),
        ('keyint_min', c_int),
        ('refs', c_int),
        ('chromaoffset', c_int),
        ('scenechange_factor', c_int),
        ('mv0_threshold', c_int),
        ('b_sensitivity', c_int),
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
    ]

class AVFrac(Structure):
    _fields_ = [
        ('val', c_int64),
        ('num', c_int64),
        ('den', c_int64),
    ]

class AVStream(Structure):
    _fields_ = [
        ('index', c_int),
        ('id', c_int),
        ('codec', POINTER(AVCodecContext)),
        ('priv_data', c_void_p),
        ('pts', AVFrac),
        ('time_base', AVRational),
        ('start_time', c_int64),
        ('duration', c_int64),
        ('nb_frames', c_int64),
        ('disposition', c_int),
        ('discard', c_int),
        ('sample_aspect_ratio', AVRational),
        ('metadata', POINTER(AVDictionary)),
        ('avg_frame_rate', AVRational),
        ('attached_pic', AVPacket),
        ('side_data', POINTER(AVPacketSideData)),
        ('nb_side_data', c_int),
        ('event_flags', c_int),
        ('info', POINTER(AVStreamInfo)),
        ('pts_wrap_bits', c_int),
        ('first_dts', c_int64),
        ('cur_dts', c_int64),
        ('last_IP_pts', c_int64),
        ('last_IP_duration', c_int),
        ('probe_packets', c_int),
        ('codec_info_nb_frames', c_int),
        ('need_parsing', c_int),
        ('parser', POINTER(AVCodecParserContext)),
        ('last_in_packet_buffer', POINTER(AVPacketList)),
        ('probe_data', AVProbeData),
        ('pts_buffer', c_int64 * (MAX_REORDER_DELAY+1)),
        ('index_entries', POINTER(AVIndexEntry)),
        ('nb_index_entries', c_int),
        ('index_entries_allocated_size', c_uint),
        ('r_frame_rate', AVRational),
        ('stream_identifier', c_int),
        ('interleaver_chunk_size', c_int64),
        ('interleaver_chunk_duration', c_int64),
        ('request_probe', c_int),
        ('skip_to_keyframe', c_int),
        ('skip_samples', c_int),
        ('start_skip_samples', c_int64),
        ('first_discard_sample', c_int64),
        ('last_discard_sample', c_int64),
        ('nb_decoded_frames', c_int),
        ('mux_ts_offset', c_int64),
        ('pts_wrap_reference', c_int64),
        ('pts_wrap_behavior', c_int),
        ('update_initial_durations_done', c_int),
        ('pts_reorder_error', c_int64 * (MAX_REORDER_DELAY+1)),
        ('pts_reorder_error_count', c_uint8 * (MAX_REORDER_DELAY+1)),
        ('last_dts_for_order_check', c_int64),
        ('dts_ordered', c_uint8),
        ('dts_misordered', c_uint8),
        ('inject_global_side_data', c_int),
        ('recommended_encoder_configuration', c_char_p),
        ('display_aspect_ratio', AVRational),
        ('priv_pts', POINTER(FFFrac)),
        ('internal', POINTER(AVStreamInternal)),
        ('codecpar', POINTER(AVCodecParameters)),
    ]
class AVProgram(Structure): pass
class AVChapter(Structure): pass
class AVFormatInternal(Structure): pass
class AVIOInterruptCB(Structure):
    _fields_ = [
        ('callback', CFUNCTYPE(c_int, c_void_p)),
        ('opaque', c_void_p)
    ]


class AVFormatContext(Structure):
    pass

AVFormatContext._fields_ = [
        ('av_class', POINTER(AVClass)),
        ('iformat', POINTER(AVInputFormat)),
        ('oformat', POINTER(AVOutputFormat)),
        ('priv_data', c_void_p),
        ('pb', POINTER(AVIOContext)),
        ('ctx_flags', c_int),
        ('nb_streams', c_uint),
        ('streams', POINTER(POINTER(AVStream))),
        ('filename', c_char*1024),
        ('start_time', c_int64),
        ('duration', c_int64),
        ('bit_rate', c_int64),
        ('packet_size', c_uint),
        ('max_delay', c_int),
        ('flag', c_int),
        ('probesize', c_int64),
        ('max_analyze_duration', c_int64),
        ('key', POINTER(c_uint8)),
        ('keylen', c_int),
        ('nb_programs', c_uint),
        ('programs', POINTER(POINTER(AVProgram))),
        ('video_codec_id', c_int),
        ('audio_codec_id', c_int),
        ('subtitle_codec_id', c_int),
        ('max_index_size', c_uint),
        ('max_picture_buffer', c_uint),
        ('nb_chapters', c_uint),
        ('chapters', POINTER(POINTER(AVChapter))),
        ('metadata', POINTER(AVDictionary)),
        ('start_time_realtime', c_int64),
        ('fps_probe_size', c_int),
        ('error_recognition', c_int),
        ('interrupt_callback', AVIOInterruptCB),
        ('debug', c_int),
        ('max_interleave_delta', c_int64),
        ('strict_std_compliance', c_int),
        ('event_flags', c_int),
        ('max_ts_probe', c_int),
        ('avoid_negative_ts', c_int),
        ('ts_id', c_int),
        ('audio_preload', c_int),
        ('max_chunk_duration', c_int),
        ('max_chunk_size', c_int),
        ('use_wallclock_as_timestamps', c_int),
        ('avio_flags', c_int),
        ('duration_estimation_method', c_uint),
        ('skip_initial_bytes', c_int64),
        ('correct_ts_overflow', c_uint),
        ('seek2any', c_int),
        ('flush_packets', c_int),
        ('probe_score', c_int),
        ('format_probesize', c_int),
        ('codec_whitelist', c_char_p),
        ('format_whitelist', c_char_p),
        ('internal', POINTER(AVFormatInternal)),
        ('io_repositioned', c_int),
        ('video_codec', POINTER(AVCodec)),
        ('audio_codec', POINTER(AVCodec)),
        ('subtitle_codec', POINTER(AVCodec)),
        ('data_codec', POINTER(AVCodec)),
        ('metadata_header_padding', c_int),
        ('opaque', c_void_p),
        ('control_message_cb', CFUNCTYPE(c_int, 
            POINTER(AVFormatContext), c_int, c_void_p,
            c_size_t)),
        ('output_ts_offset', c_int64),
        ('dump_separator', POINTER(c_uint8)),
        ('data_codec_id', c_uint),
        ('protocol_whitelist', c_char_p),
        ('io_open', CFUNCTYPE(c_int, 
            POINTER(AVFormatContext), 
            POINTER(POINTER(AVIOContext)),
            c_char_p, c_int,
            POINTER(POINTER(AVDictionary)))),
        ('io_close', CFUNCTYPE(None, 
            POINTER(AVFormatContext), POINTER(AVIOContext))),
        ('protocol_blacklist', c_char_p),
        ('max_streams', c_int)
        ]

class AVbinFile(Structure):
    _fields_ = [
        ('context', POINTER(AVFormatContext)),
        ('packet', POINTER(AVPacket))
    ]

class AVbinStream(Structure):
    _fields_ = [
        ('type', c_int32),
        ('format_context', POINTER(AVFormatContext)),
        ('codec_context', POINTER(AVCodecContext)),
        ('frame', POINTER(AVFrame)),
    ]

class AVPicture(Structure):
    _fields_ = [
        ('data', POINTER(c_uint8) * AV_NUM_DATA_POINTERS),
        ('linesize', c_int * AV_NUM_DATA_POINTERS)
    ]

class SwsContext(Structure): pass
class SwsFilter(Structure): pass

class SwrContext(Structure): pass
   
AV_TIME_BASE = 1000000  
AV_TIME_BASE_Q = AVRational(1, AV_TIME_BASE)

# Wrap FFmpeg functions. Only those needed.
AVbinLogCallback = CFUNCTYPE(None,
    c_char_p, c_int, c_char_p)

avcodec.av_packet_unref.argtypes = [POINTER(AVPacket)]
avcodec.avcodec_find_decoder.restype = POINTER(AVCodec)
avcodec.avcodec_find_decoder.argtypes = [c_int]
avcodec.avcodec_open2.restype = c_int
avcodec.avcodec_open2.argtypes = [POINTER(AVCodecContext),
            POINTER(AVCodec), 
            POINTER(POINTER(AVDictionary))]
avcodec.avcodec_free_context.argtypes = [POINTER(POINTER(AVCodecContext))]
avcodec.av_packet_alloc.restype = POINTER(AVPacket)
avcodec.av_init_packet.argtypes = [POINTER(AVPacket)]
avcodec.avcodec_decode_audio4.restype = c_int
avcodec.avcodec_decode_audio4.argtypes = [POINTER(AVCodecContext),
            POINTER(AVFrame), POINTER(c_int),
            POINTER(AVPacket)]
avcodec.avcodec_decode_video2.restype = c_int
avcodec.avcodec_decode_video2.argtypes = [POINTER(AVCodecContext),
            POINTER(AVFrame), POINTER(c_int),
            POINTER(AVPacket)]
avcodec.avpicture_fill.restype = c_int
avcodec.avpicture_fill.argtypes = [POINTER(AVPicture),
            POINTER(c_uint8), c_int,
            c_int, c_int]
avcodec.avcodec_flush_buffers.argtypes = [POINTER(AVCodecContext)]
avcodec.avcodec_alloc_context3.restype = POINTER(AVCodecContext)
avcodec.avcodec_alloc_context3.argtypes = [POINTER(AVCodec)]
avcodec.avcodec_free_context.argtypes = [POINTER(POINTER(AVCodecContext))]
avcodec.avcodec_parameters_to_context.restype = c_int
avcodec.avcodec_parameters_to_context.argtypes = [POINTER(AVCodecContext),
            POINTER(AVCodecParameters)]


avutil.av_version_info.restype = c_char_p
avutil.av_dict_get.restype = POINTER(AVDictionaryEntry)
avutil.av_dict_get.argtypes = [POINTER(AVDictionary),
            c_char_p, POINTER(AVDictionaryEntry),
            c_int]
avutil.av_rescale_q.restype = c_int64
avutil.av_rescale_q.argtypes = [c_int64, AVRational, AVRational]
avutil.av_samples_get_buffer_size.restype = c_int
avutil.av_samples_get_buffer_size.argtypes = [POINTER(c_int),
            c_int, c_int, c_int]
avutil.av_frame_alloc.restype = POINTER(AVFrame)
avutil.av_frame_free.argtypes = [POINTER(POINTER(AVFrame))]
avutil.av_get_default_channel_layout.restype = c_int64
avutil.av_get_default_channel_layout.argtypes = [c_int]
avutil.av_get_bytes_per_sample.restype = c_int
avutil.av_get_bytes_per_sample.argtypes = [c_int]
avutil.av_strerror.restype = c_int
avutil.av_strerror.argtypes = [c_int, c_char_p, c_size_t]


avformat.av_register_all.restype = None
avformat.av_find_input_format.restype = c_int
avformat.av_find_input_format.argtypes = [c_int]
avformat.avformat_open_input.restype = c_int
avformat.avformat_open_input.argtypes = [
            POINTER(POINTER(AVFormatContext)),
            c_char_p,
            POINTER(AVInputFormat),
            POINTER(POINTER(AVDictionary))]
avformat.avformat_find_stream_info.restype = c_int
avformat.avformat_find_stream_info.argtypes = [
            POINTER(AVFormatContext),
            POINTER(POINTER(AVDictionary))]
avformat.avformat_close_input.restype = None            
avformat.avformat_close_input.argtypes = [
                            POINTER(POINTER(AVFormatContext))]
avformat.av_read_frame.restype = c_int
avformat.av_read_frame.argtypes = [POINTER(AVFormatContext),
            POINTER(AVPacket)]
avformat.av_seek_frame.restype = c_int
avformat.av_seek_frame.argtypes = [POINTER(AVFormatContext),
        c_int, c_int64, c_int]
avformat.avformat_seek_file.restype = c_int
avformat.avformat_seek_file.argtypes = [POINTER(AVFormatContext),
        c_int, c_int64, c_int64, c_int64, c_int]


swscale.sws_getCachedContext.restype = POINTER(SwsContext)
swscale.sws_getCachedContext.argtypes = [POINTER(SwsContext),
            c_int, c_int, c_int, c_int, 
            c_int, c_int, c_int, 
            POINTER(SwsFilter), POINTER(SwsFilter), 
            POINTER(c_double)]
swscale.sws_freeContext.argtypes = [POINTER(SwsContext)]
swscale.sws_scale.restype = c_int
swscale.sws_scale.argtypes = [POINTER(SwsContext),
        POINTER(POINTER(c_uint8)),
        POINTER(c_int),
        c_int, c_int,
        POINTER(POINTER(c_uint8)),
        POINTER(c_int)]


swresample.swr_alloc_set_opts.restype = POINTER(SwrContext)
swresample.swr_alloc_set_opts.argtypes = [POINTER(SwrContext),
        c_int64, c_int, c_int, c_int64,
        c_int, c_int, c_int, c_void_p]
swresample.swr_init.restype = c_int
swresample.swr_init.argtypes = [POINTER(SwrContext)]
swresample.swr_free.argtypes = [POINTER(POINTER(SwrContext))]
swresample.swr_convert.restype = c_int
swresample.swr_convert.argtypes = [POINTER(SwrContext),
        POINTER(c_uint8) * SWR_CH_MAX,
        c_int,
        POINTER(POINTER(c_uint8)),
        c_int]

###################

class FFmpegException(MediaFormatException):
    pass

def avbin_get_version():
    '''Return an informative version string of FFmpeg'''
    return avutil.av_version_info().decode()

def avbin_get_audio_buffer_size():
    '''Return the audio buffer size'''
    # TODO: Should be determined by code. See ffplay.c in FFmpeg to get some
    # ideas how to do that.
    return 192000

# This AVbin function seems useless to me with the current wrapping we are 
# doing. I leave it here for reference.

# def avbin_have_feature(feature):
#     if feature == 'frame_rate':
#         # See note on avbin_have_feature() in avbin.h
#         return False
#     elif feature == 'options':
#         return True
#     elif feature == 'info':
#         return True
#     return False

def avbin_init():
    '''Initialize libavformat and register all the muxers, demuxers and 
    protocols.'''
    avformat.av_register_all()

def avbin_open_filename(filename):
    '''Open the media file.

    :rtype: AVbinFile
        :return: The structure containing all the information for the media.
    '''
    file = AVbinFile()
    result = avformat.avformat_open_input(byref(file.context), 
                                          filename, 
                                          None, 
                                          None)
    if result != 0:
        raise FFmpegException('Error opening file ' + filename)

    result = avformat.avformat_find_stream_info(file.context, None)
    if result < 0:
        raise FFmpegException('Could not find stream info')

    return file

def avbin_close_file(file):
    '''Close the media file and free resources.'''
    if file.packet:
        avcodec.av_packet_unref(file.packet)
    avformat.avformat_close_input(byref(file.context))

def avbin_file_info(file):
    '''Get information on the file:

        - number of streams
        - duration
        - artist
        - album
        - date
        - track

    :rtype: AVbinFileInfo
        :return: The structure containing all the meta information.
    '''
    info = AVbinFileInfo()
    info.n_streams = file.context.contents.nb_streams
    info.start_time = file.context.contents.start_time
    info.duration = file.context.contents.duration

    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('title'), None, 0)
    if entry:
        info.title = entry.contents.value 

    entry = avutil.av_dict_get(file.context.contents.metadata, 
                               asbytes('artist'), 
                               None, 
                               0) \
            or \
            avutil.av_dict_get(file.context.contents.metadata, 
                               asbytes('album_artist'), 
                               None, 
                               0)
    if entry:
        info.author = entry.contents.value

    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('copyright'), None, 0)
    if entry:
        info.copyright = entry.contents.value
    
    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('comment'), None, 0)
    if entry:
        info.comment = entry.contents.value
    
    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('album'), None, 0)
    if entry:
        info.album = entry.contents.value
    
    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('date'), None, 0)
    if entry:
        info.year = int(entry.contents.value)
    
    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('track'), None, 0)
    if entry:
        info.track = entry.contents.value
    
    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('genre'), None, 0)
    if entry:
        info.genre = entry.contents.value

    return info

def avbin_stream_info(file, stream_index):
    info = AVbinStreamInfo8()
    context = file.context.contents.streams[stream_index].contents.codecpar.contents
    if context.codec_type == AVMEDIA_TYPE_VIDEO:
        info.type = AVBIN_STREAM_TYPE_VIDEO
        info.u.video.width = context.width
        info.u.video.height = context.height
        info.u.video.sample_aspect_num = context.sample_aspect_ratio.num
        info.u.video.sample_aspect_den = context.sample_aspect_ratio.den
    elif context.codec_type == AVMEDIA_TYPE_AUDIO:
        info.type = AVBIN_STREAM_TYPE_AUDIO
        info.u.audio.sample_rate = context.sample_rate
        info.u.audio.channels = context.channels
        if context.format == AV_SAMPLE_FMT_U8:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_U8
            info.u.audio.sample_bits = 8
        elif context.format == AV_SAMPLE_FMT_U8P:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_U8P
            info.u.audio.sample_bits = 8
        elif context.format == AV_SAMPLE_FMT_S16:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_S16
            info.u.audio.sample_bits = 16
        elif context.format == AV_SAMPLE_FMT_S16P:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_S16P
            info.u.audio.sample_bits = 16
        elif context.format == AV_SAMPLE_FMT_S32:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_S32
            info.u.audio.sample_bits = 32
        elif context.format == AV_SAMPLE_FMT_S32P:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_S32P
            info.u.audio.sample_bits = 32
        elif context.format == AV_SAMPLE_FMT_FLT:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_FLOAT
            info.u.audio.sample_bits = 16
        elif context.format == AV_SAMPLE_FMT_FLTP:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_FLTP
            info.u.audio.sample_bits = 16
        else:
            info.u.audio.sample_format = -1
            info.u.audio.sample_bits = -1
    else:
        info.type = AVBIN_STREAM_TYPE_UNKNOWN
    return info

def avbin_open_stream(file, index):
    if not 0 <= index < file.context.contents.nb_streams:
        raise FFmpegException('index out of range. '
            'Only {} streams.'.format(file.context.contents.nb_streams))
    codec_context = avcodec.avcodec_alloc_context3(None)
    if not codec_context:
        raise MemoryError('Could not allocate Codec Context.')
    result = avcodec.avcodec_parameters_to_context(
        codec_context,
        file.context.contents.streams[index].contents.codecpar)
    if result < 0:
        avcodec.avcodec_free_context(addressof(codec_context))
        raise FFmpegException('Could not copy the AVCodecContext.')
    codec = avcodec.avcodec_find_decoder(codec_context.contents.codec_id)
    if not codec:
        raise FFmpegException('No codec found for this media.')
    result = avcodec.avcodec_open2(codec_context, codec, None)
    if result < 0:
        raise FFmpegException('Could not open the media with the codec.')
    stream = AVbinStream()
    stream.format_context = file.context
    stream.codec_context = codec_context
    stream.type = codec_context.contents.codec_type
    stream.frame = avutil.av_frame_alloc()

    return stream

def avbin_close_stream(stream):
    if stream.frame:
        avutil.av_frame_free(addressof(stream.frame))
    avcodec.avcodec_free_context(addressof(stream.codec_context))

def avbin_seek_file(file, timestamp):
    flags = AVSEEK_FLAG_BACKWARD
    max_ts = file.context.contents.duration * AV_TIME_BASE
    result = avformat.avformat_seek_file(file.context, -1, 0, timestamp, max_ts, flags)
    if result < 0:
        # buf = create_string_buffer(128)
        # avutil.av_strerror(result, buf, 128)
        # descr = buf.value
        # raise FFmpegException('Error occured while seeking. ' +
        #                       descr.decode())
        return AVBIN_RESULT_ERROR

    for i in range(file.context.contents.nb_streams):   
        codec_context = file.context.contents.streams[i].contents.codec
        if codec_context and codec_context.contents.codec:
            avcodec.avcodec_flush_buffers(codec_context)
    
    return AVBIN_RESULT_OK

def avbin_read(file, packet):
    if file.packet:
        avcodec.av_packet_unref(file.packet) # Is it the right way to free it?
    else:
        file.packet = avcodec.av_packet_alloc()
    result = avformat.av_read_frame(file.context, file.packet)
    if result < 0:
        return AVBIN_RESULT_ERROR
    
    packet.timestamp = avutil.av_rescale_q(file.packet.contents.dts,
        file.context.contents.streams[file.packet.contents.stream_index].contents.time_base,
        AV_TIME_BASE_Q)
    tb = file.context.contents.streams[file.packet.contents.stream_index].contents.time_base
    packet.stream_index = file.packet.contents.stream_index
    packet.data = file.packet.contents.data
    packet.size = file.packet.contents.size
    return AVBIN_RESULT_OK

def avbin_decode_audio(stream, data_in, size_in, data_out, size_out):
    if stream.type != AVMEDIA_TYPE_AUDIO:
        raise FFmpegException('Trying to decode audio on a non-audio stream.')
    inbuf = create_string_buffer(size_in + FF_INPUT_BUFFER_PADDING_SIZE)
    memmove(inbuf, data_in, size_in)
    
    packet = AVPacket()
    avcodec.av_init_packet(byref(packet))
    packet.data.contents = inbuf
    packet.size = size_in

    got_frame = c_int(0)
    bytes_used = avcodec.avcodec_decode_audio4(
        stream.codec_context, 
        stream.frame, 
        byref(got_frame), 
        byref(packet))
    if (bytes_used < 0):
        buf = create_string_buffer(128)
        avutil.av_strerror(bytes_used, buf, 128)
        descr = buf.value
        raise FFmpegException('Error occured while decoding audio. ' +
                              descr.decode())
    plane_size = c_int(0)
    if got_frame:
        data_size = avutil.av_samples_get_buffer_size(
            byref(plane_size),
            stream.codec_context.contents.channels,
            stream.frame.contents.nb_samples,
            stream.codec_context.contents.sample_fmt,
            1)
        if data_size < 0:
            raise FFmpegException('Error in av_samples_get_buffer_size')
        if size_out.value < data_size:
            raise FFmpegException('Output audio buffer is too small for current audio frame!')

        channel_layout = avutil.av_get_default_channel_layout(stream.codec_context.contents.channels)
        sample_rate = stream.codec_context.contents.sample_rate
        sample_format = stream.frame.contents.format
        if sample_format in (AV_SAMPLE_FMT_U8, AV_SAMPLE_FMT_U8P):
            tgt_format = AV_SAMPLE_FMT_U8
        elif sample_format in (AV_SAMPLE_FMT_S16, AV_SAMPLE_FMT_S16P):
            tgt_format = AV_SAMPLE_FMT_S16
        elif sample_format in (AV_SAMPLE_FMT_S32, AV_SAMPLE_FMT_S32P):
            tgt_format = AV_SAMPLE_FMT_S32
        elif sample_format in (AV_SAMPLE_FMT_FLT, AV_SAMPLE_FMT_FLTP):
            tgt_format = AV_SAMPLE_FMT_S16
        else:
            raise FFmpegException('Audi format not supported.')

        swr_ctx = swresample.swr_alloc_set_opts(None, 
            channel_layout, tgt_format,  sample_rate,
            channel_layout, sample_format, sample_rate,
            0, None)
        if not swr_ctx or swresample.swr_init(swr_ctx) < 0:
            swresample.swr_free(swr_ctx)
            raise FFmpegException('Cannot create sample rate converter.')

        data_in = stream.frame.contents.extended_data
        p_data_out = cast(data_out, POINTER(c_uint8))
        len_data = swresample.swr_convert(swr_ctx, 
            byref(p_data_out), data_size, 
            data_in, stream.frame.contents.nb_samples)
        size_out.value = len_data * stream.codec_context.contents.channels * avutil.av_get_bytes_per_sample(tgt_format)
        swresample.swr_free(swr_ctx)
    else:
        size_out.value = 0
    return bytes_used



def avbin_decode_video(stream, data_in, size_in, data_out):
    picture_rgb = AVPicture()
    width = stream.codec_context.contents.width
    height = stream.codec_context.contents.height
    if stream.type != AVMEDIA_TYPE_VIDEO:
        raise FFmpegException('Trying to decode video on a non-video stream.')
    inbuf = create_string_buffer(size_in + FF_INPUT_BUFFER_PADDING_SIZE)
    memmove(inbuf, data_in, size_in)
    packet = AVPacket()
    avcodec.av_init_packet(byref(packet))
    packet.data.contents = inbuf
    packet.size = size_in
    got_picture = c_int(0)
    bytes_used = avcodec.avcodec_decode_video2(
        stream.codec_context, 
        stream.frame, 
        byref(got_picture), 
        byref(packet))
    if bytes_used < 0:
        raise FFmpegException('Error decoding a video packet.')
    if not got_picture:
        raise FFmpegException('No frame could be decompressed')
    

    avcodec.avpicture_fill(byref(picture_rgb), data_out, PIX_FMT_RGB24,
        width, height)
    
    # A bit useless as it is. Should make a class with img_convert_ctx as
    # attribute. Would just need to call sws_getCachedContext on it.
    # Once instance is deleted, should call sws_freeContext
    img_convert_ctx = POINTER(SwsContext)() 
    img_convert_ctx = swscale.sws_getCachedContext(img_convert_ctx,
        width, height, stream.codec_context.contents.pix_fmt,
        width, height, PIX_FMT_RGB24, SWS_FAST_BILINEAR, None, None, None)

    swscale.sws_scale(img_convert_ctx, 
                      cast(stream.frame.contents.data, 
                                  POINTER(POINTER(c_uint8))), 
                      stream.frame.contents.linesize,
                      0, 
                      height, 
                      picture_rgb.data, 
                      picture_rgb.linesize)
    swscale.sws_freeContext(img_convert_ctx)
    return bytes_used

def avbin_set_log_level(dummy):
    pass
